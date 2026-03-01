from __future__ import annotations

from collections import deque
from pathlib import Path
from textwrap import wrap
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


def _compute_hierarchical_levels(nodes: Iterable[str], edges: Iterable[tuple[str, str]]) -> Dict[str, int]:
    """Compute stable DAG-like levels for nodes from directed edges."""

    ordered_nodes = list(dict.fromkeys(nodes))
    adjacency: Dict[str, list[str]] = {node_id: [] for node_id in ordered_nodes}
    indegree: Dict[str, int] = {node_id: 0 for node_id in ordered_nodes}

    edge_list = list(edges)
    for src, dst in edge_list:
        if src not in adjacency:
            adjacency[src] = []
            indegree[src] = 0
            ordered_nodes.append(src)
        if dst not in adjacency:
            adjacency[dst] = []
            indegree[dst] = 0
            ordered_nodes.append(dst)
        adjacency[src].append(dst)
        indegree[dst] += 1

    levels: Dict[str, int] = {node_id: 0 for node_id in ordered_nodes}
    queue = deque(node_id for node_id in ordered_nodes if indegree[node_id] == 0)

    while queue:
        current = queue.popleft()
        for child in adjacency[current]:
            levels[child] = max(levels[child], levels[current] + 1)
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    return levels


def _wrap_label_text(value: Any, max_chars: int) -> str:
    """Wrap multiline text into shorter lines for interactive graph readability."""

    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""

    wrapped_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(
            wrap(
                line,
                width=max_chars,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
    return "\n".join(wrapped_lines)


def _format_node_label(title: Any, description: Any) -> str:
    """Build node label with wrapped title/description."""

    title_text = _wrap_label_text(title, max_chars=34)
    description_text = _wrap_label_text(description, max_chars=44)
    if description_text:
        return f"{title_text}\n({description_text})"
    return title_text


def _estimate_label_width(label: str) -> float:
    """Estimate node width in pixels from wrapped label text."""

    lines = label.splitlines() or [label]
    longest = max((len(line) for line in lines), default=10)
    return max(180.0, min(520.0, 68.0 + longest * 7.2))


def _estimate_label_height(label: str) -> float:
    """Estimate node height in pixels from wrapped label text."""

    lines = label.splitlines() or [label]
    line_count = max(1, len(lines))
    return max(56.0, min(260.0, 26.0 + line_count * 17.0))


def _estimate_canvas_height(
    positions: Dict[str, tuple[float, float]],
    label_heights: Dict[str, float],
) -> int:
    """Estimate the PyVis canvas height from positioned node bounding boxes."""

    if not positions:
        return 950

    y_min = float("inf")
    y_max = float("-inf")
    for node_id, (_, y_coord) in positions.items():
        node_height = label_heights.get(node_id, 64.0)
        y_min = min(y_min, y_coord - node_height * 0.5)
        y_max = max(y_max, y_coord + node_height * 0.5)

    content_height = max(0.0, y_max - y_min)
    padded_height = content_height + 220.0
    return int(max(900.0, min(3600.0, padded_height)))


def _compute_manual_positions(
    node_ids: Iterable[str],
    edges: Iterable[tuple[str, str]],
    levels: Dict[str, int],
    label_widths: Dict[str, float],
) -> Dict[str, tuple[float, float]]:
    """Compute collision-free layered positions from node widths and levels."""

    edge_list = list(edges)
    parents: Dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for src, dst in edge_list:
        if dst not in parents:
            parents[dst] = []
        parents[dst].append(src)

    base_order = {node_id: index for index, node_id in enumerate(node_ids)}
    level_nodes: Dict[int, list[str]] = {}
    for node_id in node_ids:
        level_nodes.setdefault(levels.get(node_id, 0), []).append(node_id)

    ordered_levels = sorted(level_nodes.keys())
    ordered_nodes_by_level: Dict[int, list[str]] = {}

    for level in ordered_levels:
        nodes = list(level_nodes[level])

        if level == ordered_levels[0]:
            nodes.sort(key=lambda node_id: base_order.get(node_id, 0))
        else:
            def parent_barycenter(node_id: str) -> float:
                upstream = [parent for parent in parents.get(node_id, []) if levels.get(parent, 0) < level]
                if not upstream:
                    return float(base_order.get(node_id, 0))
                return sum(base_order.get(parent, 0) for parent in upstream) / len(upstream)

            nodes.sort(key=lambda node_id: (parent_barycenter(node_id), base_order.get(node_id, 0)))

        ordered_nodes_by_level[level] = nodes
        for local_index, node_id in enumerate(nodes):
            base_order[node_id] = local_index

    level_separation = 260.0
    min_gap = 74.0
    positions: Dict[str, tuple[float, float]] = {}

    for level in ordered_levels:
        nodes = ordered_nodes_by_level[level]
        if not nodes:
            continue
        widths = [label_widths.get(node_id, 220.0) for node_id in nodes]
        total_width = sum(widths) + min_gap * (len(nodes) - 1)
        cursor = -total_width / 2.0

        for node_id, node_width in zip(nodes, widths):
            x_coord = cursor + node_width / 2.0
            y_coord = float(level) * level_separation
            positions[node_id] = (x_coord, y_coord)
            cursor += node_width + min_gap

    return positions


def _compute_graphviz_positions(
    node_ids: Iterable[str],
    edges: Iterable[tuple[str, str]],
    label_widths: Dict[str, float],
    label_heights: Dict[str, float],
) -> tuple[Dict[str, tuple[float, float]], Dict[str, float]] | None:
    """Compute node positions from Graphviz layout when dot is available."""

    try:
        from graphviz import Digraph
        from graphviz.backend import ExecutableNotFound
    except Exception:
        return None

    dot = Digraph(comment="R3XA pyvis layout")
    dot.attr("graph", rankdir="TB", nodesep="0.55", ranksep="0.95")
    dot.attr("node", margin="0.2,0.1")

    for node_id in node_ids:
        width_in = max(1.8, label_widths.get(node_id, 220.0) / 96.0)
        dot.node(node_id, label=node_id, width=f"{width_in:.3f}")

    for src, dst in edges:
        dot.edge(src, dst)

    try:
        plain = dot.pipe(format="plain").decode("utf-8")
    except (ExecutableNotFound, RuntimeError):
        return None

    raw_positions: Dict[str, tuple[float, float]] = {}
    widths: Dict[str, float] = {}

    for line in plain.splitlines():
        if not line.startswith("node "):
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        node_id = parts[1]
        x_coord = float(parts[2])
        y_coord = float(parts[3])
        width_in = float(parts[4])
        raw_positions[node_id] = (x_coord, y_coord)
        widths[node_id] = width_in * 96.0

    if not raw_positions:
        return None

    level_nodes: Dict[float, list[str]] = {}
    for node_id, (_, y_coord) in raw_positions.items():
        key = round(y_coord, 4)
        level_nodes.setdefault(key, []).append(node_id)

    # Build vertical columns from x anchors, then size each column with the max node bbox width.
    node_columns: Dict[str, int] = {}
    columns: list[dict[str, float]] = []
    ordered_by_x = sorted(raw_positions.items(), key=lambda item: item[1][0])
    for node_id, (x_coord, _) in ordered_by_x:
        node_width_raw = max(1.8, widths.get(node_id, 220.0) / 96.0)

        best_column = -1
        best_distance = float("inf")
        for column_index, column in enumerate(columns):
            distance = abs(x_coord - column["anchor_x"])
            merge_threshold = max(0.6, 0.35 * (column["max_width_raw"] + node_width_raw))
            if distance <= merge_threshold and distance < best_distance:
                best_distance = distance
                best_column = column_index

        if best_column < 0:
            columns.append(
                {
                    "anchor_x": x_coord,
                    "max_width_raw": node_width_raw,
                    "count": 1.0,
                }
            )
            node_columns[node_id] = len(columns) - 1
            continue

        column = columns[best_column]
        column["anchor_x"] = (column["anchor_x"] * column["count"] + x_coord) / (column["count"] + 1.0)
        column["count"] += 1.0
        column["max_width_raw"] = max(column["max_width_raw"], node_width_raw)
        node_columns[node_id] = best_column

    sorted_levels = sorted(level_nodes.keys(), reverse=True)

    # Ensure monotonic columns per row (no duplicate column assignment inside one row).
    for level_key in sorted_levels:
        ordered_nodes = sorted(level_nodes[level_key], key=lambda node_id: raw_positions[node_id][0])
        previous_column = -1
        for node_id in ordered_nodes:
            column_index = node_columns.get(node_id, 0)
            if column_index <= previous_column:
                column_index = previous_column + 1
            while column_index >= len(columns):
                columns.append(
                    {
                        "anchor_x": float(column_index),
                        "max_width_raw": 1.8,
                        "count": 0.0,
                    }
                )
            node_columns[node_id] = column_index
            columns[column_index]["max_width_raw"] = max(
                columns[column_index]["max_width_raw"],
                max(1.8, widths.get(node_id, 220.0) / 96.0),
            )
            previous_column = column_index

    # Compact sparse column indices while preserving left-to-right order.
    used_columns = sorted(set(node_columns.values()))
    remap = {old_index: new_index for new_index, old_index in enumerate(used_columns)}
    node_columns = {node_id: remap[column_index] for node_id, column_index in node_columns.items()}
    column_count = len(used_columns)

    column_widths = [180.0 for _ in range(column_count)]
    for node_id, column_index in node_columns.items():
        column_widths[column_index] = max(column_widths[column_index], widths.get(node_id, 220.0))

    row_heights: list[float] = []
    for level_key in sorted_levels:
        row_height = max(label_heights.get(node_id, 64.0) for node_id in level_nodes[level_key])
        row_heights.append(max(56.0, row_height))

    horizontal_gap = 20.0
    x_centers: list[float] = []
    for column_index, column_width in enumerate(column_widths):
        if column_index == 0:
            x_centers.append(column_width * 0.5)
            continue
        previous_center = x_centers[-1]
        previous_width = column_widths[column_index - 1]
        x_centers.append(previous_center + previous_width * 0.5 + horizontal_gap + column_width * 0.5)

    if x_centers:
        x_shift = (x_centers[0] + x_centers[-1]) * 0.5
        x_centers = [center - x_shift for center in x_centers]

    vertical_margin_ratio = 0.40
    y_centers: list[float] = []
    for row_index, row_height in enumerate(row_heights):
        if row_index == 0:
            y_centers.append(0.0)
            continue
        previous_center = y_centers[-1]
        previous_height = row_heights[row_index - 1]
        vertical_gap = max(40.0, vertical_margin_ratio * max(previous_height, row_height))
        y_centers.append(previous_center + previous_height * 0.5 + vertical_gap + row_height * 0.5)

    positions: Dict[str, tuple[float, float]] = {}
    for row_index, level_key in enumerate(sorted_levels):
        y_coord = y_centers[row_index]
        for node_id in level_nodes[level_key]:
            column_index = node_columns[node_id]
            positions[node_id] = (x_centers[column_index], y_coord)

    return positions, widths


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

    styles = graphviz_styles_to_pyvis(STYLES)
    used_datasets = _compute_used_datasets(data)
    intermediate_sources = {s.get("id") for s in data.get("data_sources", []) if _get_input_data_sets(s)}
    source_ids = [source.get("id") for source in data.get("data_sources", []) if source.get("id")]
    data_set_ids = [dataset.get("id") for dataset in data.get("data_sets", []) if dataset.get("id")]

    edge_records: list[tuple[str, str, Dict[str, Any]]] = []
    for source in data.get("data_sources", []):
        source_id = source.get("id")
        if not source_id:
            continue
        for input_set in _get_input_data_sets(source):
            edge_records.append((input_set, source_id, styles["edges"]["input"]))

    for dataset in data.get("data_sets", []):
        dataset_id = dataset.get("id")
        if not dataset_id:
            continue
        for src in _get_data_sources(dataset):
            edge_style = styles["edges"]["data_initial"] if src not in intermediate_sources else styles["edges"]["data"]
            edge_records.append((src, dataset_id, edge_style))

    levels = _compute_hierarchical_levels(source_ids + data_set_ids, [(src, dst) for src, dst, _ in edge_records])

    node_labels: Dict[str, str] = {}
    for source in data.get("data_sources", []):
        source_id = source.get("id")
        if source_id:
            node_labels[source_id] = _format_node_label(source.get("title", ""), source.get("description", ""))
    for dataset in data.get("data_sets", []):
        dataset_id = dataset.get("id")
        if dataset_id:
            node_labels[dataset_id] = _format_node_label(dataset.get("title", ""), dataset.get("description", ""))

    edge_pairs = [(src, dst) for src, dst, _ in edge_records]
    label_widths = {node_id: _estimate_label_width(label) for node_id, label in node_labels.items()}
    label_heights = {node_id: _estimate_label_height(label) for node_id, label in node_labels.items()}
    graphviz_layout = _compute_graphviz_positions(
        node_ids=source_ids + data_set_ids,
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
        positions = _compute_manual_positions(
            node_ids=source_ids + data_set_ids,
            edges=edge_pairs,
            levels=levels,
            label_widths=label_widths,
        )

    canvas_height = _estimate_canvas_height(positions, label_heights)
    net = Network(height=f"{canvas_height}px", width="100%", directed=True)
    net.set_options(
        """
        {
          "nodes": {
            "font": {
              "size": 16,
              "face": "Arial"
            },
            "margin": 14,
            "widthConstraint": {
              "maximum": 420
            }
          },
          "physics": {
            "enabled": false
          },
          "edges": {
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.7
              }
            },
            "smooth": {
              "enabled": false
            }
          },
          "interaction": {
            "dragNodes": true,
            "dragView": true,
            "zoomView": true
          }
        }
        """
    )

    for source in data.get("data_sources", []):
        source_id = source.get("id")
        if not source_id:
            continue
        is_intermediate = source.get("id") in intermediate_sources
        style = styles["data_sources"]["intermediate" if is_intermediate else "initial"]
        label = node_labels.get(source_id, "")
        x_coord, y_coord = positions.get(source_id, (0.0, 0.0))
        net.add_node(source_id, label=label, x=x_coord, y=y_coord, physics=False, **style)

    for dataset in data.get("data_sets", []):
        dataset_id = dataset.get("id")
        if not dataset_id:
            continue
        is_intermediate = dataset["id"] in used_datasets
        style = styles["data_sets"]["intermediate" if is_intermediate else "final"]
        label = node_labels.get(dataset_id, "")
        x_coord, y_coord = positions.get(dataset_id, (0.0, 0.0))
        net.add_node(dataset_id, label=label, x=x_coord, y=y_coord, physics=False, **style)

    for src, dst, style in edge_records:
        net.add_edge(src, dst, **style)

    out_html = Path(output_path).with_suffix(".html")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(out_html))
    return out_html


def render_networkx_matplotlib_file(
    data: Dict[str, Any],
    output_path: Path,
    format: str = "png",
    dpi: int = 220,
) -> Path:
    """Render a static graph image with NetworkX + Matplotlib."""

    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        from matplotlib.path import Path as MplPath
        from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch
        import networkx as nx
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graph feature not available (networkx/matplotlib not installed).") from exc

    output_format = format.lower().strip()
    if output_format not in {"png", "svg", "pdf"}:
        raise ValueError("Unsupported format. Use one of: png, svg, pdf.")

    styles = STYLES
    used_datasets = _compute_used_datasets(data)
    intermediate_sources = {s.get("id") for s in data.get("data_sources", []) if _get_input_data_sets(s)}
    source_ids = [source.get("id") for source in data.get("data_sources", []) if source.get("id")]
    data_set_ids = [dataset.get("id") for dataset in data.get("data_sets", []) if dataset.get("id")]

    edge_records: list[tuple[str, str, Dict[str, Any]]] = []
    for source in data.get("data_sources", []):
        source_id = source.get("id")
        if not source_id:
            continue
        for input_set in _get_input_data_sets(source):
            edge_records.append((input_set, source_id, styles["edges"]["input"]))

    for dataset in data.get("data_sets", []):
        dataset_id = dataset.get("id")
        if not dataset_id:
            continue
        for src in _get_data_sources(dataset):
            edge_style = styles["edges"]["data_initial"] if src not in intermediate_sources else styles["edges"]["data"]
            edge_records.append((src, dataset_id, edge_style))

    node_ids = source_ids + data_set_ids
    graph = nx.DiGraph()
    graph.add_nodes_from(node_ids)
    graph.add_edges_from((src, dst) for src, dst, _ in edge_records)

    levels = _compute_hierarchical_levels(node_ids, list(graph.edges()))
    node_labels: Dict[str, str] = {}
    node_shapes: Dict[str, str] = {}
    node_style_map: Dict[str, Dict[str, Any]] = {}

    def _format_static_label(title: Any, description: Any, shape: str) -> str:
        if shape == "ellipse":
            title_chars = 18
            desc_chars = 24
        else:
            title_chars = 24
            desc_chars = 30
        title_text = _wrap_label_text(title, max_chars=title_chars)
        description_text = _wrap_label_text(description, max_chars=desc_chars)
        if description_text:
            return f"{title_text}\n({description_text})"
        return title_text

    for source in data.get("data_sources", []):
        source_id = source.get("id")
        if not source_id:
            continue
        is_intermediate = source_id in intermediate_sources
        style = styles["data_sources"]["intermediate" if is_intermediate else "initial"]
        node_shapes[source_id] = "ellipse"
        node_style_map[source_id] = style
        node_labels[source_id] = _format_static_label(
            source.get("title", ""),
            source.get("description", ""),
            "ellipse",
        )

    for dataset in data.get("data_sets", []):
        dataset_id = dataset.get("id")
        if not dataset_id:
            continue
        is_intermediate = dataset_id in used_datasets
        style = styles["data_sets"]["intermediate" if is_intermediate else "final"]
        node_shapes[dataset_id] = "box"
        node_style_map[dataset_id] = style
        node_labels[dataset_id] = _format_static_label(
            dataset.get("title", ""),
            dataset.get("description", ""),
            "box",
        )

    label_widths: Dict[str, float] = {}
    label_heights: Dict[str, float] = {}
    for node_id, label in node_labels.items():
        lines = label.splitlines() or [label]
        longest = max((len(line) for line in lines), default=16)
        line_count = max(1, len(lines))
        text_width = 20.0 + float(longest) * 8.8
        text_height = 12.0 + float(line_count) * 18.0
        if node_shapes.get(node_id, "box") == "ellipse":
            label_widths[node_id] = max(230.0, min(1500.0, text_width * 1.72))
            label_heights[node_id] = max(88.0, min(1000.0, text_height * 2.00))
        else:
            label_widths[node_id] = max(210.0, min(1500.0, text_width * 1.30))
            label_heights[node_id] = max(76.0, min(1000.0, text_height * 1.50))

    edge_pairs = list(graph.edges())
    graphviz_layout = _compute_graphviz_positions(
        node_ids=node_ids,
        edges=edge_pairs,
        label_widths=label_widths,
        label_heights=label_heights,
    )
    if graphviz_layout is not None:
        positions_raw, graphviz_widths = graphviz_layout
        for node_id, width in graphviz_widths.items():
            label_widths[node_id] = max(label_widths.get(node_id, 220.0), width)
    else:
        positions_raw = _compute_manual_positions(
            node_ids=node_ids,
            edges=edge_pairs,
            levels=levels,
            label_widths=label_widths,
        )
    x_scale = 1.0 if graphviz_layout is not None else 1.14
    positions: Dict[str, tuple[float, float]] = {
        node_id: (x_coord * x_scale, y_coord)
        for node_id, (x_coord, y_coord) in positions_raw.items()
    }

    level_nodes: Dict[int, list[str]] = {}
    for node_id in node_ids:
        level_nodes.setdefault(levels.get(node_id, 0), []).append(node_id)
    ordered_levels = sorted(level_nodes.keys())
    row_heights = {
        level: max(label_heights.get(node_id, 80.0) for node_id in level_nodes[level])
        for level in ordered_levels
    }
    row_y: Dict[int, float] = {}
    for index, level in enumerate(ordered_levels):
        if index == 0:
            row_y[level] = 0.0
            continue
        previous_level = ordered_levels[index - 1]
        previous_height = row_heights[previous_level]
        current_height = row_heights[level]
        vertical_gap = max(84.0, 0.55 * max(previous_height, current_height))
        row_y[level] = row_y[previous_level] + previous_height * 0.5 + vertical_gap + current_height * 0.5
    for node_id, (x_coord, _) in positions.items():
        positions[node_id] = (x_coord, row_y.get(levels.get(node_id, 0), 0.0))

    draw_widths: Dict[str, float] = {}
    for node_id in node_ids:
        is_ellipse = node_shapes.get(node_id, "box") == "ellipse"
        width_scale = 1.08 if is_ellipse else 1.18
        draw_widths[node_id] = label_widths.get(node_id, 220.0) * width_scale

    def _spread_row_nodes(level: int, gap: float = 42.0) -> None:
        row_nodes = [node_id for node_id in level_nodes.get(level, []) if node_id in positions]
        if len(row_nodes) < 2:
            return
        row_nodes.sort(key=lambda node_id: positions[node_id][0])
        target_center = sum(positions[node_id][0] for node_id in row_nodes) / float(len(row_nodes))
        new_x = {node_id: positions[node_id][0] for node_id in row_nodes}

        for index in range(1, len(row_nodes)):
            previous = row_nodes[index - 1]
            current = row_nodes[index]
            min_center_gap = 0.5 * draw_widths.get(previous, 220.0) + 0.5 * draw_widths.get(current, 220.0) + gap
            required_x = new_x[previous] + min_center_gap
            if new_x[current] < required_x:
                new_x[current] = required_x

        shifted_center = sum(new_x[node_id] for node_id in row_nodes) / float(len(row_nodes))
        center_shift = target_center - shifted_center
        for node_id in row_nodes:
            positions[node_id] = (new_x[node_id] + center_shift, positions[node_id][1])

    for level in ordered_levels:
        _spread_row_nodes(level)

    row_top = {level: row_y[level] - row_heights[level] * 0.5 for level in ordered_levels}
    row_bottom = {level: row_y[level] + row_heights[level] * 0.5 for level in ordered_levels}

    if not positions:
        positions = {node_id: (0.0, 0.0) for node_id in node_ids}

    x_min = min(
        positions[node_id][0] - label_widths.get(node_id, 220.0) * 0.5
        for node_id in positions
    )
    x_max = max(
        positions[node_id][0] + label_widths.get(node_id, 220.0) * 0.5
        for node_id in positions
    )
    y_min = min(
        positions[node_id][1] - label_heights.get(node_id, 64.0) * 0.5
        for node_id in positions
    )
    y_max = max(
        positions[node_id][1] + label_heights.get(node_id, 64.0) * 0.5
        for node_id in positions
    )

    padding_x = 120.0
    padding_y = 120.0
    dpi_value = max(90, int(dpi))
    layout_dpi = max(120.0, dpi_value * 0.62)
    fig_width = max(18.0, min(46.0, (x_max - x_min + 2.0 * padding_x) / layout_dpi))
    fig_height = max(12.0, min(46.0, (y_max - y_min + 2.0 * padding_y) / layout_dpi))

    figure, axis = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi_value)
    axis.set_xlim(x_min - padding_x, x_max + padding_x)
    axis.set_ylim(y_max + padding_y, y_min - padding_y)
    axis.set_aspect("auto")
    axis.axis("off")
    figure.patch.set_facecolor("white")
    axis.set_facecolor("white")

    node_patches: Dict[str, Any] = {}
    node_boxes: Dict[str, Dict[str, float]] = {}
    node_sizes: Dict[str, tuple[float, float]] = {}
    font_sizes: Dict[str, float] = {}

    for node_id in node_ids:
        x_coord, y_coord = positions.get(node_id, (0.0, 0.0))
        is_ellipse = node_shapes.get(node_id, "box") == "ellipse"
        width_scale = 1.08 if is_ellipse else 1.18
        height_scale = 1.10 if is_ellipse else 1.16
        node_width = label_widths.get(node_id, 220.0) * width_scale
        node_height = label_heights.get(node_id, 64.0) * height_scale

        style = node_style_map.get(node_id, styles["data_sets"]["intermediate"])

        edge_width = float(style.get("penwidth", 2))
        edge_color = style.get("color", "black")
        fill_color = style.get("fillcolor", "lightgrey")
        shape = node_shapes.get(node_id, style.get("shape", "box"))

        if shape == "ellipse":
            patch = Ellipse(
                xy=(x_coord, y_coord),
                width=node_width,
                height=node_height,
                facecolor=fill_color,
                edgecolor=edge_color,
                linewidth=edge_width,
                zorder=2,
            )
        else:
            patch = FancyBboxPatch(
                (x_coord - node_width * 0.5, y_coord - node_height * 0.5),
                node_width,
                node_height,
                boxstyle="round,pad=0.03,rounding_size=10",
                facecolor=fill_color,
                edgecolor=edge_color,
                linewidth=edge_width,
                zorder=2,
            )
        axis.add_patch(patch)
        node_patches[node_id] = patch
        node_sizes[node_id] = (node_width, node_height)
        node_boxes[node_id] = {
            "left": x_coord - node_width * 0.5,
            "right": x_coord + node_width * 0.5,
            "top": y_coord - node_height * 0.5,
            "bottom": y_coord + node_height * 0.5,
        }

        label = node_labels.get(node_id, "")
        lines = label.splitlines() or [label]
        longest = max((len(line) for line in lines), default=12)
        line_count = max(1, len(lines))
        width_fit = (node_width * 0.86) / max(6.0, 0.58 * float(longest))
        height_fit = (node_height * 0.80) / max(10.0, 1.35 * float(line_count))
        size_cap = 11.3 if node_shapes.get(node_id, "box") == "ellipse" else 11.0
        fitted_size = min(size_cap, width_fit, height_fit)
        if node_shapes.get(node_id, "box") == "ellipse":
            fitted_size -= 0.4
        font_sizes[node_id] = max(8.0, fitted_size)

    def _count_vertical_hits(
        x_value: float,
        y_start: float,
        y_end: float,
        src: str,
        dst: str,
    ) -> int:
        low, high = sorted((y_start, y_end))
        hits = 0
        for node_id, box in node_boxes.items():
            if node_id in {src, dst}:
                continue
            if high < box["top"] - 6.0 or low > box["bottom"] + 6.0:
                continue
            if box["left"] - 8.0 <= x_value <= box["right"] + 8.0:
                hits += 1
        return hits

    def _count_segment_hits(
        p0: tuple[float, float],
        p1: tuple[float, float],
        src: str,
        dst: str,
        margin: float = 8.0,
        samples: int = 44,
    ) -> int:
        hit_nodes: set[str] = set()
        x0, y0 = p0
        x1, y1 = p1
        for node_id, box in node_boxes.items():
            if node_id in {src, dst}:
                continue
            min_x = min(x0, x1)
            max_x = max(x0, x1)
            min_y = min(y0, y1)
            max_y = max(y0, y1)
            if max_x < box["left"] - margin or min_x > box["right"] + margin:
                continue
            if max_y < box["top"] - margin or min_y > box["bottom"] + margin:
                continue
            for step in range(1, samples):
                t = float(step) / float(samples)
                x_coord = x0 + (x1 - x0) * t
                y_coord = y0 + (y1 - y0) * t
                if (
                    box["left"] - margin <= x_coord <= box["right"] + margin
                    and box["top"] - margin <= y_coord <= box["bottom"] + margin
                ):
                    hit_nodes.add(node_id)
                    break
        return len(hit_nodes)

    def _count_direct_hits(src: str, dst: str) -> int:
        x0, y0 = positions[src]
        x1, y1 = positions[dst]
        samples = 48
        hits = 0
        for node_id, box in node_boxes.items():
            if node_id in {src, dst}:
                continue
            touched = False
            for step in range(1, samples):
                t = float(step) / float(samples)
                x = x0 + (x1 - x0) * t
                y = y0 + (y1 - y0) * t
                if (
                    box["left"] - 6.0 <= x <= box["right"] + 6.0
                    and box["top"] - 6.0 <= y <= box["bottom"] + 6.0
                ):
                    touched = True
                    break
            if touched:
                hits += 1
        return hits

    def _sample_cubic(
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
        samples: int = 44,
    ) -> list[tuple[float, float]]:
        points: list[tuple[float, float]] = []
        for index in range(samples + 1):
            t = float(index) / float(samples)
            one_minus_t = 1.0 - t
            x_coord = (
                (one_minus_t**3) * p0[0]
                + 3.0 * (one_minus_t**2) * t * p1[0]
                + 3.0 * one_minus_t * (t**2) * p2[0]
                + (t**3) * p3[0]
            )
            y_coord = (
                (one_minus_t**3) * p0[1]
                + 3.0 * (one_minus_t**2) * t * p1[1]
                + 3.0 * one_minus_t * (t**2) * p2[1]
                + (t**3) * p3[1]
            )
            points.append((x_coord, y_coord))
        return points

    def _sample_quadratic(
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        samples: int = 58,
    ) -> list[tuple[float, float]]:
        points: list[tuple[float, float]] = []
        for index in range(samples + 1):
            t = float(index) / float(samples)
            one_minus_t = 1.0 - t
            x_coord = (one_minus_t**2) * p0[0] + 2.0 * one_minus_t * t * p1[0] + (t**2) * p2[0]
            y_coord = (one_minus_t**2) * p0[1] + 2.0 * one_minus_t * t * p1[1] + (t**2) * p2[1]
            points.append((x_coord, y_coord))
        return points

    def _score_curve_points(
        curve_points: list[tuple[float, float]],
        src: str,
        dst: str,
        margin: float = 8.0,
    ) -> int:
        hit_nodes: set[str] = set()
        for node_id, box in node_boxes.items():
            if node_id in {src, dst}:
                continue
            for x_coord, y_coord in curve_points:
                if (
                    box["left"] - margin <= x_coord <= box["right"] + margin
                    and box["top"] - margin <= y_coord <= box["bottom"] + margin
                ):
                    hit_nodes.add(node_id)
                    break
        return len(hit_nodes)

    def _score_arc_route(src: str, dst: str, rad: float) -> tuple[int, int]:
        x0, y0 = positions[src]
        x1, y1 = positions[dst]
        dx = x1 - x0
        dy = y1 - y0
        distance = max(1.0, (dx * dx + dy * dy) ** 0.5)
        nx = -dy / distance
        ny = dx / distance
        bend = rad * distance * 0.85
        control = ((x0 + x1) * 0.5 + nx * bend, (y0 + y1) * 0.5 + ny * bend)
        points = _sample_quadratic((x0, y0), control, (x1, y1), samples=66)
        hard_hits = _score_curve_points(points, src, dst, margin=7.0)
        soft_hits = _score_curve_points(points, src, dst, margin=22.0)
        return hard_hits, soft_hits

    def _build_long_edge_path(src: str, dst: str) -> MplPath | None:
        src_level = levels.get(src, 0)
        dst_level = levels.get(dst, 0)
        if dst_level <= src_level + 1:
            return None

        x_src, y_src = positions[src]
        x_dst, y_dst = positions[dst]
        src_box = node_boxes[src]
        dst_box = node_boxes[dst]

        start_y = src_box["bottom"] + 10.0
        end_y = dst_box["top"] - 10.0
        if end_y <= start_y + 30.0:
            return None

        involved = [
            node_boxes[node_id]
            for node_id in node_ids
            if src_level < levels.get(node_id, src_level) < dst_level
        ]
        if involved:
            left_bound = min(box["left"] for box in involved)
            right_bound = max(box["right"] for box in involved)
        else:
            left_bound = min(x_src, x_dst) - 120.0
            right_bound = max(x_src, x_dst) + 120.0

        x_mid = (x_src + x_dst) * 0.5
        span = max(120.0, abs(x_dst - x_src) * 0.55)
        corridor_left = min(x_src, x_dst) - 180.0
        corridor_right = max(x_src, x_dst) + 180.0
        candidate_set: set[float] = {
            x_mid,
            x_src,
            x_dst,
            x_mid - span,
            x_mid + span,
            left_bound - 110.0,
            right_bound + 110.0,
            left_bound - 190.0,
            right_bound + 190.0,
        }
        for box in involved:
            candidate_set.add(box["left"] - 48.0)
            candidate_set.add(box["right"] + 48.0)
            candidate_set.add(box["left"] - 90.0)
            candidate_set.add(box["right"] + 90.0)
        candidate_min = corridor_left - 70.0
        candidate_max = corridor_right + 70.0
        candidates = sorted(v for v in candidate_set if candidate_min <= v <= candidate_max)
        if not candidates:
            candidates = [x_mid]

        y_entry = max(start_y + 34.0, row_bottom.get(src_level, start_y + 34.0) + 22.0)
        y_exit = min(end_y - 34.0, row_top.get(dst_level, end_y - 34.0) - 22.0)
        if y_exit <= y_entry + 24.0:
            y_entry = start_y + 30.0
            y_exit = end_y - 30.0
            if y_exit <= y_entry + 16.0:
                return None

        best_track = x_mid
        best_path_points: list[tuple[float, float]] | None = None
        best_path_score = float("inf")
        best_path_hits = float("inf")
        dst_margin = max(28.0, 0.16 * (dst_box["right"] - dst_box["left"]))

        def _clamp_dst_entry(value: float) -> float:
            return max(dst_box["left"] + dst_margin, min(dst_box["right"] - dst_margin, value))

        for candidate in candidates:
            vertical_hits = _count_vertical_hits(candidate, y_entry, y_exit, src, dst)
            entry_values = {
                _clamp_dst_entry(x_dst),
                _clamp_dst_entry(candidate),
                _clamp_dst_entry(candidate - 42.0),
                _clamp_dst_entry(candidate + 42.0),
            }
            for entry_x in sorted(entry_values):
                offset = max(56.0, 0.21 * (end_y - start_y))
                start = (x_src, start_y)
                end = (entry_x, end_y)
                mid = (candidate, (y_entry + y_exit) * 0.5)
                c1 = (x_src, min(y_entry, start_y + offset))
                c2 = (candidate, y_entry)
                c3 = (candidate, y_exit)
                c4 = (entry_x, max(y_exit, end_y - offset))

                first = _sample_cubic(start, c1, c2, mid, samples=40)
                second = _sample_cubic(mid, c3, c4, end, samples=40)
                curve_points = first + second[1:]
                box_hits = _score_curve_points(curve_points, src, dst)

                # Secondary exact check on straight chord segments to avoid
                # hidden overlap with large downstream boxes.
                segment_hits = _count_segment_hits(start, mid, src, dst, margin=7.0) + _count_segment_hits(
                    mid, end, src, dst, margin=7.0
                )
                total_hits = box_hits + segment_hits

                distance_penalty = abs(candidate - x_mid) + 0.40 * abs(entry_x - x_dst)
                if candidate < corridor_left:
                    distance_penalty += (corridor_left - candidate) * 4.5
                elif candidate > corridor_right:
                    distance_penalty += (candidate - corridor_right) * 4.5

                score = float(total_hits) * 1800.0 + float(vertical_hits) * 240.0 + distance_penalty
                if total_hits < best_path_hits or (total_hits == best_path_hits and score < best_path_score):
                    best_path_hits = float(total_hits)
                    best_path_score = score
                    best_track = candidate
                    best_path_points = [
                        start,
                        c1,
                        c2,
                        mid,
                        c3,
                        c4,
                        end,
                    ]

        if best_path_points is None:
            return None
        if best_path_hits > 0:
            return None

        path_vertices = best_path_points
        path_codes = [MplPath.MOVETO] + [MplPath.CURVE4] * 6
        return MplPath(path_vertices, path_codes)

    graph_center_x = 0.5 * (x_min + x_max)
    graph_span_x = max(1.0, x_max - x_min)

    for src, dst, style in edge_records:
        if src not in positions or dst not in positions:
            continue
        level_delta = levels.get(dst, 0) - levels.get(src, 0)
        direct_hits = _count_direct_hits(src, dst)
        edge_kwargs: Dict[str, Any] = {
            "arrowstyle": "-|>",
            "mutation_scale": 11,
            "linewidth": 1.2,
            "color": style.get("color", "black"),
            "zorder": 1,
        }
        x_src, _ = positions[src]
        x_dst, _ = positions[dst]
        abs_dx = abs(x_dst - x_src)
        preferred_sign = 1.0 if x_dst >= x_src else -1.0
        src_center_ratio = abs(x_src - graph_center_x) / graph_span_x
        dst_center_ratio = abs(x_dst - graph_center_x) / graph_span_x
        moves_toward_center = dst_center_ratio + 0.03 < src_center_ratio
        border_to_inner = level_delta >= 2 and src_center_ratio >= 0.34 and dst_center_ratio <= 0.30 and moves_toward_center
        outward_sign = -1.0 if x_src <= graph_center_x else 1.0

        if level_delta <= 1:
            arc_candidates = [0.0]
        else:
            base = 0.08 * min(level_delta, 5)
            if abs_dx < 280.0:
                base += 0.08
            base = min(0.34, base)
            magnitudes = [0.0, min(0.16, base * 0.75), base, min(0.28, base + 0.08), 0.34]
            arc_candidates = []
            for magnitude in magnitudes:
                if magnitude <= 0.0:
                    arc_candidates.append(0.0)
                    continue
                arc_candidates.append(preferred_sign * magnitude)
                arc_candidates.append(-preferred_sign * magnitude)
        seen_rads: set[float] = set()
        arc_candidates = [r for r in arc_candidates if not (round(r, 4) in seen_rads or seen_rads.add(round(r, 4)))]

        best_rad = 0.0
        best_hard_hits = float("inf")
        best_soft_hits = float("inf")
        best_rad_score = float("inf")
        for rad in arc_candidates:
            hard_hits, soft_hits = _score_arc_route(src, dst, rad)
            score = float(hard_hits) * 1000.0 + float(soft_hits) * 22.0 + abs(rad) * 18.0
            if rad * preferred_sign < 0.0:
                score += 2.0 if border_to_inner else 8.0
            if abs_dx < 170.0 and abs(rad) < 0.14 and level_delta >= 2:
                score += 12.0
            if border_to_inner:
                if abs(rad) < 0.08:
                    score += 34.0
                if rad * outward_sign > 0.0:
                    score -= 11.0
                elif abs(rad) >= 0.08:
                    score += 17.0
                if 0.10 <= abs(rad) <= 0.30:
                    score -= 7.0
            if (
                hard_hits < best_hard_hits
                or (hard_hits == best_hard_hits and soft_hits < best_soft_hits)
                or (hard_hits == best_hard_hits and soft_hits == best_soft_hits and score < best_rad_score)
            ):
                best_hard_hits = float(hard_hits)
                best_soft_hits = float(soft_hits)
                best_rad_score = score
                best_rad = rad

        use_long_route = level_delta >= 3 and direct_hits > 0 and best_hard_hits > 0
        long_path = _build_long_edge_path(src, dst) if use_long_route else None
        if long_path is not None:
            arrow = FancyArrowPatch(
                path=long_path,
                patchA=node_patches.get(src),
                patchB=node_patches.get(dst),
                **edge_kwargs,
            )
        else:
            arrow = FancyArrowPatch(
                posA=positions[src],
                posB=positions[dst],
                patchA=node_patches.get(src),
                patchB=node_patches.get(dst),
                connectionstyle=f"arc3,rad={best_rad:.4f}",
                **edge_kwargs,
            )
        axis.add_patch(arrow)

    for node_id, label in node_labels.items():
        if node_id not in positions:
            continue
        x_coord, y_coord = positions[node_id]
        axis.text(
            x_coord,
            y_coord,
            label,
            ha="center",
            va="center",
            fontsize=font_sizes.get(node_id, 11.0),
            linespacing=1.20,
            color="#333333",
            zorder=3,
        )

    out_path = Path(output_path).with_suffix(f".{output_format}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs: Dict[str, Any] = {"format": output_format, "bbox_inches": "tight", "pad_inches": 0.15}
    if output_format == "png":
        save_kwargs["dpi"] = dpi_value
    figure.savefig(out_path, **save_kwargs)
    plt.close(figure)
    return out_path
