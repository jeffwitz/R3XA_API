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


GRAPH_CASES = [
    ("dic_pipeline", "dic_pipeline.json"),
    ("qi_hu", "qi_hu_from_scratch.json"),
]


def _load_example_payload(filename: str) -> dict:
    root = Path(__file__).resolve().parents[2]
    payload_path = root / "examples" / "artifacts" / filename
    return json.loads(payload_path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(("case_name", "filename"), GRAPH_CASES)
def test_generate_svg_returns_svg_document(case_name: str, filename: str) -> None:
    payload = _load_example_payload(filename)
    svg = generate_svg(payload)
    svg_text = svg.decode("utf-8", errors="ignore")

    assert "<svg" in svg_text
    assert "</svg>" in svg_text


def test_graph_renderers_can_hide_descriptions(tmp_path: Path) -> None:
    payload = _load_example_payload("dic_pipeline.json")
    output_base = tmp_path / "graph_dic_pipeline_hidden"

    render_graphviz_file(payload, output_base, export_dot=True, include_description=False)
    html_path = render_pyvis_html(payload, output_base, include_description=False)

    dot_text = output_base.with_suffix(".dot").read_text(encoding="utf-8")
    html_text = html_path.read_text(encoding="utf-8")

    assert "raw images from CCD camera" not in dot_text
    assert "raw images from CCD camera" not in html_text
    assert "graylevel images" in dot_text
    assert "graylevel images" in html_text


@pytest.mark.parametrize(("case_name", "filename"), GRAPH_CASES)
def test_render_graphviz_file_exports_svg_and_dot(case_name: str, filename: str, tmp_path: Path) -> None:
    payload = _load_example_payload(filename)
    output_base = tmp_path / f"graph_{case_name}"

    svg_path = render_graphviz_file(payload, output_base, export_dot=True)
    dot_path = output_base.with_suffix(".dot")

    assert svg_path.exists()
    assert svg_path.suffix == ".svg"
    assert dot_path.exists()
    assert "digraph" in dot_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(("case_name", "filename"), GRAPH_CASES)
def test_render_pyvis_html_generates_network_page(case_name: str, filename: str, tmp_path: Path) -> None:
    payload = _load_example_payload(filename)
    output_base = tmp_path / f"graph_{case_name}"

    html_path = render_pyvis_html(payload, output_base)
    html = html_path.read_text(encoding="utf-8")

    assert html_path.exists()
    assert html_path.suffix == ".html"
    assert "new vis.Network" in html
    assert "mynetwork" in html


def test_pyvis_settings_use_anisotropic_custom_hexagons(tmp_path: Path) -> None:
    payload = _load_example_payload("qi_hu_from_scratch.json")
    html_path = render_pyvis_html(payload, tmp_path / "graph_qi_document")
    html = html_path.read_text(encoding="utf-8")

    nodes_match = re.search(r"nodes = new vis\.DataSet\((\[[\s\S]*?\])\);", html)
    assert nodes_match is not None
    nodes = json.loads(nodes_match.group(1))
    settings = [node for node in nodes if node["id"] in {"sample", "settings_Instron_tensile_test"}]

    assert len(settings) == 2
    assert all(node["shape"] == "custom" for node in settings)
    assert all(node["r3xaWidth"] != node["r3xaHeight"] for node in settings)
    assert abs(settings[0]["x"] - settings[1]["x"]) >= (
        settings[0]["r3xaWidth"] + settings[1]["r3xaWidth"]
    ) * 0.5
    assert '"ctxRenderer": r3xaHexagonRenderer' in html
    assert "function r3xaHexagonRenderer" in html
    assert '"r3xaFontColor": "#ffffff"' in html


def test_pyvis_hexagons_use_the_selected_palette_font_color(tmp_path: Path) -> None:
    payload = _load_example_payload("qi_hu_from_scratch.json")
    html_path = render_pyvis_html(payload, tmp_path / "graph_qi_classic", palette="classic")
    html = html_path.read_text(encoding="utf-8").lower()

    assert '"r3xafontcolor": "#333333"' in html
    assert "node.r3xafontcolor || font.color || \"#333333\"" in html


@pytest.mark.parametrize(("case_name", "filename"), GRAPH_CASES)
def test_pyvis_and_graphviz_export_same_node_and_edge_counts(case_name: str, filename: str, tmp_path: Path) -> None:
    payload = _load_example_payload(filename)
    output_base = tmp_path / f"graph_{case_name}"

    render_graphviz_file(payload, output_base, export_dot=True)
    html_path = render_pyvis_html(payload, output_base)

    dot_text = output_base.with_suffix(".dot").read_text(encoding="utf-8")
    html_text = html_path.read_text(encoding="utf-8")

    expected_node_ids = {
        item["id"]
        for section in ("settings", "data_sources", "data_sets")
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
        value = dataset.get("parent_data_sources")
        if not value:
            return 0
        if isinstance(value, list):
            return len([v for v in value if v])
        return 1

    def _associated_source_count(setting: dict) -> int:
        value = setting.get("attached_data_sources")
        if not value:
            return 0
        if isinstance(value, list):
            return len([item for item in value if item])
        return 1

    expected_edge_count = (
        sum(_associated_source_count(setting) for setting in payload.get("settings", []))
        + sum(_input_count(source) for source in payload.get("data_sources", []))
        + sum(_source_count(dataset) for dataset in payload.get("data_sets", []))
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


@pytest.mark.parametrize(("case_name", "filename"), GRAPH_CASES)
def test_render_pyvis_html_fallback_layout_without_graphviz(
    case_name: str,
    filename: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _load_example_payload(filename)
    output_base = tmp_path / f"graph_{case_name}_fallback"

    monkeypatch.setattr("r3xa_api.webcore._graph_pyvis.compute_graphviz_positions", lambda *args, **kwargs: None)
    html_path = render_pyvis_html(payload, output_base)
    html = html_path.read_text(encoding="utf-8")

    assert html_path.exists()
    assert "new vis.Network" in html
    assert "_route_helper_" not in html


def test_hexagon_vertices_fill_the_requested_box():
    from r3xa_api.webcore._graph_networkx import DEFAULT_LAYOUT_CONFIG, _hexagon_vertices

    vertices = _hexagon_vertices(0.0, 0.0, 200.0, 60.0, DEFAULT_LAYOUT_CONFIG)
    xs = [x for x, _ in vertices]
    ys = [y for _, y in vertices]

    assert len(vertices) == 6
    # Matplotlib has no non-isotropic hexagon: RegularPolygon takes a single
    # radius and BoxStyle offers none, so the corners are computed. They must
    # span exactly the box asked for, not a regular hexagon inside it.
    assert max(xs) - min(xs) == 200.0
    assert max(ys) - min(ys) == 60.0
    assert (max(xs) - min(xs)) != (max(ys) - min(ys))
    # Flat top and bottom, a point at mid-height on each side.
    assert sorted(ys).count(30.0) == 2 and sorted(ys).count(-30.0) == 2
    assert ys.count(0.0) == 2


def test_hexagon_inset_is_capped_on_narrow_nodes():
    from r3xa_api.webcore._graph_networkx import DEFAULT_LAYOUT_CONFIG, _hexagon_vertices

    # A tall, narrow node: a 45-degree slope would eat the whole width and
    # collapse the shape into a diamond, so the inset is capped.
    vertices = _hexagon_vertices(0.0, 0.0, 100.0, 400.0, DEFAULT_LAYOUT_CONFIG)
    xs = sorted({round(x, 6) for x, _ in vertices})

    assert len(xs) == 4, "the flat edges must survive"
    inset = xs[1] - xs[0]
    assert inset <= 100.0 * DEFAULT_LAYOUT_CONFIG.hexagon_max_inset_ratio + 1e-9


def test_each_shape_gets_its_own_drawing_margins():
    from r3xa_api.webcore._graph_networkx import DEFAULT_LAYOUT_CONFIG, _height_scale, _width_scale

    config = DEFAULT_LAYOUT_CONFIG
    # The angled ends eat horizontal room, so a hexagon needs the widest margin.
    assert _width_scale("hexagon", config) > _width_scale("box", config)
    assert _width_scale("box", config) > _width_scale("ellipse", config)
    assert _height_scale("hexagon", config) == config.hexagon_draw_height_scale
    # An unknown shape falls back to the box margins rather than failing.
    assert _width_scale("diamond", config) == _width_scale("box", config)


def test_settings_render_as_a_hexagon_patch(tmp_path, monkeypatch):
    pytest.importorskip("networkx")
    pytest.importorskip("matplotlib")
    import matplotlib.patches as patches

    from r3xa_api.webcore import _graph_networkx

    # Both palettes ask for a hexagon, and the backend used to silently draw a
    # box for anything that was not an ellipse.
    from r3xa_api.webcore._graph_core import PALETTES

    assert PALETTES["document"]["settings"]["root"]["shape"] == "hexagon"
    assert PALETTES["classic"]["settings"]["root"]["shape"] == "hexagon"

    polygons: list = []
    real_polygon = patches.Polygon

    def recording_polygon(xy, **kwargs):
        polygons.append(list(xy))
        return real_polygon(xy, **kwargs)

    monkeypatch.setattr(patches, "Polygon", recording_polygon)

    payload = {
        "settings": [{"id": "stg-a", "kind": "settings/specimen", "title": "316L"}],
        "data_sources": [],
        "data_sets": [],
    }
    path = _graph_networkx.render_networkx_matplotlib_file(payload, tmp_path / "graph")

    assert path.exists()
    assert len(polygons) == 1, "the setting must be drawn as a polygon, not a box"
    assert len(polygons[0]) == 6, "six corners, not a regular polygon patch"
