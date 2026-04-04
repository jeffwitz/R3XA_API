#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_SCHEMA = Path("r3xa_api/resources/schema.json")
DEFAULT_OUTPUT = Path("docs/specification.md")

SECTION_ORDER = ("settings", "data_sources", "data_sets")
SECTION_TITLES = {
    "settings": "Settings",
    "data_sources": "Data Sources",
    "data_sets": "Data Sets",
}
SECTION_DESCRIPTIONS = {
    "header": "Top-level metadata fields (`title`, `description`, `version`, authorship and links).",
    "settings": "Experimental setup and specimen metadata.",
    "data_sources": "Sensors and processing blocks that produce data.",
    "data_sets": "Data containers linked to one or more data sources.",
}
TYPE_NAME_OVERRIDES = {
    "unit": "Unit",
    "uint": "unsigned integer",
    "data_set_file": "Data set file",
    "data_set_id": "Data set id",
    "data_source_id": "Data source id",
    "setting_id": "Setting id",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate docs/specification.md from schema.json.")
    parser.add_argument("schema", nargs="?", default=str(DEFAULT_SCHEMA), help="Path to schema JSON.")
    parser.add_argument("output", nargs="?", default=str(DEFAULT_OUTPUT), help="Output markdown path.")
    return parser.parse_args()


def _anchor_for_type(type_name: str) -> str:
    return type_name.strip().lower().replace(" ", "-")


def _escape_md(text: str | None) -> str:
    if text is None:
        return ""
    return str(text).replace("|", r"\|").replace("\n", "<br>")


def _format_simple_type(type_name: str) -> str:
    if type_name == "uint":
        return "unsigned integer"
    if type_name in TYPE_NAME_OVERRIDES:
        pretty = TYPE_NAME_OVERRIDES[type_name]
        if type_name in {"unit", "data_set_file"}:
            return f'<a href="#{_anchor_for_type(pretty)}">{pretty}</a>'
        return pretty
    return type_name.replace("_", " ").title()


def _resolve_ref(ref: str) -> str:
    if not ref.startswith("#/$defs/"):
        return ref
    parts = ref.split("/")
    if len(parts) < 4:
        return ref
    group = parts[2]
    name = parts[3]
    if group == "types":
        return _format_simple_type(name)
    return name.replace("_", " ").title()


def _render_type(type_schema: dict[str, Any]) -> str:
    if "const" in type_schema:
        return f'"{type_schema["const"]}" (fixed)'
    if "enum" in type_schema:
        values = [json.dumps(value, ensure_ascii=False) for value in type_schema["enum"]]
        return " | ".join(values)
    if "$ref" in type_schema:
        return _resolve_ref(type_schema["$ref"])
    for union_key in ("anyOf", "oneOf"):
        if union_key in type_schema:
            return " | ".join(_render_type(option) for option in type_schema[union_key])
    if "allOf" in type_schema:
        return " + ".join(_render_type(option) for option in type_schema["allOf"])
    schema_type = type_schema.get("type")
    if isinstance(schema_type, list):
        return " | ".join(schema_type)
    if schema_type == "array":
        if "items" in type_schema:
            return f"array[{_render_type(type_schema['items'])}]"
        return "array"
    if schema_type:
        return str(schema_type)
    if "items" in type_schema:
        return f"array[{_render_type(type_schema['items'])}]"
    return "object"


def _fields_table_lines(def_schema: dict[str, Any]) -> list[str]:
    properties = def_schema.get("properties", {})
    required = set(def_schema.get("required", []))

    lines = [
        "| Field | Type | Required | Description |",
        "|---|---|---|---|",
    ]

    for field_name, field_schema in properties.items():
        field_type = _render_type(field_schema)
        mark = "✅" if field_name in required else ""
        description = field_schema.get("description") or field_schema.get("title") or ""
        lines.append(
            f"| `{_escape_md(field_name)}` | {_escape_md(field_type)} | {mark} | {_escape_md(description)} |"
        )
    return lines


def _kind_label(section_key: str, item_schema: dict[str, Any], default_name: str) -> str:
    kind_const = (
        item_schema.get("properties", {})
        .get("kind", {})
        .get("const")
    )
    if isinstance(kind_const, str) and kind_const:
        return kind_const
    return f"{section_key}/{default_name}"


def _choices_label(property_schema: dict[str, Any], schema: dict[str, Any]) -> str:
    options = property_schema.get("items", {}).get("anyOf", [])
    labels: list[str] = []
    for option in options:
        ref = option.get("$ref")
        if not ref:
            labels.append(_render_type(option))
            continue
        labels.append(_resolve_ref(ref))
    if not labels:
        return "N/A"
    return " | ".join(labels)


def _schema_version(schema: dict[str, Any]) -> str:
    version_prop = schema.get("properties", {}).get("version", {})
    const = version_prop.get("const")
    if isinstance(const, str):
        return const
    return "unknown"


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _generate_markdown(schema: dict[str, Any], schema_path: Path) -> str:
    lines: list[str] = [
        "<!-- THIS FILE IS AUTO-GENERATED -->",
        f"<!-- Source: {_display_path(schema_path)} -->",
        "<!-- Command: python scripts/dev.py generate-spec -->",
        "<!-- DO NOT EDIT MANUALLY -->",
        "",
        "# R3XA Specification",
        "",
        f"> Version : `{_escape_md(_schema_version(schema))}`",
        "",
        _escape_md(schema.get("description", "")),
        "",
        "## General Structure",
        "",
        "| Section | Description |",
        "|---|---|",
    ]

    for section_key in ("header", "settings", "data_sources", "data_sets"):
        lines.append(f"| `{section_key}` | {_escape_md(SECTION_DESCRIPTIONS[section_key])} |")

    lines.extend(
        [
            "",
            "## Header",
            "",
            "| Field | Type | Required | Description |",
            "|---|---|---|---|",
        ]
    )
    root_required = set(schema.get("required", []))
    for field_name, field_schema in schema.get("properties", {}).items():
        if field_name in SECTION_ORDER:
            continue
        field_type = _render_type(field_schema)
        mark = "✅" if field_name in root_required else ""
        description = field_schema.get("description") or field_schema.get("title") or ""
        lines.append(
            f"| `{_escape_md(field_name)}` | {_escape_md(field_type)} | {mark} | {_escape_md(description)} |"
        )

    defs = schema.get("$defs", {})
    for section_key in SECTION_ORDER:
        section_defs = defs.get(section_key, {})
        collection_schema = schema.get("properties", {}).get(section_key, {})
        lines.extend(
            [
                "",
                f"## {SECTION_TITLES[section_key]}",
                "",
                _escape_md(collection_schema.get("description", "")),
                "",
                f"Allowed item kinds: {_escape_md(_choices_label(collection_schema, schema))}",
                "",
            ]
        )
        for item_key, item_schema in section_defs.items():
            item_title = item_schema.get("title") or item_key.replace("_", " ").title()
            kind_label = _kind_label(section_key, item_schema, item_key)
            lines.extend(
                [
                    f"### {item_title} (`{_escape_md(kind_label)}`)",
                    "",
                ]
            )
            item_description = item_schema.get("description")
            if item_description:
                lines.extend([_escape_md(item_description), ""])
            lines.extend(_fields_table_lines(item_schema))
            lines.append("")

    lines.extend(
        [
            "## Appendix — Common Types",
            "",
        ]
    )

    for type_name, type_schema in defs.get("types", {}).items():
        display_name = TYPE_NAME_OVERRIDES.get(type_name, type_name.replace("_", " ").title())
        lines.extend(
            [
                f"### {display_name}",
                "",
            ]
        )

        type_description = type_schema.get("description")
        if type_description:
            lines.extend([_escape_md(type_description), ""])

        if "properties" in type_schema:
            lines.extend(_fields_table_lines(type_schema))
        else:
            base_type = _render_type(type_schema)
            lines.extend(
                [
                    "| Property | Value |",
                    "|---|---|",
                    f"| `type` | {_escape_md(base_type)} |",
                ]
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = _parse_args()
    schema_path = Path(args.schema)
    output_path = Path(args.output)

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    markdown = _generate_markdown(schema=schema, schema_path=schema_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Specification written to {output_path.as_posix()}")


if __name__ == "__main__":
    main()
