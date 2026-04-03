import importlib

from .core import R3XAFile, new_item, unit, data_set_file
from .registry import (
    load_item,
    save_item,
    load_item_path,
    save_item_path,
    validate_item,
    load_registry,
    merge_item,
    Registry,
    RegistryItem,
)
from .schema import load_schema, schema_version
from .typed import from_model
from .validate import validate

_TYPED_AVAILABLE = False
typed_available = False
models = None
try:
    models = importlib.import_module(".models", __name__)
except ModuleNotFoundError as exc:
    missing_root = (exc.name or "").split(".")[0]
    if missing_root not in {"pydantic", "pydantic_core"} and "pydantic" not in str(exc):
        raise
else:
    _TYPED_AVAILABLE = True
    typed_available = True

__all__ = [
    "R3XAFile",
    "new_item",
    "unit",
    "data_set_file",
    "from_model",
    "load_schema",
    "schema_version",
    "validate",
    "Registry",
    "RegistryItem",
    "models",
    "typed_available",
]
