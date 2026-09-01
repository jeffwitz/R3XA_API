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
async def test_api_schema_catalog() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/schema/catalog")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "2024.7.1"
    assert "data_sources/camera" in payload["sections"]["data_sources"]["kinds"]


@pytest.mark.anyio
async def test_api_ui_catalog() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/ui")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "2024.7.1"
    assert "dic_2d" in payload["profiles"]


@pytest.mark.anyio
async def test_api_profiles() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/profiles")
    assert response.status_code == 200
    assert set(response.json()) == {
        "generic",
        "mechanical_test",
        "dic_2d",
        "camera_images",
        "tabular_file",
        "torsion_test",
        "fatigue_with_overload",
        "tomography",
        "in_situ_tensile",
    }


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
@pytest.mark.parametrize("path", ["/api/validate", "/api/registry/validate", "/api/graph"])
async def test_api_rejects_malformed_json(path: str) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            path,
            content=b"{bad",
            headers={"content-type": "application/json"},
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "Request body must contain valid JSON."


@pytest.mark.anyio
@pytest.mark.parametrize("path", ["/api/registry/validate", "/api/graph"])
async def test_api_rejects_non_object_json_for_object_endpoints(path: str) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(path, json=[])
    assert response.status_code == 400
    assert response.json()["detail"] == "Request body must be a JSON object."


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
async def test_api_graph_svg_can_hide_descriptions(monkeypatch: pytest.MonkeyPatch) -> None:
    svg_payload = b"<svg xmlns='http://www.w3.org/2000/svg'><rect width='1' height='1'/></svg>"

    def _fake_generate_svg(payload: dict, include_description: bool = True) -> bytes:
        assert isinstance(payload, dict)
        assert include_description is False
        return svg_payload

    monkeypatch.setattr(api_module, "generate_svg", _fake_generate_svg)

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/graph?show_description=false", json=_load_example())

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("image/svg+xml")
    assert response.content == svg_payload


@pytest.mark.anyio
async def test_api_graph_svg_success(monkeypatch: pytest.MonkeyPatch) -> None:
    svg_payload = b"<svg xmlns='http://www.w3.org/2000/svg'><rect width='1' height='1'/></svg>"

    def _fake_generate_svg(payload: dict, include_description: bool = True) -> bytes:
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
    def _fake_generate_svg(payload: dict, include_description: bool = True) -> bytes:
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
