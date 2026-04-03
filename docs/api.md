# R3XA_API — API Reference

This page documents the public API intended for library users.

## Recommended imports
For most user code, keep imports at the SDK level:

```python
from r3xa_api import R3XAFile, Registry, RegistryItem, new_item, unit, validate
```

Use the advanced compatibility helpers only when you really need the lower-level registry functions:

```python
from r3xa_api import load_item_path, save_item_path, validate_item, merge_item
```

These compatibility helpers remain importable explicitly, but they are intentionally excluded from
`r3xa_api.__all__` to keep the recommended SDK surface small.

Web-only helpers are intentionally exposed from `r3xa_api.webcore`, not from the SDK top level:

```python
from r3xa_api.webcore import build_validation_report, build_schema_summary
```

## Stability policy
- Symbols documented on this page define the supported public SDK for the 1.x series.
- Compatibility helpers remain available throughout the 1.x series and will not be removed before `2.0`.
- Guided helpers (`add_<kind>_setting/source/data_set`) are part of the public contract and are tested against the schema-derived required fields.
- Undocumented module internals may evolve more freely.

See `STABILITY.md` at the repository root for the concise policy.

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
R3XAFile.from_dict(payload: dict) -> R3XAFile
R3XAFile.load(path: str | Path) -> R3XAFile
R3XAFile.loads(text: str) -> R3XAFile
```
Create a builder from an existing payload, JSON file, or JSON string.

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
add_<kind>_setting(...)
add_<kind>_source(...)
add_<kind>_data_set(...)
```
Schema‑driven guided helpers exist for every supported kind. They expose the schema `required`
fields as explicit parameters and accept optional schema fields through `**extra`.

Examples:

```python
add_generic_setting(title, description, **extra) -> dict
add_specimen_setting(title, description, sizes, **extra) -> dict
add_testing_machine_setting(title, description, type, **extra) -> dict
add_camera_source(title, output_components, output_dimension, output_units, image_size, **extra) -> dict
add_load_cell_source(output_components, output_dimension, output_units, capacity, **extra) -> dict
add_generic_data_set(title, description, data_sources, file_type, path, **extra) -> dict
add_list_data_set(title, description, file_type, data_sources, time_reference, timestamps, data, **extra) -> dict
add_file_data_set(title, description, data_sources, time_reference, timestamps, data, **extra) -> dict
```

Complete guided helper inventory for the current schema:

- Settings
  - `add_generic_setting(...)`
  - `add_specimen_setting(...)`
  - `add_stereorig_setting(...)`
  - `add_testing_machine_setting(...)`
- Data sources
  - `add_camera_source(...)`
  - `add_dic_measurement_source(...)`
  - `add_generic_source(...)`
  - `add_identification_source(...)`
  - `add_infrared_source(...)`
  - `add_load_cell_source(...)`
  - `add_mechanical_analysis_source(...)`
  - `add_point_temperature_source(...)`
  - `add_strain_computation_source(...)`
  - `add_strain_gauge_source(...)`
  - `add_tomograph_source(...)`
- Data sets
  - `add_file_data_set(...)`
  - `add_generic_data_set(...)`
  - `add_list_data_set(...)`
- Legacy aliases
  - `add_image_set_list(...)`
  - `add_image_set_file(...)`

Backward-compatible aliases remain available:

```python
add_image_set_list(...) == add_list_data_set(...)
add_image_set_file(...) == add_file_data_set(...)
```

```python
to_dict() -> dict
dump(indent: int = 4) -> str
validate() -> None
save(path: str | Path, indent: int = 4, validate: bool = True) -> Path
```
Serialize, validate, and write to disk.

Typical edit cycle:

```python
from r3xa_api import R3XAFile

r3xa = R3XAFile.load("experiment.json")
r3xa.set_header(title="Updated title")
r3xa.save("experiment_updated.json")
```

## Helper functions

### `unit(...)`
```python
unit(title: str | None = None, value: float | None = None, unit: str | None = None, scale: float | None = 1.0, **extra) -> dict
```
Build a schema‑compliant unit object. Only `unit` is required by the schema; `title`,
`value`, and `scale` are optional metadata.

### `data_set_file(...)`
```python
data_set_file(filename: str, delimiter: str | None = None, data_range: str | None = None, **extra) -> dict
```
Build a schema‑compliant data_set_file object.

## Registry utilities

### `load_item(path) -> dict`
Load a registry JSON item from disk.

### `save_item(path, item, validate=True, kind=None) -> Path`
Validate and save a single registry item JSON to disk. `item` can be a plain `dict`
or a `RegistryItem`.

These helpers remain available for advanced use cases and backward compatibility. For day-to-day usage,
prefer `Registry.get_item(...)`, `RegistryItem.merge(...)`, and `RegistryItem.save(...)`.

### `Registry`
Helper class that encapsulates the registry root and provides loading, validation, discovery, merge, wrapping, and save methods.

```python
from r3xa_api import Registry, new_item, unit

registry = Registry("registry")
camera = registry.get_item("data_sources/camera/avt_dolphin_f145b")

new_camera = new_item(
    "data_sources/camera",
    title="Example generated camera",
    description="Example registry camera generated with R3XA_API",
    output_components=1,
    output_dimension="surface",
    output_units=[unit(title="graylevel", value=1.0, unit="gl", scale=1.0)],
    manufacturer="Example manufacturer",
    model="Example model",
    image_size=[
        unit(title="width", value=2048, unit="px", scale=1.0),
        unit(title="height", value=1536, unit="px", scale=1.0),
    ],
)

registry.wrap(new_camera, tree_path="data_sources/camera/example_generated_camera").save()
```

Most useful instance methods:

```python
load(tree_path: str) -> dict
load_validated(tree_path: str, kind: str | None = None) -> dict
get_item(tree_path: str, validated: bool = True, kind: str | None = None) -> RegistryItem
wrap(item: Mapping[str, Any], tree_path: str | None = None) -> RegistryItem
list(section: str | None = None, kind: str | None = None) -> list[str]
iter_items(section: str | None = None, kind: str | None = None, validated: bool = False, wrapped: bool = False) -> Iterator[tuple[str, dict | RegistryItem]]
merge(tree_path: str, **overrides) -> RegistryItem
save(tree_path: str, item: dict | RegistryItem, validate: bool = True, kind: str | None = None) -> Path
```

Naming rule:
- prefer `load(...)` / `load_validated(...)` in new code because these methods read JSON files from the registry tree
- `get(...)` / `get_validated(...)` remain available as compatibility aliases

Typical registry workflow:

```python
from r3xa_api import Registry

registry = Registry("registry")

for tree_path in registry.list(kind="data_sources/camera"):
    print(tree_path)

camera = registry.get_item("data_sources/camera/avt_dolphin_f145b").merge(
    id="cam_exp01",
    description="Camera used in experiment 01",
)
camera.save("camera_exp01.json")
```

### `RegistryItem`
Dictionary-like wrapper returned by `Registry.get_item(...)`.

It keeps the current dict-based design, but attaches the common item-level operations directly to the item:
you can still use it anywhere a plain item `dict` is expected (for example `r3xa.data_sources.append(camera_item)`).

```python
validate(kind: str | None = None, schema: dict | None = None) -> RegistryItem
merge(**overrides) -> RegistryItem
save(path: str | Path | None = None, validate: bool = True, kind: str | None = None) -> Path
save_to(registry: Registry | str | Path, tree_path: str | None = None, validate: bool = True, kind: str | None = None) -> Path
bind(registry_root: str | Path | None = None, tree_path: str | None = None) -> RegistryItem
to_dict() -> dict
```

Typical workflows:

```python
from r3xa_api import Registry

registry = Registry("registry")

# Load an existing registry item, edit it, and save a standalone JSON copy.
camera = registry.get_item("data_sources/camera/avt_dolphin_f145b")
camera = camera.merge(description="Camera used in experiment 01")
camera.save("camera_exp01.json")

# Build a new item, bind it to a registry key, and save it into the registry tree.
new_camera = registry.wrap(
    {
        "id": "ds_cam_exp02",
        "kind": "data_sources/camera",
        "title": "Experiment camera",
        "description": "Bound registry item",
        "output_components": 1,
        "output_dimension": "surface",
        "output_units": [{"kind": "unit", "unit": "gl"}],
        "manufacturer": "Example",
        "model": "Cam-01",
        "image_size": [{"kind": "unit", "unit": "px"}],
    },
    tree_path="data_sources/camera/experiment_camera",
)
new_camera.validate().save()
```

### `validate_item(item, kind=None, schema=None) -> None`
Validate a single item against its schema definition (e.g. `data_sources/camera`).

This function is part of the advanced compatibility helper layer. It remains supported in the
1.x series, but for end-user workflows the recommended entry points are `RegistryItem.validate(...)`
and `Registry.validate(...)`.

### Advanced
`load_item_path(root, tree_path) -> dict`  
Internal/advanced helper to load a registry item by its tree path string, e.g. `settings/specimen/openhole_sample`.

`save_item_path(root, tree_path, item, validate=True, kind=None) -> Path`  
Validate then save a registry item using a `section/kind/name` tree path, e.g. `data_sources/camera/example_generated_camera`.

### `load_registry(root) -> dict`
Load a full registry tree into memory.

### `merge_item(base, **overrides) -> dict`
Create a new item by overriding fields of a registry item.

This is a shallow merge helper. For end-user workflows, prefer `RegistryItem.merge(...)`
or `Registry.merge(...)`.

## Schema utilities

### `load_schema(path: str | None = None) -> dict`
Load the embedded schema (or a custom path).

### `schema_version(path: str | None = None) -> str | None`
Extract the schema version.

### `validate(instance: dict, schema: dict | None = None) -> None`
Validate a JSON instance against the schema.

## Related pages
This page stays focused on the core SDK contract.

For adjacent topics, use the dedicated pages:
- `typed_models.md` for generated Pydantic models and `from_model(...)`
- `examples.md` for runnable scripts, including `graph_r3xa.py`
- `notebooks.md` for the Marimo notebook workflow
- `web.md` for the FastAPI web UI/API
