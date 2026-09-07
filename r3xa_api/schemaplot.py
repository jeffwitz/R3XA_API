from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path


@dataclass
class Case:
    id: str
    name: str
    parent_ids: list[str] = field(default_factory=list)
    color: str = "white"
    text_color: str = "white"


def generate_block_diagram(
    cases: Iterable[Case],
    *,
    direction: Literal["TB", "LR"] = "TB",
    box_width: float = 2.5,
    box_height: float = 0.8,
    horizontal_spacing: float = 0.8,
    vertical_spacing: float = 1.2,
    figsize: tuple[float, float] | None = None,
    show: bool = True,
    save_path: str | None = None,
):
    """
    Generate a hierarchical block diagram from a list of Case objects.

    The algorithm:
        1. Builds the parent/child graph.
        2. Detects cycles and invalid references.
        3. Computes the hierarchical level of each node.
        4. Reorders nodes using barycenter minimization.
        5. Positions children close to the barycenter of their parents.
        6. Draws curved Bézier connections between nodes.

    Parameters
    ----------
    cases:
        Iterable of Case objects.

    direction:
        "TB" = Top -> Bottom.
        "LR" = Left -> Right.

    box_width:
        Width of each block.

    box_height:
        Height of each block.

    horizontal_spacing:
        Minimum spacing between blocks on the same level.

    vertical_spacing:
        Spacing between hierarchy levels.

    figsize:
        Optional Matplotlib figure size.

    show:
        If True, display the figure.

    save_path:
        Optional path for saving the generated figure.

    Returns
    -------
    fig, ax
        Matplotlib Figure and Axes.
    """

    # ================================================================
    # Prepare cases
    # ================================================================

    cases = list(cases)

    if not cases:
        raise ValueError("The list of cases is empty.")

    # ================================================================
    # Create case lookup
    # ================================================================

    case_by_id: dict[str, Case] = {}

    for case in cases:

        if case.id in case_by_id:
            raise ValueError(
                f"Duplicate case id detected: {case.id!r}"
            )

        case_by_id[case.id] = case

    # ================================================================
    # Build parent / child relationships
    # ================================================================

    parents: dict[str, list[str]] = {
        case.id: list(case.parent_ids)
        for case in cases
    }

    children: dict[str, list[str]] = {
        case.id: []
        for case in cases
    }

    for case in cases:

        for parent_id in case.parent_ids:

            if parent_id not in case_by_id:
                raise ValueError(
                    f"Case {case.id!r} references "
                    f"unknown parent {parent_id!r}"
                )

            children[parent_id].append(case.id)

    # ================================================================
    # Detect cycles
    # ================================================================

    visited: set[str] = set()
    active: set[str] = set()

    def visit(node_id: str) -> None:

        if node_id in active:
            raise ValueError(
                "Cycle detected in the Case graph."
            )

        if node_id in visited:
            return

        active.add(node_id)

        for child_id in children[node_id]:
            visit(child_id)

        active.remove(node_id)
        visited.add(node_id)

    for case_id in case_by_id:
        visit(case_id)

    # ================================================================
    # Compute hierarchical levels
    # ================================================================

    levels: dict[str, int] = {}

    def compute_level(node_id: str) -> int:

        if node_id in levels:
            return levels[node_id]

        # Root
        if not parents[node_id]:
            levels[node_id] = 0
            return 0

        level = max(
            compute_level(parent_id)
            for parent_id in parents[node_id]
        ) + 1

        levels[node_id] = level

        return level

    for case_id in case_by_id:
        compute_level(case_id)

    # ================================================================
    # Group nodes by level
    # ================================================================

    level_nodes: dict[int, list[str]] = {}

    for node_id, level in levels.items():

        level_nodes.setdefault(
            level,
            [],
        ).append(node_id)

    max_level = max(level_nodes)

    # ================================================================
    # Initial ordering
    # ================================================================

    # The initial ordering is only used as a deterministic starting
    # point. It does NOT depend on the order in which Case objects
    # were supplied.

    for level in level_nodes:

        level_nodes[level].sort(
            key=lambda node_id:
            case_by_id[node_id].name.lower()
        )

    # ================================================================
    # Barycenter ordering
    # ================================================================

    #
    # This is the important part of the automatic layout.
    #
    # For each level, a node is moved toward the average position
    # of its parents.
    #
    # Then we perform the reverse operation using children.
    #
    # Repeating this several times greatly reduces edge crossings.
    #

    for _ in range(30):

        # ------------------------------------------------------------
        # Downward pass
        # ------------------------------------------------------------

        for level in range(1, max_level + 1):

            previous_level = level_nodes[level - 1]

            previous_positions = {
                node_id: index
                for index, node_id
                in enumerate(previous_level)
            }

            def parent_barycenter(node_id: str) -> float:

                parent_positions = [
                    previous_positions[parent_id]
                    for parent_id in parents[node_id]
                    if parent_id in previous_positions
                ]

                if not parent_positions:
                    return float("inf")

                return sum(parent_positions) / len(
                    parent_positions
                )

            level_nodes[level].sort(
                key=parent_barycenter
            )

        # ------------------------------------------------------------
        # Upward pass
        # ------------------------------------------------------------

        for level in range(max_level - 1, -1, -1):

            next_level = level_nodes[level + 1]

            next_positions = {
                node_id: index
                for index, node_id
                in enumerate(next_level)
            }

            def child_barycenter(node_id: str) -> float:

                child_positions = [
                    next_positions[child_id]
                    for child_id in children[node_id]
                    if child_id in next_positions
                ]

                if not child_positions:
                    return float("inf")

                return sum(child_positions) / len(
                    child_positions
                )

            level_nodes[level].sort(
                key=child_barycenter
            )

    # ================================================================
    # Calculate positions
    # ================================================================

    positions: dict[str, tuple[float, float]] = {}

    if direction == "TB":

        # ------------------------------------------------------------
        # Width of each level
        # ------------------------------------------------------------

        level_widths: dict[int, float] = {}

        for level, nodes in level_nodes.items():

            level_widths[level] = (
                len(nodes) * box_width
                + max(0, len(nodes) - 1)
                * horizontal_spacing
            )

        max_width = max(level_widths.values())

        # ------------------------------------------------------------
        # Initial positions
        # ------------------------------------------------------------

        for level, nodes in level_nodes.items():

            level_width = level_widths[level]

            start_x = (
                max_width - level_width
            ) / 2

            y = -level * (
                box_height
                + vertical_spacing
            )

            for index, node_id in enumerate(nodes):

                x = (
                    start_x
                    + box_width / 2
                    + index * (
                        box_width
                        + horizontal_spacing
                    )
                )

                positions[node_id] = (
                    x,
                    y,
                )

    else:

        # ------------------------------------------------------------
        # Horizontal layout
        # ------------------------------------------------------------

        level_heights: dict[int, float] = {}

        for level, nodes in level_nodes.items():

            level_heights[level] = (
                len(nodes) * box_height
                + max(0, len(nodes) - 1)
                * horizontal_spacing
            )

        max_height = max(level_heights.values())

        for level, nodes in level_nodes.items():

            level_height = level_heights[level]

            start_y = (
                max_height - level_height
            ) / 2

            x = level * (
                box_width
                + vertical_spacing
            )

            for index, node_id in enumerate(nodes):

                y = -(
                    start_y
                    + box_height / 2
                    + index * (
                        box_height
                        + horizontal_spacing
                    )
                )

                positions[node_id] = (
                    x,
                    y,
                )

    # ================================================================
    # Move nodes towards their parents
    # ================================================================

    if direction == "TB":

        for _ in range(8):

            for level in range(1, max_level + 1):

                nodes = level_nodes[level]

                desired_positions: list[
                    tuple[str, float]
                ] = []

                for node_id in nodes:

                    parent_xs = [
                        positions[parent_id][0]
                        for parent_id in parents[node_id]
                    ]

                    if parent_xs:

                        desired_x = (
                            sum(parent_xs)
                            / len(parent_xs)
                        )

                    else:

                        desired_x = positions[node_id][0]

                    desired_positions.append(
                        (
                            node_id,
                            desired_x,
                        )
                    )

                # Keep the graph ordering while moving the nodes
                desired_positions.sort(
                    key=lambda item: item[1]
                )

                current_x: float | None = None

                for node_id, desired_x in desired_positions:

                    if current_x is None:

                        x = desired_x

                    else:

                        x = max(
                            desired_x,
                            current_x
                            + box_width
                            + horizontal_spacing,
                        )

                    y = positions[node_id][1]

                    positions[node_id] = (
                        x,
                        y,
                    )

                    current_x = x

    # ================================================================
    # Center graph
    # ================================================================

    min_x = min(
        x
        for x, _ in positions.values()
    )

    max_x = max(
        x
        for x, _ in positions.values()
    )

    center_x = (
        min_x + max_x
    ) / 2

    for node_id, (x, y) in positions.items():

        positions[node_id] = (
            x - center_x,
            y,
        )

    # ================================================================
    # Figure
    # ================================================================

    if figsize is None:

        if direction == "TB":

            width = max(
                8,
                (
                    max_x - min_x
                    + box_width
                    + 2
                ),
            )

            height = max(
                5,
                (
                    max_level + 1
                )
                * (
                    box_height
                    + vertical_spacing
                )
                + 2,
            )

        else:

            width = max(
                8,
                (
                    max_level + 1
                )
                * (
                    box_width
                    + vertical_spacing
                )
                + 2,
            )

            height = max(
                5,
                (
                    max(
                        len(nodes)
                        for nodes in level_nodes.values()
                    )
                    * (
                        box_height
                        + horizontal_spacing
                    )
                    + 2
                ),
            )

        figsize = (
            width,
            height,
        )

    fig, ax = plt.subplots(
        figsize=figsize
    )

    # ================================================================
    # Draw curved connections
    # ================================================================

    for child_id, parent_ids in parents.items():

        child_x, child_y = positions[child_id]

        for parent_id in parent_ids:

            parent_x, parent_y = positions[parent_id]

            if direction == "TB":

                # ----------------------------------------------------
                # Start at bottom of parent
                # ----------------------------------------------------

                start = (
                    parent_x,
                    parent_y - box_height / 2,
                )

                # ----------------------------------------------------
                # End at top of child
                # ----------------------------------------------------

                end = (
                    child_x,
                    child_y + box_height / 2,
                )

                dy = abs(
                    end[1] - start[1]
                )

                # ----------------------------------------------------
                # Bézier control points
                # ----------------------------------------------------

                control_distance = (
                    dy * 0.45
                )

                dx = (
                    child_x
                    - parent_x
                )

                # The curve becomes more pronounced when the
                # child is far away horizontally.
                horizontal_factor = max(
                    -0.5,
                    min(
                        0.5,
                        dx / (
                            box_width * 4
                        ),
                    ),
                )

                control1 = (
                    parent_x
                    + horizontal_factor,
                    start[1]
                    - control_distance,
                )

                control2 = (
                    child_x
                    - horizontal_factor,
                    end[1]
                    + control_distance,
                )

            else:

                # ----------------------------------------------------
                # Start at right of parent
                # ----------------------------------------------------

                start = (
                    parent_x + box_width / 2,
                    parent_y,
                )

                # ----------------------------------------------------
                # End at left of child
                # ----------------------------------------------------

                end = (
                    child_x - box_width / 2,
                    child_y,
                )

                dx = abs(
                    end[0] - start[0]
                )

                control_distance = (
                    dx * 0.45
                )

                dy = (
                    child_y
                    - parent_y
                )

                vertical_factor = max(
                    -0.5,
                    min(
                        0.5,
                        dy / (
                            box_height * 4
                        ),
                    ),
                )

                control1 = (
                    start[0]
                    + control_distance,
                    parent_y
                    + vertical_factor,
                )

                control2 = (
                    end[0]
                    - control_distance,
                    child_y
                    - vertical_factor,
                )

            # --------------------------------------------------------
            # Bézier path
            # --------------------------------------------------------

            vertices = [
                start,
                control1,
                control2,
                end,
            ]

            codes = [
                Path.MOVETO,
                Path.CURVE4,
                Path.CURVE4,
                Path.CURVE4,
            ]

            path = Path(
                vertices,
                codes,
            )

            patch = PathPatch(
                path,
                fill=False,
                linewidth=1.2,
            )

            ax.add_patch(patch)

            # --------------------------------------------------------
            # Arrow head
            # --------------------------------------------------------

            if direction == "TB":

                # Tangent near the end of the Bézier curve
                arrow_start = (
                    end[0],
                    end[1] + 0.08,
                )

            else:

                arrow_start = (
                    end[0] + 0.08,
                    end[1],
                )

            ax.annotate(
                "",
                xy=end,
                xytext=arrow_start,
                arrowprops=dict(
                    arrowstyle="->",
                    linewidth=1.2,
                ),
            )

    # ================================================================
    # Draw blocks
    # ================================================================

    for case_id, case in case_by_id.items():

        x, y = positions[case_id]

        box = FancyBboxPatch(
            (
                x - box_width / 2,
                y - box_height / 2,
            ),
            box_width,
            box_height,
            boxstyle=(
                "round,"
                "pad=0.05,"
                "rounding_size=0.08"
            ),
            linewidth=1.5,
            facecolor=case.color,
            edgecolor="black",
        )

        ax.add_patch(box)

        ax.text(
            x,
            y,
            case.name,
            ha="center",
            va="center",
            fontsize=10,
            color=case.text_color,
            wrap=True,
        )

    # ================================================================
    # Formatting
    # ================================================================

    ax.set_aspect("equal")
    ax.axis("off")

    margin = 1.0

    xs = [
        x
        for x, _ in positions.values()
    ]

    ys = [
        y
        for _, y in positions.values()
    ]

    ax.set_xlim(
        min(xs)
        - box_width / 2
        - margin,
        max(xs)
        + box_width / 2
        + margin,
    )

    ax.set_ylim(
        min(ys)
        - box_height / 2
        - margin,
        max(ys)
        + box_height / 2
        + margin,
    )

    plt.tight_layout()

    # ================================================================
    # Save
    # ================================================================

    if save_path is not None:

        fig.savefig(
            save_path,
            bbox_inches="tight",
            dpi=300,
        )

    if show:
        plt.show()

    return fig, ax