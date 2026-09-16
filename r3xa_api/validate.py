from datetime import date
from typing import Any, Dict, Mapping, Optional
import jsonschema
from .schema import load_schema


def integrity_errors(instance: Mapping[str, Any]) -> list[str]:
    """Return semantic errors for a complete R3XA document."""

    errors: list[str] = []
    identifiers: dict[str, str] = {}
    source_ids: set[str] = set()
    data_set_ids: set[str] = set()

    sections = {
        section: instance.get(section, [])
        for section in ("settings", "data_sources", "data_sets")
    }
    for section, items in sections.items():
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if not isinstance(item, Mapping):
                continue
            item_path = f"{section}/{index}"
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                errors.append(f"{item_path}/id: item id must be a non-empty string")
                continue
            previous = identifiers.get(item_id)
            if previous is not None:
                errors.append(f"{item_path}/id: duplicate id {item_id!r}; already used at {previous}")
            else:
                identifiers[item_id] = item_path
            if section == "data_sources":
                source_ids.add(item_id)
            elif section == "data_sets":
                data_set_ids.add(item_id)

    for section, items in sections.items():
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if not isinstance(item, Mapping):
                continue
            item_path = f"{section}/{index}"
            if section == "data_sets":
                references = item.get("parent_data_sources", [])
                for reference_index, reference in enumerate(references if isinstance(references, list) else []):
                    if not isinstance(reference, str) or reference not in source_ids:
                        errors.append(
                            f"{item_path}/parent_data_sources/{reference_index}: "
                            f"unknown data source reference {reference!r}"
                        )
            if section == "data_sources":
                references = item.get("input_data_sets", [])
                for reference_index, reference in enumerate(references if isinstance(references, list) else []):
                    if not isinstance(reference, str) or reference not in data_set_ids:
                        errors.append(
                            f"{item_path}/input_data_sets/{reference_index}: "
                            f"unknown data set reference {reference!r}"
                        )
            if section == "settings":
                references = item.get("attached_data_sources", [])
                for reference_index, reference in enumerate(references if isinstance(references, list) else []):
                    if not isinstance(reference, str) or reference not in source_ids:
                        errors.append(
                            f"{item_path}/attached_data_sources/{reference_index}: "
                            f"unknown data source reference {reference!r}"
                        )
    authors = instance.get("authors")
    author_orcids = instance.get("author_orcids")
    if isinstance(authors, list) and isinstance(author_orcids, list) and len(authors) != len(author_orcids):
        errors.append("author_orcids: must have one entry for each author")

    experiment_date = instance.get("date")
    if isinstance(experiment_date, str):
        try:
            date.fromisoformat(experiment_date)
        except ValueError:
            errors.append("date: must be a real calendar date in YYYY-MM-DD format")

    return errors


def validate_integrity(instance: Mapping[str, Any]) -> None:
    """Validate semantic references and consistency in a complete document."""

    errors = integrity_errors(instance)
    if errors:
        raise jsonschema.exceptions.ValidationError("\n".join(f"- {error}" for error in errors))


def _make_context_message(error: jsonschema.ValidationError, context_error: jsonschema.ValidationError) -> str:
    """Build a readable message for a nested anyOf/oneOf validation branch."""

    path = list(context_error.relative_schema_path)
    branch = error.validator_value[path[0]] if path and isinstance(error.validator_value, list) else None
    reference = branch.get("$ref") if isinstance(branch, dict) else None
    if isinstance(reference, str):
        return context_error.message + " of " + reference.replace("#/$defs/", "")
    return context_error.message


def validate(instance: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> None:
    """Validate an R3XA payload and raise ValidationError with aggregated details."""

    schema = schema or load_schema()
    validator = jsonschema.validators.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=jsonschema.exceptions.relevance)

    if not errors:
        validate_integrity(instance)
        return

    error_messages = []
    for error in errors:
        if error.path:
            p = f"{'/'.join(map(str, error.path))} validation error"
        else:
            p = "root validation error"
        error_message = [f"{p}: {error.message}"] + [_make_context_message(error, e) for e in error.context]
        error_messages.append("\n\t- ".join(error_message))

    msg = "\n".join([f"- {e}" for e in error_messages])
    raise jsonschema.exceptions.ValidationError(msg)
