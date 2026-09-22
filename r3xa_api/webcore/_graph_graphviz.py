from __future__ import annotations

from pathlib import Path
import os
import subprocess
from typing import Any, Dict

from ._graph_core import (
    build_graph_model,
    compact_hexagon_style,
    format_node_label,
    resolve_styles,
    resolve_edge_style,
)


_DEFAULT_NATIVE_TIMEOUT_SECONDS = 30.0


def _native_timeout_seconds() -> float:
    raw_timeout = os.getenv(
        "R3XA_GRAPHVIZ_NATIVE_TIMEOUT_SECONDS",
        str(_DEFAULT_NATIVE_TIMEOUT_SECONDS),
    )
    try:
        timeout = float(raw_timeout)
    except ValueError as exc:
        raise RuntimeError(
            "R3XA_GRAPHVIZ_NATIVE_TIMEOUT_SECONDS must be a positive number."
        ) from exc
    if timeout <= 0:
        raise RuntimeError(
            "R3XA_GRAPHVIZ_NATIVE_TIMEOUT_SECONDS must be a positive number."
        )
    return timeout


def _pipe_native(dot: Any) -> bytes:
    """Render DOT with a bounded native Graphviz subprocess."""

    from graphviz.backend import dot_command, execute

    command = dot_command.command("dot", "svg")
    try:
        completed = execute.run_check(
            command,
            input=dot.source.encode("utf-8"),
            capture_output=True,
            quiet=True,
            timeout=_native_timeout_seconds(),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Native Graphviz rendering exceeded its configured timeout."
        ) from exc
    return completed.stdout


def build_graphviz_dot(
    data: Dict[str, Any],
    format: str = "svg",
    include_description: bool = True,
    palette: str | None = None,
    relations: str = "all",
) -> Any:
    """Build a Graphviz Digraph from a full R3XA payload."""

    try:
        from graphviz import Digraph
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (graphviz not installed).") from exc

    styles = resolve_styles(palette)
    dot = Digraph(comment="R3XA graph", format=format)
    dot.attr("node", margin="0.2,0.1")
    model = build_graph_model(data, relations=relations)

    for setting in data.get("settings", []):
        setting_id = setting.get("id")
        if not setting_id:
            continue
        label = format_node_label(
            setting.get("title", ""),
            setting.get("description", ""),
            include_description=include_description,
        )
        dot.node(setting_id, label, **compact_hexagon_style(styles["settings"]["root"], label))

    for source in data.get("data_sources", []):
        is_intermediate = source.get("id") in model.intermediate_sources
        style = styles["data_sources"]["intermediate" if is_intermediate else "initial"]
        label = format_node_label(
            source.get("title", ""),
            source.get("description", ""),
            include_description=include_description,
        )
        dot.node(source["id"], label, **style)

    for dataset in data.get("data_sets", []):
        is_intermediate = dataset["id"] in model.used_datasets
        style = styles["data_sets"]["intermediate" if is_intermediate else "final"]
        label = format_node_label(
            dataset.get("title", ""),
            dataset.get("description", ""),
            include_description=include_description,
        )
        dot.node(dataset["id"], label, **style)

    for edge in model.edge_records:
        edge_style = dict(resolve_edge_style(styles, edge))
        if edge.label:
            edge_style["label"] = edge.label
        dot.edge(edge.src, edge.dst, **edge_style)

    return dot


def generate_svg(
    data: Dict[str, Any],
    include_description: bool = True,
    palette: str | None = None,
    relations: str = "all",
) -> bytes:
    """Generate an SVG graph from an R3XA payload."""

    try:
        from graphviz.backend import ExecutableNotFound
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (graphviz not installed).") from exc

    dot = build_graphviz_dot(
        data,
        format="svg",
        include_description=include_description,
        palette=palette,
        relations=relations,
    )
    try:
        return _pipe_native(dot)
    except ExecutableNotFound as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("Graph feature not available (dot executable missing).") from exc


def render_graphviz_file(
    data: Dict[str, Any],
    output_path: Path,
    export_dot: bool = False,
    include_description: bool = True,
    palette: str | None = None,
    relations: str = "all",
) -> Path:
    """Render a Graphviz SVG file and optionally export the DOT source."""

    try:
        from graphviz.backend import ExecutableNotFound
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (graphviz not installed).") from exc

    out_base = Path(output_path)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    dot = build_graphviz_dot(
        data,
        format="svg",
        include_description=include_description,
        palette=palette,
        relations=relations,
    )

    if export_dot:
        dot.save(str(out_base.with_suffix(".dot")))

    svg_path = out_base.with_suffix(".svg")
    try:
        svg_path.write_bytes(_pipe_native(dot))
        return svg_path
    except ExecutableNotFound as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("Graph feature not available (dot executable missing).") from exc
