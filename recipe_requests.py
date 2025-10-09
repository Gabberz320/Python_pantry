import requests
import random
from dotenv import load_dotenv
import os

import flask
from flask import redirect, request, url_for, session
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests
import pathlib

load_dotenv()



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
    
    # Store user information in session
    session["user"] = {
        "id": user_info.get("sub"),
        "name": user_info.get("name"),
        "email": user_info.get("email"),
        "picture": user_info.get("picture"),
    }
    
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    """Logout user and clear session"""
    session.pop("user", None)
    session.pop("state", None)
    return redirect(url_for("index"))




API_KEY = os.getenv("API_KEY")
API_HOST = "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
API_URL = f"https://{API_HOST}"
SEARCH_URL = f"https://{API_HOST}/recipes/complexSearch"
RECIPE_INFO_URL = f"https://{API_HOST}/recipes/{{id}}/information"
JOKE_URL = f"https://{API_HOST}/food/jokes/random"

NUM_RESULTS = random.randint(50, 100)
NUM_SKIP = random.randint(1, 10)

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}
# search for the recipe with the given ingredients
# return the list of recipes for future info search
def search_recipes(ingredients, cuisine, diet, allergies):
    
    params = {'number': NUM_RESULTS,
            'includeIngredients': ','.join(ingredients), 
            'cuisine': ','.join(cuisine),
            'diet': diet, 
            'intolerances': allergies,
            'addRecipeInformation': True, 
            'ignorePantry': False,
            'ranking': 2,
            'sort': 'min-missing-ingredients',
            'offset': NUM_SKIP }
  
    try: 
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('results',[])
    except requests.exceptions.RequestException as e:
        print(f'An error occured: {e}')
        return None
    
# Get recipe info with ID for saved recipes    
def get_recipe_info(recipe_id):
    try:
                
        response = requests.get(RECIPE_INFO_URL.format(id=recipe_id), headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error fetching details for recipe ID {recipe_id}: {e}')
        return None
    
# Display recipes 
def display_recipes(recipes):
    for recipe_summary in recipes[:10]:
            
            title = recipe_summary.get('title','N/A')
            cook_time = recipe_summary.get('readyInMinutes','N/A')
            source_url = recipe_summary.get('sourceUrl', 'N/A')

            if recipe_summary:

                print(f'{title}')
                print(f'Time to cook: {cook_time} minutes')
                print(f'URL: {source_url}', end = '\n')
                print('\n')
                
# Random joke 
def get_random_joke():
    try:
       
        response = requests.get(JOKE_URL, headers=headers)
        response.raise_for_status()
        joke = response.json()
        if len(joke.get('text','N/A')) > 200:
            joke = {'text': 'Why did the tomato turn red? Because it saw the salad dressing!'}

        return joke.get('text','N/A')
    except requests.exceptions.RequestException as e:
        print(f"Error occured while fetching joke {e}")
        return None



def main():
    
    ingredients_str = input('Enter ingredients separated by commas: ').strip()
    ingredients = [ n.strip() for n in ingredients_str.split(',')] if ingredients_str else []
    cuisine_str = input('Enter the cuisine you\'re craving: ').strip()
    cuisine = [n.strip() for n in cuisine_str.split(',')] if cuisine_str else []
    diet = input('Enter dietary preferences: ').strip()
    allergies = input('Allergies? Enter them here separated by a comma: ')

    recipes_found = search_recipes(ingredients,cuisine, diet, allergies)
    

    if not recipes_found:
        print('Sorry none found')
        return
    else:

       #Display recipe information
       joke = get_random_joke()
       print(joke, '\n \n')
       
       display_recipes(recipes_found)

        
            

#main()

if __name__ == "__main__":
    app.run(debug=True)
