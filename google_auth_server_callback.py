import mysql.connector
from googleapiclient.discovery import build
from flask import redirect

@app.route("/callback")
def callback():
    # 'state' contains the user_id we passed from Telegram
    user_id = request.args.get("state") 
    
    # 1. Re-initialize the OAuth flow so the callback function knows what 'flow' is
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email", 
            "https://www.googleapis.com/auth/calendar", 
            "openid"
        ],
        state=user_id,
        redirect_uri="http://localhost:5050/callback"
    )
    
    # 2. Fetch OAuth token
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    
    # 3. Fetch the user's actual Google Email
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    user_email = user_info.get("email")
    
    # 4. Update the MySQL Database
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
        
    # 5. Redirect the user back to your Telegram Bot smoothly
    return redirect("https://t.me/skin_net_bot?start=welcome")