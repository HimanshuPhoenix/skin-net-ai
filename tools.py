import logging
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from toolbox_core import ToolboxSyncClient
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.utilities.arxiv import ArxivAPIWrapper

# 1. State Memory Tool
def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    """Saves the user's initial prompt to the state."""
    tool_context.state["PROMPT"] = prompt
    logging.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}

# 2. Wikipedia Fallback Tool
wikipedia_tool = LangchainTool(
    tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
)

# 3. Below your Wikipedia tool, add the arXiv tool
arxiv_tool = LangchainTool(
    tool=ArxivQueryRun(api_wrapper=ArxivAPIWrapper())
)

# MCP Toolbox for Databases (MySQL)
# Connects to the local MCP Toolbox server running on port 5000
toolbox = ToolboxSyncClient("http://127.0.0.1:5000")
db_tools = toolbox.load_toolset('research_db_toolset')

