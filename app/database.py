# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, configure_mappers
import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Явная конфигурация мапперов после импорта всех моделей
def configure_database():
    """Конфигурирует все мапперы после импорта моделей"""
    # Импортируем все модели для регистрации
    from app.models.user import User, RefreshToken
    from app.models.contact import Contact, ContactDialog, DialogMessage
    from app.models.group import Group, GroupMember, ScheduledGroupCall
    from app.models.prompt_template import PromptTemplate
    from app.models.scheduled_call import ScheduledCall
    
    # Конфигурируем мапперы
    configure_mappers()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()