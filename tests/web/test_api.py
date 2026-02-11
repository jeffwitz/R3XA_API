import json
from pathlib import Path

import httpx
import pytest

pytest.importorskip("fastapi")

from httpx import ASGITransport
from web.app.main import create_app


def _load_example() -> dict:
    root = Path(__file__).resolve().parents[2]
    path = root / "examples" / "artifacts" / "dic_pipeline.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _load_registry_item() -> dict:
    root = Path(__file__).resolve().parents[2]
    path = root / "registry" / "data_sources" / "camera" / "avt_dolphin_f145b.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.anyio
async def test_api_schema_summary() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/schema/summary")
    assert response.status_code == 200
    payload = response.json()
    assert "schema_version" in payload
    assert "sections" in payload


@pytest.mark.anyio
async def test_api_schema_raw() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/schema")
    assert response.status_code == 200
    payload = response.json()
    assert "properties" in payload


@pytest.mark.anyio
async def test_api_validate_valid() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = _load_example()
        response = await client.post("/api/validate", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert report["valid"] is True
    assert report["errors"] == []


@pytest.mark.anyio
async def test_api_validate_invalid() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = _load_example()
        payload["version"] = "invalid"
        response = await client.post("/api/validate", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert report["valid"] is False
    assert report["errors"]


@pytest.mark.anyio
async def test_api_registry_validate_valid() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        item = _load_registry_item()
        response = await client.post("/api/registry/validate", json={"item": item})
    assert response.status_code == 200
    report = response.json()
    assert report["valid"] is True
    assert report["errors"] == []


@pytest.mark.anyio
async def test_api_registry_validate_invalid() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        item = _load_registry_item()
        item.pop("kind", None)
        response = await client.post("/api/registry/validate", json={"item": item})
    assert response.status_code == 200
    report = response.json()
    assert report["valid"] is False
    assert report["errors"]


@pytest.mark.anyio
async def test_registry_page_available() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/registry")
    assert response.status_code == 200
