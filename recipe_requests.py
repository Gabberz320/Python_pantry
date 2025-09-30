import requests



API_KEY = "ab1ce54d449b4fac9a3d4feb66bb5707"
API_URL = "https://api.spoonacular.com"
SEARCH_URL = f"{API_URL}/recipes/complexSearch"
RECIPE_INFO_URL = "https://api.spoonacular.com/recipes/{id}/information"
NUM_RESULTS = 5

# search for the recipe with the given ingredients
# return the list of recipes for future info search
def search_recipes(query, ingredients, cuisine, diet):
    params = {'apiKey': API_KEY, 'number': NUM_RESULTS,
            'query': query, 'includeIngredients': ', '.join(ingredients), 
            'cuisine': ','.join(cuisine),
            'diet': diet}

    try: 
        response = requests.get(SEARCH_URL, params=params)
        response.raise_for_status()
        return response.json().get('results',[])
    except requests.exceptions.RequestException as e:
        print(f'An error occured: {e}')
        return None
# Get the reipe infomation to display from the recipe ID
def get_recipe_details(recipe_id):
    try:
        params = {'apiKey': API_KEY}
        response = requests.get(RECIPE_INFO_URL.format(id = recipe_id), params = params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error fetching details: {recipe_id} {e}')
        return None

def main():
    query = []
    ingredients_str = input('Enter ingredients separated by commas: ').strip()
    ingredients = [ n.strip() for n in ingredients_str.split(',')] if ingredients_str else []
    cuisine_str = input('Enter the cuisine you\'re craving: ').strip()
    cuisine = [n.strip() for n in cuisine_str.split(',')] if cuisine_str else []
    diet = input('Enter dietary preferences: ').strip()

    recipies_found = search_recipes(query,ingredients,cuisine, diet)

    if not recipies_found:
        print('Sorry none found')
        return
    
    # Search for the recipe information (cooktime, URL, anf title of the recipe)
    for recipe_summary in recipies_found:
        recipe_id = recipe_summary['id']

        details = get_recipe_details(recipe_id)

        title = details.get('title','N/A')
        cook_time = details.get('readyInMinutes','N/A')
        source_url = details.get('sourceUrl')

        if details:
            print(f'{title}')
            print(f'Time to cook: {cook_time} minutes')
            print(f'URL: {source_url}', end = '\n')
            print('\n')
            

main()