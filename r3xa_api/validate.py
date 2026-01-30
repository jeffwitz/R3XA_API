from typing import Any, Dict, Optional
import jsonschema
from .schema import load_schema


def _make_context_message(error: jsonschema.ValidationError, context_error: jsonschema.ValidationError) -> str:
    i = list(context_error.relative_schema_path)[0]
    return context_error.message + " of " + error.validator_value[i]["$ref"].replace("#/$defs/", "")


def validate(instance: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> None:
    schema = schema or load_schema()
    validator = jsonschema.validators.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=jsonschema.exceptions.relevance)

    if not errors:
        return

    error_messages = []
    for error in errors:
        p = f"{list(error.path)[0]} validation error" if error.path.count(0) else "root validation error"
        error_message = [f"{p}: {error.message}"] + [_make_context_message(error, e) for e in error.context]
        error_messages.append("\n\t- ".join(error_message))

    msg = "\n".join([f"- {e}" for e in error_messages])
    raise jsonschema.exceptions.ValidationError(msg)
