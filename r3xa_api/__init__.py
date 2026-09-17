from . import core as _core
from .core import R3XAFile, R3XAItem, author, new_item, unit, data_set_file
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
from .validate import integrity_errors, validate, validate_integrity

from . import models

_TYPED_AVAILABLE = True
typed_available = True

__all__ = [
    "R3XAFile",
    "R3XAItem",
    "author",
    "new_item",
    "unit",
    "data_set_file",
    "from_model",
    "load_schema",
    "schema_version",
    "validate",
    "integrity_errors",
    "validate_integrity",
    "Registry",
    "RegistryItem",
    "models",
    "typed_available",
]

# Standalone item helpers, generated from the schema alongside R3XAFile
# guided helpers: `new_testing_machine_setting(...)` mirrors
# `document.add_testing_machine_setting(...)` but needs no document.
for _builder_name in _core.GUIDED_BUILDERS:
    globals()[_builder_name] = getattr(_core, _builder_name)
__all__ += sorted(_core.GUIDED_BUILDERS)

# Surface the generated classes on the package itself, so the object-first API
# is discoverable as `r3xa_api.CameraSource`, not only as `r3xa_api.models.CameraSource`.
_typed_names = [name for name in models.__all__ if name not in __all__]
globals().update({name: getattr(models, name) for name in _typed_names})
__all__ += _typed_names
