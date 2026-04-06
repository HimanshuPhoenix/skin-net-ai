from flask import Flask, request, redirect, session
from google_auth_oauthlib.flow import Flow
import os
import mysql.connector
from googleapiclient.discovery import build

# BYPASS HTTPS REQUIREMENT FOR LOCAL OAUTH TESTING
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = Flask(__name__)

# 1. ADD THIS LINE: Flask requires a secret key to use 'session' memory
app.secret_key = "super_secret_key_for_testing"

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email", 
    "https://www.googleapis.com/auth/calendar", 
    "openid"
]

@app.route("/auth/google")
def auth_google():
    user_id = request.args.get("user_id") 
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=user_id,
        redirect_uri="http://localhost:5050/callback"
    )
    
    auth_url, state = flow.authorization_url(prompt='consent')
    
    # 2. SAVE THE CODE VERIFIER: Store it in the user's browser session before they leave
    session['code_verifier'] = flow.code_verifier
    
    return redirect(auth_url)


@app.route("/callback")
def callback():
    # 'state' contains the user_id we passed from Telegram
    user_id = request.args.get("state") 
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=user_id,
        redirect_uri="http://localhost:5050/callback"
    )
    
    # 3. RETRIEVE THE CODE VERIFIER: Load it back into the new Flow object
    flow.code_verifier = session.get('code_verifier')
    
    # 4. Fetch OAuth token (This will now succeed!)
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    
    # 5. Fetch the user's actual Google Email
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    user_email = user_info.get("email")
    
    # 6. Update the MySQL Database
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "skin_net")
        )
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET email = %s, google_connected = 1 
            WHERE user_id = %s
        """, (user_email, user_id))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return f"Authentication succeeded, but database update failed: {e}"
        
    # 7. Redirect the user back to your Telegram Bot smoothly
    return redirect("https://t.me/your_bot_username_here")

if __name__ == "__main__":
    app.run(port=5050)