import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Novo Contact App"
    PROJECT_VERSION: str = "1.0.0"
    
    # JWT настройки
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

settings = Settings()