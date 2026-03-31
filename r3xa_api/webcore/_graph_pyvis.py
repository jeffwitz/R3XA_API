from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ._graph_core import (
    STYLES,
    build_graph_model,
    compute_graphviz_positions,
    compute_manual_positions,
    estimate_canvas_height,
    estimate_label_height,
    estimate_label_width,
    format_node_label,
    graphviz_styles_to_pyvis,
)


PYVIS_OPTIONS = {
    "nodes": {
        "font": {"size": 16, "face": "Arial"},
        "margin": 14,
        "widthConstraint": {"maximum": 420},
    },
    "physics": {"enabled": False},
    "edges": {
        "arrows": {"to": {"enabled": True, "scaleFactor": 0.7}},
        "smooth": {"enabled": False},
    },
    "interaction": {
        "dragNodes": True,
        "dragView": True,
        "zoomView": True,
    },
}


def render_pyvis_html(data: Dict[str, Any], output_path: Path) -> Path:
    """Render an interactive PyVis HTML graph from an R3XA payload."""

    try:
        from pyvis.network import Network
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (pyvis not installed).") from exc

    styles = graphviz_styles_to_pyvis(STYLES)
    model = build_graph_model(data)

    node_labels: Dict[str, str] = {}
    for source in data.get("data_sources", []):
        source_id = source.get("id")
        if source_id:
            node_labels[source_id] = format_node_label(source.get("title", ""), source.get("description", ""))
    for dataset in data.get("data_sets", []):
        dataset_id = dataset.get("id")
        if dataset_id:
            node_labels[dataset_id] = format_node_label(dataset.get("title", ""), dataset.get("description", ""))

    edge_pairs = [(edge.src, edge.dst) for edge in model.edge_records]
    label_widths = {node_id: estimate_label_width(label) for node_id, label in node_labels.items()}
    label_heights = {node_id: estimate_label_height(label) for node_id, label in node_labels.items()}
    graphviz_layout = compute_graphviz_positions(
        node_ids=model.node_ids,
        edges=edge_pairs,
        label_widths=label_widths,
        label_heights=label_heights,
    )
    if graphviz_layout is not None:
        positions, graphviz_widths = graphviz_layout
        label_widths.update(
            {
                node_id: max(label_widths.get(node_id, 220.0), width)
                for node_id, width in graphviz_widths.items()
            }
        )
    else:
        positions = compute_manual_positions(
            node_ids=model.node_ids,
            edges=edge_pairs,
            levels=model.levels,
            label_widths=label_widths,
        )

    canvas_height = estimate_canvas_height(positions, label_heights)
    net = Network(height=f"{canvas_height}px", width="100%", directed=True)
    net.set_options(json.dumps(PYVIS_OPTIONS))

    for source in data.get("data_sources", []):
        source_id = source.get("id")
        if not source_id:
            continue
        is_intermediate = source_id in model.intermediate_sources
        style = styles["data_sources"]["intermediate" if is_intermediate else "initial"]
        label = node_labels.get(source_id, "")
        x_coord, y_coord = positions.get(source_id, (0.0, 0.0))
        net.add_node(source_id, label=label, x=x_coord, y=y_coord, physics=False, **style)

    for dataset in data.get("data_sets", []):
        dataset_id = dataset.get("id")
        if not dataset_id:
            continue
        is_intermediate = dataset_id in model.used_datasets
        style = styles["data_sets"]["intermediate" if is_intermediate else "final"]
        label = node_labels.get(dataset_id, "")
        x_coord, y_coord = positions.get(dataset_id, (0.0, 0.0))
        net.add_node(dataset_id, label=label, x=x_coord, y=y_coord, physics=False, **style)

    for edge in model.edge_records:
        net.add_edge(edge.src, edge.dst, **styles["edges"][edge.style_key])

    out_html = Path(output_path).with_suffix(".html")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(out_html))
    return out_html
