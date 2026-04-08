import os
import json
import logging
import urllib.parse
import requests
import mimetypes
import dotenv
from google import genai
from google.genai import types
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
import urllib.parse
import datetime
import traceback
import google.oauth2.credentials
import google.auth.transport.requests

from toolbox_core import ToolboxSyncClient 
mcp_client = ToolboxSyncClient("http://127.0.0.1:5000")
MODEL_NAME = os.getenv("MODEL", "gemini-3.0-flash")
def send_telegram_alert(message: str, chat_id: str) -> str:
    """Sends an urgent health or logistics alert to a family member via Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return "Error: Telegram Bot Token not configured."
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logging.info(f"Telegram alert sent to {chat_id}")
            return "Alert sent successfully."
        else:
            return f"Failed to send alert. Status: {response.status_code}"
    except Exception as e:
        return f"Error sending message: {str(e)}"

def get_maps_mcp_toolset():
    """Configures the MCP Toolset for Google Maps."""
    dotenv.load_dotenv()
    maps_api_key = os.getenv('MAPS_API_KEY', 'no_api_found')
    maps_mcp_url = os.getenv('MAPS_MCP_URL')
    
    tools = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=maps_mcp_url,
            headers={"X-Goog-Api-Key": maps_api_key}
        )
    )
    return tools

def analyze_medical_document(file_path: str) -> str:
    """Reads images or PDFs of prescriptions and lab tests, extracting the patient's name and report parameters."""
    client = genai.Client()
    file_path = file_path.strip('\"\'')
    # Dynamically guess the MIME type based on the file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/pdf" if file_path.lower().endswith('.pdf') else "image/jpeg"

    try:
        # 1. Google Cloud Storage
        if file_path.startswith("gs://"):
            document_part = types.Part.from_uri(file_uri=file_path, mime_type=mime_type)
            
        # 2. Web URLs & ADK Chat Attachments
        elif file_path.startswith("http://") or file_path.startswith("https://"):
            response = requests.get(file_path, timeout=15)
            response.raise_for_status()
            document_part = types.Part.from_bytes(data=response.content, mime_type=mime_type)
            
        # 3. Local Files
        else:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            document_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            
    except Exception as e:
        return f"Error loading document: {str(e)}"

    prompt = """
    You are a highly accurate medical assistant for SKIn-Net.
    Analyze this medical document and return ONLY a JSON object:
    {
      "patient_name": "Exact name of the patient on the document",
      "doctor_name": "Name of the doctor",
      "report_date": "YYYY-MM-DD",
      "parameters": [
        {"parameter_name": "name", "current_value": "value", "normal_range": "range"}
      ],
      "medicines": [
        {"medicine_name": "name", "dosage": "dosage"}
      ]
    }
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[document_part, prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return response.text
    except Exception as e:
        return f"TOOL_ERROR: AI Analysis failed. Details: {str(e)}"

def generate_uber_booking_link(destination_address: str) -> str:
    """
    Generates a real, clickable Uber Universal Link.
    When the user clicks this, it securely opens the Uber app on their device
    with the destination pre-filled, showing live fares and allowing them to book natively.
    """
    # URL encode the address so it safely parses in the browser
    encoded_destination = urllib.parse.quote(destination_address)
    
    # External Reference: Standard Uber Universal Link structure
    return f"https://m.uber.com/ul/?action=setPickup&pickup=my_location&dropoff[formatted_address]={encoded_destination}"


def generate_whatsapp_link(phone_number: str, message: str) -> str:
    """
    Generates a clickable WhatsApp link to send a prescription or order to a pharmacist.
    The frontend will display this link for the user to click and hit "Send".
    """
    encoded_message = urllib.parse.quote(message)
    clean_number = ''.join(filter(str.isdigit, phone_number))
    return f"https://wa.me/{clean_number}?text={encoded_message}"

def generate_phone_call_link(phone_number: str) -> str:
    """Generates a clickable tel: link to allow the user to call a saved contact."""
    return f"tel:{phone_number}"

def identify_unknown_medicine(file_path: str) -> str:
    """
    Use this tool when a user clicks a photo of a loose pill or unknown medicine.
    Identifies the medicine and returns its general uses alongside a medical disclaimer.
    """
    client = genai.Client()
    file_path = file_path.strip('\"\'')

    # Dynamically guess the MIME type based on the file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "image/jpeg"
        
    try:
        # 1. Google Cloud Storage (Natively supported by Vertex AI)
        if file_path.startswith("gs://"):
            image_part = types.Part.from_uri(file_uri=file_path, mime_type=mime_type)
            
        # 2. Web URLs & ADK Chat Attachments (Must be downloaded into memory first)
        elif file_path.startswith("http://") or file_path.startswith("https://"):
            response = requests.get(file_path, timeout=15)
            response.raise_for_status() # Ensure the download was successful
            image_part = types.Part.from_bytes(data=response.content, mime_type=mime_type)
            
        # 3. Local Files on your Hard Drive
        else:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            image_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            
    except Exception as e:
        return f"Error loading image: {str(e)}"
        
    prompt = """
    You are a highly accurate medical assistant for SKIn-Net.
    Identify this medicine or pill. If expiry date is available, also educate the user about it. If the medicine is already expire, alert the user. Provide its general medical uses, common name, 
    and an EXPLICIT medical disclaimer stating that this is an AI estimation and the user 
    MUST consult their doctor. Return as a clean JSON object.
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return response.text
    except Exception as e:
        return f"TOOL_ERROR: AI Analysis failed. Details: {str(e)}"


def schedule_calendar_event(user_id: str, event_title: str, start_time_iso: str, end_time_iso: str = " ", description: str = "") -> str:
    """Schedules an event on the user's connected Google Calendar via REST API."""
    try:
        # 1. BULLETPROOF DATETIME MATH: Handle missing or malformed end_time from the LLM
        if not end_time_iso or "T" not in end_time_iso:
            try:
                # Force strictly correct ISO parsing and add 1 hour automatically
                start_dt = datetime.datetime.fromisoformat(start_time_iso.replace('Z', '+00:00'))
                end_time_iso = (start_dt + datetime.timedelta(hours=1)).isoformat()
            except ValueError:
                return f"Error: start_time_iso '{start_time_iso}' is not a valid ISO format."

        # 2. STRICT MCP FETCH: Get Google Credentials
        credentials_string = None
        try:
            # Step A: Load the tool from the MCP server as a Python callable
            get_creds_tool = mcp_client.load_tool("get_google_credentials")
            
            # Step B: Execute the callable directly
            db_response = get_creds_tool(user_id=user_id)
            
            print(f"Raw MCP Response: {db_response}") # Helpful for debugging!
            
            # Step C: Parse the response
            # SQL tools typically return a JSON string or a direct Python list
            if isinstance(db_response, str):
                parsed_response = json.loads(db_response)
            else:
                parsed_response = db_response
                
            if isinstance(parsed_response, list) and len(parsed_response) > 0:
                credentials_string = parsed_response[0].get("google_credentials")
            elif isinstance(parsed_response, dict):
                # Handle nested dict structures if the toolbox wraps the result
                if "google_credentials" in parsed_response:
                    credentials_string = parsed_response.get("google_credentials")
                elif "result" in parsed_response and isinstance(parsed_response["result"], list):
                    credentials_string = parsed_response["result"][0].get("google_credentials")
                             
        except Exception as mcp_err:
            print(f"MCP Fetch Error: {mcp_err}")
            return f"Database Error: Failed to retrieve credentials via MCP Toolkit. Details: {mcp_err}"

        if not credentials_string:
            return "Error: The user has not connected their Google Calendar. Please ask them to click the Google SSO link to connect."
            
        # Safely handle the credentials whether MCP returns a string or a pre-parsed dictionary
        if isinstance(credentials_string, dict):
            creds_dict = credentials_string
        else:
            creds_dict = json.loads(credentials_string)
            
        # Reconstruct the Google Credentials object
        credentials = google.oauth2.credentials.Credentials(
            token=creds_dict.get("token"),
            refresh_token=creds_dict.get("refresh_token"),
            token_uri=creds_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=creds_dict.get("client_id"),
            client_secret=creds_dict.get("client_secret")
        )

        # FORCE REFRESH: Guarantee a 100% fresh token directly before calling the API
        if credentials.refresh_token:
            print("Refreshing token automatically to bypass 401 error...")
            credentials.refresh(google.auth.transport.requests.Request())
            
        # STRIP UTC MARKERS: Google Calendar rejects 'Z' if timeZone is specified
        start_time_iso = start_time_iso.replace("Z", "")
        end_time_iso = end_time_iso.replace("Z", "")
        
        # 3. Make Request to Google Calendar API using the guaranteed fresh token
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
        event_data = {
            "summary": event_title,
            "description": description,
            "start": {"dateTime": start_time_iso, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time_iso, "timeZone": "Asia/Kolkata"}
        }
        
        print(f"\n--- CALENDAR DEBUG --- \nSending Payload: {event_data}\n----------------------\n") 
        
        response = requests.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers=headers,
            json=event_data
        )
        
        if response.status_code == 200:
            print(f"CALENDAR SUCCESS: Scheduled {event_title}")
            return f"Successfully scheduled '{event_title}' on Google Calendar."
        else:
            print(f"GOOGLE API ERROR: {response.text}")
            return f"Google Calendar API Error: {response.text}"
            
    except Exception as e:
        print(f"CRITICAL CALENDAR EXCEPTION:\n{traceback.format_exc()}")
        return f"Failed to schedule event due to a system error: {str(e)}"