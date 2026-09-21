from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from pathlib import Path
import re
from typing import Any, Dict, Iterable
from xml.etree import ElementTree

from ._graph_graphviz import build_graphviz_dot

_WASM_RESOURCE = "resources/graphviz/graphviz-12.2.1.wasm"


def _load_wasmtime() -> Any:
    try:
        import wasmtime
    except ImportError as exc:  # pragma: no cover - broken/incomplete installation
        raise RuntimeError(
            "Graphviz WebAssembly is not available. Reinstall r3xa-api with its "
            "standard dependencies."
        ) from exc
    return wasmtime


@lru_cache(maxsize=1)
def _module() -> tuple[Any, Any]:
    wasmtime = _load_wasmtime()
    engine = wasmtime.Engine()
    resource = files("r3xa_api").joinpath(_WASM_RESOURCE)
    try:
        module = wasmtime.Module(engine, resource.read_bytes())
    except Exception as exc:  # pragma: no cover - corrupted package data
        raise RuntimeError("The bundled Graphviz WebAssembly module could not be loaded.") from exc
    return wasmtime, (engine, module)


def _render_dot(dot_source: str) -> bytes:
    wasmtime, (engine, module) = _module()
    store = wasmtime.Store(engine)
    wasi = wasmtime.WasiConfig()
    wasi.argv = ["r3xa-graphviz"]
    store.set_wasi(wasi)
    linker = wasmtime.Linker(engine)
    linker.define_wasi()
    instance = linker.instantiate(store, module)
    exports = instance.exports(store)
    memory = exports["memory"]
    malloc = exports["malloc"]
    free = exports["free"]
    render = exports["r3xa_graphviz_render"]
    last_error = exports["r3xa_graphviz_last_error"]

    encoded = dot_source.encode("utf-8")
    source_ptr = malloc(store, len(encoded) + 1)
    length_ptr = malloc(store, 4)
    memory.write(store, encoded + b"\0", source_ptr)
    try:
        result_ptr = render(store, source_ptr, len(encoded), length_ptr)
        if not result_ptr:
            error_ptr = last_error(store)
            error = bytes(memory.read(store, error_ptr, error_ptr + 256)).split(b"\0", 1)[0]
            message = error.decode("utf-8", errors="replace") or "unknown Graphviz WebAssembly error"
            raise RuntimeError(f"Graphviz WebAssembly rendering failed: {message}")
        result_length = int.from_bytes(memory.read(store, length_ptr, length_ptr + 4), "little")
        result = bytes(memory.read(store, result_ptr, result_ptr + result_length))
        free(store, result_ptr)
        return result
    finally:
        free(store, source_ptr)
        free(store, length_ptr)


def compute_graphviz_positions_wasm(
    node_ids: Iterable[str],
    edges: Iterable[tuple[str, str]],
    label_widths: Dict[str, float],
) -> tuple[Dict[str, tuple[float, float]], Dict[str, float]] | None:
    """Return Graphviz positions using the bundled WebAssembly layout engine."""

    node_ids = list(node_ids)
    edges = list(edges)
    try:
        from graphviz import Digraph

        dot = Digraph(comment="R3XA pyvis layout")
        dot.attr("graph", rankdir="TB", nodesep="0.55", ranksep="0.95")
        dot.attr("node", margin="0.2,0.1")
        for node_id in node_ids:
            width_in = max(1.8, label_widths.get(node_id, 220.0) / 96.0)
            dot.node(node_id, label=node_id, width=f"{width_in:.3f}")
        for src, dst in edges:
            dot.edge(src, dst)

        root = ElementTree.fromstring(_render_dot(dot.source))
    except Exception:
        return None

    raw_positions: Dict[str, tuple[float, float]] = {}
    widths: Dict[str, float] = {}
    for group in root.iter():
        if group.tag.rsplit("}", 1)[-1] != "g" or group.attrib.get("class") != "node":
            continue
        title = next(
            (child.text for child in group if child.tag.rsplit("}", 1)[-1] == "title"),
            None,
        )
        shape = next(
            (
                child
                for child in group
                if child.tag.rsplit("}", 1)[-1] in {"ellipse", "polygon"}
            ),
            None,
        )
        if not title or shape is None:
            continue

        shape_name = shape.tag.rsplit("}", 1)[-1]
        if shape_name == "ellipse":
            center_x = float(shape.attrib["cx"])
            center_y = float(shape.attrib["cy"])
            width_points = 2.0 * float(shape.attrib["rx"])
        else:
            points = [
                (float(x), float(y))
                for x, y in re.findall(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", shape.attrib["points"])
            ]
            if not points:
                continue
            center_x = sum(x for x, _ in points) / len(points)
            center_y = sum(y for _, y in points) / len(points)
            width_points = max(x for x, _ in points) - min(x for x, _ in points)

        # SVG coordinates are points (72 per inch) and grow downwards. The
        # existing layout post-processing expects Graphviz plain-output units.
        raw_positions[title] = (center_x / 72.0, -center_y / 72.0)
        widths[title] = width_points * (96.0 / 72.0)

    if set(raw_positions) != set(node_ids):
        return None
    return raw_positions, widths


def generate_svg_wasm(
    data: Dict[str, Any],
    include_description: bool = True,
    palette: str | None = None,
    relations: str = "all",
) -> bytes:
    """Generate an SVG with the bundled Graphviz WASI module.

    This backend uses the same DOT source and graph styling as the native
    Graphviz backend, but does not require the system ``dot`` executable.
    """

    dot = build_graphviz_dot(
        data,
        format="svg",
        include_description=include_description,
        palette=palette,
        relations=relations,
    )
    return _render_dot(dot.source)


def render_graphviz_wasm_file(
    data: Dict[str, Any],
    output_path: Path,
    export_dot: bool = False,
    include_description: bool = True,
    palette: str | None = None,
    relations: str = "all",
) -> Path:
    """Render a Graphviz WebAssembly SVG file and optionally export DOT."""

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
    svg_path.write_bytes(_render_dot(dot.source))
    return svg_path
