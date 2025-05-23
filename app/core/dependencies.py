import json
import logging
from functools import lru_cache

from app.core.config import Settings
from app.db.mongo import MongoDBClient
from app.schema import user


@lru_cache()
def get_settings():
    return Settings()


def get_service_account_credentials():
    settings = get_settings()
    credentials = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
    credentials["private_key"] = credentials["private_key"].replace("\\n", "\n")
    return credentials

def get_logger():
    logger = logging.getLogger("main")

    if not logger.handlers:  # Prevent duplicate handlers
        logger.setLevel(logging.INFO)

        # Define log format
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # File handler
        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setFormatter(formatter)

        # Console handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger


@lru_cache()
def get_mongo():
    settings = get_settings()
    return MongoDBClient(
        mongo_uri=settings.MONGO_DB_URI,
        database_name=settings.MONGO_DB_DATABASE_NAME,
        document_models=[user.UserDocument]
    )