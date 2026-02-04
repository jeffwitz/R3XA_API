import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .pages import router as pages_router
from .settings import STATIC_DIR


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("uvicorn.error").info("Starting R3XA Web")
    app = FastAPI(title="R3XA Web")
    origins = [
        origin.strip()
        for origin in os.getenv("R3XA_CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if origins:
        allow_credentials = os.getenv("R3XA_CORS_ALLOW_CREDENTIALS", "0") == "1"
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=allow_credentials,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
        )
    app.include_router(api_router, prefix="/api")
    app.include_router(pages_router)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


app = create_app()
