from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .settings import TEMPLATES_DIR, APP_START

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _page_context(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "app_start": APP_START,
        "app_base": "",
        "static_base": "/static",
        "runtime_name": "runtime.js",
    }


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", _page_context(request))


@router.get("/edit", response_class=HTMLResponse)
async def edit(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "edit.html", _page_context(request))


@router.get("/schema", response_class=HTMLResponse)
async def schema(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "schema.html", _page_context(request))


@router.get("/registry", response_class=HTMLResponse)
async def registry(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "registry.html", _page_context(request))
