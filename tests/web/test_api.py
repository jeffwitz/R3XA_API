import json
from pathlib import Path

import httpx
import pytest

pytest.importorskip("fastapi")

from httpx import ASGITransport
from web.app import api as api_module
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


@pytest.mark.anyio
async def test_api_graph_svg_success(monkeypatch: pytest.MonkeyPatch) -> None:
    svg_payload = b"<svg xmlns='http://www.w3.org/2000/svg'><rect width='1' height='1'/></svg>"

    def _fake_generate_svg(payload: dict) -> bytes:
        assert isinstance(payload, dict)
        return svg_payload

    monkeypatch.setattr(api_module, "generate_svg", _fake_generate_svg)

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/graph", json=_load_example())

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("image/svg+xml")
    assert response.content == svg_payload


@pytest.mark.anyio
async def test_api_graph_svg_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_generate_svg(payload: dict) -> bytes:
        raise RuntimeError("Graph feature not available (graphviz not installed).")

    monkeypatch.setattr(api_module, "generate_svg", _fake_generate_svg)

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/graph", json=_load_example())

    assert response.status_code == 503
    assert response.json()["detail"] == "Graph feature not available (graphviz not installed)."


@pytest.mark.anyio
async def test_health_endpoint() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload
    assert "timestamp" in payload
