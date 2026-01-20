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
    APP_NAME: str = "Campus Tamizha"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./campustamizha_dev.db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-9876543210")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: list = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
        if origin.strip()
    ]
    
    # Admin credentials (for initial setup)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@campustamizha.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme123")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    LOG_SQL_QUERIES: bool = os.getenv("LOG_SQL_QUERIES", "false").lower() == "true"

    #application status
    APPLICATION_STATUS_OPTIONS: list = ["pending", "under_review", "accepted", "rejected"]


settings = Settings()
