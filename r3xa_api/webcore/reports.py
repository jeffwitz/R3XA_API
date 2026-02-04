from typing import Any, Dict, List, Optional

import jsonschema

from ..schema import load_schema


def _path_to_string(path: Any) -> str:
    return "/".join(map(str, path))


def _schema_path_to_string(schema_path: Any) -> str:
    return "#/" + "/".join(map(str, schema_path))


def build_validation_report(
    instance: Dict[str, Any], schema: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    schema = schema or load_schema()
    validator = jsonschema.validators.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=jsonschema.exceptions.relevance)

    if not errors:
        return {"valid": True, "errors": []}

    report_errors: List[Dict[str, Any]] = []
    for error in errors:
        report_errors.append(
            {
                "path": _path_to_string(error.path),
                "message": error.message,
                "validator": error.validator,
                "schema_path": _schema_path_to_string(error.schema_path),
            }
        )

    return {"valid": False, "errors": report_errors}
