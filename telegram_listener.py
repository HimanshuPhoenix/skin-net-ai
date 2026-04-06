import os
import time
import requests
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Dictionary to track conversation state for each chat_id
# Format: { 'chat_id': {'step': 'WAITING_USERID', 'data': {}} }
user_states = {}

def register_contact_in_db(data, chat_id):
    """Saves the fully collected contact to the database."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"), user=os.getenv("DB_USER", "root"), 
            password=os.getenv("DB_PASSWORD", ""), database=os.getenv("DB_NAME", "skin_net")
        )
        cursor = conn.cursor()
        # Ensure SOS is stored as a tinyint (1 or 0)
        is_sos = 1 if data['sos'].lower() in ['yes', 'y', 'true', '1'] else 0
        cursor.callproc('sp_register_contact', (data['userid'], data['name'], data['type'], is_sos, chat_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False

def send_reply(chat_id, text):
    try:
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print(f"Failed to send message: {e}")

def poll_messages():
    print("Starting Stateful Telegram Listener...")
    update_id = None
    
    while True:
        try:
            url = f"{TELEGRAM_API_URL}/getUpdates?timeout=10"
            if update_id: url += f"&offset={update_id}"
            
            # ADDED: timeout=15 forces the socket to close if the network drops, preventing hangs
            response = requests.get(url, timeout=15).json()
                        
            for result in response.get("result", []):
                update_id = result["update_id"] + 1
                message = result.get("message", {})
                text = message.get("text", "").strip()
                chat_id = str(message.get("chat", {}).get("id", ""))
                
                # If user wants to start registration
                if text.lower() == "add me":
                    user_states[chat_id] = {'step': 'WAITING_USERID', 'data': {}}
                    send_reply(chat_id, "Let's get you registered! First, what is the Patient's User ID (e.g., test12)?")
                    continue
                
                # If we are currently tracking this user's state
                if chat_id in user_states:
                    state = user_states[chat_id]
                    
                    if state['step'] == 'WAITING_USERID':
                        state['data']['userid'] = text
                        state['step'] = 'WAITING_NAME'
                        send_reply(chat_id, "Got it. What is your Name (e.g., John Doe)?")
                        
                    elif state['step'] == 'WAITING_NAME':
                        state['data']['name'] = text
                        state['step'] = 'WAITING_PHONE'
                        send_reply(chat_id, f"Nice to meet you {state['data']['name']}! Please enter your Phone Number with country code (e.g., +1234567890)")
                    
                    elif state['step'] == 'WAITING_PHONE':
                        state['data']['phone'] = text
                        state['step'] = 'WAITING_TYPE'
                        send_reply(chat_id, "Thanks! What is your Contact Type/Role (e.g., Son, Pharmacist, Driver)?")
                        
                    elif state['step'] == 'WAITING_TYPE':
                        state['data']['type'] = text
                        state['step'] = 'WAITING_SOS'
                        send_reply(chat_id, "Finally, is this an SOS Contact for immediate emergencies? (Reply 'Yes' or 'No')")
                        
                    elif state['step'] == 'WAITING_SOS':
                        state['data']['sos'] = text
                        # Complete the registration!
                        if register_contact_in_db(state['data'], chat_id):
                            send_reply(chat_id, f"✅ Success! You are registered as '{state['data']['type']}' for user {state['data']['userid']}.")
                        else:
                            send_reply(chat_id, "❌ Registration failed due to an error. Type 'Add Me' to try again.")
                        # Clear state
                        del user_states[chat_id]

        except requests.exceptions.ReadTimeout:
            # Expected behavior if no messages arrive within the timeout period
            pass
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    poll_messages()