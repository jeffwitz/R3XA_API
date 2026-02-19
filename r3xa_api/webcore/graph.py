from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable


STYLES = {
    "data_sources": {
        "initial": {
            "shape": "ellipse",
            "fillcolor": "white",
            "color": "lightgreen",
            "style": "filled",
            "penwidth": "4",
        },
        "intermediate": {
            "shape": "ellipse",
            "fillcolor": "lightblue",
            "color": "black",
            "style": "filled",
            "penwidth": "2",
        },
    },
    "data_sets": {
        "intermediate": {
            "shape": "box",
            "fillcolor": "lightgrey",
            "color": "black",
            "style": "filled",
            "penwidth": "2",
        },
        "final": {
            "shape": "box",
            "fillcolor": "#FFA07A",
            "color": "red",
            "style": "filled",
            "penwidth": "6",
        },
    },
    "edges": {
        "data_initial": {"color": "black"},
        "data": {"color": "black"},
        "input": {"color": "black"},
    },
}


def _get_input_data_sets(source: Dict[str, Any]) -> Iterable[str]:
    """Return upstream dataset ids declared by a data source."""

    value = source.get("input_data_sets")
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    if isinstance(value, dict):
        return [v for v in value.values() if v]
    return []


def _get_data_sources(dataset: Dict[str, Any]) -> Iterable[str]:
    """Return source ids that feed a dataset, handling legacy singular key."""

    value = dataset.get("data_sources")
    if value is None and "data_source" in dataset:
        value = dataset.get("data_source")
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    return [value]


def _compute_used_datasets(data: Dict[str, Any]) -> set[str]:
    """Return dataset ids consumed as inputs by intermediate data sources."""

    used = set()
    for source in data.get("data_sources", []):
        for ds_id in _get_input_data_sets(source):
            used.add(ds_id)
    return used


def graphviz_styles_to_pyvis(styles: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Map Graphviz styles to PyVis styles using a single source of truth."""

    graphviz_styles = styles or STYLES
    pyvis_styles: Dict[str, Any] = {"data_sources": {}, "data_sets": {}, "edges": {}}

    for node_type in ("data_sources", "data_sets"):
        for status, attrs in graphviz_styles[node_type].items():
            pyvis_styles[node_type][status] = {
                "borderWidth": int(attrs.get("penwidth", 2)),
                "color": {
                    "border": attrs.get("color", "black"),
                    "background": attrs.get("fillcolor", "lightgrey"),
                },
                "shape": attrs.get("shape", "ellipse"),
            }

    for edge_type, attrs in graphviz_styles["edges"].items():
        pyvis_styles["edges"][edge_type] = {"color": attrs.get("color", "black")}

    return pyvis_styles


def _build_graphviz_dot(data: Dict[str, Any], format: str = "svg") -> Any:
    """Build a Graphviz Digraph from a full R3XA payload."""

    try:
        from graphviz import Digraph
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (graphviz not installed).") from exc

    dot = Digraph(comment="R3XA graph", format=format)
    dot.attr("node", margin="0.2,0.1")

    used_datasets = _compute_used_datasets(data)
    intermediate_sources = {s.get("id") for s in data.get("data_sources", []) if _get_input_data_sets(s)}

    for source in data.get("data_sources", []):
        is_intermediate = source.get("id") in intermediate_sources
        style = STYLES["data_sources"]["intermediate" if is_intermediate else "initial"]
        label = f"{source.get('title','')}\n({source.get('description','')})"
        dot.node(source["id"], label, **style)

    for dataset in data.get("data_sets", []):
        is_intermediate = dataset["id"] in used_datasets
        style = STYLES["data_sets"]["intermediate" if is_intermediate else "final"]
        label = f"{dataset.get('title','')}\n({dataset.get('description','')})"
        dot.node(dataset["id"], label, **style)

    for source in data.get("data_sources", []):
        for input_set in _get_input_data_sets(source):
            dot.edge(input_set, source["id"], **STYLES["edges"]["input"])

    for dataset in data.get("data_sets", []):
        for src in _get_data_sources(dataset):
            edge_style = (
                STYLES["edges"]["data_initial"] if src not in intermediate_sources else STYLES["edges"]["data"]
            )
            dot.edge(src, dataset["id"], **edge_style)

    return dot


def generate_svg(data: Dict[str, Any]) -> bytes:
    """Generate an SVG graph from an R3XA payload."""

    try:
        from graphviz.backend import ExecutableNotFound
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (graphviz not installed).") from exc

    dot = _build_graphviz_dot(data, format="svg")
    try:
        return dot.pipe(format="svg")
    except ExecutableNotFound as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("Graph feature not available (dot executable missing).") from exc


def render_graphviz_file(data: Dict[str, Any], output_path: Path, export_dot: bool = False) -> Path:
    """Render a Graphviz SVG file and optionally export the DOT source."""

    try:
        from graphviz.backend import ExecutableNotFound
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (graphviz not installed).") from exc

    out_base = Path(output_path)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    dot = _build_graphviz_dot(data, format="svg")

    if export_dot:
        dot.save(str(out_base.with_suffix(".dot")))

    try:
        return Path(dot.render(str(out_base), view=False, cleanup=True))
    except ExecutableNotFound as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("Graph feature not available (dot executable missing).") from exc


def render_pyvis_html(data: Dict[str, Any], output_path: Path) -> Path:
    """Render an interactive PyVis HTML graph from an R3XA payload."""

    try:
        from pyvis.network import Network
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (pyvis not installed).") from exc

    net = Network(height="900px", width="1000px", directed=True)
    net.set_options(
        """
        {
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -3000,
              "centralGravity": 0.2,
              "springLength": 2,
              "springConstant": 0.003,
              "damping": 0.09,
              "avoidOverlap": 0
            },
            "solver": "barnesHut"
          }
        }
        """
    )

    styles = graphviz_styles_to_pyvis(STYLES)
    used_datasets = _compute_used_datasets(data)
    intermediate_sources = {s.get("id") for s in data.get("data_sources", []) if _get_input_data_sets(s)}

    for source in data.get("data_sources", []):
        is_intermediate = source.get("id") in intermediate_sources
        style = styles["data_sources"]["intermediate" if is_intermediate else "initial"]
        label = f"{source.get('title','')}\n({source.get('description','')})"
        net.add_node(source["id"], label=label, **style)

    for dataset in data.get("data_sets", []):
        is_intermediate = dataset["id"] in used_datasets
        style = styles["data_sets"]["intermediate" if is_intermediate else "final"]
        label = f"{dataset.get('title','')}\n({dataset.get('description','')})"
        net.add_node(dataset["id"], label=label, **style)

    for source in data.get("data_sources", []):
        for input_set in _get_input_data_sets(source):
            net.add_edge(input_set, source["id"], **styles["edges"]["input"])

    for dataset in data.get("data_sets", []):
        for src in _get_data_sources(dataset):
            edge_style = styles["edges"]["data_initial"] if src not in intermediate_sources else styles["edges"]["data"]
            net.add_edge(src, dataset["id"], **edge_style)

    out_html = Path(output_path).with_suffix(".html")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(out_html))
    return out_html
