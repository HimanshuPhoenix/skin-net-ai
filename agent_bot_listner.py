import os
from dotenv import load_dotenv
import logging
from google.adk.tools.tool_context import ToolContext
from google.adk.agents import Agent, SequentialAgent
from toolbox_core import ToolboxSyncClient

# Import tools
from . import tools
from .tools import (
    analyze_medical_document,
    generate_uber_booking_link,
    schedule_calendar_event,
    send_telegram_alert,
    generate_whatsapp_link,
    generate_phone_call_link,
    identify_unknown_medicine
)

# Load env
load_dotenv()
model_name = os.getenv("MODEL", "gemini-2.5-flash")

# Load toolsets
maps_toolset = tools.get_maps_mcp_toolset()
toolbox = ToolboxSyncClient("http://127.0.0.1:5000")
db_tools = toolbox.load_toolset("kin_db_toolset")

# =========================================================
# STATE TOOL
# =========================================================

def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict:
    if prompt and not prompt.startswith("Handle the requests"):
        tool_context.state["PROMPT"] = prompt

        if "chat_id" in tool_context.state:
            tool_context.state["CHAT_ID"] = tool_context.state["chat_id"]

        logging.info(f"[STATE] USER PROMPT: {prompt}")
    else:
        logging.warning(f"[STATE] Ignored system prompt: {prompt}")

    return {"status": "success"}


# =========================================================
# EMERGENCY AGENT
# =========================================================

emergency_sos_agent = Agent(
    name="emergency_sos_agent",
    model=model_name,
    description="Handles emergencies",
    instruction="""
You are the Emergency SOS Agent.

If user expresses emergency (help, pain, fallen, urgent):

1. Call get_priority_contacts
2. Filter contacts where IsSOS = 1
3. Call send_telegram_alert for those contacts
4. Generate emergency call link using generate_phone_call_link

If no contacts:
- provide emergency number (112 for India)

ALWAYS return a clear response:
"🚨 Emergency detected. I've alerted your SOS contacts."

Use the user's latest message from context.
""",
    tools=db_tools + [send_telegram_alert, generate_phone_call_link],
)

# =========================================================
# HEALTH ANALYZER
# =========================================================

health_analyzer = Agent(
    name="health_analyzer",
    model=model_name,
    description="Handles medical tasks",
    instruction="""
You are the medical assistant.

Understand user intent and act:

1. Inventory - call get_medicine_inventory
2. Reports - call compare_latest_reports
3. Prescription - analyze + log + update inventory
4. Image - use identify_unknown_medicine

If image URL present - pass directly to tool.

If unclear - ask clarification.

ALWAYS return meaningful explanation to user.
""",
    tools=db_tools + [analyze_medical_document, identify_unknown_medicine],
    output_key="health_data",
)

# =========================================================
# LOGISTICS AGENT
# =========================================================

logistics_coordinator = Agent(
    name="logistics_coordinator",
    model=model_name,
    description="Handles logistics",
    instruction="""
You are logistics coordinator.

Tasks:
- Notify contacts - send_telegram_alert
- Order medicine - generate_whatsapp_link
- Travel - generate_uber_booking_link
- Appointments - schedule_calendar_event

Use HEALTH_DATA to respond.

ALWAYS return final friendly response.
""",
    tools=[
        maps_toolset,
        generate_uber_booking_link,
        schedule_calendar_event,
        send_telegram_alert,
        generate_whatsapp_link,
        generate_phone_call_link,
    ],
)

# =========================================================
# WORKFLOW
# =========================================================

skin_net_workflow = SequentialAgent(
    name="skin_net_workflow",
    description="Main workflow",
    sub_agents=[health_analyzer, logistics_coordinator],
)

# =========================================================
# ROOT AGENT (IMPORTANT)
# =========================================================

root_agent = Agent(
    name="skin_net_root",
    model=model_name,
    description="Main entry point",
    instruction="""
You are SKIN Net AI, a helpful healthcare assistant.

IMPORTANT FLOW:

STEP 1:
CRITICAL:

- Extract the USER'S ACTUAL MESSAGE
- Pass ONLY that exact message to add_prompt_to_state
- DO NOT pass system instructions or context

Example:
User says: "help"
- pass "help" to add_prompt_to_state, NOT the entire prompt or system instructions.

STEP 2:
Decide routing:

Use PROMPT from state ONLY.

If PROMPT contains:
- help
- emergency
- pain
- fallen
- emergency_sos_agent

Else:
- skin_net_workflow

STEP 3:
ALWAYS return final response to user.
""",
    tools=[add_prompt_to_state],
    sub_agents=[skin_net_workflow, emergency_sos_agent],
)
# Can you check if I have enough Vitamin E capsules left, and if not, find the closest pharmacy to my location and tell me how long it takes to drive there? I need 50 pills in stock. My id is test12, located at Nehru Colony, Dehradun.
# I just uploaded a picture of my new medicine at 1.jpg. Can you tell me what the dosage is and see if the nearest pharmacy has it? My id is test12, located at Nehru Colony, Dehradun.