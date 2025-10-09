import os
import flask
from flask import redirect, request, url_for, session, Response
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests
import pathlib
import json

app = flask.Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_uri="http://localhost:5000/login/callback"  # Update for production
)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# def save_to_database(user_info):
#     google_id = user_info.get("id")
#     name = user_info.get("name")
#     email = user_info.get("email")

@app.route("/login")
def login():
    """Initiate Google OAuth login"""
    auth_url, state = flow.authorization_url(prompt="consent")
    session["state"] = state
    return redirect(auth_url)


@app.route("/login/callback")
def callback():
    """Handle OAuth callback from Google"""
    # Verify state to prevent CSRF attacks
    if session.get("state") != request.args.get("state"):
        return "Invalid state parameter", 400
    
    try:
    
        # Exchange authorization code for credentials
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        
        # Verify and decode the ID token
        request_session = google.auth.transport.requests.Request()
        user_info = id_token.verify_oauth2_token(
            credentials.id_token,
            request_session,
            GOOGLE_CLIENT_ID
        )
        # save_user_to_database(user_info)
        # Store user information in session
        session["user"] = {
            "id": user_info.get("sub"),
            "name": user_info.get("name"),
            "email": user_info.get("email"),
            "picture": user_info.get("picture"),
        }
        
        return redirect(url_for("index"))
    
    except Exception as e:
        return f"An error occurred: {e}", 500


@app.route("/logout")
def logout():
    """Logout user and clear session"""
    session.clear()
    return redirect(url_for("index"))

@app.route("/api/user")
def get_user():
    #API endpoint to get current user info (for frontend)
    if "user" not in session:
        return flask.Response(
            json.dumps({"error": "Not authenticated"}),
            status=401,
            mimetype='application/json'
        )
    
    return flask.Response(
        json.dumps(session["user"]),
        mimetype='application/json'
    )



if __name__ == "__main__":
    app.run("localhost", 5000)