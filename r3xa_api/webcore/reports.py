from typing import Any, Dict, List, Optional

import jsonschema

from ..schema import load_schema
from ..validate import integrity_errors


def _path_to_string(path: Any) -> str:
    """Serialize a jsonschema error path to slash-separated notation."""

    return "/".join(map(str, path))


def _schema_path_to_string(schema_path: Any) -> str:
    """Serialize a schema path to `#/...` notation."""

    return "#/" + "/".join(map(str, schema_path))


def _friendly_message(error: jsonschema.ValidationError) -> str:
    """Turn common schema failures into messages suitable for guided UI users."""

    validator = error.validator
    if validator == "required":
        missing = error.message.split("'")[1] if "'" in error.message else "information"
        return f"Add the required field '{missing}'."
    if validator == "type":
        return f"Enter a value of type '{error.validator_value}'."
    if validator == "enum":
        choices = ", ".join(map(str, error.validator_value))
        return f"Choose one of: {choices}."
    if validator == "const":
        return f"Use the required value '{error.validator_value}'."
    if validator == "pattern":
        return "Use the expected text format."
    if validator == "minItems":
        return f"Add at least {error.validator_value} item(s)."
    if validator == "maxItems":
        return f"Use no more than {error.validator_value} item(s)."
    if validator in {"minimum", "exclusiveMinimum"}:
        return f"Enter a value greater than or equal to {error.validator_value}."
    if validator in {"maximum", "exclusiveMaximum"}:
        return f"Enter a value less than or equal to {error.validator_value}."
    return error.message


def build_validation_report(
    instance: Dict[str, Any], schema: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Return a stable validation report for UI/API consumption."""

    schema = schema or load_schema()
    validator = jsonschema.validators.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=jsonschema.exceptions.relevance)

    report_errors: List[Dict[str, Any]] = []
    for error in errors:
        report_errors.append(
            {
                "path": _path_to_string(error.path),
                "message": error.message,
                "user_message": _friendly_message(error),
                "validator": error.validator,
                "schema_path": _schema_path_to_string(error.schema_path),
            }
        )

    if not errors:
        for message in integrity_errors(instance):
            path, separator, detail = message.partition(": ")
            report_errors.append(
                {
                    "path": path if separator else "",
                    "message": detail if separator else message,
                    "user_message": detail if separator else message,
                    "validator": "integrity",
                    "schema_path": "#/integrity",
                }
            )

    return {"valid": not report_errors, "errors": report_errors}
