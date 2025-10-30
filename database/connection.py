from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()

def init_connection_engine(app):
    # Detect whether app is running on PythonAnywhere
    hostname = os.uname().nodename if hasattr(os, "uname") else ""
    on_pythonanywhere = (
        "PYTHONANYWHERE_DOMAIN" in os.environ
        or "pythonanywhere" in hostname.lower()
        or "pythonanywhere" in os.getcwd().lower()
    )

    if on_pythonanywhere:
        print("Using PythonAnywhere MySQL database")
        db_user = os.getenv("PA_DB_USER")
        db_password = os.getenv("PA_DB_PASSWORD")
        db_name = os.getenv("PA_DB_NAME")
        db_host = os.getenv("PA_DB_HOST")
    else:
        print("Using local MySQL database")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST")

    # Build URI and print it (password masked)
    db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    masked_uri = db_uri.replace(db_password, "*****") if db_password else db_uri
    print(f"Database URI: {masked_uri}")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        try:
            db.engine.connect()
            print("database connected successfully.")
        except OperationalError as e:
            print("database connection failed:", e)

    # try:
    #     with app.app_context():
    #         result = db.session.execute(text("SELECT 1")).scalar()
    #         print(f"Test Query: {result}")
    # except OperationalError as error:
    #     print("Connection Failure...")
    #     print(f"Error: {error}")


# from sqlalchemy import URL, text
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.exc import OperationalError

# import os
# from dotenv import load_dotenv

# load_dotenv()

# db = SQLAlchemy()

# url_object = URL.create(
#     "mysql+pymysql",
#     username="root",
#     password="Gfj2e_7719",
#     host="localhost",
#     database="recipe_database"
# )

# def init_connection_engine(app):
#     app.config['SQLALCHEMY_DATABASE_URI'] = url_object
#     app.config ['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#     db.init_app(app)

    # try:
    #     with app.app_context():
    #         result = db.session.execute(text("SELECT 1")).scalar()
    #         print(f"Test Query: {result}")
    # except OperationalError as error:
    #     print("Connection Failure...")
    #     print(f"Error: {error}")



# def init_connection_engine(app):
#     db_user = os.getenv("DB_USER")
#     db_password = os.getenv("DB_PASSWORD")
#     db_name = os.getenv("DB_NAME")
#     db_host = os.getenv("DB_HOST")

#     app.config["SQLALCHEMY_DATABASE_URI"] = (
#         f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
#     )
#     app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#     db.init_app(app)

#     with app.app_context():
#         try:
#             db.engine.connect()
#             print("database connected successfully.")
#         except Exception as e:
#             print("dabase connection failed:", e)
