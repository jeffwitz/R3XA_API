from typing import Any, Dict

from fastapi import APIRouter, Request

from r3xa_api.webcore import build_schema_summary, build_validation_report

router = APIRouter()


@router.post("/validate")
async def validate_payload(request: Request) -> Dict[str, Any]:
    payload = await request.json()
    return build_validation_report(payload)


@router.get("/schema-summary")
async def schema_summary() -> Dict[str, Any]:
    return build_schema_summary()
