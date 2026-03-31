from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from ._graph_core import (
    STYLES,
    build_graph_model,
    compute_graphviz_positions,
    compute_manual_positions,
    wrap_label_text,
)


@dataclass(frozen=True)
class NetworkXLayoutConfig:
    """Heuristic constants used by the NetworkX + Matplotlib backend."""

    manual_x_scale_without_graphviz: float = 1.14
    row_height_fallback: float = 80.0
    row_vertical_gap_min: float = 84.0
    row_vertical_gap_ratio: float = 0.55
    row_spread_gap: float = 42.0
    node_width_fallback: float = 220.0
    node_height_fallback: float = 64.0
    ellipse_draw_width_scale: float = 1.08
    box_draw_width_scale: float = 1.18
    ellipse_draw_height_scale: float = 1.10
    box_draw_height_scale: float = 1.16
    figure_padding_x: float = 120.0
    figure_padding_y: float = 120.0
    min_dpi: int = 90
    layout_min_dpi: float = 120.0
    layout_dpi_ratio: float = 0.62
    figure_width_min: float = 18.0
    figure_width_max: float = 46.0
    figure_height_min: float = 12.0
    figure_height_max: float = 46.0
    edge_arrow_scale: float = 11.0
    edge_linewidth: float = 1.2
    edge_direct_hit_margin: float = 6.0
    edge_direct_hit_samples: int = 48
    curve_hard_margin: float = 7.0
    curve_soft_margin: float = 22.0
    curve_segment_margin: float = 7.0
    curve_segment_samples: int = 44
    quadratic_samples: int = 58
    arc_samples: int = 66
    curve_vertical_margin_y: float = 6.0
    curve_vertical_margin_x: float = 8.0
    curve_vertical_score_weight: float = 240.0
    curve_collision_score_weight: float = 1800.0
    curve_outside_corridor_weight: float = 4.5
    curve_entry_dx_weight: float = 0.40
    long_route_level_delta_min: int = 3
    long_route_start_offset: float = 10.0
    long_route_end_offset: float = 10.0
    long_route_min_vertical_room: float = 30.0
    long_route_default_extra_span: float = 120.0
    long_route_mid_span_ratio: float = 0.55
    long_route_corridor_padding: float = 180.0
    long_route_bound_near: float = 110.0
    long_route_bound_far: float = 190.0
    long_route_box_near: float = 48.0
    long_route_box_far: float = 90.0
    long_route_candidate_padding: float = 70.0
    long_route_entry_offset: float = 34.0
    long_route_row_clearance: float = 22.0
    long_route_entry_exit_min_gap: float = 24.0
    long_route_fallback_offset: float = 30.0
    long_route_fallback_min_gap: float = 16.0
    long_route_dst_margin_min: float = 28.0
    long_route_dst_margin_ratio: float = 0.16
    long_route_dst_entry_delta: float = 42.0
    long_route_control_offset_min: float = 56.0
    long_route_control_offset_ratio: float = 0.21
    long_route_cubic_samples: int = 40
    arc_level_delta_threshold: int = 2
    arc_base_per_level: float = 0.08
    arc_base_level_cap: int = 5
    arc_small_dx_threshold: float = 280.0
    arc_small_dx_bonus: float = 0.08
    arc_base_max: float = 0.34
    arc_mag_small_cap: float = 0.16
    arc_mag_medium_cap: float = 0.28
    arc_mag_medium_plus: float = 0.08
    arc_soft_score_weight: float = 22.0
    arc_hard_score_weight: float = 1000.0
    arc_abs_score_weight: float = 18.0
    arc_reverse_penalty_border: float = 2.0
    arc_reverse_penalty_default: float = 8.0
    arc_short_dx_threshold: float = 170.0
    arc_short_dx_small_rad: float = 0.14
    arc_short_dx_penalty: float = 12.0
    border_src_ratio: float = 0.34
    border_dst_ratio: float = 0.30
    border_move_ratio_eps: float = 0.03
    border_small_rad: float = 0.08
    border_small_rad_penalty: float = 34.0
    border_outward_bonus: float = 11.0
    border_wrong_rad_penalty: float = 17.0
    border_mid_rad_min: float = 0.10
    border_mid_rad_max: float = 0.30
    border_mid_rad_bonus: float = 7.0
    save_pad_inches: float = 0.15


DEFAULT_LAYOUT_CONFIG = NetworkXLayoutConfig()


def render_networkx_matplotlib_file(
    data: Dict[str, Any],
    output_path: Path,
    format: str = "png",
    dpi: int = 220,
    layout_config: NetworkXLayoutConfig | None = None,
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
    config = layout_config or DEFAULT_LAYOUT_CONFIG

    styles = STYLES
    model = build_graph_model(data)
    node_ids = model.node_ids
    graph = nx.DiGraph()
    graph.add_nodes_from(node_ids)
    graph.add_edges_from((edge.src, edge.dst) for edge in model.edge_records)

    levels = model.levels
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
        title_text = wrap_label_text(title, max_chars=title_chars)
        description_text = wrap_label_text(description, max_chars=desc_chars)
        if description_text:
            return f"{title_text}\n({description_text})"
        return title_text

    for source in data.get("data_sources", []):
        source_id = source.get("id")
        if not source_id:
            continue
        is_intermediate = source_id in model.intermediate_sources
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
        is_intermediate = dataset_id in model.used_datasets
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

    edge_pairs = [(edge.src, edge.dst) for edge in model.edge_records]
    graphviz_layout = compute_graphviz_positions(
        node_ids=node_ids,
        edges=edge_pairs,
        label_widths=label_widths,
        label_heights=label_heights,
    )
    if graphviz_layout is not None:
        positions_raw, graphviz_widths = graphviz_layout
        for node_id, width in graphviz_widths.items():
            label_widths[node_id] = max(label_widths.get(node_id, config.node_width_fallback), width)
    else:
        positions_raw = compute_manual_positions(
            node_ids=node_ids,
            edges=edge_pairs,
            levels=levels,
            label_widths=label_widths,
        )
    x_scale = 1.0 if graphviz_layout is not None else config.manual_x_scale_without_graphviz
    positions: Dict[str, tuple[float, float]] = {
        node_id: (x_coord * x_scale, y_coord)
        for node_id, (x_coord, y_coord) in positions_raw.items()
    }

    level_nodes: Dict[int, list[str]] = {}
    for node_id in node_ids:
        level_nodes.setdefault(levels.get(node_id, 0), []).append(node_id)
    ordered_levels = sorted(level_nodes.keys())
    row_heights = {
        level: max(label_heights.get(node_id, config.row_height_fallback) for node_id in level_nodes[level])
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
        vertical_gap = max(config.row_vertical_gap_min, config.row_vertical_gap_ratio * max(previous_height, current_height))
        row_y[level] = row_y[previous_level] + previous_height * 0.5 + vertical_gap + current_height * 0.5
    for node_id, (x_coord, _) in positions.items():
        positions[node_id] = (x_coord, row_y.get(levels.get(node_id, 0), 0.0))

    draw_widths: Dict[str, float] = {}
    for node_id in node_ids:
        is_ellipse = node_shapes.get(node_id, "box") == "ellipse"
        width_scale = config.ellipse_draw_width_scale if is_ellipse else config.box_draw_width_scale
        draw_widths[node_id] = label_widths.get(node_id, config.node_width_fallback) * width_scale

    def _spread_row_nodes(level: int, gap: float = config.row_spread_gap) -> None:
        row_nodes = [node_id for node_id in level_nodes.get(level, []) if node_id in positions]
        if len(row_nodes) < 2:
            return
        row_nodes.sort(key=lambda node_id: positions[node_id][0])
        target_center = sum(positions[node_id][0] for node_id in row_nodes) / float(len(row_nodes))
        new_x = {node_id: positions[node_id][0] for node_id in row_nodes}

        for index in range(1, len(row_nodes)):
            previous = row_nodes[index - 1]
            current = row_nodes[index]
            min_center_gap = (
                0.5 * draw_widths.get(previous, config.node_width_fallback)
                + 0.5 * draw_widths.get(current, config.node_width_fallback)
                + gap
            )
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
        positions[node_id][0] - label_widths.get(node_id, config.node_width_fallback) * 0.5
        for node_id in positions
    )
    x_max = max(
        positions[node_id][0] + label_widths.get(node_id, config.node_width_fallback) * 0.5
        for node_id in positions
    )
    y_min = min(
        positions[node_id][1] - label_heights.get(node_id, config.node_height_fallback) * 0.5
        for node_id in positions
    )
    y_max = max(
        positions[node_id][1] + label_heights.get(node_id, config.node_height_fallback) * 0.5
        for node_id in positions
    )

    padding_x = config.figure_padding_x
    padding_y = config.figure_padding_y
    dpi_value = max(config.min_dpi, int(dpi))
    layout_dpi = max(config.layout_min_dpi, dpi_value * config.layout_dpi_ratio)
    fig_width = max(config.figure_width_min, min(config.figure_width_max, (x_max - x_min + 2.0 * padding_x) / layout_dpi))
    fig_height = max(
        config.figure_height_min,
        min(config.figure_height_max, (y_max - y_min + 2.0 * padding_y) / layout_dpi),
    )

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
        width_scale = config.ellipse_draw_width_scale if is_ellipse else config.box_draw_width_scale
        height_scale = config.ellipse_draw_height_scale if is_ellipse else config.box_draw_height_scale
        node_width = label_widths.get(node_id, config.node_width_fallback) * width_scale
        node_height = label_heights.get(node_id, config.node_height_fallback) * height_scale

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
            if high < box["top"] - config.curve_vertical_margin_y or low > box["bottom"] + config.curve_vertical_margin_y:
                continue
            if box["left"] - config.curve_vertical_margin_x <= x_value <= box["right"] + config.curve_vertical_margin_x:
                hits += 1
        return hits

    def _count_segment_hits(
        p0: tuple[float, float],
        p1: tuple[float, float],
        src: str,
        dst: str,
        margin: float = config.curve_segment_margin,
        samples: int = config.curve_segment_samples,
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
        samples = config.edge_direct_hit_samples
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
                    box["left"] - config.edge_direct_hit_margin <= x <= box["right"] + config.edge_direct_hit_margin
                    and box["top"] - config.edge_direct_hit_margin <= y <= box["bottom"] + config.edge_direct_hit_margin
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
        samples: int = config.curve_segment_samples,
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
        samples: int = config.quadratic_samples,
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
        margin: float = config.curve_segment_margin,
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
        points = _sample_quadratic((x0, y0), control, (x1, y1), samples=config.arc_samples)
        hard_hits = _score_curve_points(points, src, dst, margin=config.curve_hard_margin)
        soft_hits = _score_curve_points(points, src, dst, margin=config.curve_soft_margin)
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

        start_y = src_box["bottom"] + config.long_route_start_offset
        end_y = dst_box["top"] - config.long_route_end_offset
        if end_y <= start_y + config.long_route_min_vertical_room:
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
            left_bound = min(x_src, x_dst) - config.long_route_default_extra_span
            right_bound = max(x_src, x_dst) + config.long_route_default_extra_span

        x_mid = (x_src + x_dst) * 0.5
        span = max(config.long_route_default_extra_span, abs(x_dst - x_src) * config.long_route_mid_span_ratio)
        corridor_left = min(x_src, x_dst) - config.long_route_corridor_padding
        corridor_right = max(x_src, x_dst) + config.long_route_corridor_padding
        candidate_set: set[float] = {
            x_mid,
            x_src,
            x_dst,
            x_mid - span,
            x_mid + span,
            left_bound - config.long_route_bound_near,
            right_bound + config.long_route_bound_near,
            left_bound - config.long_route_bound_far,
            right_bound + config.long_route_bound_far,
        }
        for box in involved:
            candidate_set.add(box["left"] - config.long_route_box_near)
            candidate_set.add(box["right"] + config.long_route_box_near)
            candidate_set.add(box["left"] - config.long_route_box_far)
            candidate_set.add(box["right"] + config.long_route_box_far)
        candidate_min = corridor_left - config.long_route_candidate_padding
        candidate_max = corridor_right + config.long_route_candidate_padding
        candidates = sorted(v for v in candidate_set if candidate_min <= v <= candidate_max)
        if not candidates:
            candidates = [x_mid]

        y_entry = max(
            start_y + config.long_route_entry_offset,
            row_bottom.get(src_level, start_y + config.long_route_entry_offset) + config.long_route_row_clearance,
        )
        y_exit = min(
            end_y - config.long_route_entry_offset,
            row_top.get(dst_level, end_y - config.long_route_entry_offset) - config.long_route_row_clearance,
        )
        if y_exit <= y_entry + config.long_route_entry_exit_min_gap:
            y_entry = start_y + config.long_route_fallback_offset
            y_exit = end_y - config.long_route_fallback_offset
            if y_exit <= y_entry + config.long_route_fallback_min_gap:
                return None

        best_path_points: list[tuple[float, float]] | None = None
        best_path_score = float("inf")
        best_path_hits = float("inf")
        dst_margin = max(config.long_route_dst_margin_min, config.long_route_dst_margin_ratio * (dst_box["right"] - dst_box["left"]))

        def _clamp_dst_entry(value: float) -> float:
            return max(dst_box["left"] + dst_margin, min(dst_box["right"] - dst_margin, value))

        for candidate in candidates:
            vertical_hits = _count_vertical_hits(candidate, y_entry, y_exit, src, dst)
            entry_values = {
                _clamp_dst_entry(x_dst),
                _clamp_dst_entry(candidate),
                _clamp_dst_entry(candidate - config.long_route_dst_entry_delta),
                _clamp_dst_entry(candidate + config.long_route_dst_entry_delta),
            }
            for entry_x in sorted(entry_values):
                offset = max(config.long_route_control_offset_min, config.long_route_control_offset_ratio * (end_y - start_y))
                start = (x_src, start_y)
                end = (entry_x, end_y)
                mid = (candidate, (y_entry + y_exit) * 0.5)
                c1 = (x_src, min(y_entry, start_y + offset))
                c2 = (candidate, y_entry)
                c3 = (candidate, y_exit)
                c4 = (entry_x, max(y_exit, end_y - offset))

                first = _sample_cubic(start, c1, c2, mid, samples=config.long_route_cubic_samples)
                second = _sample_cubic(mid, c3, c4, end, samples=config.long_route_cubic_samples)
                curve_points = first + second[1:]
                box_hits = _score_curve_points(curve_points, src, dst)

                segment_hits = _count_segment_hits(start, mid, src, dst, margin=config.curve_hard_margin) + _count_segment_hits(
                    mid, end, src, dst, margin=config.curve_hard_margin
                )
                total_hits = box_hits + segment_hits

                distance_penalty = abs(candidate - x_mid) + config.curve_entry_dx_weight * abs(entry_x - x_dst)
                if candidate < corridor_left:
                    distance_penalty += (corridor_left - candidate) * config.curve_outside_corridor_weight
                elif candidate > corridor_right:
                    distance_penalty += (candidate - corridor_right) * config.curve_outside_corridor_weight

                score = (
                    float(total_hits) * config.curve_collision_score_weight
                    + float(vertical_hits) * config.curve_vertical_score_weight
                    + distance_penalty
                )
                if total_hits < best_path_hits or (total_hits == best_path_hits and score < best_path_score):
                    best_path_hits = float(total_hits)
                    best_path_score = score
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

    for edge in model.edge_records:
        src = edge.src
        dst = edge.dst
        if src not in positions or dst not in positions:
            continue
        style = styles["edges"][edge.style_key]
        level_delta = levels.get(dst, 0) - levels.get(src, 0)
        direct_hits = _count_direct_hits(src, dst)
        edge_kwargs: Dict[str, Any] = {
            "arrowstyle": "-|>",
            "mutation_scale": config.edge_arrow_scale,
            "linewidth": config.edge_linewidth,
            "color": style.get("color", "black"),
            "zorder": 1,
        }
        x_src, _ = positions[src]
        x_dst, _ = positions[dst]
        abs_dx = abs(x_dst - x_src)
        preferred_sign = 1.0 if x_dst >= x_src else -1.0
        src_center_ratio = abs(x_src - graph_center_x) / graph_span_x
        dst_center_ratio = abs(x_dst - graph_center_x) / graph_span_x
        moves_toward_center = dst_center_ratio + config.border_move_ratio_eps < src_center_ratio
        border_to_inner = (
            level_delta >= config.arc_level_delta_threshold
            and src_center_ratio >= config.border_src_ratio
            and dst_center_ratio <= config.border_dst_ratio
            and moves_toward_center
        )
        outward_sign = -1.0 if x_src <= graph_center_x else 1.0

        if level_delta <= 1:
            arc_candidates = [0.0]
        else:
            base = config.arc_base_per_level * min(level_delta, config.arc_base_level_cap)
            if abs_dx < config.arc_small_dx_threshold:
                base += config.arc_small_dx_bonus
            base = min(config.arc_base_max, base)
            magnitudes = [
                0.0,
                min(config.arc_mag_small_cap, base * 0.75),
                base,
                min(config.arc_mag_medium_cap, base + config.arc_mag_medium_plus),
                config.arc_base_max,
            ]
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
            score = (
                float(hard_hits) * config.arc_hard_score_weight
                + float(soft_hits) * config.arc_soft_score_weight
                + abs(rad) * config.arc_abs_score_weight
            )
            if rad * preferred_sign < 0.0:
                score += config.arc_reverse_penalty_border if border_to_inner else config.arc_reverse_penalty_default
            if (
                abs_dx < config.arc_short_dx_threshold
                and abs(rad) < config.arc_short_dx_small_rad
                and level_delta >= config.arc_level_delta_threshold
            ):
                score += config.arc_short_dx_penalty
            if border_to_inner:
                if abs(rad) < config.border_small_rad:
                    score += config.border_small_rad_penalty
                if rad * outward_sign > 0.0:
                    score -= config.border_outward_bonus
                elif abs(rad) >= config.border_small_rad:
                    score += config.border_wrong_rad_penalty
                if config.border_mid_rad_min <= abs(rad) <= config.border_mid_rad_max:
                    score -= config.border_mid_rad_bonus
            if (
                hard_hits < best_hard_hits
                or (hard_hits == best_hard_hits and soft_hits < best_soft_hits)
                or (hard_hits == best_hard_hits and soft_hits == best_soft_hits and score < best_rad_score)
            ):
                best_hard_hits = float(hard_hits)
                best_soft_hits = float(soft_hits)
                best_rad_score = score
                best_rad = rad

        use_long_route = level_delta >= config.long_route_level_delta_min and direct_hits > 0 and best_hard_hits > 0
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
    save_kwargs: Dict[str, Any] = {
        "format": output_format,
        "bbox_inches": "tight",
        "pad_inches": config.save_pad_inches,
    }
    if output_format == "png":
        save_kwargs["dpi"] = dpi_value
    figure.savefig(out_path, **save_kwargs)
    plt.close(figure)
    return out_path
