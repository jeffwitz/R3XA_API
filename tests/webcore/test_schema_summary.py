import pytest

from r3xa_api.webcore import build_schema_catalog, build_schema_summary, build_ui_catalog
from r3xa_api.webcore.ui_catalog import _validate_profile_questions


def test_schema_summary_sections() -> None:
    summary = build_schema_summary()
    assert summary["schema_version"] == "2024.7.1"
    assert set(summary["sections"].keys()) == {
        "header",
        "settings",
        "data_sources",
        "data_sets",
    }


def test_schema_catalog_contains_all_resolved_kinds() -> None:
    catalog = build_schema_catalog()

    assert catalog["schema_version"] == "2024.7.1"
    assert set(catalog["sections"]["settings"]["kinds"]) == {
        "settings/generic",
        "settings/specimen",
        "settings/testing_machine",
        "settings/stereorig",
    }
    assert len(catalog["sections"]["data_sources"]["kinds"]) == 11
    assert set(catalog["sections"]["data_sets"]["kinds"]) == {
        "data_sets/generic",
        "data_sets/file",
        "data_sets/list",
    }

    camera = catalog["sections"]["data_sources"]["kinds"]["data_sources/camera"]
    assert camera["properties"]["output_components"]["type"] == "integer"
    assert camera["properties"]["image_size"]["items"]["properties"]["kind"]["const"] == "unit"
    assert camera["properties"]["image_size"]["items"]["ref"] == "#/$defs/types/unit"


def test_schema_catalog_resolves_combinators_and_refs() -> None:
    schema = {
        "type": "object",
        "properties": {
            "version": {"const": "test"},
            "settings": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"$ref": "#/$defs/base"},
                        {"$ref": "#/$defs/special"},
                    ]
                },
            },
            "data_sources": {"type": "array", "items": {"anyOf": []}},
            "data_sets": {"type": "array", "items": {"anyOf": []}},
        },
        "required": ["version"],
        "$defs": {
            "base": {
                "type": "object",
                "properties": {
                    "kind": {"const": "settings/base"},
                    "name": {"type": "string"},
                },
                "required": ["kind"],
            },
            "special": {
                "allOf": [
                    {"$ref": "#/$defs/base"},
                    {
                        "type": "object",
                        "properties": {
                            "kind": {"const": "settings/special"},
                            "level": {"type": "integer"},
                        },
                        "required": ["level"],
                    },
                ]
            },
        },
    }

    catalog = build_schema_catalog(schema)
    special = catalog["sections"]["settings"]["kinds"]["settings/special"]

    assert special["required"] == ["kind", "level"]
    assert special["properties"]["name"]["type"] == "string"


def test_schema_catalog_discovers_kinds_from_all_of_items() -> None:
    schema = {
        "type": "object",
        "properties": {
            "version": {"const": "test"},
            "settings": {
                "type": "array",
                "items": {
                    "allOf": [
                        {"$ref": "#/$defs/base"},
                        {
                            "type": "object",
                            "properties": {
                                "kind": {"const": "settings/composed"},
                                "value": {"type": "number"},
                            },
                            "required": ["value"],
                        },
                    ]
                },
            },
            "data_sources": {"type": "array", "items": {"anyOf": []}},
            "data_sets": {"type": "array", "items": {"anyOf": []}},
        },
        "$defs": {
            "base": {
                "type": "object",
                "properties": {"kind": {"type": "string"}},
                "required": ["kind"],
            }
        },
    }

    catalog = build_schema_catalog(schema)

    composed = catalog["sections"]["settings"]["kinds"]["settings/composed"]
    assert composed["required"] == ["kind", "value"]
    assert composed["properties"]["value"]["type"] == "number"


def test_ui_catalog_profiles_reference_schema_kinds() -> None:
    catalog = build_ui_catalog()

    assert catalog["schema_version"] == "2024.7.1"
    assert catalog["default"]["fields"]["kind"]["level"] == "expert"
    assert set(catalog["profiles"]) == {"generic", "mechanical_test", "dic_2d"}
    assert catalog["profiles"]["dic_2d"]["steps"][-1]["kind"] == "data_sources/dic_measurement"
    assert catalog["profiles"]["dic_2d"]["steps"][0]["questions"][0]["field"] == "title"


def test_ui_profile_validation_reports_invalid_sections_and_steps() -> None:
    schema_catalog = build_schema_catalog()

    with pytest.raises(ValueError, match="unknown section"):
        _validate_profile_questions(
            {"id": "broken", "steps": [{"id": "bad", "section": "unknown"}]},
            schema_catalog,
        )

    with pytest.raises(ValueError, match="steps must contain objects"):
        _validate_profile_questions(
            {"id": "broken", "steps": ["bad"]},
            schema_catalog,
        )
