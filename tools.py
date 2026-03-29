import os
import dotenv

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams 
import json
from google import genai
from google.genai import types


def get_maps_mcp_toolset():
    dotenv.load_dotenv()
    maps_api_key = os.getenv('MAPS_API_KEY', 'no_api_found')
    maps_mcp_url = os.getenv('MAPS_MCP_URL')
    
    tools = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=maps_mcp_url,
            headers={
                "X-Goog-Api-Key": maps_api_key
            }
        )
    )
    print("Maps MCP Toolset configured.")
    return tools

def analyze_medicine_image(image_path: str) -> str:
    """
    Use this tool to read an image of a medicine bottle or prescription.
    Pass the file path of the image to extract the medicine details.
    """
    client = genai.Client() # Assumes your environment credentials are set
    
    # Read the image file into bytes
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Define a strict prompt to extract structured JSON data
    prompt = """
    You are a highly accurate medical assistant for the SKIn-Net app.
    Analyze this medicine bottle or prescription and return ONLY a JSON object:
    {
      "medicine_name": "Exact name of the medicine",
      "dosage_instructions": "How and when to take it",
      "pills_count": "Estimated quantity or NA"
    }
    """
    
    # Call the model (using your working 2.5-flash model)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"), 
            prompt
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    
    return response.text