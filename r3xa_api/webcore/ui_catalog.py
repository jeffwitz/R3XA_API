from __future__ import annotations

import json
from importlib import resources
from typing import Any, Dict, Optional

from .schema_catalog import build_schema_catalog


def _load_json_resource(path: str) -> Dict[str, Any]:
    resource = resources.files("r3xa_api.resources").joinpath(path)
    with resource.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"UI resource must contain an object: {path}")
    return value


def _profile_kinds(schema_catalog: Dict[str, Any]) -> set[str]:
    kinds: set[str] = set()
    for section in ("settings", "data_sources", "data_sets"):
        kinds.update(schema_catalog["sections"][section].get("kinds", {}))
    return kinds


def _profile_references(profile: Dict[str, Any]) -> set[str]:
    recommended = profile.get("recommended_kinds", [])
    if not isinstance(recommended, list) or not all(
        isinstance(kind, str) for kind in recommended
    ):
        raise ValueError(
            f"Profile {profile.get('id', '<unknown>')} recommended_kinds must be a list of strings"
        )
    references = set(recommended)
    steps = profile.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError(f"Profile {profile.get('id', '<unknown>')} steps must be a list")
    for step in steps:
        if isinstance(step, dict) and isinstance(step.get("kind"), str):
            references.add(step["kind"])
    return references


def _validate_profile_questions(
    profile: Dict[str, Any], schema_catalog: Dict[str, Any]
) -> None:
    for step in profile.get("steps", []):
        if not isinstance(step, dict):
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} steps must contain objects"
            )
        step_id = step.get("id")
        if not isinstance(step_id, str) or not step_id:
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} steps must define non-empty ids"
            )
        section = step.get("section")
        if section == "header":
            properties = schema_catalog["sections"]["header"].get("properties", {})
        elif isinstance(section, str) and isinstance(step.get("kind"), str):
            section_catalog = schema_catalog["sections"].get(section)
            if section_catalog is None:
                raise ValueError(f"Profile {profile.get('id', '<unknown>')} references unknown section: {section}")
            kind = step["kind"]
            kind_catalog = section_catalog.get("kinds", {}).get(kind)
            if kind_catalog is None:
                raise ValueError(f"Profile {profile.get('id', '<unknown>')} references unknown kind: {kind}")
            properties = kind_catalog.get("properties", {})
        elif isinstance(section, str) and section in schema_catalog["sections"]:
            properties = {}
        else:
            raise ValueError(f"Profile {profile.get('id', '<unknown>')} references unknown section: {section}")
        questions = step.get("questions", [])
        if not isinstance(questions, list):
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} step {step_id} questions must be a list"
            )
        for question in questions:
            if not isinstance(question, dict):
                raise ValueError(
                    f"Profile {profile.get('id', '<unknown>')} step {step_id} questions must contain objects"
                )
            field = question.get("field")
            if not isinstance(field, str) or field not in properties:
                raise ValueError(
                    f"Profile {profile.get('id', '<unknown>')} references unknown field: {field}"
                )


def build_ui_catalog(
    schema_catalog: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Load presentation rules and profiles without changing schema validity."""

    schema_catalog = schema_catalog or build_schema_catalog()
    known_kinds = _profile_kinds(schema_catalog)
    profiles: Dict[str, Dict[str, Any]] = {}
    profile_dir = resources.files("r3xa_api.resources").joinpath("ui/profiles")
    for entry in profile_dir.iterdir():
        if entry.name.endswith(".json"):
            profile = _load_json_resource(f"ui/profiles/{entry.name}")
            unknown = _profile_references(profile) - known_kinds
            if unknown:
                names = ", ".join(sorted(unknown))
                raise ValueError(f"Profile {entry.name} references unknown kinds: {names}")
            _validate_profile_questions(profile, schema_catalog)
            profile_id = profile.get("id")
            if not isinstance(profile_id, str) or not profile_id:
                raise ValueError(f"Profile {entry.name} must define a non-empty id")
            profiles[profile_id] = profile

    return {
        "version": 1,
        "schema_version": schema_catalog.get("schema_version"),
        "default": _load_json_resource("ui/default.json"),
        "profiles": profiles,
    }
