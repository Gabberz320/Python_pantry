import requests
import os
import json


API_KEY = "ab1ce54d449b4fac9a3d4feb66bb5707"
API_URL = "https://api.spoonacular.com"
SEARCH_API_URL = f"{API_URL}/recipes/findByIngredients"
RECIPE_INFO_URL = f"{API_URL}/recipes/{id}/information"
NUM_RESULTS = 5

def search_recipes(ingredients):
    params = {'apiKey': API_KEY, 'ingredients': ','.join(ingredients),
              'number': NUM_RESULTS, 'ranking': 1}
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()

def display_recipes(recipes):
    if not recipes:
        print("Sorry, no results found")
    for i, recipe in enumerate(recipes,1):
        title = recipe['title']
        used_ingredients_count = recipe['usedIngredientCount']
        missed_ingredient_count = recipe['missedIngredientCount']
        if missed_ingredient_count < 2:
            missed_ingredients = [ing['name'] for ing in recipe['missedIngredients']]
            print(f"you are only missing {missed_ingredient_count} ingredients")
            print(f"-Missing {','.join(missed_ingredients)}\n {recipe}")
        else:
            print('you got it all', recipe)

def main():
    input_str = (input("Enter ingredients, separated by commas.: "))
    ingredients = [ingredient.strip() for ingredient in input_str.split(',')]

    recipies_found = search_recipes(ingredients)

    if recipies_found is not None:
        display_recipes(recipies_found)
    else:
        print("sorry")
main()