# Object-first models — `dic_pipeline` example

This page explains the object-first workflow. R3XA objects are generated from the JSON Schema by
`datamodel-code-generator` and use Pydantic for IDE completion and assignment validation.

## Goal

The object-first layer gives:
- IDE autocompletion
- Earlier validation while building objects

The wire format stays unchanged:
- object attributes are serialized by `to_dict()`
- references are objects in memory and IDs in JSON
- JSON output remains standard R3XA JSON

`R3XAFile` is the public generated Pydantic document model. It may be incomplete
while an experiment is being assembled, and its collections contain the same
generated Pydantic objects used everywhere else in the API. There is no second
in-memory builder representation: `to_dict()` is the explicit JSON boundary and
`validate()` checks the completed document against the schema.

## Why Pydantic helps in the workflow

Pydantic is the object model used by the Python SDK. It gives IDE completion,
attribute access, assignment validation, and an explicit `to_dict()` boundary
before the final JSON Schema validation step.

| What changes | Auto-generated after schema update | Still manual |
|---|---|---|
| New `kind` in the schema | Model class and schema-driven guided helper after regeneration | Dedicated business profile or widget, if needed |
| New field in an existing object | Updated typed constructor and field hints | Business logic that depends on that field |
| New object compatible with the schema | Usable through `new_item(...)` / `add_item(...)` | A dedicated helper like `add_lidar_source(...)` |
| Schema constraint changes | Reflected in generated models and validation | Business logic that depends on the old structure |

Main benefit:
- faster feedback in the IDE
- less trial-and-error while assembling objects
- same JSON output in the end
- the JSON boundary remains ordinary R3XA JSON

## Install

```bash
python -m pip install r3xa-api
```

Typed models are generated from the schema:

```bash
python scripts/dev.py generate-models
```

Generated file:
- {glsrc}`r3xa_api/models.py` (auto-generated; do not edit by hand)

## Public typed entry points

- `from r3xa_api import models`
- `from r3xa_api import typed_available`

`R3XAFile` and `R3XADocument` use the same generated object model. The legacy
`from_model(...)` bridge remains available for integrations, but it is not part
of the normal construction workflow.

## Ergonomic model helpers

Generated models inherit common helpers from `R3XAItem` (also exported as `R3XAModel`). Specialized classes know their
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
- `merge(...)` for a typed copy with selected attribute overrides
- `from_dict()` and `load()` for typed reconstruction
- `validate()` for validation against the canonical R3XA schema
- `save()` for validated JSON serialization
- `required_fields()`, `optional_fields()`, and `field_descriptions()` for discovery
- `summary()` and `print()` for readable inspection in a notebook or terminal
- `add_setting()`, `add_data_source()`, and `add_data_set()` for document assembly
- `find()`, `link_output()`, and `link_input()` for explicit document relationships
- `integrity_errors()` and `validate_integrity()` for reference checks

Object validation checks one item. Validation of references between settings, data
sources, and data sets belongs to the complete document (`R3XAFile` or `R3XADocument`).

## `dic_pipeline` in typed mode

This follows the same logic as {glsrc}`examples/python/complex_dic_pipeline.py`, but creates typed objects first.

```python
from r3xa_api import R3XAFile, models

r3xa = R3XAFile(
    title="Open-hole tensile test with DIC",
    description="Camera acquisition + DIC processing pipeline (typed)",
    authors=[{"name": "R3XA API"}],
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
r3xa.settings.append(specimen)

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
r3xa.data_sources.append(camera)

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
    parent_data_sources=[camera],
    time_reference=models.Unit(kind="unit", title="time_reference", value=0.0, unit="s", scale=1.0),
    timestamps=timestamps,
    values=image_files,
)
r3xa.data_sets.append(images)

dic_source = models.GenericSource(
    id="src_dic_01",
    kind="data_sources/generic",
    title="DIC processing (pyxel)",
    description="2D DIC using pyxel",
    input_data_sets=[images],
    output_components=2,
    output_dimension="surface",
    output_units=[
        models.Unit(kind="unit", title="ux", value=1.0, unit="mm", scale=1.0),
        models.Unit(kind="unit", title="uy", value=1.0, unit="mm", scale=1.0),
    ],
    manufacturer="Pyxel",
    model="pyxel-2d",
)
r3xa.data_sources.append(dic_source)

dic_data = models.ImageSetList(
    id="ds_dic_01",
    kind="data_sets/list",
    title="DIC displacement fields",
    description="ux, uy per frame",
    path="dic/",
    data_type="text/csv",
    parent_data_sources=[dic_source],
    time_reference=models.Unit(kind="unit", title="time_reference", value=0.0, unit="s", scale=1.0),
    timestamps=timestamps,
    values=dic_files,
)
r3xa.data_sets.append(dic_data)

r3xa.validate()
r3xa.save("examples/artifacts/dic_pipeline_typed.json")
```

## JSON boundary

Pydantic is required by the object-first Python API. The generated JSON file remains an ordinary
R3XA document and can be consumed by any implementation that follows the schema.

## Ready-to-run example script

The repository includes a typed example script:

- {glsrc}`examples/python/typed_dic_pipeline.py`

Run it from project root:

```bash
python examples/python/typed_dic_pipeline.py
```

Generated output:

- `examples/artifacts/dic_pipeline_typed.json`
