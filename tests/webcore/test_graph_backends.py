import json
import re
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


def test_pyvis_and_graphviz_export_same_node_and_edge_counts(tmp_path: Path) -> None:
    payload = _load_example_payload()
    output_base = tmp_path / "graph_dic_pipeline"

    render_graphviz_file(payload, output_base, export_dot=True)
    html_path = render_pyvis_html(payload, output_base)

    dot_text = output_base.with_suffix(".dot").read_text(encoding="utf-8")
    html_text = html_path.read_text(encoding="utf-8")

    expected_node_ids = {
        item["id"]
        for section in ("data_sources", "data_sets")
        for item in payload.get(section, [])
        if item.get("id")
    }
    def _input_count(source: dict) -> int:
        value = source.get("input_data_sets")
        if not value:
            return 0
        if isinstance(value, list):
            return len([v for v in value if v])
        if isinstance(value, dict):
            return len([v for v in value.values() if v])
        return 0

    def _source_count(dataset: dict) -> int:
        value = dataset.get("data_sources")
        if value is None and "data_source" in dataset:
            value = dataset.get("data_source")
        if not value:
            return 0
        if isinstance(value, list):
            return len([v for v in value if v])
        return 1

    expected_edge_count = sum(_input_count(source) for source in payload.get("data_sources", [])) + sum(
        _source_count(dataset) for dataset in payload.get("data_sets", [])
    )

    dot_node_ids = {
        node_id
        for node_id in re.findall(r"^\s*([A-Za-z0-9_]+)\s+\[", dot_text, flags=re.MULTILINE)
        if node_id != "node"
    }
    dot_edge_count = len(re.findall(r"->", dot_text))

    nodes_match = re.search(r"nodes = new vis\.DataSet\((\[[\s\S]*?\])\);", html_text)
    edges_match = re.search(r"edges = new vis\.DataSet\((\[[\s\S]*?\])\);", html_text)
    assert nodes_match is not None
    assert edges_match is not None

    pyvis_nodes = json.loads(nodes_match.group(1))
    pyvis_edges = json.loads(edges_match.group(1))
    pyvis_node_ids = {node["id"] for node in pyvis_nodes}

    assert dot_node_ids == expected_node_ids
    assert pyvis_node_ids == expected_node_ids
    assert dot_edge_count == expected_edge_count
    assert len(pyvis_edges) == expected_edge_count
