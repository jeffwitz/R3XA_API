# R3XA_API — API Reference

This page documents the public API intended for library users.

## Core class

### `R3XAFile`
Create and manage a full R3XA document.

**Constructor**
```python
R3XAFile(version: str | None = None, **header)
```
- `version`: optional schema version, defaults to the embedded schema.
- `header`: any header fields (`title`, `description`, `authors`, `date`, `repository`, ...).

**Methods**
```python
set_header(**fields) -> R3XAFile
```
Update header fields.

```python
add_setting(kind: str, **fields) -> dict
add_data_source(kind: str, **fields) -> dict
add_data_set(kind: str, **fields) -> dict
```
Low‑level methods for any schema kind.

```python
add_generic_setting(title: str, description: str, **extra) -> dict
add_specimen_setting(title: str, description: str, sizes=None, patterning_technique=None, **extra) -> dict
```
Guided helpers for settings.

```python
add_camera_source(
    title: str,
    description: str,
    output_components: int,
    output_dimension: str,
    output_units: Sequence[dict],
    manufacturer: str,
    model: str,
    image_size: Sequence[dict],
    **extra,
) -> dict
```
Guided helper for camera data sources.

```python
add_image_set_list(
    title: str,
    description: str,
    path: str,
    file_type: str,
    data_sources: Sequence[str],
    time_reference: float,
    timestamps: Sequence[float],
    data: Sequence[str],
    **extra,
) -> dict
```
Guided helper for list‑based datasets.

```python
add_image_set_file(
    title: str,
    description: str,
    data_sources: Sequence[str],
    time_reference: float,
    timestamps: str | dict,
    data: str | dict,
    **extra,
) -> dict
```
Guided helper for file‑based datasets.

```python
to_dict() -> dict
validate() -> None
save(path: str, indent: int = 4) -> None
```
Serialize, validate, and write to disk.

## Helper functions

### `unit(...)`
```python
unit(title: str, value: float, unit: str, scale: float = 1.0, **extra) -> dict
```
Build a schema‑compliant unit object.

### `data_set_file(...)`
```python
data_set_file(filename: str, delimiter: str | None = None, data_range: list[str] | None = None, **extra) -> dict
```
Build a schema‑compliant data_set_file object.

## Registry utilities

### `load_item(path) -> dict`
Load a registry JSON item from disk.

### `Registry`
Helper class that encapsulates the registry root and provides `get()` and `get_validated()` methods.

```python
from r3xa_api import Registry

registry = Registry("registry")
camera = registry.get_validated("data_sources/camera/avt_dolphin_f145b")
```

### `validate_item(item, kind=None, schema=None) -> None`
Validate a single item against its schema definition (e.g. `data_sources/camera`).

### Advanced
`load_item_path(root, tree_path) -> dict`  
Internal/advanced helper to load a registry item by its tree path string, e.g. `settings/specimen/openhole_sample`.

### `load_registry(root) -> dict`
Load a full registry tree into memory.

### `merge_item(base, **overrides) -> dict`
Create a new item by overriding fields of a registry item.

## Schema utilities

### `load_schema(path: str | None = None) -> dict`
Load the embedded schema (or a custom path).

### `schema_version(path: str | None = None) -> str | None`
Extract the schema version.

### `validate(instance: dict, schema: dict | None = None) -> None`
Validate a JSON instance against the schema.
