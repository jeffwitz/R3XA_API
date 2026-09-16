from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..schema import load_schema


_NODE_KEYS = (
    "title",
    "description",
    "type",
    "required",
    "enum",
    "const",
    "default",
    "format",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "pattern",
    "examples",
    "additionalProperties",
    "uniqueItems",
)
_SECTION_NAMES = ("settings", "data_sources", "data_sets")


def _resolve_pointer(root: Dict[str, Any], reference: str) -> Optional[Dict[str, Any]]:
    if not reference.startswith("#/"):
        return None

    value: Any = root
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or token not in value:
            return None
        value = value[token]
    return value if isinstance(value, dict) else None


def _resolve_node(
    node: Dict[str, Any],
    root: Dict[str, Any],
    stack: Tuple[str, ...] = (),
) -> Dict[str, Any]:
    if "$ref" not in node:
        resolved = deepcopy(node)
    else:
        reference = node["$ref"]
        if not isinstance(reference, str):
            return deepcopy(node)
        target = _resolve_pointer(root, reference)
        if target is None or reference in stack:
            return deepcopy(node)
        resolved = _resolve_node(target, root, stack + (reference,))
        resolved.update(
            deepcopy({key: value for key, value in node.items() if key != "$ref"})
        )
        resolved["_source_ref"] = reference

    if isinstance(resolved.get("allOf"), list):
        merged = {
            key: value for key, value in resolved.items() if key != "allOf"
        }
        for branch in resolved["allOf"]:
            if not isinstance(branch, dict):
                continue
            branch = _resolve_node(branch, root, stack)
            if isinstance(branch.get("properties"), dict):
                merged.setdefault("properties", {}).update(
                    deepcopy(branch["properties"])
                )
            if isinstance(branch.get("required"), list):
                required = merged.setdefault("required", [])
                for name in branch["required"]:
                    if name not in required:
                        required.append(name)
            for key, value in branch.items():
                if key not in {"properties", "required"}:
                    merged.setdefault(key, deepcopy(value))
        resolved = merged

    child_stack = stack
    if "$ref" in node and isinstance(node["$ref"], str):
        child_stack = stack + (node["$ref"],)

    if isinstance(resolved.get("properties"), dict):
        resolved["properties"] = {
            key: _resolve_node(value, root, child_stack)
            for key, value in resolved["properties"].items()
        }
    if isinstance(resolved.get("items"), dict):
        resolved["items"] = _resolve_node(resolved["items"], root, child_stack)
    if isinstance(resolved.get("prefixItems"), list):
        resolved["prefixItems"] = [
            _resolve_node(value, root, child_stack)
            for value in resolved["prefixItems"]
            if isinstance(value, dict)
        ]
    for key in ("anyOf", "oneOf", "allOf"):
        if isinstance(resolved.get(key), list):
            resolved[key] = [
                _resolve_node(value, root, child_stack)
                for value in resolved[key]
                if isinstance(value, dict)
            ]
    return resolved


def _catalog_node(node: Dict[str, Any]) -> Dict[str, Any]:
    catalog: Dict[str, Any] = {
        key: node[key]
        for key in _NODE_KEYS
        if key in node
    }
    if "$ref" in node:
        catalog["ref"] = node["$ref"]
    elif "_source_ref" in node:
        catalog["ref"] = node["_source_ref"]
    if isinstance(node.get("properties"), dict):
        catalog["properties"] = {
            key: _catalog_node(value)
            for key, value in node["properties"].items()
        }
    if isinstance(node.get("items"), dict):
        catalog["items"] = _catalog_node(node["items"])
    if isinstance(node.get("prefixItems"), list):
        catalog["prefixItems"] = [
            _catalog_node(value)
            for value in node["prefixItems"]
            if isinstance(value, dict)
        ]
    for key in ("anyOf", "oneOf", "allOf"):
        if isinstance(node.get(key), list):
            catalog[key] = [_catalog_node(value) for value in node[key]]
    return catalog


def _kind_options(node: Dict[str, Any], root: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    items = node.get("items", {})
    if not isinstance(items, dict):
        return ()
    items = _resolve_node(items, root)
    for key in ("anyOf", "oneOf"):
        options = items.get(key)
        if isinstance(options, list):
            return (option for option in options if isinstance(option, dict))
    if isinstance(items.get("properties"), dict):
        return (items,)
    return ()


def _section_catalog(schema: Dict[str, Any], section: str) -> Dict[str, Any]:
    section_node = schema.get("properties", {}).get(section, {})
    kinds: Dict[str, Dict[str, Any]] = {}
    for option in _kind_options(section_node, schema):
        resolved = _resolve_node(option, schema)
        kind = resolved.get("properties", {}).get("kind", {}).get("const")
        if isinstance(kind, str):
            kinds[kind] = _catalog_node(resolved)

    return {
        key: section_node[key]
        for key in ("title", "description", "type", "required")
        if key in section_node
    } | {"kinds": kinds}


def build_schema_catalog(schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build a resolved, UI-oriented catalogue of the R3XA schema kinds."""

    schema = schema or load_schema()
    properties = schema.get("properties", {})
    header_properties = {
        key: value
        for key, value in properties.items()
        if key not in _SECTION_NAMES
    }
    header_node = {
        "type": "object",
        "properties": header_properties,
        "required": [
            key
            for key in schema.get("required", [])
            if key not in _SECTION_NAMES
        ],
    }

    version = properties.get("version", {}).get("const")
    return {
        "schema_version": version,
        "sections": {
            "header": _catalog_node(_resolve_node(header_node, schema)),
            **{
                section: _section_catalog(schema, section)
                for section in _SECTION_NAMES
            },
        },
    }
