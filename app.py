from flask import Flask, render_template, redirect, request, url_for, session
from database.connection import init_connection_engine, db
from sqlalchemy import text
import os
import pathlib
import requests
import random
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "supersecretkey"

init_connection_engine(app)

# @app.route("/test")
# def test():
#     result = db.session.execute(text("SELECT 1")).scalar()
#     print(f"Test Query: {result}")
    
# @app.route("/")
# def index():
#     return render_template("index.html")

# if __name__ == "__main__":
#     app.run(debug=True)


# ---------- GOOGLE OAUTH SETUP ----------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

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

    print(session["user"])

    # ✅ Always return something valid
    return redirect(url_for("index"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------- SPOONACULAR API SETUP ----------
API_KEY = os.getenv("API_KEY")
API_HOST = "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
API_URL = f"https://{API_HOST}"
SEARCH_URL = f"{API_URL}/recipes/complexSearch"
RECIPE_INFO_URL = f"{API_URL}/recipes/{{id}}/information"
JOKE_URL = f"{API_URL}/food/jokes/random"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST,
}

@app.route("/search_recipes")
def search_recipes():
    ingredients = request.args.get("ingredients", "")
    cuisine = request.args.get("cuisine", "")
    diet = request.args.get("diet", "")
    allergies = request.args.get("allergies", "")

    params = {
        "number": random.randint(10, 20),
        "includeIngredients": ingredients,
        "cuisine": cuisine,
        "diet": diet,
        "intolerances": allergies,
        "addRecipeInformation": True,
        "ignorePantry": False,
        "ranking": 2,
        "sort": "min-missing-ingredients",
        "offset": random.randint(1, 10)
    }

    try:
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

@app.route("/random_joke")
def random_joke():
    try:
        response = requests.get(JOKE_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        joke = data.get("text", "Why did the tomato turn red? Because it saw the salad dressing!")
        return {"joke": joke}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", user=user)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
