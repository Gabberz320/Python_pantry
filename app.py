from flask import Flask, render_template, redirect, request, url_for, session
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests
import os
import pathlib

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "supersecretkey"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # allow HTTP for local dev

# ---------------- LOGIN ----------------
@app.route("/login")
def login():
    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        redirect_uri=url_for("callback", _external=True),
    )
    auth_url, state = flow.authorization_url(prompt="consent")
    session["state"] = state
    return redirect(auth_url)


# ---------------- CALLBACK ----------------
@app.route("/login/callback")
def callback():
    # Validate the 'state' parameter
    if session.get("state") != request.args.get("state"):
        return "Invalid state parameter", 400

    # Rebuild flow with the same settings and redirect_uri
    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        redirect_uri=url_for("callback", _external=True),
    )

    # Exchange code for token
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    # Verify ID token and extract user info
    request_session = google.auth.transport.requests.Request()
    user_info = id_token.verify_oauth2_token(
        credentials.id_token,
        request_session,
        GOOGLE_CLIENT_ID,
    )

    # Store info in session
    session["user"] = {
        "id": user_info.get("sub"),
        "name": user_info.get("name"),
        "email": user_info.get("email"),
        "picture": user_info.get("picture"),
    }

    # ✅ Always return something valid
    return redirect(url_for("index"))


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------- HOME ----------------
@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", user=user)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
