from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from .schema import load_schema


@lru_cache(maxsize=1)
def reference_fields() -> dict[str, str]:
    """Return schema-declared reference fields and their target sections."""

    id_types = {
        "#/$defs/types/setting_id": "settings",
        "#/$defs/types/data_source_id": "data_sources",
        "#/$defs/types/data_set_id": "data_sets",
    }
    fields: dict[str, str] = {}

    def visit(node: Any, field: str | None = None) -> None:
        if isinstance(node, Mapping):
            ref = node.get("$ref")
            if field and ref in id_types:
                fields[field] = id_types[ref]
            items = node.get("items")
            if field and isinstance(items, Mapping) and items.get("$ref") in id_types:
                fields[field] = id_types[items["$ref"]]
            properties = node.get("properties")
            if isinstance(properties, Mapping):
                for name, value in properties.items():
                    visit(value, str(name))
            definitions = node.get("$defs")
            if isinstance(definitions, Mapping):
                for group in definitions.values():
                    if isinstance(group, Mapping):
                        for value in group.values():
                            visit(value, field)
            if isinstance(items, Mapping):
                visit(items, field)
            for key in ("anyOf", "oneOf", "allOf"):
                for value in node.get(key, ()) or ():
                    visit(value, field)
        elif isinstance(node, list):
            for value in node:
                visit(value, field)

    visit(load_schema())
    return fields


def reference_id(value: Any) -> str | None:
    """Extract an R3XA identifier from a string, model, or mapping."""

    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        raw = value.get("root", value.get("id"))
    else:
        raw = getattr(value, "root", getattr(value, "id", None))
    return raw if isinstance(raw, str) else None
