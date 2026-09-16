# Typed models (optional) — `dic_pipeline` example

This page explains the optional typed workflow built on top of the existing dict-based API.

## Goal

The typed layer gives:
- IDE autocompletion
- Earlier validation while building objects

The core API stays unchanged:
- `R3XAFile` still consumes plain `dict`
- JSON output remains standard R3XA JSON

## Why Pydantic helps in the workflow

Pydantic is useful here as an **authoring layer**, not as a replacement for the dict-based API.
It gives earlier feedback while the JSON is being built, before the final schema validation step.

| What changes | Auto-generated after schema update | Still manual |
|---|---|---|
| New `kind` in the schema | Typed model class in `r3xa_api/models.py` | Convenience helpers in `R3XAFile` |
| New field in an existing object | Updated typed constructor and field hints | Builder methods that hard-code that object |
| New object compatible with the schema | Usable through `new_item(...)` / `add_item(...)` | A dedicated helper like `add_lidar_source(...)` |
| Schema constraint changes | Reflected in generated models and validation | Business logic that depends on the old structure |

Main benefit:
- faster feedback in the IDE
- less trial-and-error while assembling objects
- same JSON output in the end
- no change for dict-only users

## Install

```bash
pip install -e ".[typed]"
```

Typed models are generated from the schema:

```bash
python scripts/dev.py generate-models
```

Generated file:
- {glsrc}`r3xa_api/models.py` (auto-generated; do not edit by hand)

## Public typed entry points

- `from r3xa_api import models`
- `from r3xa_api import from_model`
- `from r3xa_api import _TYPED_AVAILABLE` (or `typed_available`)

`from_model(...)` converts a Pydantic model into a plain dict compatible with `R3XAFile`.

## Ergonomic model helpers

Generated models inherit common helpers from `R3XAModel`. Specialized classes know their
schema `kind`, and item identifiers are generated when they are not provided explicitly.
The generated `version` field also defaults to the packaged schema version.

```python
from r3xa_api import models

camera = models.CameraSource(
    title="CCD Camera",
    output_components=1,
    output_dimension="surface",
    output_units=[models.Unit(unit="graylevel")],
    image_size=[
        models.Unit(unit="px", value=1392),
        models.Unit(unit="px", value=1040),
    ],
)

camera.validate()
camera.print()
camera.save("camera.json")
loaded_camera = models.CameraSource.load("camera.json")
```

The following helpers are available on generated models:

- `to_dict()` and `to_json()` for JSON-compatible representations
- `from_dict()` and `load()` for typed reconstruction
- `validate()` for validation against the canonical R3XA schema
- `save()` for validated JSON serialization
- `required_fields()`, `optional_fields()`, and `field_descriptions()` for discovery
- `summary()` and `print()` for readable inspection in a notebook or terminal
- `add_setting()`, `add_data_source()`, and `add_data_set()` for document assembly
- `find()`, `link_output()`, and `link_input()` for explicit document relationships
- `integrity_errors()` and `validate_integrity()` for reference checks

Object validation checks one item. Validation of references between settings, data
sources, and data sets belongs to the complete typed `R3XADocument`.

## `dic_pipeline` in typed mode

This follows the same logic as {glsrc}`examples/python/complex_dic_pipeline.py`, but creates typed objects first.

```python
from r3xa_api import R3XAFile, from_model, models

r3xa = R3XAFile(
    title="Open-hole tensile test with DIC",
    description="Camera acquisition + DIC processing pipeline (typed)",
    authors=["R3XA API"],
    date="2026-02-19",
)

specimen = models.SpecimenSetting(
    id="set_specimen_01",
    kind="settings/specimen",
    title="Openhole sample",
    description="Glass-epoxy specimen",
    sizes=[
        models.Unit(kind="unit", title="width", value=30.0, unit="mm", scale=1.0),
        models.Unit(kind="unit", title="thickness", value=2.0, unit="mm", scale=1.0),
    ],
    patterning_technique="white background with black spray paint",
)
r3xa.settings.append(from_model(specimen))

camera = models.CameraSource(
    id="ds_camera_01",
    kind="data_sources/camera",
    title="CCD Camera",
    output_components=1,
    output_dimension="surface",
    output_units=[models.Unit(kind="unit", title="graylevel", value=1.0, unit="gl", scale=1.0)],
    manufacturer="Allied Vision Technologies (AVT)",
    model="Dolphin F-145B",
    image_size=[
        models.Unit(kind="unit", title="width", value=1392, unit="px", scale=1.0),
        models.Unit(kind="unit", title="height", value=1040, unit="px", scale=1.0),
    ],
)
r3xa.data_sources.append(from_model(camera))

num_frames = 5
timestamps = [i * 0.5 for i in range(num_frames)]
image_files = [f"img_{i:04d}.tif" for i in range(num_frames)]
dic_files = [f"dic_{i:04d}.csv" for i in range(num_frames)]

images = models.ImageSetList(
    id="ds_images_01",
    kind="data_sets/list",
    title="graylevel images",
    description="raw images from CCD camera",
    path="images/",
    data_type="image/tiff",
    parent_data_sources=[camera.id],
    time_reference=models.Unit(kind="unit", title="time_reference", value=0.0, unit="s", scale=1.0),
    timestamps=timestamps,
    values=image_files,
)
r3xa.data_sets.append(from_model(images))

dic_source = models.GenericSource(
    id="src_dic_01",
    kind="data_sources/generic",
    title="DIC processing (pyxel)",
    description="2D DIC using pyxel",
    input_data_sets=[images.id],
    output_components=2,
    output_dimension="surface",
    output_units=[
        models.Unit(kind="unit", title="ux", value=1.0, unit="mm", scale=1.0),
        models.Unit(kind="unit", title="uy", value=1.0, unit="mm", scale=1.0),
    ],
    manufacturer="Pyxel",
    model="pyxel-2d",
)
r3xa.data_sources.append(from_model(dic_source))

dic_data = models.ImageSetList(
    id="ds_dic_01",
    kind="data_sets/list",
    title="DIC displacement fields",
    description="ux, uy per frame",
    path="dic/",
    data_type="text/csv",
    parent_data_sources=[dic_source.id],
    time_reference=models.Unit(kind="unit", title="time_reference", value=0.0, unit="s", scale=1.0),
    timestamps=timestamps,
    values=dic_files,
)
r3xa.data_sets.append(from_model(dic_data))

r3xa.validate()
r3xa.save("examples/artifacts/dic_pipeline_typed.json")
```

## Important compatibility note

- A script that imports `r3xa_api.models` requires the `[typed]` extra.
- The generated JSON file itself does **not** depend on Pydantic and remains usable by dict-only users.

## Ready-to-run example script

The repository includes a typed example script:

- {glsrc}`examples/python/typed_dic_pipeline.py`

Run it from project root:

```bash
python examples/python/typed_dic_pipeline.py
```

Generated output:

- `examples/artifacts/dic_pipeline_typed.json`
