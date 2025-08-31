from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import secrets

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, default="user")  # "user" или "admin"
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Связи
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    prompt_templates = relationship("PromptTemplate", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    revoked = Column(Boolean, default=False)
    
    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)