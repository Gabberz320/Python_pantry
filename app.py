from flask import Flask, render_template, redirect, request, url_for, session, flash, jsonify
from flask_login import LoginManager, login_user, logout_user
from flask_bcrypt import Bcrypt
from database.connection import init_connection_engine, db
from database.models import ManualUser, Oauth_User
from sqlalchemy import select
import os
import requests
import random
import pathlib
import aiohttp
import asyncio
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests

import csv
from rapidfuzz import process, fuzz
import re

NUM_RESULTS = 100
NUM_SKIP = random.randint(1, 5)

# ---------------- APP SETUP ----------------
app = Flask(__name__)
load_dotenv()  # Load environment variables

app.secret_key = os.getenv("SECRET_KEY") or "supersecretkey"
init_connection_engine(app)

# ---------------- GOOGLE OAUTH SETUP ----------------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# ---------------- Flask Login Setup ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "userlogin"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(ManualUser, int(user_id))

# ---------------- Bcrypt Password Hashing ----------------
bcrypt = Bcrypt()
bcrypt.init_app(app)

# ---------------- HOME PAGE ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- GOOGLE LOGIN ----------------
@app.route("/google_login")
def google_login():
    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        redirect_uri=url_for("google_callback", _external=True),
    )
    auth_url, state = flow.authorization_url(prompt="consent")
    session["state"] = state
    return redirect(auth_url)

# ---------------- GOOGLE CALLBACK ----------------
@app.route("/login/callback")
def google_callback():
    if session.get("state") != request.args.get("state"):
        return "Invalid state parameter", 400

    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        redirect_uri=url_for("google_callback", _external=True),
    )

    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    request_session = google.auth.transport.requests.Request()
    user_info = id_token.verify_oauth2_token(
        credentials.id_token,
        request_session,
        GOOGLE_CLIENT_ID,
    )
    
    oauth_id = user_info.get("sub")
    
    user = db.session.execute(select(Oauth_User).where(Oauth_User.oauth_id == oauth_id)).scalar()
    
    if user:
        user.name = user_info.get("name")
        user.picture_url = user_info.get("picture")
    else:
        user = Oauth_User(
            oauth_id=oauth_id,
            name=user_info.get("name"),
            email=user_info.get("email"),
            picture_url=user_info.get("picture")
        )
        db.session.add(user)

        db.session.commit()

    session["user"] = {
        "id": user_info.get("sub"),
        "name": user_info.get("name"),
        "email": user_info.get("email"),
        "picture": user_info.get("picture"),
    }

    print(session["user"])
    return redirect(url_for("index"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    logout_user()
    flash("I love potatoes", "success")
    return redirect(url_for("index"))
# ---------------- CHECK LOGIN STATUS (ADD THIS HERE) ----------------
@app.route("/check_login")
def check_login():
    """API endpoint to check if user is logged in"""
    if "user" in session:
        return jsonify({
            "logged_in": True,
            "user": session["user"]
        })
    else:
        return jsonify({
            "logged_in": False,
            "user": None
        })

# ---------------- MANUAL LOGIN ----------------
@app.route("/userlogin", methods=["GET", "POST"])
def userlogin():
    # Get the login info from the user
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        # If username or password not entered, redirect
        if not email or not password:
            flash("Potato must enter both username and password", "danger")
            return redirect(url_for("userlogin"))
        
        # Retrieve the user from the database
        user = db.session.execute(select(ManualUser).where(ManualUser.email == email)).scalar()
        
        # Check for correct username and password, login user if both correct
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash(f"Welcome back potato {email}", "success")
            return redirect(url_for("index"))
        else:
            flash("Stop being a stupid potato and enter the right username or password!", "danger")
            return redirect(url_for("userlogin"))

    return render_template("login.html")

def check_password(password):
    reg = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$#%()])[A-Za-z\d@$#%()]{6,20}$"
    
    pattern = re.compile(reg)
    
    is_valid = re.search(pattern, password)
    
    if is_valid:
        return True
    else:
        return False

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    # Get username and password
    if request.method == "POST":
        username = request.form["username"]  # Changed from email
        password = request.form["password"]
        
        # Find whether a user with that username already exists
        if db.session.execute(select(ManualUser).where(ManualUser.username == username)).scalar():
            flash("That username already exists", "error")
            return redirect(url_for("register"))
        
        # Hash password with bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        # Create a user with that entry
        user = ManualUser(
            username=username,  # Changed from email
            password=hashed_password
        )
        
        # Commit it to the database
        db.session.add(user)
        db.session.commit()
        
        # Login with login_user function and redirect to index page
        login_user(user)

        flash(f"Account created successfully! Welcome {username}", "success")
        return redirect(url_for("index"))

    return render_template("register.html")

# ---------------- MAIN ----------------
# if __name__ == "__main__":
#     app.run(debug=True, use_reloader=False)



# ---------- SPOONACULAR API SETUP ----------
# API_KEY = os.getenv("Edamam_APP_KEY")
# API_HOST = "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
# API_URL = f"https://{API_HOST}"
# SEARCH_URL = f"{API_URL}/recipes/complexSearch"
# RECIPE_INFO_URL = f"{API_URL}/recipes/{{id}}/information"
# JOKE_URL = f"{API_URL}/food/jokes/random"

EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID")
EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY")

EDAMAM_API_URL = "https://api.edamam.com/api/recipes/v2"

# Timeout (seconds) for external API calls to avoid hanging the Flask worker
#REQUEST_TIMEOUT = 10

# headers = {
#     "x-rapidapi-key": API_KEY,
#     "x-rapidapi-host": API_HOST,
# }

# if not API_KEY:
#     # Helpful runtime message for debugging missing API key (do not log sensitive values)
#     print("WARNING: API_KEY environment variable is not set. Requests to the Spoonacular/RapidAPI endpoint will fail with 401 Unauthorized.")

async def is_valid_link(session, url, timeout=1):
    if not url:
        return False
    try:
        # Use aiohttp's timeout object
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with session.get(url, timeout=client_timeout, allow_redirects=True, headers={"Range": "bytes=0-0"}) as response:
             if response.status < 400:
                 return True
             else: 
                 return False
    # This line is for catching any network errors connecting to a link
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False
    

async def filter_links(hits):
    valid_recipes = []
    async with aiohttp.ClientSession() as session:
        # Create a list of tasks, checking the links of each recipe returned from the API
        tasks = []
        for hit in hits:
            recipe_data = hit.get("recipe", {})
            source_url = recipe_data.get("url")
            task = asyncio.create_task(is_valid_link(session, source_url))
            tasks.append((task, recipe_data))
        
        # Waits for all the tasks to complete
        for task, recipe in tasks:
            is_valid = await task
            if is_valid:
                valid_recipes.append(recipe)
    
    return valid_recipes


#---------autocomplete---------
INGREDIENTS = []
csv_path = os.path.join(os.path.dirname(__file__), "ingredients-with-possible-units.csv")

try:
    with open(csv_path, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            raw_name = row[0].strip().lower()
            name = re.split(r"[;,:]", raw_name)[0].strip()
            units = ", ".join([cell.strip() for cell in row[1:] if cell.strip()])
            if name:
                INGREDIENTS.append({"name": name, "unit": units})
    print(f"Loaded {len(INGREDIENTS)} ingredients from CSV.")
except Exception as e:
    print("Error loading ingredients CSV:", e)

@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("query", "").strip().lower()
    if not query:
        return {"error": "Missing query parameter"}, 400

    names = [item["name"] for item in INGREDIENTS]

    results = process.extract(query, names, limit=5, scorer=fuzz.WRatio)

    matches = []
    for name, score, _ in results:
        for item in INGREDIENTS:
            if item["name"] == name:
                matches.append({
                    "name": item["name"],
                    "unit": item["unit"]
                })
                break

    return matches




@app.route("/search_recipes")
def search_recipes():
    ingredients = request.args.get("ingredients", "")
    #cuisine = request.args.get("cuisine", "")
    diet = request.args.get("diet", "")
    allergies = request.args.get("allergies", "")

    # Fail fast if API key missing
    if not EDAMAM_APP_ID or not EDAMAM_APP_KEY:
        return {"error": "Server misconfiguration: API_KEY is not set."}, 500

    

    # params = {
    #     'number': NUM_RESULTS,
    #     'includeIngredients': ingredients, 
    #     'cuisine': cuisine,
    #     'diet': diet, 
    #     'intolerances': allergies,
    #     'ranking': 2,
    #     'addRecipeInformation': True, 
    #     'ignorePantry': False,
    #     'addRecipeNutrition': True,
    #     'sort': 'min-missing-ingredients',
    #     'offset': NUM_SKIP}
    params = {
        'type': 'public',
        'q': ingredients,
        'app_id': EDAMAM_APP_ID,
        'app_key': EDAMAM_APP_KEY,
        }
    if diet:
        params['diet'] = diet
    if allergies:
        params['health'] = allergies

    try:
        response = requests.get(EDAMAM_API_URL, params={k: v for k, v in params.items() if v})
        response.raise_for_status()
        initial_hits = response.json().get("hits", [])

        # Uses aiohttp to filter out the API results with bad links, ensures users always get ones that are working
        valid_recipes = asyncio.run(filter_links(initial_hits))
        random.shuffle(valid_recipes)

        unique_recipes = []
        seen_uris = set()
        for recipe in valid_recipes:
            uri = recipe.get("uri")
            if uri not in seen_uris:
                seen_uris.add(uri)
                unique_recipes.append(recipe)

        return unique_recipes
        #return valid_recipes
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
    
# @app.route("/get_recipe_info")    
# def get_recipe_info(recipe_id):
#     params = {'includeNutrition': 'true'}
#     try:        
#         response = requests.get(RECIPE_INFO_URL.format(id=recipe_id), headers=headers, params=params, timeout=REQUEST_TIMEOUT)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.Timeout:
#         app.logger.warning(f"Timeout when fetching recipe info for id={recipe_id}")
#         return {"error": "Upstream API request timed out."}, 504
#     except requests.exceptions.HTTPError as e:
#         status = getattr(e.response, 'status_code', 502)
#         app.logger.warning(f"HTTP error from Spoonacular for id={recipe_id}: {status} - {e}")
#         return {"error": f"Upstream service returned HTTP {status}."}, 502
#     except requests.exceptions.RequestException as e:
#         app.logger.warning(f"Error fetching details for recipe ID {recipe_id}: {e}")
#         return {"error": str(e)}, 502

# @app.route("/random_joke")
# def random_joke():
#     try:
#         response = requests.get(JOKE_URL, headers=headers, timeout=REQUEST_TIMEOUT)
#         response.raise_for_status()
#         data = response.json()
#         joke = data.get("text", "Why did the tomato turn red? Because it saw the salad dressing!")
#         return {"joke": joke}
#     except requests.exceptions.Timeout:
#         app.logger.warning("Timeout when fetching random joke from Spoonacular")
#         return {"error": "Upstream API request timed out."}, 504
#     except requests.exceptions.HTTPError as e:
#         status = getattr(e.response, 'status_code', 502)
#         app.logger.warning(f"HTTP error from Spoonacular joke endpoint: {status} - {e}")
#         return {"error": f"Upstream service returned HTTP {status}."}, 502
#     except requests.exceptions.RequestException as e:
#         app.logger.warning(f"Error fetching joke from Spoonacular: {e}")
#         return {"error": str(e)}, 502


# @app.route("/")
# def index():
#     user = session.get("user")
#     return render_template("index.html", user=user)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
