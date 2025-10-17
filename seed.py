from sqlalchemy import insert
from database.connection import db
from database.models import Ingredient
from app import app

def main():
    with app.app_context():
        db.drop_all()
        db.create_all()
        try:
            with open("database/ingredients.txt", "r") as file:
                print("Inserting ingredient data...")
                for line in file:
                    ingredient = line.strip()
                    new_ingredient = Ingredient(ingredient_name=ingredient)
                    db.session.add(new_ingredient)
                db.session.commit()
        except FileNotFoundError:
            print("Error: file ingredients.txt not found")

if __name__ == "__main__":        
    main()
    