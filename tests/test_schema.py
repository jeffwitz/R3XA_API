import json
from pathlib import Path

from r3xa_api.schema import load_schema, schema_version


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
