from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ._graph_core import (
    resolve_styles,
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
        "ctxRenderer": "__R3XA_HEXAGON_RENDERER__",
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


PYVIS_CUSTOM_HEXAGON_SCRIPT = """
function r3xaHexagonRenderer({ctx, id, x, y, state, style, label}) {
    const node = nodes.get(id) || {};
    const width = Number(node.r3xaWidth) || 220;
    const height = Number(node.r3xaHeight) || 80;
    const halfWidth = width * 0.5;
    const halfHeight = height * 0.5;
    const inset = Math.min(halfHeight * 0.5 * 2.0, width * 0.22);
    const vertices = [
        [x - halfWidth, y],
        [x - halfWidth + inset, y + halfHeight],
        [x + halfWidth - inset, y + halfHeight],
        [x + halfWidth, y],
        [x + halfWidth - inset, y - halfHeight],
        [x - halfWidth + inset, y - halfHeight],
    ];
    const color = style.color || {};
    const colors = typeof color === "object" ? color : {};
    const defaultColor = typeof color === "string" ? color : "#e8f1fb";
    const baseBackground = colors.background || defaultColor;
    const baseBorder = colors.border || defaultColor;
    const selectedColors = typeof colors.highlight === "string"
        ? {background: colors.highlight, border: colors.highlight}
        : colors.highlight || {};
    const hoverColors = typeof colors.hover === "string"
        ? {background: colors.hover, border: colors.hover}
        : colors.hover || {};
    const fillColor = state.selected
        ? selectedColors.background || baseBackground
        : state.hover
          ? hoverColors.background || baseBackground
          : baseBackground;
    const borderColor = state.selected
        ? selectedColors.border || baseBorder || fillColor
        : state.hover
          ? hoverColors.border || baseBorder || fillColor
          : baseBorder || fillColor;
    const font = style.font || {};
    const lines = String(label || "").split("\\n");

    function drawNode() {
        ctx.beginPath();
        ctx.moveTo(vertices[0][0], vertices[0][1]);
        for (let index = 1; index < vertices.length; index += 1) {
            ctx.lineTo(vertices[index][0], vertices[index][1]);
        }
        ctx.closePath();
        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.strokeStyle = borderColor;
        ctx.lineWidth = state.selected
            ? style.borderWidthSelected || style.borderWidth || 1
            : style.borderWidth || 1;
        ctx.stroke();

        ctx.fillStyle = node.r3xaFontColor || font.color || "#333333";
        ctx.font = `${font.size || 16}px ${font.face || "Arial"}`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const lineHeight = (font.size || 16) * 1.2;
        const firstLineY = y - (lines.length - 1) * lineHeight * 0.5;
        lines.forEach((line, index) => {
            ctx.fillText(line, x, firstLineY + index * lineHeight);
        });
    }

    return {
        drawNode,
        nodeDimensions: {width, height},
    };
}
""".strip()

PYVIS_HEXAGON_WIDTH_PADDING = 28.0
PYVIS_HEXAGON_HEIGHT_PADDING = 4.0


def _patch_pyvis_custom_shapes(html: str) -> str:
    """Install the JavaScript renderer used for anisotropic settings."""

    marker = json.dumps("__R3XA_HEXAGON_RENDERER__")
    options_marker = f'"ctxRenderer": {marker}'
    if options_marker not in html:
        raise RuntimeError("PyVis options do not contain the custom hexagon marker.")

    patched = html.replace(
        options_marker,
        '"ctxRenderer": r3xaHexagonRenderer',
        1,
    )
    options_declaration = "                  var options = "
    if options_declaration not in patched:
        raise RuntimeError("PyVis HTML does not contain its options declaration.")
    return patched.replace(
        options_declaration,
        f"                  {PYVIS_CUSTOM_HEXAGON_SCRIPT}\n\n{options_declaration}",
        1,
    )


def render_pyvis_html(
    data: Dict[str, Any],
    output_path: Path,
    include_description: bool = True,
    palette: str | None = None,
) -> Path:
    """Render an interactive PyVis HTML graph from an R3XA payload."""

    try:
        from pyvis.network import Network
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (pyvis not installed).") from exc

    styles = graphviz_styles_to_pyvis(resolve_styles(palette))
    model = build_graph_model(data)

    node_labels: Dict[str, str] = {}
    for setting in data.get("settings", []):
        setting_id = setting.get("id")
        if setting_id:
            node_labels[setting_id] = format_node_label(
                setting.get("title", ""),
                setting.get("description", ""),
                include_description=include_description,
            )
    for source in data.get("data_sources", []):
        source_id = source.get("id")
        if source_id:
            node_labels[source_id] = format_node_label(
                source.get("title", ""),
                source.get("description", ""),
                include_description=include_description,
            )
    for dataset in data.get("data_sets", []):
        dataset_id = dataset.get("id")
        if dataset_id:
            node_labels[dataset_id] = format_node_label(
                dataset.get("title", ""),
                dataset.get("description", ""),
                include_description=include_description,
            )

    edge_pairs = [(edge.src, edge.dst) for edge in model.edge_records]
    label_widths = {node_id: estimate_label_width(label) for node_id, label in node_labels.items()}
    label_heights = {node_id: estimate_label_height(label) for node_id, label in node_labels.items()}
    setting_ids = {
        setting.get("id")
        for setting in data.get("settings", [])
        if setting.get("id")
    }
    for setting_id in setting_ids:
        label_widths[setting_id] = label_widths.get(setting_id, 220.0) + PYVIS_HEXAGON_WIDTH_PADDING
        label_heights[setting_id] = label_heights.get(setting_id, 64.0) + PYVIS_HEXAGON_HEIGHT_PADDING
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

    for setting in data.get("settings", []):
        setting_id = setting.get("id")
        if not setting_id:
            continue
        style = dict(styles["settings"]["root"])
        style.update(
            {
                "shape": "custom",
                "r3xaWidth": label_widths.get(setting_id, 220.0),
                "r3xaHeight": label_heights.get(setting_id, 64.0),
            }
        )
        label = node_labels.get(setting_id, "")
        x_coord, y_coord = positions.get(setting_id, (0.0, 0.0))
        net.add_node(setting_id, label=label, x=x_coord, y=y_coord, physics=False, **style)

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
    out_html.write_text(
        _patch_pyvis_custom_shapes(out_html.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return out_html
