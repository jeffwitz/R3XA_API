import json
from pathlib import Path

import pytest

pytest.importorskip("wasmtime")

from r3xa_api.webcore.graph import generate_svg_wasm, render_graph_content, render_graphviz_wasm_file


def _load_payload() -> dict:
    root = Path(__file__).resolve().parents[2]
    return json.loads((root / "examples" / "artifacts" / "dic_pipeline.json").read_text(encoding="utf-8"))


def test_generate_svg_wasm_does_not_need_system_dot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "")
    svg = generate_svg_wasm(_load_payload())

    assert b"<svg" in svg
    assert b"</svg>" in svg


def test_graphviz_wasm_backend_returns_svg_content() -> None:
    content, media_type, extension = render_graph_content(_load_payload(), backend="graphviz-wasm")

    assert b"<svg" in content
    assert media_type == "image/svg+xml"
    assert extension == "svg"


def test_render_graphviz_wasm_file_exports_svg_and_dot(tmp_path: Path) -> None:
    output_base = tmp_path / "graph"

    svg_path = render_graphviz_wasm_file(_load_payload(), output_base, export_dot=True)

    assert svg_path == output_base.with_suffix(".svg")
    assert b"<svg" in svg_path.read_bytes()
    assert "digraph" in output_base.with_suffix(".dot").read_text(encoding="utf-8")
