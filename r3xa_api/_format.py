from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def format_number(value: Any) -> str:
    """Render an integral float without its trailing zero."""

    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _format_data_set_file(value: Mapping[str, Any]) -> str:
    filename = str(value["filename"])
    selector: list[str] = []
    if "col" in value:
        selector.extend((format_json_value(value["col"]), "x"))
    if "rows" in value:
        selector.append(format_json_value(value["rows"]))
    suffix = " " + " ".join(selector) if selector else ""
    return "{" + filename + (":" + suffix if suffix else "") + "}"


def format_json_value(value: Any) -> str:
    """Render a JSON-compatible value in a compact, human-readable form."""

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict) and not isinstance(value, Mapping):
        return format_json_value(to_dict())
    if value is None:
        return "None"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, Mapping):
        if value.get("kind") == "data_set_file" and "filename" in value:
            return _format_data_set_file(value)
        if value.get("kind") == "unit" and "value" in value and "unit" in value:
            return f"{format_number(value['value'])} {value['unit']}"
        inner = ", ".join(
            f"{key}: {format_json_value(item)}" for key, item in value.items()
        )
        return "{" + inner + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(format_json_value(item) for item in value) + "]"
    return format_number(value)
