import json
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from r3xa_api.schema import load_schema, schema_version
from r3xa_api.validate import validate


def test_load_schema_returns_equal_but_distinct_objects() -> None:
    first = load_schema()
    second = load_schema()

    assert first == second
    assert first is not second


def test_load_schema_cached_content_is_not_mutated_by_callers() -> None:
    expected_version = schema_version()

    payload = load_schema()
    payload["properties"]["version"]["const"] = "mutated-version"

    reloaded = load_schema()
    assert reloaded["properties"]["version"]["const"] == expected_version


def test_schema_version_returns_none_when_external_schema_has_no_const(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        json.dumps({"properties": {"version": {"type": "string"}}}),
        encoding="utf-8",
    )

    assert schema_version(str(schema_path)) is None


def test_required_document_metadata_cannot_be_empty() -> None:
    schema = load_schema()
    for field in ("title", "description"):
        assert schema["properties"][field]["minLength"] == 1
    assert schema["properties"]["authors"]["items"]["minLength"] == 1

    with pytest.raises(ValidationError):
        validate(
            {
                "title": "",
                "description": "",
                "authors": [""],
                "date": "2026-09-05",
                "version": schema_version(),
                "settings": [],
                "data_sources": [],
                "data_sets": [],
            }
        )


def test_validation_formats_non_reference_union_errors() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "oneOf": [{"type": "integer"}, {"type": "string"}],
            }
        },
        "required": ["value"],
    }

    with pytest.raises(ValidationError, match="not valid under any"):
        validate({"value": []}, schema)
