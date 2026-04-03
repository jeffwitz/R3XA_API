# API Stability Policy

This repository follows a pragmatic stability policy for the `1.x` series.

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
- `load_item_path(...)`
- `save_item_path(...)`
- `load_registry(...)`
- `merge_item(...)`

remain importable explicitly during the `1.x` series, but are no longer part of the recommended top-level surface.

They will not be removed before `2.0`.

## Registry naming

For new code:
- prefer `Registry.load(...)` / `Registry.load_validated(...)` for file-backed registry access
- use `Registry.get_item(...)` when you want a `RegistryItem` wrapper

Compatibility aliases:
- `Registry.get(...)`
- `Registry.get_validated(...)`

remain available during `1.x`.

## Guided helpers

Schema-driven helpers such as:
- `add_camera_source(...)`
- `add_specimen_setting(...)`
- `add_generic_data_set(...)`

are part of the public contract.

For `1.x`, the project guarantees:
- helper existence for schema-supported kinds
- required fields derived from the schema
- stable naming pattern: `add_<kind>_setting/source/data_set`

The internal implementation may change in a future major version.
