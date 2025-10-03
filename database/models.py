from database.connection import db
from datetime import datetime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import String, Integer, DateTime

class User(db.Model):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    oauth_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    oauth_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    #Oauth tokens
    
    def __repr__(self):
        return f'<User {self.email}>'