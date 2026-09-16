from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ._graph_core import PALETTES, STYLES, graphviz_styles_to_pyvis, resolve_styles
from ._graph_graphviz import (
    build_graphviz_dot,
    generate_svg,
    render_graphviz_file as _render_graphviz_file,
)
from ._graph_networkx import render_networkx_matplotlib_file as _render_networkx_matplotlib_file
from ._graph_pyvis import render_pyvis_html as _render_pyvis_html

__all__ = [
    "PALETTES",
    "STYLES",
    "build_graphviz_dot",
    "generate_svg",
    "graphviz_styles_to_pyvis",
    "resolve_styles",
    "render_graphviz_file",
    "render_networkx_matplotlib_file",
    "render_pyvis_html",
]


def render_graphviz_file(
    data: Dict[str, Any],
    output_path: Path,
    export_dot: bool = False,
    include_description: bool = True,
    palette: str | None = None,
) -> Path:
    """Render a Graphviz SVG file and optionally export the DOT source."""

    return _render_graphviz_file(
        data,
        output_path,
        export_dot=export_dot,
        include_description=include_description,
        palette=palette,
    )


def render_pyvis_html(
    data: Dict[str, Any],
    output_path: Path,
    include_description: bool = True,
    palette: str | None = None,
) -> Path:
    """Render an interactive PyVis HTML graph from an R3XA payload."""

    return _render_pyvis_html(
        data, output_path, include_description=include_description, palette=palette
    )


def render_networkx_matplotlib_file(
    data: Dict[str, Any],
    output_path: Path,
    format: str = "png",
    dpi: int = 220,
    include_description: bool = True,
    palette: str | None = None,
) -> Path:
    """Render a static graph image with NetworkX + Matplotlib."""

    return _render_networkx_matplotlib_file(
        data,
        output_path,
        format=format,
        dpi=dpi,
        include_description=include_description,
        palette=palette,
    )
