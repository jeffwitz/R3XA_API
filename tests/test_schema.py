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
    assert schema["$defs"]["types"]["author"]["properties"]["name"]["minLength"] == 1

    with pytest.raises(ValidationError):
        validate(
            {
                "title": "",
                "description": "",
                "authors": [{"name": ""}],
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


def test_validate_rejects_broken_document_references() -> None:
    payload = {
        "title": "Integrity test",
        "description": "Test semantic document validation",
        "authors": [{"name": "Tester"}],
        "date": "2026-09-05",
        "version": schema_version(),
        "settings": [],
        "data_sources": [],
        "data_sets": [
            {
                "id": "dataset-1",
                "kind": "data_sets/list",
                "title": "Images",
                "parent_data_sources": ["missing-source"],
                "timestamps": [0.0],
                "values": ["image.tif"],
            }
        ],
    }

    with pytest.raises(ValidationError, match="unknown data source reference"):
        validate(payload)


def test_validate_rejects_an_impossible_calendar_date() -> None:
    payload = {
        "title": "Integrity test",
        "description": "Test semantic document validation",
        "authors": [{"name": "Tester"}, {"name": "Another tester"}],
        "date": "2026-02-31",
        "version": schema_version(),
        "settings": [],
        "data_sources": [],
        "data_sets": [],
    }

    with pytest.raises(ValidationError) as error:
        validate(payload)
    assert "real calendar date" in str(error.value)


def test_author_orcids_is_gone_and_orcids_belong_to_their_author() -> None:
    base = {
        "title": "Authorship",
        "description": "ORCIDs are carried by the author object",
        "authors": [
            {"name": "Tester", "orcid": "https://orcid.org/0000-0002-1825-0097"},
            {"name": "Another tester", "affiliation": "Univ. Lille"},
        ],
        "date": "2026-02-28",
        "version": schema_version(),
        "settings": [],
        "data_sources": [],
        "data_sets": [],
    }
    validate(base)

    # The parallel array is no longer part of the document at all, so the
    # mismatch it allowed cannot be expressed: the schema rejects it outright
    # rather than relying on a hand-written length check.
    with pytest.raises(ValidationError, match="author_orcids"):
        validate({**base, "author_orcids": [None]})

    with pytest.raises(ValidationError):
        validate({**base, "authors": ["Tester", "Another tester"]})
