import json
import shutil
from pathlib import Path

import pytest

pytest.importorskip("graphviz")
pytest.importorskip("pyvis")

if shutil.which("dot") is None:
    pytest.skip("graphviz 'dot' executable is not available", allow_module_level=True)

from r3xa_api.webcore.graph import generate_svg, render_graphviz_file, render_pyvis_html


def _load_example_payload() -> dict:
    root = Path(__file__).resolve().parents[2]
    payload_path = root / "examples" / "artifacts" / "dic_pipeline.json"
    return json.loads(payload_path.read_text(encoding="utf-8"))


def test_generate_svg_returns_svg_document() -> None:
    payload = _load_example_payload()
    svg = generate_svg(payload)
    svg_text = svg.decode("utf-8", errors="ignore")

    assert "<svg" in svg_text
    assert "</svg>" in svg_text


def test_render_graphviz_file_exports_svg_and_dot(tmp_path: Path) -> None:
    payload = _load_example_payload()
    output_base = tmp_path / "graph_dic_pipeline"

    svg_path = render_graphviz_file(payload, output_base, export_dot=True)
    dot_path = output_base.with_suffix(".dot")

    assert svg_path.exists()
    assert svg_path.suffix == ".svg"
    assert dot_path.exists()
    assert "digraph" in dot_path.read_text(encoding="utf-8")


def test_render_pyvis_html_generates_network_page(tmp_path: Path) -> None:
    payload = _load_example_payload()
    output_base = tmp_path / "graph_dic_pipeline"

    html_path = render_pyvis_html(payload, output_base)
    html = html_path.read_text(encoding="utf-8")

    assert html_path.exists()
    assert html_path.suffix == ".html"
    assert "new vis.Network" in html
    assert "mynetwork" in html
