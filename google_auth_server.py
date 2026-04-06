from flask import Flask, request, redirect
from google_auth_oauthlib.flow import Flow
import os

app = Flask(__name__)

CLIENT_SECRETS_FILE = "client_secret.json"

@app.route("/auth/google")
def auth_google():
    user_id = request.args.get("user_id")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/calendar"
        ],
        redirect_uri="http://localhost:5000/callback"
    )

    auth_url, state = flow.authorization_url(
        state=user_id
    )

    return redirect(auth_url)

@app.route("/callback")
def callback():
    user_id = request.args.get("state")

    # TODO: extract email from token

    # call MCP tool OR store in DB

    return f"✅ Google connected for {user_id}"
    
app.run(port=5050)