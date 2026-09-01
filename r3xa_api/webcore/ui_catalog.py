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
        defaults = step.get("defaults", {})
        if not isinstance(defaults, dict):
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} step {step_id} defaults must be an object"
            )
        protected_defaults = {"id", "kind"}.intersection(defaults)
        if protected_defaults:
            names = ", ".join(sorted(protected_defaults))
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} step {step_id} cannot default: {names}"
            )
        unknown_defaults = set(defaults) - set(properties)
        if unknown_defaults:
            names = ", ".join(sorted(unknown_defaults))
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} step {step_id} references unknown default fields: {names}"
            )
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


def _validate_profile_links(
    profile: Dict[str, Any], schema_catalog: Dict[str, Any]
) -> None:
    links = profile.get("links", [])
    if not isinstance(links, list):
        raise ValueError(f"Profile {profile.get('id', '<unknown>')} links must be a list")
    steps = {
        step["id"]: step
        for step in profile.get("steps", [])
        if isinstance(step, dict) and isinstance(step.get("id"), str)
    }
    for link in links:
        if not isinstance(link, dict):
            raise ValueError(f"Profile {profile.get('id', '<unknown>')} links must contain objects")
        from_step = steps.get(link.get("from_step"))
        to_step = steps.get(link.get("to_step"))
        if from_step is None or to_step is None:
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} link references an unknown step"
            )
        if not isinstance(from_step.get("kind"), str) or not isinstance(to_step.get("kind"), str):
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} links require kind-specific steps"
            )
        section_catalog = schema_catalog["sections"].get(to_step.get("section"), {})
        kind_catalog = section_catalog.get("kinds", {}).get(to_step["kind"], {})
        field = link.get("to_field")
        if not isinstance(field, str):
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} link references unknown target field: {field}"
            )
        field_meta = kind_catalog.get("properties", {}).get(field)
        if field_meta is None:
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} link references unknown target field: {field}"
            )
        to_many = link.get("to_many", True)
        if not isinstance(to_many, bool):
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} link to {field} must define a boolean to_many"
            )
        if to_many and field_meta.get("type") != "array":
            raise ValueError(
                f"Profile {profile.get('id', '<unknown>')} link target must be an array: {field}"
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
            _validate_profile_links(profile, schema_catalog)
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
