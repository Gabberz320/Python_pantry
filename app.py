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
import asyncio
import aiohttp


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "supersecretkey"

init_connection_engine(app)

# Load environment variables from a .env file (if present)
load_dotenv()

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

# Timeout (seconds) for external API calls to avoid hanging the Flask worker
REQUEST_TIMEOUT = 10

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST,
}

if not API_KEY:
    # Helpful runtime message for debugging missing API key (do not log sensitive values)
    print("WARNING: API_KEY environment variable is not set. Requests to the Spoonacular/RapidAPI endpoint will fail with 401 Unauthorized.")
    
async def is_valid_link(session, url, timeout=1):
    if not url:
        return False
    try:
        # Use aiohttp's timeout object
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with session.head(url, timeout=client_timeout, allow_redirects=True) as response:
             if response.status < 400:
                 return True
             else: 
                 return False
    # This line is for catching any network errors connecting to a link
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False
    

async def filter_links(recipes):
    valid_recipes = []
    async with aiohttp.ClientSession() as session:
        # Create a list of tasks, checking the links of each recipe returned from the API
        tasks = []
        for recipe in recipes:
            task = asyncio.create_task(is_valid_link(session, recipe.get("sourceUrl")))
            tasks.append((task, recipe))
        
        # Waits for all the tasks to complete
        for task, recipe in tasks:
            is_valid = await task
            if is_valid:
                valid_recipes.append(recipe)
    
    return valid_recipes

@app.route("/search_recipes")
def search_recipes():
    ingredients = request.args.get("ingredients", "")
    cuisine = request.args.get("cuisine", "")
    diet = request.args.get("diet", "")
    allergies = request.args.get("allergies", "")

    # Fail fast if API key missing
    if not API_KEY:
        return {"error": "Server misconfiguration: API_KEY is not set."}, 500

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
        response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        initial_recipes = response.json().get("results", [])
        
        
        valid_recipes = asyncio.run(filter_links(initial_recipes))
        
        return valid_recipes
    except requests.exceptions.Timeout:
        # Upstream timed out
        app.logger.warning("Timeout when calling Spoonacular API for search_recipes")
        return {"error": "Upstream API request timed out."}, 504
    except requests.exceptions.HTTPError as e:
        # Return the upstream status code & message as a 502-level error
        status = getattr(e.response, 'status_code', 502)
        app.logger.warning(f"HTTP error from Spoonacular: {status} - {e}")
        return {"error": f"Upstream service returned HTTP {status}."}, 502
    except requests.exceptions.RequestException as e:
        app.logger.warning(f"Error calling Spoonacular: {e}")
        return {"error": str(e)}, 502
    
@app.route("/get_recipe_info")    
def get_recipe_info(recipe_id):
    try:        
        response = requests.get(RECIPE_INFO_URL.format(id=recipe_id), headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        app.logger.warning(f"Timeout when fetching recipe info for id={recipe_id}")
        return {"error": "Upstream API request timed out."}, 504
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 502)
        app.logger.warning(f"HTTP error from Spoonacular for id={recipe_id}: {status} - {e}")
        return {"error": f"Upstream service returned HTTP {status}."}, 502
    except requests.exceptions.RequestException as e:
        app.logger.warning(f"Error fetching details for recipe ID {recipe_id}: {e}")
        return {"error": str(e)}, 502

@app.route("/random_joke")
def random_joke():
    try:
        response = requests.get(JOKE_URL, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        joke = data.get("text", "Why did the tomato turn red? Because it saw the salad dressing!")
        return {"joke": joke}
    except requests.exceptions.Timeout:
        app.logger.warning("Timeout when fetching random joke from Spoonacular")
        return {"error": "Upstream API request timed out."}, 504
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 502)
        app.logger.warning(f"HTTP error from Spoonacular joke endpoint: {status} - {e}")
        return {"error": f"Upstream service returned HTTP {status}."}, 502
    except requests.exceptions.RequestException as e:
        app.logger.warning(f"Error fetching joke from Spoonacular: {e}")
        return {"error": str(e)}, 502


@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", user=user)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
