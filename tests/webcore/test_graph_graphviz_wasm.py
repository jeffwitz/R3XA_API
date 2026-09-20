import json
from pathlib import Path

import pytest

from r3xa_api.webcore.graph import generate_svg_wasm, render_graph_content, render_graphviz_wasm_file
from r3xa_api.webcore._graph_core import compute_graphviz_positions


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


def test_graphviz_wasm_layout_is_available_without_system_dot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "")
    positions = compute_graphviz_positions(
        ["source", "dataset", "result"],
        [("source", "dataset"), ("dataset", "result")],
        {"source": 220.0, "dataset": 220.0, "result": 220.0},
        {"source": 64.0, "dataset": 64.0, "result": 64.0},
    )

    assert positions is not None
    node_positions, node_widths = positions
    assert set(node_positions) == {"source", "dataset", "result"}
    assert set(node_widths) == set(node_positions)
    assert node_positions["source"][1] < node_positions["dataset"][1] < node_positions["result"][1]


def test_render_graphviz_wasm_file_exports_svg_and_dot(tmp_path: Path) -> None:
    output_base = tmp_path / "graph"

    svg_path = render_graphviz_wasm_file(_load_payload(), output_base, export_dot=True)

    assert svg_path == output_base.with_suffix(".svg")
    assert b"<svg" in svg_path.read_bytes()
    assert "digraph" in output_base.with_suffix(".dot").read_text(encoding="utf-8")
