import os
import time
import requests
import mimetypes
from dotenv import load_dotenv
import json

load_dotenv()
MAIN_BOT_TOKEN = os.getenv("TELEGRAM_MAIN_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}"
TELEGRAM_FILE_URL = f"https://api.telegram.org/file/bot{MAIN_BOT_TOKEN}"

BASE_URL = "http://127.0.0.1:8000"
APP_NAME = "skin-net-ai"

## Ensure a local directory exists to save downloaded Telegram images locally
if not os.path.exists("downloads"):
    os.makedirs("downloads")

def download_telegram_file(file_id: str, file_name: str) -> str:
    """Securely downloads an image from Telegram's servers to the local disk."""
    try:
        file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
        response = requests.get(file_info_url).json()
        if not response.get("ok"): return None
        
        file_path = response["result"]["file_path"]
        download_url = f"{TELEGRAM_FILE_URL}/{file_path}"
        img_data = requests.get(download_url).content
        
        # ADK fileUri requires the absolute local path to process the image
        local_path = os.path.abspath(os.path.join("downloads", file_name))
        with open(local_path, "wb") as f:
            f.write(img_data)
            
        return local_path
    except Exception as e:
        print(f"Download Error: {e}")
        return None

def send_reply(chat_id: str, text: str):
    """Sends the response back to the user robustly."""
    try:
        # FIX: Removed parse_mode="Markdown" so LLM-generated underscores (like in kin_8130...) 
        # don't cause Telegram to silently reject the message.
        requests.post(
            f"{TELEGRAM_API_URL}/sendMessage", 
            json={"chat_id": chat_id, "text": text},
            # FIX: Force a fresh socket connection to prevent 10054 errors
            headers={"Connection": "close"}, 
            timeout=15
        )
    except Exception as e:
        print(f"Failed to send message: {e}")

def poll_main_bot():
    print("🚀 Starting SKIn-Net Main User Bot with SSE Streaming...")
    update_id = None
    
    while True:
        try:
            url = f"{TELEGRAM_API_URL}/getUpdates?timeout=180"
            if update_id: 
                url += f"&offset={update_id}"
                
            response = requests.get(url, timeout=200).json()
            
            for result in response.get("result", []):
                update_id = result["update_id"] + 1
                message = result.get("message", {})
                chat_id = str(message.get("chat", {}).get("id", ""))
                
                if not chat_id: continue

                # 1. EXTRACT BOTH TEXT AND IMAGES SAFELY
                text_content = message.get("text", "")
                caption = message.get("caption", "")
                prompt_text = text_content or caption
                
                photos = message.get("photo", [])
                document = message.get("document")
                
                if not prompt_text.strip() and not photos and not document: 
                    continue

                print(f"Processing Request for {chat_id}...")

                uid = f"SK{chat_id}"
                contextual_prompt = f"[SYSTEM CONTEXT: The user's Telegram Chat ID is {chat_id} and their assigned User ID is {uid}.] \n\nUser says: {prompt_text}"
                
                # FIX 3: Handle both Images and Documents
                local_path = None
                if photos:
                    file_id = photos[-1]["file_id"]  # -1 grabs the highest resolution version
                    file_name = f"{file_id}.jpg"
                    local_path = download_telegram_file(file_id, file_name)
                elif document:
                    file_id = document["file_id"]
                    file_name = document.get("file_name", f"{file_id}.pdf")
                    local_path = download_telegram_file(file_id, file_name)
                    
                if local_path:
                    # FIX 4: Sanitize Windows paths to prevent JSON escape character corruption
                    safe_path = local_path.replace("\\", "/")
                    contextual_prompt += f"\n\n[ATTACHED FILE PATH: {safe_path}]"

                session_url = f"{BASE_URL}/apps/{APP_NAME}/users/{uid}/sessions/{chat_id}"
                
                # FIX 5: Remove "Connection: close" to allow SSE streaming to stay alive
                adk_headers = {"Accept": "text/event-stream"}
                
                try:
                    check_session = requests.get(session_url, headers=adk_headers, timeout=10)
                    if check_session.status_code == 404: 
                        requests.post(session_url, headers=adk_headers, json={}, timeout=10)
                        
                    run_url = f"{BASE_URL}/run_sse"
                    adk_payload = {
                        "appName": APP_NAME,
                        "userId": uid,
                        "sessionId": str(chat_id),
                        "newMessage": {
                            "role": "user",
                            "parts": [{"text": contextual_prompt}] # <-- Now passing only the text array!
                        }
                    }
                    
                    # stream=True forces Python to constantly read the real-time data, keeping the TCP socket alive
                    #adk_response = requests.post(run_url, json=adk_payload, headers=adk_headers, stream=True, timeout=180)
                    # FIX: Increased timeout to 300 to survive temporary GCP quota backoffs
                    adk_response = requests.post(run_url, json=adk_payload, headers=adk_headers, stream=True, timeout=300)
                    
                    if adk_response.status_code == 200:
                        reply_text = ""
                        
                        # Loop over the continuous Server-Sent Events (SSE) chunks
                        for line in adk_response.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                
                                if decoded_line.startswith("data: "):
                                    data_str = decoded_line[6:].strip()
                                    if data_str == "[DONE]":
                                        break
                                    try:
                                        msg = json.loads(data_str)
                                        # Safely extract and accumulate the streamed text tokens
                                        msg_parts = msg.get("content", {}).get("parts", [])
                                        for part in msg_parts:
                                            if "text" in part:
                                                reply_text += part["text"]
                                    except (json.JSONDecodeError, KeyError, TypeError):
                                        continue
                                        
                        final_text = reply_text.strip()
                        if not final_text:
                            final_text = "I am processing your medical data right now..."
                            
                        send_reply(chat_id, final_text)
                    else:
                        send_reply(chat_id, f"API Error: {adk_response.status_code} - {adk_response.text}")
                        
                except Exception as e:
                    print(f"ADK API Error: {e}")
                    send_reply(chat_id, "The medical assistant is experiencing a brief delay due to heavy data processing. Please try again.")

        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.ReadTimeout:
            pass
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    poll_main_bot()