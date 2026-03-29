import os
from dotenv import load_dotenv
import logging
from google.adk.tools.tool_context import ToolContext
import google.auth
from google.adk.agents import Agent
from toolbox_core import ToolboxSyncClient
from google.adk.agents import SequentialAgent
from . import tools
from .tools import analyze_medicine_image

# Load environment variables
load_dotenv()
model_name = os.getenv("MODEL", "gemini-2.5-flash")

# Load the Maps Toolset
maps_toolset = tools.get_maps_mcp_toolset()

# 1. Connect to your local MCP Toolbox server
toolbox = ToolboxSyncClient("http://127.0.0.1:5000")

# 2. Load the MySQL toolset you defined in your tools.yaml
# (Ensure the toolset name matches exactly what is in your tools.yaml)
db_tools = toolbox.load_toolset('kin_db_toolset')

# Greet user and save their prompt
def add_prompt_to_state(
    tool_context: ToolContext, prompt: str
) -> dict[str, str]:
    """Saves the user's initial prompt to the state."""
    tool_context.state["PROMPT"] = prompt
    logging.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}

# 3. Create the SKIn-Net Agent
#  Health Analyzer Agent (Handles Vision & Database)
health_analyzer = Agent(
    name="health_analyzer",
    model=model_name,
    description="Analyzes medical images and checks user inventory.",
    instruction="""
    You are the medical data specialist for SKIn-Net.
    First, use the vision tool to read any provided prescription or medicine images.
    Second, use the database tool to check the user's current medicine inventory.
    Output a combined summary of what the user needs and what they currently have.
    
    PROMPT:
    { PROMPT }
    """,
    tools=db_tools + [analyze_medicine_image],
    output_key="health_data" 
)

#  Logistics Coordinator Agent (Handles Maps)
logistics_coordinator = Agent(
    name="logistics_coordinator",
    model=model_name,
    description="Finds pharmacies and travel routes.",
    instruction="""
    You are the logistics coordinator for SKIn-Net.
    Review the HEALTH_DATA. If the user is low on any medicine, use your Maps tool 
    to find the nearest pharmacy and calculate the driving route.
    Format a warm, conversational final response for the user, combining both 
    their health inventory status and the travel logistics.
    
    HEALTH_DATA:
    {health_data}
    """,
    tools=[maps_toolset]
)

#  Define the Workflow
skin_net_workflow = SequentialAgent(
    name="skin_net_workflow",
    description="Workflow to analyze health data and plan logistics.",
    sub_agents=[
        health_analyzer,      # Step 1: Read image and check DB
        logistics_coordinator # Step 2: Check Maps and format response
    ]
)

#  The Main Greeter Agent
root_agent = Agent(
    name="skin_net_greeter",
    model=model_name,
    description="Main entry point for SKIn-Net.",
    instruction="""
    You are a warm, conversational family member assisting with elderly care.
    When the user asks for help, use the 'add_prompt_to_state' tool to save their request.
    After using the tool, transfer control to the 'skin_net_workflow' agent.
    """,
    tools=[add_prompt_to_state],
    sub_agents=[skin_net_workflow]
)
# Can you check if I have enough Vitamin E capsules left, and if not, find the closest pharmacy to my location and tell me how long it takes to drive there? I need 50 pills in stock. My id is test12, located at Nehru Colony, Dehradun.
# I just uploaded a picture of my new medicine at 1.jpg. Can you tell me what the dosage is and see if the nearest pharmacy has it? My id is test12, located at Nehru Colony, Dehradun.