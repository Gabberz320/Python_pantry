import requests
import random


API_KEY = "" # add your API key here
API_URL = "https://api.spoonacular.com"
SEARCH_URL = f"{API_URL}/recipes/complexSearch"
NUM_RESULTS = random.randint(50, 100)
NUM_SKIP = random.randint(1, 500)

# search for the recipe with the given ingredients
# return the list of recipes for future info search
def search_recipes(ingredients, cuisine, diet):
    params = {'apiKey': API_KEY, 'number': NUM_RESULTS,
            'includeIngredients': ','.join(ingredients), 
            'cuisine': ','.join(cuisine),
            'diet': diet, 'addRecipeInformation': True, 'ignorePantry': False, 'sort': 'min-missing-ingredients', 'offset': NUM_SKIP}

    try: 
        response = requests.get(SEARCH_URL, params=params)
        response.raise_for_status()
        return response.json().get('results',[])
    except requests.exceptions.RequestException as e:
        print(f'An error occured: {e}')
        return None


def main():
    
    ingredients_str = input('Enter ingredients separated by commas: ').strip()
    ingredients = [ n.strip() for n in ingredients_str.split(',')] if ingredients_str else []
    cuisine_str = input('Enter the cuisine you\'re craving: ').strip()
    cuisine = [n.strip() for n in cuisine_str.split(',')] if cuisine_str else []
    diet = input('Enter dietary preferences: ').strip()

    recipies_found = search_recipes(ingredients,cuisine, diet)
    

    if not recipies_found:
        print('Sorry none found')
        return
    else:

       #Display recipe information
        for recipe_summary in recipies_found[:10]:
            
            title = recipe_summary.get('title','N/A')
            cook_time = recipe_summary.get('readyInMinutes','N/A')
            source_url = recipe_summary.get('sourceUrl', 'N/A')

            if recipe_summary:

                print(f'{title}')
                print(f'Time to cook: {cook_time} minutes')
                print(f'URL: {source_url}', end = '\n')
                print('\n')
            

main()