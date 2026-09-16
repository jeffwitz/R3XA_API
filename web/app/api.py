from json import JSONDecodeError
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, Response, HTTPException, Query
from jsonschema.exceptions import ValidationError
from r3xa_api.registry import validate_item
from r3xa_api.schema import load_schema
from r3xa_api.webcore import (
    build_schema_catalog,
    build_schema_summary,
    build_ui_catalog,
    build_validation_report,
    generate_svg,
)

router = APIRouter()


async def _read_json(request: Request) -> Any:
    try:
        return await request.json()
    except (JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Request body must contain valid JSON.") from exc


@router.post("/validate")
async def validate_payload(request: Request) -> Dict[str, Any]:
    payload = await _read_json(request)
    return build_validation_report(payload)


@router.post("/registry/validate")
async def validate_registry_item(request: Request) -> Dict[str, Any]:
    payload = await _read_json(request)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object.")
    item = payload.get("item", payload)
    kind = payload.get("kind")
    try:
        validate_item(item, kind=kind)
    except (ValidationError, ValueError) as exc:
        return {"valid": False, "errors": [line for line in str(exc).splitlines() if line.strip()]}
    return {"valid": True, "errors": []}


@router.post("/graph")
async def graph_svg(
    request: Request,
    show_description: bool = Query(default=True),
    palette: Optional[str] = Query(default=None),
) -> Response:
    payload = await _read_json(request)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object.")
    try:
        svg_bytes = generate_svg(
            payload,
            include_description=show_description,
            palette=palette,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(content=svg_bytes, media_type="image/svg+xml")

@router.get("/schema")
async def schema_raw() -> Dict[str, Any]:
    return load_schema()


@router.get("/schema/summary")
async def schema_summary() -> Dict[str, Any]:
    return build_schema_summary()


@router.get("/schema/catalog")
async def schema_catalog() -> Dict[str, Any]:
    return build_schema_catalog()


@router.get("/ui")
async def ui_catalog() -> Dict[str, Any]:
    return build_ui_catalog()


@router.get("/profiles")
async def profiles() -> Dict[str, Any]:
    return build_ui_catalog()["profiles"]


@router.get("/schema-summary")
async def schema_summary_legacy() -> Dict[str, Any]:
    return build_schema_summary()
