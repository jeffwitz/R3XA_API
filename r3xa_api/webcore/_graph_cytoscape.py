from __future__ import annotations

from html import escape
from importlib.resources import files
import json
from pathlib import Path
from string import Template
from typing import Any, Dict

from ._graph_core import PALETTES, build_graph_relation_catalog, resolve_styles
from ._graph_graphviz_wasm import generate_svg_wasm
from .schema_catalog import build_schema_catalog


def render_cytoscape_html(
    data: Dict[str, Any],
    output_path: Path,
    include_description: bool = True,
    palette: str | None = None,
    relations: str = "all",
) -> Path:
    """Write a standalone, read-only Cytoscape graph and object inspector."""

    selected_palette = palette or "document"
    resolve_styles(selected_palette)
    svg = generate_svg_wasm(
        data,
        include_description=include_description,
        palette=selected_palette,
        relations=relations,
    ).decode("utf-8")
    catalog = build_schema_catalog()
    items = {}
    for section in ("settings", "data_sources", "data_sets"):
        kinds = catalog["sections"][section]["kinds"]
        for item in data.get(section, []):
            item_id = item.get("id")
            if item_id:
                properties = kinds.get(item.get("kind"), {}).get("properties", {})
                items[item_id] = {"item": item, "properties": properties}

    state = {
        "payload": data,
        "layoutSvg": svg,
        "palettes": PALETTES,
        "relationCatalog": build_graph_relation_catalog(),
        "options": {
            "includeDescription": include_description,
            "palette": selected_palette,
            "relations": relations,
        },
        "items": items,
        "labels": {
            "selectTitle": "Select an object",
            "selectHelp": "Click a graph node to inspect its fields.",
            "id": "ID",
        },
    }
    resources = files("r3xa_web")
    template = Template(
        resources.joinpath("templates/standalone_cytoscape.html").read_text(encoding="utf-8")
    )
    bundle = resources.joinpath("static/standalone-cytoscape.generated.js").read_text(
        encoding="utf-8"
    )
    output = output_path.with_suffix(".html")
    output.write_text(
        template.substitute(
            document_title=escape(str(data.get("title") or "R3XA")),
            payload_json=escape(json.dumps(data, indent=2, ensure_ascii=False)),
            state_json=json.dumps(state, ensure_ascii=False).replace("<", "\\u003c"),
            bundle=bundle.replace("</script", "<\\/script"),
        ),
        encoding="utf-8",
    )
    return output
