import os
from typing import Optional
env_type = os.getenv("ENV", "development")
from dotenv import load_dotenv
load_dotenv()

env_file_map = {
    "development": ".env.dev",
    "uat": ".env.uat",
    "production": ".env.prod"
}

load_dotenv(dotenv_path=env_file_map.get(env_type, ".env.dev"))

class Settings:
    # Application
    APP_NAME: str = "campus Tamizha"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./campustamizha_dev.db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-9876543210")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Admin credentials (for initial setup)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@campustamizha.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme123")


settings = Settings()
