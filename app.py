from flask import Flask, render_template, redirect, request, url_for, session, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from database.connection import init_connection_engine, db
from database.models import ManualUser, Oauth_User, SavedRecipe
from sqlalchemy import select
from datetime import datetime, date, timedelta, timezone
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
import uuid
from mailer import send_reset_email
import csv
from rapidfuzz import process, fuzz
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
import re


# ---------------- APP SETUP ----------------
app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

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
def load_user(user_id_str):
    # Handles both manual and oauth using flask_login
    try:
        user_type, user_id = user_id_str.split('_')
        user_id = int(user_id)
    except (ValueError, AttributeError):
        return None
    
    if user_type == "manual":
        return db.session.get(ManualUser, user_id)
    elif user_type == "oauth":
        return db.session.get(Oauth_User, user_id)
    
    return None

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error="ratelimit exceeded", description=str(error.description)), 429
    
    flash("Too many requests. Please wait a moment and try again.", "danger")
    
    template = "index.html"
    if request.endpoint == "userlogin":
        template = "userlogin"
    elif request.endpoint == "register":
        template = "register"
    elif request.endpoint == "reset_password":
        template = "reset_password"
    
    return redirect(url_for(template))

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


    login_user(user)

    flash("Welcome my potato!", "success")
    return redirect(url_for("index"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
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

# ---------------- RESET PASSWORD ----------------
#generate the token and send the email
@app.route("/reset_password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def reset_password():
    if request.method == "POST":
        email = request.form["email"]
        user = db.session.execute(select(ManualUser).where(ManualUser.email == email)).scalar()
        if user:
            token = str(uuid.uuid4())
            user.reset_token = token
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            db.session.commit()
            
            # Enhanced email sending with better error handling
            try:
                email_sent = send_reset_email(user.email, token)
                if email_sent:
                    flash("Password reset email sent! Check your inbox.", "success")
                    app.logger.info(f"Reset email sent to {user.email}")
                else:
                    flash("Failed to send reset email. Please try again later.", "error")
                    app.logger.error(f"Failed to send reset email to {user.email}")
            except Exception as e:
                flash("Error sending reset email. Please contact support.", "error")
                app.logger.error(f"Exception in send_reset_email: {e}")
        else:
            # Don't reveal whether email exists for security
            flash("If that email exists in our system, a reset link has been sent.", "info")
            
    return render_template("reset_password.html")

# ---------------- RESET WITH TOKEN ----------------
@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    user = db.session.execute(select(ManualUser).where(ManualUser.reset_token == token)).scalar()
    if not user:
        flash("Invalid or expired token")
        return redirect(url_for("reset_password"))
    
    if user.reset_token_expires is None or user.reset_token_expires < datetime.now(timezone.utc):
        flash("This reset link has expired. Please request a new one.", "error")
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        return redirect(url_for('reset_password'))
        
    if request.method == "POST":
        new_password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        user.password = hashed_password
        user.reset_token = None
        db.session.commit()
        flash("Password has been reset", "success")
        return redirect(url_for("userlogin"))

    return render_template("reset_with_token.html", token=token) # subject to change based on frontend

# ---------------- MANUAL LOGIN ----------------
@app.route("/userlogin", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
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
@limiter.limit("10 per hour")
def register():
    # Get username and password
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        password = request.form["password"]
        
        # if not check_password(password):
        #     flash("""Password must contain one uppercase letter, one lowercase
        #           letter, one special character ($, @, #, %) and between 6 and 20 characters""", "error")
        #     return redirect(url_for("register"))
        
        # Find whether a user with that username already exists
        if db.session.execute(select(ManualUser).where(ManualUser.email == email)).scalar():
            flash("That potato already exists", "error")
            return redirect(url_for("register"))
        
        # Hash password with bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        # Create a user with that entry
        user = ManualUser(
            email=email,
            name=name,
            password=hashed_password
        )
        
        # Commit it to the database
        db.session.add(user)
        db.session.commit()
        
        # Login with login_user function and redirect to index page
        login_user(user)

        flash("A potato has been registered", "success")
        return redirect(url_for("index"))

    return render_template("register.html")

# Edamam API setup
EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID")
EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY")

EDAMAM_BY_URI_URL = "https://api.edamam.com/api/recipes/v2/by-uri"
EDAMAM_API_URL = "https://api.edamam.com/api/recipes/v2"

# async to filter out bad links
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


# -------API Search------------------

@app.route("/search_recipes")
def search_recipes():
    ingredients = request.args.get("ingredients", "")
    cuisine = request.args.get("cuisine", "")
    diet = request.args.get("diet", "")
    allergies = request.args.get("allergies", "")

    # Fail fast if API key missing
    if not EDAMAM_APP_ID or not EDAMAM_APP_KEY:
        return {"error": "Server misconfiguration: API_KEY is not set."}, 500

   # Params for Edamam
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
    if cuisine:
        params['cuisineType'] = cuisine

    try:
        response = requests.get(EDAMAM_API_URL, params={k: v for k, v in params.items() if v})
        response.raise_for_status()
        initial_hits = response.json().get("hits", [])

        # Uses aiohttp to filter out the API results with bad links, ensures users always get ones that are working
        
        # valid_recipes = asyncio.run(filter_links(initial_hits))
        # random.shuffle(valid_recipes)

#COMMENTED OUT THE ABOVE TWO LINES AND REPLACED WITH THE BELOW LINES TO WORK ON PYTHONANYWHERE
        valid_recipes = []
        for hit in initial_hits:
            recipe = hit.get("recipe", {})
            if recipe.get("url", "").startswith("http"):
                valid_recipes.append(recipe)

        random.shuffle(valid_recipes)

#END COMMENT
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
        app.logger.warning("Timeout when calling Edamam API for search_recipes")
        return {"error": "Upstream API request timed out."}, 504
    except requests.exceptions.HTTPError as e:
        # Return the upstream status code & message as a 502-level error
        status = getattr(e.response, 'status_code', 502)
        app.logger.warning(f"HTTP error from Edamam: {status} - {e}")
        return {"error": f"Too many API calls. Please wait 60 seconds before searching again."}, 502
    except requests.exceptions.RequestException as e:
        app.logger.warning(f"Error calling Spoonacular: {e}")
        return {"error": str(e)}, 502
    

    
# ---------------- Saved Recipes ----------------
@app.route("/saved_recipes", methods=["GET"])
@login_required
def saved_recipe():
    saved_recipes = current_user.saved_recipes
    
    recipe_data = []
    for recipe in saved_recipes:
        recipe_data.append({
            "id": recipe.recipe_id,
            "title": recipe.title,
            "image": recipe.image,
            "link": recipe.link,
        })
        
    return jsonify(recipe_data)

@app.route("/save_recipe", methods=["POST"])
@login_required
def save_recipe():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Saved recipe not found"}), 400
    
    recipe_id = data.get("id")
    if not recipe_id:
        return jsonify({"error": "Recipe id not found"}), 400
    

    query = select(SavedRecipe).where(SavedRecipe.recipe_id == recipe_id)
    if isinstance(current_user, ManualUser):
        query = query.where(SavedRecipe.manual_id == current_user.manual_id)
    elif isinstance(current_user, Oauth_User):
        query = query.where(SavedRecipe.user_id == current_user.user_id)
    
    
    is_saved = db.session.execute(query).scalar_one_or_none() is not None
    # is_saved = db.session.execute(query).first() is not None
    
    if is_saved:
        return jsonify({"error": "Recipe is already saved. I'm a sad potato"}), 409
    
    new_recipe = SavedRecipe(
        recipe_id = recipe_id,
        title = data.get("title"),
        image=data.get("image"),
        link = data.get("link"),
    )
    
    current_user.saved_recipes.append(new_recipe)
    
    try:
        db.session.commit()
        return jsonify({"message": "Recipe saved successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "database error"}), 500

@app.route("/delete_saved_recipe", methods=["POST"])
@login_required
def delete_saved_recipe():
    data = request.get_json()
    recipe_id = data.get("id")
    
    if not recipe_id:
        return jsonify({"error": "Missing potato ID dumb dumb"})
    
    recipe_to_delete = next((r for r in current_user.saved_recipes if r.recipe_id == recipe_id), None)
    
    if recipe_to_delete:
        try:
            db.session.delete(recipe_to_delete)
            db.session.commit()
            return jsonify({"message": "Recipe deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "database error"})
        
    return jsonify({"error": "Recipe not found"})

@app.route("/random_joke")
def random_joke():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    jokes_path = os.path.join(base_dir, "food_jokes.txt")

    try:
        with open(jokes_path, "r", encoding="utf-8") as f:
            jokes = [line.strip() for line in f if line.strip()]
        return random.choice(jokes)
    except Exception as e:
        print("Error loading jokes:", e)
        return "No food jokes available at the moment"


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)