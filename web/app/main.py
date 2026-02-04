from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from time import time

from .api import router as api_router
from .pages import router as pages_router
from .settings import STATIC_DIR


APP_START = int(time())


def create_app() -> FastAPI:
    app = FastAPI(title="R3XA Web")
    app.include_router(api_router, prefix="/api")
    app.include_router(pages_router)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


app = create_app()
