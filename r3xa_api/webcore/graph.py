from __future__ import annotations

from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Any, Dict

from ._graph_core import PALETTES, STYLES, graphviz_styles_to_pyvis, resolve_styles
from ._graph_graphviz import (
    build_graphviz_dot,
    generate_svg,
    render_graphviz_file as _render_graphviz_file,
)
from ._graph_graphviz_wasm import (
    generate_svg_wasm,
    render_graphviz_wasm_file as _render_graphviz_wasm_file,
)
from ._graph_networkx import render_networkx_matplotlib_file as _render_networkx_matplotlib_file
from ._graph_pyvis import render_pyvis_html as _render_pyvis_html

__all__ = [
    "PALETTES",
    "STYLES",
    "build_graphviz_dot",
    "generate_svg",
    "generate_svg_wasm",
    "graphviz_styles_to_pyvis",
    "resolve_styles",
    "render_graphviz_file",
    "render_graphviz_wasm_file",
    "render_networkx_matplotlib_file",
    "render_pyvis_html",
    "render_graph_content",
]

GRAPH_BACKENDS = ("graphviz-wasm", "graphviz", "pyvis", "matplotlib")


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


def render_graphviz_wasm_file(
    data: Dict[str, Any],
    output_path: Path,
    export_dot: bool = False,
    include_description: bool = True,
    palette: str | None = None,
) -> Path:
    """Render a Graphviz SVG with the bundled WebAssembly backend."""

    return _render_graphviz_wasm_file(
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


def render_graph_content(
    data: Dict[str, Any],
    backend: str = "graphviz-wasm",
    include_description: bool = True,
    palette: str | None = None,
) -> tuple[bytes, str, str]:
    """Render a graph backend for HTTP delivery.

    Returns the content bytes, media type, and suggested file extension. The
    file-oriented renderer APIs remain available for Python callers.
    """

    if backend not in GRAPH_BACKENDS:
        available = ", ".join(GRAPH_BACKENDS)
        raise ValueError(f"Unknown graph backend {backend!r}. Available: {available}")
    if backend == "graphviz":
        return generate_svg(data, include_description=include_description, palette=palette), "image/svg+xml", "svg"
    if backend == "graphviz-wasm":
        return (
            generate_svg_wasm(data, include_description=include_description, palette=palette),
            "image/svg+xml",
            "svg",
        )

    with TemporaryDirectory(prefix="r3xa-graph-") as temporary_directory:
        output_base = Path(temporary_directory) / "graph"
        if backend == "pyvis":
            output_path = render_pyvis_html(
                data,
                output_base,
                include_description=include_description,
                palette=palette,
            )
            return output_path.read_bytes(), "text/html; charset=utf-8", "html"
        output_path = render_networkx_matplotlib_file(
            data,
            output_base,
            format="png",
            include_description=include_description,
            palette=palette,
        )
        return output_path.read_bytes(), "image/png", "png"
