from database.connection import db
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class ManualUser(db.Model, UserMixin):
    __tablename__ = "manual_users"
    
    manual_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    reset_token: Mapped[str] = mapped_column(String(36), nullable=True, unique=True)
    reset_token_expires: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    saved_recipes = relationship("SavedRecipe", back_populates="manual_user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.manual_id} {self.email}>'
    
    def get_id(self):
        return f"manual_{self.manual_id}"

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
        return f"oauth_{self.user_id}"
    
class SavedRecipe(db.Model):
    __tablename__ = "saved_recipes"
    
    saved_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    image: Mapped[str] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(Text, nullable=True)
    date_saved: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    manual_user = relationship("ManualUser", back_populates="saved_recipes")
    oauth_user = relationship("Oauth_User", back_populates="saved_recipes")
    
    manual_id: Mapped[int] = mapped_column(ForeignKey("manual_users.manual_id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("oauth_users.user_id"), nullable=True)
    
    def __repr__(self):
        return f"<Saved recipe {self.title}>"
