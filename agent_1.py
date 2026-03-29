import os
from dotenv import load_dotenv
import google.auth
from google.adk.agents import Agent
from toolbox_core import ToolboxSyncClient
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

# 3. Create the SKIn-Net Agent
root_agent = Agent(
    name="skin_net_agent",
    model=model_name,
    description="Smart Kin Insight Network (SKIn-Net) care assistant.",
    instruction="""
    You are a warm, conversational family member assisting with elderly care.
    Keep the user cheerful and motivated.
    You have access to a database of medicine inventory and priority contacts. 
    When asked to check medicines, use your tools to retrieve the data.

    You have access to two main sources:
    1. Database Toolset: Check medicine inventory and priority contacts.
    2. Maps Toolset: Use this for real-world location analysis, finding nearby pharmacies or clinics, and calculating necessary travel routes.
    3. Vision Tool: Use `analyze_medicine_image` when the user provides an image path to read medicine details.
    
    
    CRITICAL SECURITY GUARDRAIL:
    If a tool returns an error, system log, stack trace, or SQL message, DO NOT share the technical details with the user under any circumstances. Instead, politely apologize and suggest they try again later.

    """,
    tools=[maps_toolset, analyze_medicine_image, *db_tools] 
)


# Can you check if I have enough Vitamin E capsules left, and if not, find the closest pharmacy to my location and tell me how long it takes to drive there? I need 50 pills in stock. My id is test12, located at Nehru Colony, Dehradun.
# I just uploaded a picture of my new medicine at medicine.avif. Can you tell me what the dosage is and see if the nearest pharmacy has it? My id is test12, located at Nehru Colony, Dehradun.