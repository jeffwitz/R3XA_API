from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ._graph_core import STYLES, build_graph_model


def build_graphviz_dot(data: Dict[str, Any], format: str = "svg") -> Any:
    """Build a Graphviz Digraph from a full R3XA payload."""

    try:
        from graphviz import Digraph
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (graphviz not installed).") from exc

    dot = Digraph(comment="R3XA graph", format=format)
    dot.attr("node", margin="0.2,0.1")
    model = build_graph_model(data)

    for source in data.get("data_sources", []):
        is_intermediate = source.get("id") in model.intermediate_sources
        style = STYLES["data_sources"]["intermediate" if is_intermediate else "initial"]
        label = f"{source.get('title','')}\n({source.get('description','')})"
        dot.node(source["id"], label, **style)

    for dataset in data.get("data_sets", []):
        is_intermediate = dataset["id"] in model.used_datasets
        style = STYLES["data_sets"]["intermediate" if is_intermediate else "final"]
        label = f"{dataset.get('title','')}\n({dataset.get('description','')})"
        dot.node(dataset["id"], label, **style)

    for edge in model.edge_records:
        dot.edge(edge.src, edge.dst, **STYLES["edges"][edge.style_key])

    return dot


def generate_svg(data: Dict[str, Any]) -> bytes:
    """Generate an SVG graph from an R3XA payload."""

    try:
        from graphviz.backend import ExecutableNotFound
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (graphviz not installed).") from exc

    dot = build_graphviz_dot(data, format="svg")
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
    dot = build_graphviz_dot(data, format="svg")

    if export_dot:
        dot.save(str(out_base.with_suffix(".dot")))

    try:
        return Path(dot.render(str(out_base), view=False, cleanup=True))
    except ExecutableNotFound as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("Graph feature not available (dot executable missing).") from exc
