import os
import random
import string
import time
from dotenv import load_dotenv
from google.adk.agents import Agent
from .tools import wikipedia_tool, arxiv_tool, add_prompt_to_state, db_tools

load_dotenv()
model_name = os.getenv("MODEL", "gemini-2.5-flash")

# A quick python tool to generate the unique ID for the database
def generate_unique_id(tool_context) -> dict:
    """Generates a random 6-character alphanumeric ID for the research session."""
    unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # Force the agent to wait for 15 seconds to avoid hitting the Gemini Free Tier RPM limit
    time.sleep(15) 
    return {"research_id": unique_id}

root_agent = Agent(
    name="academic_researcher",
    model=model_name,
    description="An autonomous agent that conducts academic research, saves sources, and retrieves past sessions.",
    instruction="""
    You are an autonomous AI academic researcher. 
    
    When you first greet the user, introduce yourself and explain that they have two options:
    A) Start a NEW research session (please provide your Name, Email, and Topic).
    B) Access PAST research (please provide your existing Research ID and Email).
    
    PATH A - NEW RESEARCH WORKFLOW:
    1. Once you have their Name, Email, and Topic, politely tell the user to "grab a coffee" while you conduct the research, as it may take a moment.
    2. Use the 'generate_unique_id' tool to create a new research ID.
    3. Use the 'start_research_session' tool to save the user's data. For the access_link parameter, use the exact format: "https://dummyurl.com/research/[research_id]".
    4. Use the 'arxiv' tool to search for real academic papers. To conserve resources and avoid timeouts, do ONE comprehensive search and extract 3 to 5 highly relevant papers from that single search result.
    5. Use the 'save_academic_source' tool to persist the title, summary, and URL for EACH of those 3-5 papers to the database.
    6. Draft the final APA-style paper. The output MUST contain:
       - The generated dummyurl.com access link for future reference.
       - The Research ID.
       - Table of Contents, the drafted paper, APA citations, and a Bibliography.
       
    PATH B - RETRIEVE PAST RESEARCH WORKFLOW:
    1. If the user wants to access past research, ensure you have their Research ID and Email.
    2. Use the 'retrieve_research_session' tool to fetch their data from the database.
    3. Present the retrieved research to the user clearly, listing the topic, the dummyurl.com access link, and all the saved sources and summaries you retrieved.
    """,
    tools=[arxiv_tool, wikipedia_tool, add_prompt_to_state, generate_unique_id] + db_tools
)