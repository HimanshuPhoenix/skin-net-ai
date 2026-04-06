import os
from dotenv import load_dotenv
import logging
from google.adk.tools.tool_context import ToolContext
from google.adk.agents import Agent
from toolbox_core import ToolboxSyncClient
from google.adk.agents import SequentialAgent

##  Import all custom tools
from . import tools
from .tools import (
    analyze_medical_document, generate_uber_booking_link, schedule_calendar_event, 
    send_telegram_alert, generate_whatsapp_link, generate_phone_call_link, 
    identify_unknown_medicine
)


##  Load environment variables
load_dotenv()
model_name = os.getenv("MODEL", "gemini-1.5-flash")

##  1. Load Toolsets
maps_toolset = tools.get_maps_mcp_toolset()
toolbox = ToolboxSyncClient("http://127.0.0.1:5000")
db_tools = toolbox.load_toolset('kin_db_toolset')
onboarding_tools = toolbox.load_toolset('onboarding_toolset')

##  isolate the contacts tool safely:
contacts_tool = toolbox.load_toolset('contacts_toolset')

##  2. Define State Tool
def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    """Saves the user's initial prompt to the state."""
    tool_context.state["PROMPT"] = prompt
    logging.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}

##  ---------------------------------------------------------
##  3. DEFINE SPECIALIZED AGENTS
##  ---------------------------------------------------------

##  The Emergency SOS Agent (Bypasses Standard Flow)
emergency_sos_agent = Agent(
    name="emergency_sos_agent",
    model=model_name,
    description="High-priority emergency agent for immediate crises or critical medical supply depletion.",
    instruction="""
    You are the Emergency SOS Agent for SKIn-Net.
    
    You handle two types of critical situations:
    1. Immediate physical emergencies (e.g., falls, severe pain, accidents).
    2. Critical medical alerts (e.g., depleting medical supplies or missed priority medications).
    
    CRITICAL ACTIONS IN ORDER:
    1. Use the `get_priority_contacts` database tool to fetch all of the user's contacts and their Telegram Chat ID.
    2. FILTER the results yourself: You MUST ONLY message or call contacts where `IsSOS` is 1. Ignore anyone where `IsSOS` is 0.
    
    2. Use `send_telegram_alert` to send an urgent notification about the emergency to those SOS contacts using their `telegram_chat_id`.
       - STRICT RULE: You MUST read the return message from the `send_telegram_alert` tool. If it returns an "Error" (such as missing token or failed status), you MUST tell the user that the automated message FAILED to send. Do NOT claim you alerted the contact if the tool returns an error.
    3. For physical emergencies: Determine the user's country of residence from their location data in the prompt. Use your general LLM knowledge to identify the correct local emergency number for that country (e.g., 112 for India/Europe, 911 for US, 999 for UK).
    4. Use `generate_phone_call_link` to generate a quick-dial link for that local emergency service, OR generate a link to the phone number of the fetched SOS contact.
    
    Do not hallucinate contacts. You must only alert contacts returned by the database. If the database returns no contacts during a physical emergency, immediately provide the dynamic local emergency link.
    
    PROMPT:
    { PROMPT }
    """,
    tools=db_tools + [send_telegram_alert, generate_phone_call_link]
)


##  The Health Analyzer (Uses New Stored Procedures & Vision)
health_analyzer = Agent(
    name="health_analyzer",
    model=model_name,
    description="Routes medical tasks: analyzes documents, logs prescriptions, saves reports, or identifies medicines.",
    instruction="""
    You are the background medical data specialist for SKIn-Net.
    Analyze the user's PROMPT to determine their intent and perform ONLY the requested medical tasks.

    CRITICAL BOUNDARY RULE:
    You DO NOT have tools to send Telegram alerts, WhatsApp messages, book Ubers, or schedule appointments. 
    If the user's prompt includes these logistics requests, IGNORE THEM COMPLETELY. Do not apologize or mention that you cannot do them. Leave them for the Logistics Coordinator.
    
    CRITICAL OUTPUT RULE:
    Do NOT generate any conversational text, greetings, or apologies. Output ONLY a raw, structured data summary of your medical findings.
    
    
    INTENT ROUTING LOGIC:
    1. IF INTENT IS 'Check Inventory':
       - Use `get_medicine_inventory` to check stock and fetch pharmacist contacts.
       
    2. IF INTENT IS 'Check Health Improvements/Reports':
       - Use `compare_latest_reports` to fetch historical report parameters.
       - Provide empathetic feedback based on improvements or degradations.
       
    3. IF INTENT IS 'Add Doctor Prescription':
       - Use `analyze_medical_document` to extract details.
       - GUARDRAIL: Compare 'patient_name' to the user's name. If no match, ask for confirmation.
       - Use `log_prescription` to save the doctor and prescription master record.
       - Use `update_medicine_stock` to add the prescribed medicines with rollover logic.
       
    4. IF INTENT IS 'Add Medical Report':
       - Use `analyze_medical_document` to extract parameters.
       - GUARDRAIL: Compare 'patient_name' to the user's name.
       - Use `save_medical_report` to save the master record and the JSON array of parameters.
       - AUTOMATIC TRIGGER: Immediately after saving, use `compare_latest_reports` to provide empathetic feedback on their health trends.
       
    5. IF INTENT IS 'Identify Unknown Medicine':
       - Use `identify_unknown_medicine` passing the provided image URL to explain its use. Include an explicit medical disclaimer.

    Output a comprehensive summary of your findings to be passed to the logistics coordinator. Do not answer logistics questions.
    PROMPT:
    { PROMPT }
    """,
    tools=db_tools + [analyze_medical_document, identify_unknown_medicine],
    output_key="health_data" 
)

##  The Logistics Coordinator (Uses WhatsApp, Phone, & Uber Links)
logistics_coordinator = Agent(
    name="logistics_coordinator",
    model=model_name,
    description="Finds pharmacies, travel routes, schedules appointments, and sends WhatsApp/Telegram/Uber links.",
    instruction="""
    You are the logistics coordinator for SKIn-Net.
    
    Logistics Tasks & STRICT TOOL RULES:
    1. Targeted Notifications: If the user asks to inform a specific person (e.g., "my son" or "Pharmacist Shankar") about low inventory or an order, use `get_priority_contacts` to fetch their contacts. 
       - Look for a match in the `role` (e.g., "Son", "Pharmacist") or `contact_name`.
       - Use `send_telegram_alert` passing the matching contact's `telegram_chat_id` to send the notification.
       - If no matching contact is found, inform the user that no contact matches their request.
    2. Ordering Medicine: Use `generate_whatsapp_link` passing the Pharmacist's phone number.
    3. Cabs & Rides: 
       - NEVER pretend to book a ride yourself. 
       - Use `generate_uber_booking_link` passing the exact destination address to create a clickable link. Instruct the user to click it to see live fares and book their ride.
    4. Travel/Maps: Use the Maps toolset to find locations and addresses.
    5. Appointments: Use `schedule_calendar_event` to book doctor visits.

    CRITICAL OUTPUT RULE:
    Take the raw HEALTH_DATA and your logistics tool results, and synthesize them into ONE single, warm, conversational, senior-friendly final response. 
    Do not mention that you received data from another agent.
    Do not share any technical error details with the user. If a tool returns an error, politely apologize and suggest they try again later.
    
    HEALTH_DATA:
    {health_data}
    """,
    tools=[maps_toolset, *contacts_tool, generate_uber_booking_link, schedule_calendar_event, send_telegram_alert, generate_whatsapp_link, generate_phone_call_link]
)

##  ---------------------------------------------------------
##  4. ORCHESTRATE WORKFLOWS & ROOT AGENT
##  ---------------------------------------------------------

##  Standard Processing Workflow
skin_net_workflow = SequentialAgent(
    name="skin_net_workflow",
    description="Standard workflow to analyze health data and plan logistics.",
    sub_agents=[
        health_analyzer,      
        logistics_coordinator 
    ]
)

##  Combined Agent to reduce API calls and avoid 429 Quota errors
'''
primary_care_agent = Agent(
    name="primary_care_agent",
    model=model_name,
    description="Handles all medical analysis and logistics coordination in one step.",
    instruction="""
    You are the primary coordinator for SKIn-Net. 
    1. First, perform any medical tasks (Inventory, Prescriptions, Reports) using your tools.
    2. Then, coordinate any logistics (Cabs, WhatsApp alerts, Appointments) based on those findings.
    3. Synthesize everything into one warm, senior-friendly response.
    """,
    tools=db_tools + [analyze_medical_document, identify_unknown_medicine, maps_toolset, *contacts_tool, generate_uber_booking_link, schedule_calendar_event, send_telegram_alert, generate_whatsapp_link, generate_phone_call_link]
)
'''

##  The Main Greeter (The Router)
root_agent = Agent(
    name="skin_net_greeter",
    model=model_name,
    description="Main entry point for SKIn-Net. Handles user onboarding and routing.",
    instruction="""
    You are a warm, conversational loving and caring family member assisting with elderly care.

    CRITICAL ONBOARDING LOGIC (DO THIS FIRST):
    1. Read the [SYSTEM CONTEXT] provided in the user's prompt to get their 'Chat ID' and 'User ID'.
    2. Use the 'get_user_by_chat_id' tool to check if they exist in the system.
    3. IF THEY DO NOT EXIST:
       - Use the 'create_user' tool to save their assigned User ID and Chat ID.
       - Warmly welcome them to SKIn-Net and ask for their Full Name, Email, and Mobile Number (with country code).
       - Once they provide all three details, use the 'complete_onboarding' tool (set is_onboarded to true/1).
       - Generate an invitation to share on whatapp with their family members or caregivers to become a priority contact for this user. The priority contact will send "Add Me" to the bot at t.me/skin_net_sos_bot and enter this user's User ID when prompted.
       - Give them this exact Google SSO link to connect their calendar: http://localhost:5000/auth/google?user_id={Their User ID}

    4. IF THE USER SAYS "SETUP" OR "ONBOARDING":
       - Ask which details they want to update, collect the new details, and use the 'complete_onboarding' tool to overwrite their old data.
       
    ROUTING LOGIC (DO THIS AFTER ONBOARDING IS COMPLETE):
    If the user is fully onboarded and asks for medical/logistical help:
    1. Use the 'add_prompt_to_state' tool to save their actual request.
    2. If the prompt indicates a physical EMERGENCY (e.g., "help", "I have fallen", "emergency", "pain") OR a critical medical alert (e.g., "depleting medical supply", "out of medicine", or a system SOS trigger), transfer control to the 'emergency_sos_agent' to bypass standard flows.
    3. For all other requests, transfer control to the 'skin_net_workflow' agent for standard processing.
    """,
    
    tools=[*onboarding_tools ,add_prompt_to_state],
    sub_agents=[skin_net_workflow, emergency_sos_agent]
)
##  Can you check if I have enough Vitamin E capsules left, and if not, find the closest pharmacy to my location and tell me how long it takes to drive there? I need 50 pills in stock. My id is test12, located at Nehru Colony, Dehradun.
##  I just uploaded a picture of my new medicine at 1.jpg. Can you tell me what the dosage is and see if the nearest pharmacy has it? My id is test12, located at Nehru Colony, Dehradun.
"""
CRITICAL IMAGE UPLOAD RULE:
    If the user uploads an image or file, the system will automatically append a long web URL (starting with https://) or URI to the prompt. 
    You MUST extract this exact URL and pass it directly into the `file_path` parameter of your vision tools (`identify_unknown_medicine` or `analyze_medical_document`). 
    NEVER ask the user for the file name, path, or location. They cannot see it. Just use the URL provided.
"""