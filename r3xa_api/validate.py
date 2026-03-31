from typing import Any, Dict, Optional
import jsonschema
from .schema import load_schema


def _make_context_message(error: jsonschema.ValidationError, context_error: jsonschema.ValidationError) -> str:
    """Build a readable message for a nested anyOf/oneOf validation branch."""

    i = list(context_error.relative_schema_path)[0]
    return context_error.message + " of " + error.validator_value[i]["$ref"].replace("#/$defs/", "")


def validate(instance: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> None:
    """Validate an R3XA payload and raise ValidationError with aggregated details."""

    schema = schema or load_schema()
    validator = jsonschema.validators.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=jsonschema.exceptions.relevance)

    if not errors:
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
