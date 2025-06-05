from typing import List

from dotenv import load_dotenv, find_dotenv
from pydantic import Field, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(find_dotenv(usecwd=True))

class Settings(BaseSettings):

    # App settings
    PROJECT_NAME: str = "Neemble Eat"
    PROJECT_VERSION: str = "1.0.0"
    API_BASE_ROUTE: str = "/api"


    # Environment
    ENVIRONMENT: str = Field(default="development")

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "https://neemble-eat-frontend-485828523035.africa-south1.run.app",
        "https://neemble-eat-frontend-485828523035.africa-south1.run.app",
        "https://frontend-485828523035.africa-south1.run.app",
        "https://neemble-frontend-485828523035.europe-west1.run.app"
    ]

    # MongoDB Config
    MONGO_DB_URI: str
    MONGO_DB_DATABASE_NAME: str = Field(default="neemble_eat_db")

    # Firebase/Auth settings
    FIREBASE_SERVICE_ACCOUNT_KEY: str
    CLOCK_SKEW_SECONDS: int = 60

    # Cloud Storage config
    BUCKET_NAME: str

    # Google Cloud
    GOOGLE_CLOUD_SERVICE_ACCOUNT_KEY: str

    # Notion
    NOTION_INTERNAL_INTEGRATION_SECRET: str
    NOTION_BLOG_DATABASE: str

    model_config = SettingsConfigDict(case_sensitive=True, env_file_encoding='utf-8')
