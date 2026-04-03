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
Validate and save a single registry item JSON to disk.

### `Registry`
Helper class that encapsulates the registry root and provides loading, validation, discovery, merge, and save methods.

```python
from r3xa_api import Registry, new_item, save_item_path, unit

registry = Registry("registry")
camera = registry.get_validated("data_sources/camera/avt_dolphin_f145b")

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

save_item_path("registry", "data_sources/camera/example_generated_camera", new_camera)
```

Most useful instance methods:

```python
load(tree_path: str) -> dict
load_validated(tree_path: str, kind: str | None = None) -> dict
list(section: str | None = None, kind: str | None = None) -> list[str]
iter_items(section: str | None = None, kind: str | None = None, validated: bool = False) -> Iterator[tuple[str, dict]]
merge(tree_path: str, **overrides) -> dict
save(tree_path: str, item: dict, validate: bool = True, kind: str | None = None) -> Path
```

Typical registry workflow:

```python
from r3xa_api import Registry

registry = Registry("registry")

for tree_path in registry.list(kind="data_sources/camera"):
    print(tree_path)

camera = registry.merge(
    "data_sources/camera/avt_dolphin_f145b",
    id="cam_exp01",
    description="Camera used in experiment 01",
)
```

### `validate_item(item, kind=None, schema=None) -> None`
Validate a single item against its schema definition (e.g. `data_sources/camera`).

### Advanced
`load_item_path(root, tree_path) -> dict`  
Internal/advanced helper to load a registry item by its tree path string, e.g. `settings/specimen/openhole_sample`.

`save_item_path(root, tree_path, item, validate=True, kind=None) -> Path`  
Validate then save a registry item using a `section/kind/name` tree path, e.g. `data_sources/camera/example_generated_camera`.

### `load_registry(root) -> dict`
Load a full registry tree into memory.

### `merge_item(base, **overrides) -> dict`
Create a new item by overriding fields of a registry item.

This is a shallow merge helper. For end-user workflows, prefer `Registry.merge(...)`.

## Schema utilities

### `load_schema(path: str | None = None) -> dict`
Load the embedded schema (or a custom path).

### `schema_version(path: str | None = None) -> str | None`
Extract the schema version.

### `validate(instance: dict, schema: dict | None = None) -> None`
Validate a JSON instance against the schema.

## Graph export (Graphviz / PyVis)
The `examples/python/graph_r3xa.py` tool can export SVG/HTML, and optionally the **Graphviz DOT** source.

PyVis HTML now uses a directed hierarchical layout (`UD`) with physics disabled to stay visually close to Graphviz layering.

Example:
```bash
python examples/python/graph_r3xa.py --input examples/artifacts/dic_pipeline.json --output examples/artifacts/graph_dic_pipeline --dot
```
This creates:
- `graph_dic_pipeline.svg` (Graphviz)
- `graph_dic_pipeline.html` (PyVis)
- `graph_dic_pipeline.dot` (Graphviz DOT source)

Optional non-intrusive backend (experimental):
- Install: `pip install -e ".[graph_nx]"`
- Export static image with NetworkX + Matplotlib:
```bash
python examples/python/graph_r3xa.py \
  --input examples/artifacts/dic_pipeline.json \
  --output examples/artifacts/graph_dic_pipeline \
  --networkx \
  --networkx-format png \
  --networkx-dpi 220
```
This adds:
- `graph_dic_pipeline_nx.png` (NetworkX + Matplotlib)

## Typed models (optional)
Detailed walkthrough with a DIC pipeline example: `typed_models.md`.

Install typed support:

```bash
pip install -e ".[typed]"
```

Public typed entry points:
- `r3xa_api.models` (generated Pydantic models)
- `r3xa_api.from_model(model) -> dict` (bridge to dict-based API)
- `r3xa_api._TYPED_AVAILABLE` / `r3xa_api.typed_available`

Typical usage:

```python
from r3xa_api import R3XAFile, from_model, models

camera = models.CameraSource(
    id="cam_01",
    kind="data_sources/camera",
    title="CCD Camera",
    output_components=1,
    output_dimension="surface",
    output_units=[models.Unit(kind="unit", unit="gl")],
    image_size=[models.Unit(kind="unit", unit="px")],
)

r3xa = R3XAFile(title="...", description="...", authors="...", date="2026-02-19")
r3xa.data_sources.append(from_model(camera))
r3xa.validate()
```

Model generation workflow:

```bash
make generate-models
```

`r3xa_api/models.py` is generated from `r3xa_api/resources/schema.json` and should not be edited manually.
