from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

# Find project root (where .env lives)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    print("Loading env from:", ENV_FILE)
    # Database
    DATABASE_URL: str

    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 50

    # CORS
    CORS_ORIGINS: List[str] = [
    "https://sagafe.vercel.app",
    "http://localhost:3000",
]
    
    FRONTEND_URL: str = "http://localhost:3000"
    SMTP_HOST: str = "smtp.gmail.com" 
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = os.getenv("SMTP_EMAIL")
    SMTP_FROM_NAME: str = os.getenv("SMTP_EMAIL")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_EMAIL")
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")


settings = Settings()
