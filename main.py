from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, Request
from starlette.middleware.cors import CORSMiddleware
import json

from app.auth.firebase import initialize_firebase
from app.core.dependencies import get_settings, get_logger, get_mongo
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.response_middleware import ResponseFormatterMiddleware

from app.api.base_router import router as base_router
from app.services.websocket_manager import get_websocket_manger
from app.utils.time import now_in_luanda

settings = get_settings()
logger = get_logger()
websocket_manager = get_websocket_manger()


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
        "timestamp": now_in_luanda().isoformat(),
        "version": app.version
    }


@app.post("/compile-latex")
async def compile_latex(request: Request):
    body = await request.json()
    latex_code = body["inputs"]["main.tex"]

    files = {
        'file': ('main.tex', latex_code, 'application/x-tex')
    }

    try:
        response = requests.post("https://latexonline.cc/data", files=files)

        if response.headers.get("Content-Type") != "application/pdf":
            # fallback: latexonline returned an error PDF or text
            return Response(content=response.content, media_type=response.headers.get("Content-Type", "text/plain"))

        return Response(
            content=response.content,
            media_type="application/pdf"
        )
    except Exception as e:
        return Response(content=str(e), status_code=500)



@app.websocket("/ws/{restaurant_id}/{category}")
async def websocket_endpoint(
        websocket: WebSocket,
        restaurant_id: str,
        category: str):
    key = f"{restaurant_id}/{category}"
    await websocket_manager.connect(websocket, key)
    try:
        while True:
            # if websocket.application_state == WebSocketState.CONNECTED:
            data = await websocket.receive_text()
            data_json = json.loads(data)  # Deserialize JSON string to Python dict
            response_json = json.dumps({"message": category, "data": data_json})
            await websocket_manager.broadcast(response_json, key)
    except WebSocketDisconnect as close:
        logger.info(f"WebSocket disconnected: {restaurant_id} to the websocket {category}")
        logger.info(f"Reason: {close.reason} ({close.code})")
    except Exception as error:
        logger.error(f"Error: {error}")
    finally:
        await websocket_manager.disconnect(websocket, key)