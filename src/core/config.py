from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find project root (where .env lives)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


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
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = [
    "https://sagafe.vercel.app",
    "http://localhost:3000",
]
    
    FRONTEND_URL: str = "http://localhost:3000"
    SMTP_HOST: str = "smtp.gmail.com" 
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "sagagolfevents@gmail.com"
    SMTP_FROM_NAME: str = "sagagolfevents@gmail.com"
    SMTP_FROM_EMAIL: str = "sagagolfevents@gmail.com"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PASSWORD: str = "ynwjxiescwdystot"


settings = Settings()
