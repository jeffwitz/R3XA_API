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

    net = Network(height="950px", width="100%", directed=True)
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
