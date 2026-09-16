"""Guard the vendored schema against drift from R3XA_SPEC.

``r3xa_api/resources/schema.json`` is a copy of the schema published by the
R3XA_SPEC repository. Nothing in the build regenerates it, so a divergence
would otherwise stay invisible until a document failed to validate somewhere
downstream.

This test compares the copy against a local R3XA_SPEC checkout when one is
reachable, and skips otherwise so a plain ``pytest`` run stays self-contained.
The ``schema-sync`` CI job supplies a fresh clone through ``R3XA_SPEC_PATH``
and fails if the schema is missing, so the check cannot be silently skipped on
the pipeline.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VENDORED_SCHEMA = ROOT / "r3xa_api" / "resources" / "schema.json"


def _spec_schema_path() -> Path | None:
    """Return the R3XA_SPEC ``schema.json`` if a checkout can be located.

    An explicit ``R3XA_SPEC_PATH`` is honoured strictly: a wrong path must fail
    loudly rather than fall back to a sibling checkout and report on the wrong
    tree.
    """

    override = os.environ.get("R3XA_SPEC_PATH")
    if override:
        schema = Path(override) / "schema.json"
        if not schema.is_file():
            raise AssertionError(
                f"R3XA_SPEC_PATH points at {override!r}, which has no schema.json."
            )
        return schema

    # Sibling checkout, the usual local layout.
    schema = ROOT.parent / "R3XA_SPEC" / "schema.json"
    return schema if schema.is_file() else None


def _version(schema_text: str) -> str | None:
    payload = json.loads(schema_text)
    return payload.get("properties", {}).get("version", {}).get("const")


def test_vendored_schema_matches_spec() -> None:
    spec_schema = _spec_schema_path()
    if spec_schema is None:
        pytest.skip(
            "No R3XA_SPEC checkout found. Set R3XA_SPEC_PATH to one, or rely on "
            "the schema-sync CI job."
        )

    vendored_text = VENDORED_SCHEMA.read_text(encoding="utf-8")
    spec_text = spec_schema.read_text(encoding="utf-8")

    if vendored_text != spec_text:
        raise AssertionError(
            f"{VENDORED_SCHEMA} has drifted from {spec_schema}.\n"
            f"  vendored version: {_version(vendored_text)}\n"
            f"  R3XA_SPEC version: {_version(spec_text)}\n"
            "The vendored file is a copy, never an edit target: refresh it from "
            "R3XA_SPEC, then regenerate the derived artefacts with "
            "`python scripts/dev.py generate-models` and "
            "`python scripts/dev.py generate-spec`."
        )
