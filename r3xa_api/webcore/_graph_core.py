from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from textwrap import wrap
from typing import Any, Dict, Iterable

from .._references import reference_fields


STYLES = {
    "settings": {
        "root": {
            "shape": "hexagon",
            "margin": "0.2,0.0",
            "fillcolor": "#e8f1fb",
            "color": "#2b587a",
            "style": "filled",
            "penwidth": "3",
        },
    },
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
        "setting": {"color": "#2b587a", "style": "dashed"},
        "reference": {"color": "#2b587a", "style": "dashed"},
        "data_initial": {"color": "black"},
        "data": {"color": "black"},
        "input": {"color": "black"},
    },
}


# J-C. Passieux's document palette, and the default: solid fills with white
# text. Hue marks the section; darker outlines distinguish initial sources and
# final data sets without changing their palette fill colour.
#
# The settings fill is a darkened ochre rather than his #c4894f: white text on
# that original gives a 2.98 contrast ratio, well under the 4.5 WCAG AA
# threshold. #9a6636 keeps the hue and reaches 4.85, so the whole palette can
# stay white-on-colour instead of switching text colour per section.
_OCHRE, _CRIMSON, _TEAL = "#9a6636", "#bf0040", "#038181"
_CRIMSON_DEEP, _TEAL_DEEP = "#5c001f", "#004545"
_WHITE = "#ffffff"


def _solid(
    shape: str,
    fill: str,
    *,
    border: str | None = None,
    penwidth: str = "1",
    margin: str | None = None,
) -> Dict[str, Any]:
    """A filled node with an optional contrasting outline and white text."""

    style = {
        "shape": shape,
        "fillcolor": fill,
        "color": border or fill,
        "fontcolor": _WHITE,
        "style": "filled",
        "penwidth": penwidth,
    }
    if margin is not None:
        style["margin"] = margin
    return style


DOCUMENT_STYLES = {
    "settings": {"root": _solid("hexagon", _OCHRE, margin="0.2,0.0")},
    "data_sources": {
        "initial": _solid("ellipse", _CRIMSON, border=_CRIMSON_DEEP, penwidth="4"),
        "intermediate": _solid("ellipse", _CRIMSON),
    },
    "data_sets": {
        "intermediate": _solid("box", _TEAL),
        "final": _solid("box", _TEAL, border=_TEAL_DEEP, penwidth="4"),
    },
    "edges": {
        "setting": {"color": _OCHRE, "style": "dashed"},
        "reference": {"color": _OCHRE, "style": "dashed"},
        "data_initial": {"color": "#555555"},
        "data": {"color": "#555555"},
        "input": {"color": "#555555"},
    },
}


PALETTES: Dict[str, Dict[str, Any]] = {
    "document": DOCUMENT_STYLES,
    "classic": STYLES,
}

DEFAULT_PALETTE = "document"


RELATION_SEMANTICS: Dict[str, Dict[str, Any]] = {
    "parent_data_sources": {
        "direction": "target_to_owner",
        "role": "dataflow",
        "style_key": "data",
    },
    "input_data_sets": {
        "direction": "target_to_owner",
        "role": "dataflow",
        "style_key": "input",
    },
    "attached_data_sources": {
        "direction": "owner_to_target",
        "role": "context",
        "style_key": "setting",
    },
    "mesh": {
        "direction": "target_to_owner",
        "role": "context",
        "style_key": "setting",
        "label": "mesh",
    },
}


def build_graph_relation_catalog() -> Dict[str, Any]:
    """Return schema-derived graph references and their drawing semantics."""

    from ..schema import load_schema

    schema = load_schema()
    fields: Dict[str, Dict[str, str]] = {}
    for section in ("settings", "data_sources", "data_sets"):
        for name in schema.get("$defs", {}).get(section, {}):
            kind = f"{section}/{name}"
            references = reference_fields(kind)
            if references:
                fields[kind] = references
    return {"fields": fields, "semantics": RELATION_SEMANTICS}


def resolve_styles(
    palette: str | None = None,
    styles: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Return the style table for a palette name, or an explicit override.

    `styles` wins when given, so a caller can still pass a bespoke table.
    """

    if styles is not None:
        return styles
    name = palette or DEFAULT_PALETTE
    try:
        return PALETTES[name]
    except KeyError:
        raise ValueError(
            f"Unknown palette {name!r}. Available: {', '.join(sorted(PALETTES))}"
        ) from None


@dataclass(frozen=True)
class EdgeRecord:
    """Directed edge between two graph nodes with style category."""

    src: str
    dst: str
    style_key: str
    relation: str | None = None
    role: str = "dataflow"
    label: str | None = None


@dataclass(frozen=True)
class GraphModel:
    """Normalized graph model shared by all render backends."""

    setting_ids: list[str]
    source_ids: list[str]
    data_set_ids: list[str]
    node_ids: list[str]
    used_datasets: set[str]
    intermediate_sources: set[str]
    edge_records: list[EdgeRecord]
    levels: Dict[str, int]


def get_input_data_sets(source: Dict[str, Any]) -> Iterable[str]:
    """Return upstream dataset ids declared by a data source."""

    value = source.get("input_data_sets")
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    if isinstance(value, dict):
        return [v for v in value.values() if v]
    return []


def get_data_sources(dataset: Dict[str, Any]) -> Iterable[str]:
    """Return source ids that feed a dataset."""

    value = dataset.get("parent_data_sources")
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    return [value]


def get_associated_data_sources(setting: Dict[str, Any]) -> Iterable[str]:
    """Return data source ids attached to an experimental setting."""

    value = setting.get("attached_data_sources")
    if not value:
        return []
    if isinstance(value, list):
        return [item for item in value if item]
    return [value]


def compute_used_datasets(data: Dict[str, Any]) -> set[str]:
    """Return dataset ids consumed as inputs by intermediate data sources."""

    used = set()
    for source in data.get("data_sources", []):
        for ds_id in get_input_data_sets(source):
            used.add(ds_id)
    return used


def _reference_values(value: Any) -> Iterable[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    if isinstance(value, dict):
        return [item for item in value.values() if isinstance(item, str) and item]
    return [value] if isinstance(value, str) else []


def _item_reference_fields(item: Dict[str, Any]) -> Dict[str, str]:
    kind = item.get("kind")
    if isinstance(kind, str):
        return reference_fields(kind)
    # A few programmatic callers build graph payloads before assigning kinds.
    # Keep those payloads useful without making the actual kind-aware path
    # depend on a hand-maintained global union.
    return {
        field: "data_sources" if field in {"attached_data_sources", "parent_data_sources"} else target
        for field, target in {
            "attached_data_sources": "data_sources",
            "input_data_sets": "data_sets",
            "parent_data_sources": "data_sources",
            "mesh": "settings",
        }.items()
    }


def _edge_for_reference(
    owner_section: str,
    owner_id: str,
    field: str,
    target_id: str,
    intermediate_sources: set[str],
) -> EdgeRecord:
    semantic = RELATION_SEMANTICS.get(
        field,
        {
            "direction": "owner_to_target",
            "role": "context",
            "style_key": "reference",
        },
    )
    if semantic["direction"] == "target_to_owner":
        src, dst = target_id, owner_id
    else:
        src, dst = owner_id, target_id

    style_key = semantic["style_key"]
    if field == "parent_data_sources":
        style_key = "data" if target_id in intermediate_sources else "data_initial"
    return EdgeRecord(
        src=src,
        dst=dst,
        style_key=style_key,
        relation=field,
        role=semantic["role"],
        label=semantic.get("label"),
    )


def build_graph_model(data: Dict[str, Any], relations: str = "all") -> GraphModel:
    """Build a normalized graph model reused across all rendering backends."""

    if relations not in {"all", "dataflow"}:
        raise ValueError("Unknown graph relation view. Use 'all' or 'dataflow'.")

    used_datasets = compute_used_datasets(data)
    intermediate_sources = {source.get("id") for source in data.get("data_sources", []) if get_input_data_sets(source)}

    setting_ids = [setting.get("id") for setting in data.get("settings", []) if setting.get("id")]
    source_ids = [source.get("id") for source in data.get("data_sources", []) if source.get("id")]
    data_set_ids = [dataset.get("id") for dataset in data.get("data_sets", []) if dataset.get("id")]
    node_ids = setting_ids + source_ids + data_set_ids

    edge_records: list[EdgeRecord] = []

    sections = {
        "settings": data.get("settings", []),
        "data_sources": data.get("data_sources", []),
        "data_sets": data.get("data_sets", []),
    }
    for owner_section, items in sections.items():
        for item in items:
            owner_id = item.get("id")
            if not owner_id:
                continue
            for field in _item_reference_fields(item):
                if field not in item:
                    continue
                for target_id in _reference_values(item[field]):
                    edge = _edge_for_reference(
                        owner_section,
                        owner_id,
                        field,
                        target_id,
                        intermediate_sources,
                    )
                    if relations == "dataflow" and edge.role != "dataflow":
                        continue
                    edge_records.append(edge)

    edge_pairs = [(edge.src, edge.dst) for edge in edge_records]
    levels = compute_hierarchical_levels(node_ids, edge_pairs)

    return GraphModel(
        setting_ids=setting_ids,
        source_ids=source_ids,
        data_set_ids=data_set_ids,
        node_ids=node_ids,
        used_datasets=used_datasets,
        intermediate_sources=intermediate_sources,
        edge_records=edge_records,
        levels=levels,
    )


def compute_hierarchical_levels(nodes: Iterable[str], edges: Iterable[tuple[str, str]]) -> Dict[str, int]:
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


def wrap_label_text(value: Any, max_chars: int) -> str:
    """Wrap multiline text into shorter lines for graph readability."""

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


def format_node_label(title: Any, description: Any, include_description: bool = True) -> str:
    """Build node label with wrapped title and optional description."""

    title_text = wrap_label_text(title, max_chars=34)
    if not include_description:
        return title_text
    description_text = wrap_label_text(description, max_chars=44)
    if description_text:
        return f"{title_text}\n({description_text})"
    return title_text


def compact_hexagon_style(style: Dict[str, Any], label: str) -> Dict[str, Any]:
    """Keep a hexagon as close to its label height as Graphviz allows."""

    if style.get("shape") != "hexagon":
        return style

    line_count = max(1, len(label.splitlines()))
    height = max(0.5, line_count * 0.2333 + 0.06)
    longest_line = max((len(line) for line in label.splitlines()), default=1)
    width = max(0.75, longest_line * 0.11 + 0.5)
    return {
        **style,
        "fixedsize": "shape",
        "height": f"{height:.3f}",
        "width": f"{width:.3f}",
    }


def estimate_label_width(label: str) -> float:
    """Estimate node width in pixels from wrapped label text."""

    lines = label.splitlines() or [label]
    longest = max((len(line) for line in lines), default=10)
    return max(180.0, min(520.0, 68.0 + longest * 7.2))


def estimate_label_height(label: str) -> float:
    """Estimate node height in pixels from wrapped label text."""

    lines = label.splitlines() or [label]
    line_count = max(1, len(lines))
    return max(56.0, min(260.0, 26.0 + line_count * 17.0))


def estimate_canvas_height(
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


def compute_manual_positions(
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


def compute_graphviz_positions(
    node_ids: Iterable[str],
    edges: Iterable[tuple[str, str]],
    label_widths: Dict[str, float],
    label_heights: Dict[str, float],
) -> tuple[Dict[str, tuple[float, float]], Dict[str, float]] | None:
    """Compute node positions with the bundled Graphviz WebAssembly engine."""

    try:
        from ._graph_graphviz_wasm import compute_graphviz_positions_wasm

        wasm_layout = compute_graphviz_positions_wasm(node_ids, edges, label_widths)
    except Exception:
        return None

    if wasm_layout is None:
        return None
    raw_positions, widths = wasm_layout

    if not raw_positions:
        return None

    level_nodes: Dict[float, list[str]] = {}
    for node_id, (_, y_coord) in raw_positions.items():
        key = round(y_coord, 4)
        level_nodes.setdefault(key, []).append(node_id)

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
    pyvis_styles: Dict[str, Any] = {"settings": {}, "data_sources": {}, "data_sets": {}, "edges": {}}

    for node_type in ("settings", "data_sources", "data_sets"):
        for status, attrs in graphviz_styles[node_type].items():
            pyvis_styles[node_type][status] = {
                "borderWidth": int(attrs.get("penwidth", 2)),
                "color": {
                    "border": attrs.get("color", "black"),
                    "background": attrs.get("fillcolor", "lightgrey"),
                },
                "shape": attrs.get("shape", "ellipse"),
                # Carried through so a solid-fill palette can put white text
                # on its nodes, like Graphviz does natively.
                "font": {"color": attrs.get("fontcolor", "#333333")},
                "r3xaFontColor": attrs.get("fontcolor", "#333333"),
            }

    for edge_type, attrs in graphviz_styles["edges"].items():
        pyvis_styles["edges"][edge_type] = {
            "color": attrs.get("color", "black"),
            "dashes": attrs.get("style") == "dashed",
        }

    return pyvis_styles


def resolve_edge_style(styles: Dict[str, Any], edge: EdgeRecord) -> Dict[str, Any]:
    """Resolve an edge style while tolerating older custom style tables."""

    edge_styles = styles.get("edges", {})
    return edge_styles.get(
        edge.style_key,
        edge_styles.get("reference", edge_styles.get("setting", {})),
    )
