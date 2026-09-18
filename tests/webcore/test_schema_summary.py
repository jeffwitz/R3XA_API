from copy import deepcopy

import pytest

from r3xa_api.webcore import build_schema_catalog, build_schema_summary, build_ui_catalog
from r3xa_api.webcore._graph_core import build_graph_model
from r3xa_api.webcore.ui_catalog import (
    _validate_messages,
    _validate_profile_links,
    _validate_profile_questions,
    _validate_registry_examples,
)
from r3xa_api.validate import validate


def _prefilled_profile_document(profile: dict) -> dict:
    payload = {
        "version": build_schema_catalog()["schema_version"],
        "settings": [],
        "data_sources": [],
        "data_sets": [],
    }
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
        target = items[link["to_step"]]
        field = link["to_field"]
        current = target.get(field, [])
        if not isinstance(current, list):
            current = [current]
        current.append(items[link["from_step"]]["id"])
        target[field] = list(dict.fromkeys(current))
    return payload


def test_schema_summary_sections() -> None:
    summary = build_schema_summary()
    assert summary["schema_version"] == "2026.9.18"
    assert set(summary["sections"].keys()) == {
        "header",
        "settings",
        "data_sources",
        "data_sets",
    }


def test_schema_catalog_contains_all_resolved_kinds() -> None:
    catalog = build_schema_catalog()

    assert catalog["schema_version"] == "2026.9.18"
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
    assert image_set["properties"]["parent_data_sources"]["items"]["ref"] == "#/$defs/types/data_source_id"
    assert camera["properties"]["image_size"]["items"]["properties"]["kind"]["const"] == "unit"
    assert camera["properties"]["image_size"]["items"]["ref"] == "#/$defs/types/unit"
    data_set_file = catalog["sections"]["data_sets"]["kinds"]["data_sets/file"]["properties"]
    rows = data_set_file["timestamps"]["properties"]["rows"]
    assert rows["prefixItems"][0]["type"] == "integer"
    assert rows["prefixItems"][1]["type"] == ["integer", "null"]


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

    assert catalog["schema_version"] == "2026.9.18"
    assert catalog["default"]["fields"]["kind"]["level"] == "expert"
    assert catalog["messages"]["languages"]["fr"]["editor.title"] == "Éditeur R3XA"
    assert set(catalog["profiles"]) == {
        "generic",
        "mechanical_test",
        "dic_2d",
        "camera_images",
        "tabular_file",
        "torsion_test",
        "fatigue_with_overload",
        "tomography",
        "in_situ_tensile",
        "stereo_dic",
    }
    assert catalog["profiles"]["dic_2d"]["steps"][-2]["kind"] == "data_sources/dic_measurement"
    assert catalog["profiles"]["dic_2d"]["steps"][0]["questions"][0]["field"] == "title"
    assert catalog["profiles"]["dic_2d"]["steps"][0]["defaults"]["title"] == "Tensile test with 2D DIC"
    assert catalog["profiles"]["dic_2d"]["steps"][-1]["kind"] == "data_sets/file"
    assert catalog["profiles"]["dic_2d"]["steps"][-1]["defaults"]["values"]["filename"] == "displacement_fields.h5"
    assert catalog["registry_examples"]["completion_strategy"] == "schema-driven"
    assert len(catalog["registry_examples"]["kinds"]) == 18
    assert {
        (link["from_step"], link["to_step"], link["to_field"])
        for link in catalog["profiles"]["dic_2d"]["links"]
    } == {
        ("machine", "machine_data", "parent_data_sources"),
        ("camera", "images", "parent_data_sources"),
        ("images", "dic", "input_data_sets"),
        ("dic", "displacement_fields", "parent_data_sources"),
    }


def test_registry_examples_reject_unknown_fields() -> None:
    catalog = build_ui_catalog()
    examples = deepcopy(catalog["registry_examples"])
    examples["field_examples"]["not_a_schema_field"] = "invalid"
    with pytest.raises(ValueError, match="unknown fields"):
        _validate_registry_examples(examples, build_schema_catalog())


def test_ui_messages_require_complete_string_translations() -> None:
    catalog = build_ui_catalog()
    _validate_messages(catalog["messages"])

    with pytest.raises(ValueError, match="match default-language keys"):
        _validate_messages(
            {
                "default_language": "en",
                "languages": {"en": {"title": "Title"}, "fr": {}},
            }
        )


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
    assert machine_data["parent_data_sources"] == ["machine_id"]
    assert images["parent_data_sources"] == ["camera_id"]
    assert dic["input_data_sets"] == ["images_id"]
    assert displacement_fields["parent_data_sources"] == ["dic_id"]
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


@pytest.mark.parametrize(
    ("profile_id", "expected_edges"),
    [
        (
            "mechanical_test",
            {("machine_id", "machine_data_id")},
        ),
        (
            "camera_images",
            {("camera_id", "images_id")},
        ),
        (
            "tabular_file",
            {("measurement_id", "measurement_file_id")},
        ),
        (
            "torsion_test",
            {
                ("torque_source_id", "rotation_torque_id"),
                ("angle_source_id", "rotation_angle_id"),
                ("angle_source_id", "torsion_angle_id"),
                ("torque_source_id", "torsion_torque_id"),
            },
        ),
        (
            "fatigue_with_overload",
            {
                ("camera_id", "images_id"),
                ("images_id", "fe_dic_id"),
                ("load_sensor_id", "load_data_id"),
                ("sif_extractor_id", "sif_data_id"),
                ("fe_dic_id", "displacement_id"),
            },
        ),
        (
            "tomography",
            {
                ("tomograph_id", "projections_id"),
                ("projections_id", "reconstruction_id"),
                ("reconstruction_id", "volume_id"),
                ("volume_id", "dvc_id"),
                ("dvc_id", "dvc_displacement_id"),
            },
        ),
        (
            "in_situ_tensile",
            {
                ("machine_id", "machine_data_id"),
                ("camera_id", "images_id"),
                ("images_id", "dic_id"),
                ("dic_id", "displacement_fields_id"),
            },
        ),
        (
            "stereo_dic",
            {
                ("stereo_rig_id", "camera_left_id"),
                ("stereo_rig_id", "camera_right_id"),
                ("camera_left_id", "left_images_id"),
                ("camera_right_id", "right_images_id"),
                ("left_images_id", "stereo_dic_source_id"),
                ("right_images_id", "stereo_dic_source_id"),
                ("stereo_dic_source_id", "displacement_fields_id"),
            },
        ),
    ],
)
def test_prefilled_profiles_build_valid_dependency_graph(
    profile_id: str, expected_edges: set[tuple[str, str]]
) -> None:
    profile = build_ui_catalog()["profiles"][profile_id]
    payload = _prefilled_profile_document(profile)

    validate(payload)
    assert {
        (edge.src, edge.dst) for edge in build_graph_model(payload).edge_records
    } == expected_edges
    for step in profile["steps"]:
        for question in step.get("questions", []):
            assert question["field"] in step.get("defaults", {})


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
