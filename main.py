from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime

from app.auth.firebase import initialize_firebase
from app.core.dependencies import get_settings, get_logger, get_mongo
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.response_middleware import ResponseFormatterMiddleware

from app.api.base_router import router as base_router

settings = get_settings()
logger = get_logger()

@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:

    logger.info(f"App started in {settings.ENVIRONMENT} mode")

    initialize_firebase()
    logger.info("Initializing Firebase")

    mongo_client = get_mongo()
    logger.info("Initializing Mongo DB client")

    try:
        await mongo_client.init_db()
    except Exception as error:
        logger.error(error)

    yield

    logger.info("Closing Mongo DB client connection")
    await mongo_client.close_connection()

    logger.info("Shutting down")


app = FastAPI(lifespan=lifespan,
              title=settings.PROJECT_NAME)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(ResponseFormatterMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(base_router, prefix=settings.API_BASE_ROUTE)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": app.version
    }