from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .settings import TEMPLATES_DIR, APP_START

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"request": request, "app_start": APP_START})


@router.get("/edit", response_class=HTMLResponse)
async def edit(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "edit.html", {"request": request, "app_start": APP_START})


@router.get("/schema", response_class=HTMLResponse)
async def schema(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "schema.html", {"request": request, "app_start": APP_START})


@router.get("/registry", response_class=HTMLResponse)
async def registry(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "registry.html", {"request": request, "app_start": APP_START})
