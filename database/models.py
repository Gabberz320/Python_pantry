from database.connection import db
from datetime import datetime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, SmallInteger, JSON
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class ManualUser(db.Model, UserMixin):
    __tablename__ = "manual_users"
    
    manual_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    saved_recipes = relationship("SavedRecipe", back_populates="manual_user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.manual_id} {self.username}>'
    
    def get_id(self):
        return str(self.manual_id)

class Oauth_User(db.Model, UserMixin):
    __tablename__ = "oauth_users"
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oauth_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255))
    picture_url: Mapped[str] = mapped_column(String(512), nullable=True)
    
    saved_recipes = relationship("SavedRecipe", back_populates="oauth_user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.user_id} {self.email}>'
    
    def get_id(self):
        return str(self.user_id)
    
class SavedRecipe(db.Model):
    __tablename__ = "saved_recipes"
    
    saved_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    calories: Mapped[int] = mapped_column(Integer, nullable=True)
    servings: Mapped[int] = mapped_column(Integer, nullable=True)
    cook_time: Mapped[str] = mapped_column(String(50), nullable=True)
    image: Mapped[str] = mapped_column(String(400), nullable=True)
    link: Mapped[str] = mapped_column(Text, nullable=True)
    ingredients: Mapped[list] = mapped_column(JSON, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    
    manual_user = relationship("ManualUser", back_populates="saved_recipes")
    oauth_user = relationship("Oauth_User", back_populates="saved_recipes")
    
    manual_id: Mapped[int] = mapped_column(ForeignKey("manual_users.manual_id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("oauth_users.user_id"), nullable=True)
    
    def __repr__(self):
        return f"<Saved recipe {self.recipe_name}>"
