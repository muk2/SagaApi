from pathlib import Path
from typing import List, Optional
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
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_EMAIL")
    SMTP_FROM_NAME: Optional[str] = os.getenv("SMTP_EMAIL")
    SMTP_FROM_EMAIL: Optional[str] = os.getenv("SMTP_EMAIL")
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")

    # North Payment Gateway
    NORTH_MID: Optional[str] = os.getenv("NORTH_MID")
    NORTH_DEVELOPER_KEY: Optional[str] = os.getenv("NORTH_DEVELOPER_KEY")
    NORTH_PASSWORD: Optional[str] = os.getenv("NORTH_PASSWORD")
    NORTH_BASE_URL: str = os.getenv("NORTH_BASE_URL", "https://secure.networkmerchants.com/api/transact.php")
    NORTH_TIMEOUT_SECONDS: int = int(os.getenv("NORTH_TIMEOUT_SECONDS", "30"))


settings = Settings()
