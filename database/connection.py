from sqlalchemy import URL, text
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()

url_object = URL.create(
    "mysql+pymysql",
    username="root",
    password="Gfj2e_7719",
    host="localhost",
    database="recipe_database"
)

def init_connection_engine(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = url_object
    app.config ['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # try:
    #     with app.app_context():
    #         result = db.session.execute(text("SELECT 1")).scalar()
    #         print(f"Test Query: {result}")
    # except OperationalError as error:
    #     print("Connection Failure...")
    #     print(f"Error: {error}")