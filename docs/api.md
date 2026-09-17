# R3XA_API — API Reference

This page is **reference documentation**.
Use it to look up exact symbols, signatures, and return types.

This page documents the public API intended for library users.

## Recommended imports
For most user code, keep imports at the SDK level:

```python
from r3xa_api import R3XAFile, R3XAItem, Registry, RegistryItem, author, new_item, unit, validate
```

The generated Pydantic model classes are part of the standard object-first API and are exported
from the package as well, so they need not be reached through `r3xa_api.models`:

```python
from r3xa_api import CameraSource, SpecimenSetting, FileDataSet, R3XADocument
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
- Symbols documented on this page define the supported public SDK for the 2.x series.
- Compatibility helpers may remain importable, but they do not restore source or document compatibility with pre-2.0 releases.
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

Header fields are exposed as direct attributes (`document.title`, `document.authors`, ...).
`document.header` remains a mapping view for migration, but new code should use attributes.
The document collections contain generated Pydantic object instances, not
dictionaries. The document itself is already the generated object model and may
remain incomplete while it is being assembled; call `validate()` before saving
or exporting it.

**Methods**
```python
R3XAFile.from_dict(payload: dict) -> R3XAFile
R3XAFile.load(path: str | Path) -> R3XAFile
R3XAFile.loads(text: str) -> R3XAFile
R3XAFile.from_model(model) -> R3XAFile
```
Create a generated document from an existing payload, JSON file, or JSON string.
`from_model()` is a legacy integration bridge, not a separate authoring model.

```python
set_header(**fields) -> R3XAFile
to_model() -> R3XAFile
```
Update header fields, or return the already-generated document after validation.

```python
add_setting(kind: str, **fields) -> R3XAItem
add_data_source(kind: str, **fields) -> R3XAItem
add_data_set(kind: str, **fields) -> R3XAItem
```
Low‑level methods for any schema kind. They return the `R3XAItem` stored in the collection,
so mutating the returned item updates the document.

```python
add_<kind>_setting(...)
add_<kind>_source(...)
add_<kind>_data_set(...)
```
Schema‑driven guided helpers exist for every supported kind. They expose the schema `required`
fields as explicit parameters and accept optional schema fields through `**extra`.

Examples:

```python
add_generic_setting(title, **extra) -> R3XAItem
add_specimen_setting(title, **extra) -> R3XAItem
add_testing_machine_setting(title, **extra) -> R3XAItem
add_stereorig_setting(title, **extra) -> R3XAItem
add_camera_source(title, output_components, output_dimension, output_units, **extra) -> R3XAItem
add_load_cell_source(title, output_components, output_dimension, output_units, **extra) -> R3XAItem
add_generic_data_set(title, parent_data_sources, path, **extra) -> R3XAItem
add_list_data_set(title, timestamps, values, **extra) -> R3XAItem
add_file_data_set(title, timestamps, values, **extra) -> R3XAItem
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

```python
to_dict() -> dict
dump(indent: int = 4) -> str
validate() -> None
save(path: str | Path, indent: int = 4, validate: bool = True) -> Path
```
Serialize, validate, and write to disk.

```python
summary() -> str
print() -> None
```
Readable listing of the header followed by each collection's item titles. Field order and the
`*` required markers come from the schema. `print(document)` prints the same listing.

```python
plot(path: str | Path, *, backend: str = "graphviz", palette: str | None = None, include_description: bool = True) -> Path
```
Render the item graph and return the file written. `backend` is `"graphviz"` (SVG),
`"pyvis"` (interactive HTML) or `"matplotlib"` (PNG); each requires its optional extra.
The extension comes from the backend, so pass a path without one.

**Colour palettes.** `palette` selects the colour scheme and applies identically to all three
backends. Two are available, `"document"` being the default:

| `palette` | Settings | Data sources | Data sets | Look |
|---|---|---|---|---|
| `"document"` (default) | ochre `#9a6636` | crimson `#bf0040` | teal `#038181` | solid fills, white text; darker outlines for initial/final nodes |
| `"classic"` | blue | green / blue | grey / salmon | light fills with a contrasting outline |

`"document"` is J-C. Passieux's scheme for figures going into a printed document. The hue marks
the section. Initial data sources and final data sets keep the same crimson or teal fill as the
other nodes in their section, and are distinguished by a noticeably darker outline.

The settings fill is a darkened ochre rather than the original `#c4894f`: white text on that
colour reaches a contrast ratio of only 2.98, below the 4.5 WCAG AA threshold. `#9a6636` keeps the
hue and reaches 4.85, so the whole palette can stay white-on-colour.

```python
from r3xa_api import R3XAFile

document = R3XAFile.load("experiment.json")

document.plot("graph")                                  # graph.svg, document palette
document.plot("graph-classic", palette="classic")       # the older outlined scheme
document.plot("graph", backend="pyvis")                 # interactive HTML
document.plot("graph", backend="matplotlib")            # PNG
```

The same argument exists on the lower-level renderers, for a payload that is not held by an
`R3XAFile`:

```python
from r3xa_api.webcore.graph import render_graphviz_file, render_pyvis_html, render_networkx_matplotlib_file

render_graphviz_file(payload, Path("graph"), palette="classic")
```

and on the example script:

```bash
python examples/python/graph_r3xa.py --input experiment.json --output graph --palette classic
```

Typical edit cycle:

```python
from r3xa_api import R3XAFile

r3xa = R3XAFile.load("experiment.json")
r3xa.set_header(title="Updated title")
r3xa.save("experiment_updated.json")
```

### `R3XAItem`
An item held by an `R3XAFile` collection: a setting, a data source, or a data set.

`R3XAItem` is the common Pydantic base class for generated R3XA objects. Concrete objects such as
`CameraSource`, `TestingMachineSetting`, and `FileDataSet` expose schema fields as attributes, so
IDE completion and assignment validation work directly while the model remains JSON-compatible
through `to_dict()`.

```python
summary() -> str
print() -> None
```
List every field the schema defines for the item's kind — including fields the item does not
carry — with `*` on required ones and units collapsed to `30 mm`. `print(item)` prints the same
listing; `repr(item)` stays Pydantic's compact object representation.

```python
validate(schema: dict | None = None) -> R3XAItem
save(path: str | Path, *, validate: bool = True, indent: int = 2) -> Path
R3XAItem.load(path: str | Path) -> R3XAItem
to_dict() -> dict
```
Validate against the item's own schema kind, or write and read one item independently of the
document that contains it.

```python
kind -> str | None
required_fields() -> list[str]
optional_fields() -> list[str]
missing_fields() -> list[str]
field_descriptions() -> dict[str, str]
```
Schema introspection, to discover which fields may still be filled in.

```python
from r3xa_api import R3XAFile, unit

document = R3XAFile(title="Tutorial", description="Minimal file", authors=[{"name": "JC Passieux"}], date="2026-04-02")
specimen = document.add_specimen_setting(
    title="Openhole sample",
    description="Glass-epoxy specimen",
    sizes=[unit(title="width", value=30.0, unit="mm")],
)
specimen.print()
print(specimen.optional_fields())

camera = document.add_camera_source(
    title="CCD Camera",
    output_components=1,
    output_dimension="surface",
    output_units=[unit(unit="gl")],
    image_size=[
        unit(title="width", value=1392, unit="px"),
        unit(title="height", value=1040, unit="px"),
    ],
)
assert camera is document.data_sources[0]
document.data_sources[0].print()
```

The three document collections (`settings`, `data_sources`, and `data_sets`) are lists of generated
`R3XAItem` objects. References are object references in memory and become identifier arrays only
when `to_dict()`, `save()`, or validation serializes the document:

```python
camera = document.data_sources[0]
images = document.data_sets[0]
images.parent_data_sources = [camera]
assert document.to_dict()["data_sets"][0]["parent_data_sources"] == [camera.id]
```

`item.merge(...)` returns another typed item with the requested attribute overrides. This is useful
when adapting an object loaded from the registry while keeping the object-first workflow.

`R3XAFile.required_fields()`, `optional_fields()`, and `missing_fields()` provide the same
top-level discovery helpers as item models. A standalone item can be loaded with `R3XAItem.load()`.

## Helper functions

### `author(...)`
```python
author(name: str, affiliation: str | None = None, orcid: str | None = None, **extra) -> R3XAItem
```
Build a schema‑compliant author object. Only `name` is required.

```python
from r3xa_api import R3XAFile, author

document = R3XAFile(
    title="Torsion test",
    description="…",
    authors=[author("J-F. Witz", orcid="https://orcid.org/0000-0002-1825-0097"), author("Q. Hu")],
    date="2026-09-16",
)
```

Since schema `2026.9.16` an author carries its own ORCID; the former parallel `author_orcids`
array is gone.

### `unit(...)`
```python
unit(title: str | None = None, value: float | None = None, unit: str | None = None, scale: float | None = 1.0, **extra) -> R3XAItem
```
Build a schema‑compliant unit object. Only `unit` is required by the schema; `title`,
`value`, and `scale` are optional metadata.

### `data_set_file(...)`
```python
data_set_file(filename: str | None = None, file_type: str | None = None, delimiter: str | None = None, col: int | str | None = None, rows: list[int | None] | None = None, **extra) -> R3XAItem
```
Build an editable data_set_file object. `filename`, `col`, and `rows` may be
filled after construction; the object is schema-valid only once all required
fields are present.
The former `data_range` argument is intentionally rejected in the 2.x API; use
`col=` and `rows=[first_row, last_row]` instead.

## Registry utilities

### `load_item(path) -> R3XAItem`
Load a registry JSON item from disk.

### `save_item(path, item, validate=True, kind=None) -> Path`
Validate and save a single registry item JSON to disk. `item` can be an `R3XAItem`,
a plain `dict`, or a `RegistryItem`.

These helpers remain available for advanced use cases and backward compatibility. For object-first usage,
prefer `Registry.load(...)`, `R3XAItem.merge(...)`, and `R3XAItem.save(...)`; use
`Registry.get_item(...)` when mapping semantics or registry binding are needed.

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
load(tree_path: str) -> R3XAItem
load_validated(tree_path: str, kind: str | None = None) -> R3XAItem
get_item(tree_path: str, validated: bool = True, kind: str | None = None) -> RegistryItem
wrap(item: Mapping[str, Any], tree_path: str | None = None) -> RegistryItem
list(section: str | None = None, kind: str | None = None) -> list[str]
iter_items(section: str | None = None, kind: str | None = None, validated: bool = False, wrapped: bool = False) -> Iterator[tuple[str, R3XAItem | RegistryItem]]
merge(tree_path: str, **overrides) -> RegistryItem
save(tree_path: str, item: R3XAItem | dict | RegistryItem, validate: bool = True, kind: str | None = None) -> Path
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

`RegistryItem` is an explicit mapping wrapper for registry metadata and binding information.
For the object-first SDK, prefer the `R3XAItem` returned by `Registry.load()`; use this wrapper
when you need mapping semantics or a bound registry path.

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
2.x series, but for end-user workflows the recommended entry points are `RegistryItem.validate(...)`
and `Registry.validate(...)`.

### Advanced
`load_item_path(root, tree_path) -> R3XAItem`  
Internal/advanced helper to load a registry item by its tree path string, e.g. `settings/specimen/openhole_sample`.

`save_item_path(root, tree_path, item, validate=True, kind=None) -> Path`  
Validate then save a registry item using a `section/kind/name` tree path, e.g. `data_sources/camera/example_generated_camera`.

### `load_registry(root) -> dict[str, dict[str, dict[str, R3XAItem]]]`
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
Validate a complete JSON instance against the schema and its semantic integrity rules.
This includes duplicate identifiers, dangling dependency references, real calendar dates,
and reference integrity.

### `integrity_errors(instance: Mapping[str, Any]) -> list[str]`
Return semantic integrity errors without raising. Use this when an application needs to
display or combine the errors with its own diagnostics.

### `validate_integrity(instance: Mapping[str, Any]) -> None`
Validate semantic integrity independently of JSON Schema validation.

## Related pages
This page stays focused on the core SDK contract.

For adjacent topics, use the dedicated pages:
- `typed_models.md` for generated Pydantic object models and `from_model(...)`
- `examples.md` for runnable scripts, including `graph_r3xa.py`
- `notebooks.md` for the Marimo notebook workflow
- `web.md` for the FastAPI web UI/API
