from typing import Any, Dict

from fastapi import APIRouter, Request, Response, HTTPException
from r3xa_api.schema import load_schema
from r3xa_api.webcore import build_schema_summary, build_validation_report, generate_svg

router = APIRouter()


@router.post("/validate")
async def validate_payload(request: Request) -> Dict[str, Any]:
    payload = await request.json()
    return build_validation_report(payload)


@router.post("/graph")
async def graph_svg(request: Request) -> Response:
    payload = await request.json()
    try:
        svg_bytes = generate_svg(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(content=svg_bytes, media_type="image/svg+xml")

@router.get("/schema")
async def schema_raw() -> Dict[str, Any]:
    return load_schema()


@router.get("/schema/summary")
async def schema_summary() -> Dict[str, Any]:
    return build_schema_summary()


@router.get("/schema-summary")
async def schema_summary_legacy() -> Dict[str, Any]:
    return build_schema_summary()
