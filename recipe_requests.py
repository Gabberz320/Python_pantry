import requests
import random


API_KEY = "" # add your API key here
API_URL = "https://api.spoonacular.com"
SEARCH_URL = f"{API_URL}/recipes/complexSearch"
RECIPE_INFO_URL = f"{API_URL}/recipes/{id}/information"
NUM_RESULTS = random.randint(50, 100)
NUM_SKIP = random.randint(1, 10)

# search for the recipe with the given ingredients
# return the list of recipes for future info search
def search_recipes(ingredients, cuisine, diet):
    params = {'apiKey': API_KEY, 'number': NUM_RESULTS,
            'includeIngredients': ','.join(ingredients), 
            'cuisine': ','.join(cuisine),
            'diet': diet, 'addRecipeInformation': True, 'ignorePantry': False, 'sort': 'max-used-ingredients','offset': NUM_SKIP}

    try: 
        response = requests.get(SEARCH_URL, params=params)
        response.raise_for_status()
        return response.json().get('results',[])
    except requests.exceptions.RequestException as e:
        print(f'An error occured: {e}')
        return None
    
def get_recipe_info(recipe_id):
    try:
        params = {'apiKey': API_KEY}
        response = requests.get(RECIPE_INFO_URL.format(id=recipe_id), params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error fetching details for recipe ID {recipe_id}: {e}')
        return None

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



def main():
    
    ingredients_str = input('Enter ingredients separated by commas: ').strip()
    ingredients = [ n.strip() for n in ingredients_str.split(',')] if ingredients_str else []
    cuisine_str = input('Enter the cuisine you\'re craving: ').strip()
    cuisine = [n.strip() for n in cuisine_str.split(',')] if cuisine_str else []
    diet = input('Enter dietary preferences: ').strip()

    recipes_found = search_recipes(ingredients,cuisine, diet)
    

    if not recipes_found:
        print('Sorry none found')
        return
    else:

       #Display recipe information
       display_recipes(recipes_found)
        
            

main()