from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from .schema import load_schema


_REFERENCE_TYPES = {
    "#/$defs/types/setting_id": "settings",
    "#/$defs/types/data_source_id": "data_sources",
    "#/$defs/types/data_set_id": "data_sets",
}


def _collect_reference_fields(node: Any) -> dict[str, str]:
    fields: dict[str, str] = {}

    def visit(value: Any, field: str | None = None) -> None:
        if isinstance(value, Mapping):
            ref = value.get("$ref")
            if field and ref in _REFERENCE_TYPES:
                fields[field] = _REFERENCE_TYPES[ref]
            items = value.get("items")
            if field and isinstance(items, Mapping) and items.get("$ref") in _REFERENCE_TYPES:
                fields[field] = _REFERENCE_TYPES[items["$ref"]]
            properties = value.get("properties")
            if isinstance(properties, Mapping):
                for name, property_schema in properties.items():
                    visit(property_schema, str(name))
            if isinstance(items, Mapping):
                visit(items, field)
            for key in ("anyOf", "oneOf", "allOf"):
                for option in value.get(key, ()) or ():
                    visit(option, field)
        elif isinstance(value, list):
            for option in value:
                visit(option, field)

    visit(node)
    return fields


@lru_cache(maxsize=None)
def reference_fields(kind: str | None = None) -> dict[str, str]:
    """Return schema-declared reference fields, optionally scoped to a kind.

    With no kind, return the historical union used by document-level helpers.
    Passing a concrete kind keeps reference semantics local to the schema
    definition instead of assuming that a property name has one meaning
    everywhere.
    """

    schema = load_schema()
    if kind is None:
        return _collect_reference_fields(schema)
    if "/" not in kind:
        return {}
    section, name = kind.split("/", 1)
    definition = schema.get("$defs", {}).get(section, {}).get(name)
    return _collect_reference_fields(definition) if isinstance(definition, Mapping) else {}


def reference_id(value: Any) -> str | None:
    """Extract an R3XA identifier from a string, model, or mapping."""

    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        raw = value.get("root", value.get("id"))
    else:
        raw = getattr(value, "root", getattr(value, "id", None))
    return raw if isinstance(raw, str) else None
