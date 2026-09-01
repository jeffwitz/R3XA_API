from copy import deepcopy

import pytest

from r3xa_api.webcore import build_schema_catalog, build_schema_summary, build_ui_catalog
from r3xa_api.webcore._graph_core import build_graph_model
from r3xa_api.webcore.ui_catalog import _validate_profile_links, _validate_profile_questions
from r3xa_api.validate import validate


def _prefilled_profile_document(profile: dict) -> dict:
    payload = {"settings": [], "data_sources": [], "data_sets": []}
    steps = {step["id"]: step for step in profile["steps"]}
    items = {}
    for step in profile["steps"]:
        if step["section"] == "header":
            payload.update(deepcopy(step.get("defaults", {})))
            continue
        if "kind" not in step:
            continue
        item = {
            "id": f"{step['id']}_id",
            "kind": step["kind"],
            **deepcopy(step.get("defaults", {})),
        }
        payload[step["section"]].append(item)
        items[step["id"]] = item
    for link in profile.get("links", []):
        items[link["to_step"]][link["to_field"]] = [items[link["from_step"]]["id"]]
    return payload


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
    assert camera["properties"]["input_data_sets"]["items"]["ref"] == "#/$defs/types/data_set_id"
    image_set = catalog["sections"]["data_sets"]["kinds"]["data_sets/list"]
    assert image_set["properties"]["data_sources"]["items"]["ref"] == "#/$defs/types/data_source_id"
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
    assert catalog["profiles"]["dic_2d"]["steps"][-2]["kind"] == "data_sources/dic_measurement"
    assert catalog["profiles"]["dic_2d"]["steps"][0]["questions"][0]["field"] == "title"
    assert catalog["profiles"]["dic_2d"]["steps"][0]["defaults"]["title"] == "Tensile test with 2D DIC"
    assert catalog["profiles"]["dic_2d"]["steps"][-1]["kind"] == "data_sets/file"
    assert catalog["profiles"]["dic_2d"]["steps"][-1]["defaults"]["data"]["filename"] == "displacement_fields.h5"
    assert {
        (link["from_step"], link["to_step"], link["to_field"])
        for link in catalog["profiles"]["dic_2d"]["links"]
    } == {
        ("machine", "machine_data", "data_sources"),
        ("camera", "images", "data_sources"),
        ("images", "dic", "input_data_sets"),
        ("dic", "displacement_fields", "data_sources"),
    }


def test_prefilled_dic_profile_builds_a_valid_dependency_chain() -> None:
    profile = build_ui_catalog()["profiles"]["dic_2d"]
    payload = _prefilled_profile_document(profile)

    validate(payload)
    items = {item["id"]: item for section in ("settings", "data_sources", "data_sets") for item in payload[section]}
    machine = items["machine_id"]
    camera = items["camera_id"]
    images = items["images_id"]
    dic = items["dic_id"]
    displacement_fields = items["displacement_fields_id"]
    machine_data = items["machine_data_id"]

    assert "input_data_sets" not in camera
    assert "input_data_sets" not in machine
    assert machine_data["data_sources"] == ["machine_id"]
    assert images["data_sources"] == ["camera_id"]
    assert dic["input_data_sets"] == ["images_id"]
    assert displacement_fields["data_sources"] == ["dic_id"]
    graph = build_graph_model(payload)
    assert "images_id" in graph.used_datasets
    assert "machine_data_id" not in graph.used_datasets
    assert "displacement_fields_id" not in graph.used_datasets
    assert graph.levels["machine_id"] == 0
    assert graph.levels["camera_id"] == 0
    assert graph.levels["specimen_id"] == 0
    assert {(edge.src, edge.dst) for edge in graph.edge_records} == {
        ("machine_id", "machine_data_id"),
        ("camera_id", "images_id"),
        ("images_id", "dic_id"),
        ("dic_id", "displacement_fields_id"),
    }


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

    with pytest.raises(ValueError, match="unknown default fields"):
        _validate_profile_questions(
            {
                "id": "broken",
                "steps": [
                    {
                        "id": "camera",
                        "section": "data_sources",
                        "kind": "data_sources/camera",
                        "defaults": {"unknown": "value"},
                    }
                ],
            },
            schema_catalog,
        )


def test_ui_profile_validation_reports_invalid_links() -> None:
    schema_catalog = build_schema_catalog()
    profile = {
        "id": "broken",
        "steps": [
            {"id": "source", "section": "data_sources", "kind": "data_sources/camera"},
            {"id": "data", "section": "data_sets", "kind": "data_sets/file"},
        ],
        "links": [{"from_step": "source", "to_step": "data", "to_field": "unknown"}],
    }

    with pytest.raises(ValueError, match="unknown target field"):
        _validate_profile_links(profile, schema_catalog)

    profile["links"][0]["to_field"] = "title"
    with pytest.raises(ValueError, match="target must be an array"):
        _validate_profile_links(profile, schema_catalog)
