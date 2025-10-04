from database.connection import db
from datetime import datetime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    oauth_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    oauth_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    #Oauth tokens
    # Table will be completed when login and registration page is designed
    
    def __repr__(self):
        return f'<User {self.email}>'
    
class SavedRecipe(db.model):
    __tablename__ = "saved_recipes"
    
    saved_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    recipe_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    recipe_name: Mapped[str] = mapped_column(String(400), nullable=False)
    thumbnail: Mapped[str] = mapped_column(String(400), nullable=True, unique=True)
    
    # Will be stored in a comma seperated list
    missed_ingredients: Mapped[str] = mapped_column(Text, nullable=True)            
    ingredients: Mapped[str] = mapped_column(Text, nullable=True)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    
    def __repr__(self):
        return f"<Saved recipe {self.recipe_name}>"