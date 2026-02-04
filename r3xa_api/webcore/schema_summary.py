from typing import Any, Dict, Optional

from ..schema import load_schema


def _summarize_node(node: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for key in ("title", "description", "type", "required", "enum", "const"):
        if key in node:
            summary[key] = node[key]

    if "$ref" in node:
        summary["ref"] = node["$ref"]
        return summary

    if node.get("type") == "object":
        properties = node.get("properties", {})
        summary["properties"] = {k: _summarize_node(v) for k, v in properties.items()}

    if node.get("type") == "array" and "items" in node:
        summary["items"] = _summarize_node(node["items"])

    return summary


def build_schema_summary(schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    schema = schema or load_schema()
    version = schema.get("properties", {}).get("version", {}).get("const")
    properties = schema.get("properties", {})

    header_fields = {
        k: v
        for k, v in properties.items()
        if k not in {"settings", "data_sources", "data_sets"}
    }

    return {
        "schema_version": version,
        "sections": {
            "header": _summarize_node({"type": "object", "properties": header_fields}),
            "settings": _summarize_node(properties.get("settings", {})),
            "data_sources": _summarize_node(properties.get("data_sources", {})),
            "data_sets": _summarize_node(properties.get("data_sets", {})),
        },
    }
