from flask import Flask, render_template
from database.connection import init_connection_engine, db
from sqlalchemy import text

app = Flask(__name__)

init_connection_engine(app)

@app.route("/test")
def test():
    result = db.session.execute(text("SELECT 1")).scalar()
    print(f"Test Query: {result}")
    
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)