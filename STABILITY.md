# API Stability Policy

This repository follows a pragmatic stability policy for the `2.x` series.

The `2.x` line is a breaking line relative to the stable `1.x` releases. In
particular, documents and calls using the pre-`2.0` schema field names are not
silently converted. Users should migrate them explicitly before adoption.

## Public SDK

The documented API in `docs/api.md` is the public contract for library users.

This includes:
- `R3XAFile`
- `Registry`
- `RegistryItem`
- `new_item(...)`
- `unit(...)`
- `data_set_file(...)`
- `validate(...)`
- schema-driven guided helpers on `R3XAFile`

## Compatibility helpers

Lower-level helpers such as:
- `load_item(...)`
- `save_item(...)`
- `validate_item(...)`
- `load_item_path(...)`
- `save_item_path(...)`
- `load_registry(...)`
- `merge_item(...)`

remain importable explicitly during the `2.x` series where implemented, but are
not part of the recommended top-level surface.

Their continued availability does not imply compatibility with pre-`2.0` schema
field names or call signatures.

## Registry naming

For new code:
- prefer `Registry.load(...)` / `Registry.load_validated(...)` for file-backed registry access
- use `Registry.get_item(...)` when you want a `RegistryItem` wrapper

Compatibility aliases:
- `Registry.get(...)`
- `Registry.get_validated(...)`

remain available during `2.x` where implemented.

## Guided helpers

Schema-driven helpers such as:
- `add_camera_source(...)`
- `add_specimen_setting(...)`
- `add_generic_data_set(...)`

are part of the public contract.

For `2.x`, the project guarantees:
- helper existence for schema-supported kinds
- required fields derived from the schema
- stable naming pattern: `add_<kind>_setting/source/data_set`

The internal implementation may change in a future major version.

## Object-first models

Schema-generated Pydantic models are part of the standard `r3xa_api` installation
and are available through `r3xa_api.models` or directly from `r3xa_api`. The
stable public model names and common helpers are part of the object-first API:

- `to_dict()` / `to_json()`
- `from_dict()` / `load()`
- `validate()` / `save()`
- `required_fields()` / `optional_fields()`
- `summary()` / `print()`

Document models additionally expose `add_setting()`, `add_data_source()`,
`add_data_set()`, `find()`, `link_output()`, `link_input()`, and
`validate_integrity()`.

References are objects while a model is used in memory and become IDs at the
JSON boundary. `to_dict()` is the explicit serialization boundary. The
generated file must not be edited manually; regenerate it from `R3XA_SPEC` after
schema changes while these stable names and behaviors remain the public
compatibility surface.
