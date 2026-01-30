# R3XA_API — Overview

![R3XA logo](figures/R3XA.png)

**Credits and origin**
- Initial implementation by **E. Roubin**, based on a shared specification led by **J‑C. Passieux**.
- Original repository: `https://gitlab.com/photomecanics/r3xa`

## Why R3XA
Researchers often lose crucial experimental context (camera focal length, calibration targets, acquisition settings). R3XA proposes a **metadata standard** to help remember, reuse, and replicate experiments without inventing a new data format.

## Core idea
- **Not another file format**: R3XA is a *metadata layer* over existing data files.
- **JSON Schema**: human‑readable, tool‑friendly, and easy to validate.
- **Shareable and scalable**: structured but extensible as practices evolve.

## JSON structure (high level)
An R3XA file is a single JSON document composed of:
- `header` fields (version, title, description, authors, date, …)
- `settings`: experimental parameters and devices
- `data_sources`: sensors or analysis steps that produce data
- `data_sets`: the actual datasets and their time/space organization

### Structure diagram
```{mermaid}
graph TD
  R3XA["R3XA JSON"]
  H["Header (version, title, description, authors, date, ...)"]
  S["settings[]"]
  DS["data_sources[]"]
  DSET["data_sets[]"]

  R3XA --> H
  R3XA --> S
  R3XA --> DS
  R3XA --> DSET
```

## Header (minimal)
Required fields:
- `version`, `title`, `description`, `authors`, `date`

Example:
```json
{
  "version": "2024.7.1",
  "title": "Hello World",
  "description": "Minimal R3XA file",
  "authors": "JC Passieux",
  "date": "2024-10-30",
  "settings": [],
  "data_sources": [],
  "data_sets": []
}
```

## Settings
Describe experimental parameters **not directly linked** to a specific dataset (specimen, machine, lighting, environment, …).

Example (generic):
```json
{
  "id": "id0",
  "kind": "settings/generic",
  "title": "Testing machine",
  "description": "Instron 5800 — electromechanical tensile machine"
}
```

Example (specimen):
```json
{
  "id": "id1",
  "kind": "settings/specimen",
  "title": "Openhole sample",
  "description": "The sample is a glass epoxy",
  "sizes": [
    {"kind": "unit", "title": "width", "value": 30.0, "unit": "mm", "scale": 1.0}
  ],
  "patterning_technique": "white background with black spray paint"
}
```

## Data sources
A **data source** is a system or procedure that produces a dataset (camera, DIC, FEA, load cell, …).

Example (camera):
```json
{
  "id": "id3",
  "kind": "data_sources/camera",
  "title": "CCD Camera",
  "description": "Encoding: 8-bit",
  "output_components": 1,
  "output_dimension": "surface",
  "output_units": [
    {"kind": "unit", "title": "graylevel", "value": 1.0, "unit": "gl", "scale": 1.0}
  ],
  "manufacturer": "Allied Vision Technologies (AVT)",
  "model": "Dolphin F-145B",
  "image_size": [
    {"kind": "unit", "title": "width", "value": 1392, "unit": "px", "scale": 1.0},
    {"kind": "unit", "title": "height", "value": 1040, "unit": "px", "scale": 1.0}
  ]
}
```

### Flow diagram
```{mermaid}
flowchart LR
  Setting[Settings] --> Source[Data source] --> Dataset[Data set]
  Setting -. context .-> Source
```

## Data sets
A **data set** describes where the data lives and how it is organized in time.

Example (list of files):
```json
{
  "id": "id4",
  "kind": "data_sets/list",
  "title": "graylevel images",
  "description": "images taken by the CCD camera",
  "path": "images/",
  "file_type": "image/tiff",
  "data_sources": ["id3"],
  "time_reference": 0.0,
  "timestamps": [0.0, 1.0],
  "data": ["img_0001.tif", "img_0002.tif"]
}
```

Example (tabular files):
```json
{
  "id": "id5",
  "kind": "data_sets/file",
  "title": "force time series",
  "description": "force vs time",
  "folder": "data/",
  "data_sources": ["id3"],
  "time_reference": 0.0,
  "timestamps": {"kind": "data_set_file", "filename": "timestamps.csv", "file_type": "text/csv"},
  "data": {"kind": "data_set_file", "filename": "force.csv", "file_type": "text/csv"}
}
```

## Using the SDK
The SDK provides guided helpers to create these structures without writing raw JSON:

```python
from r3xa_api import R3XAFile, unit

r3xa = R3XAFile(
    title="Hello World",
    description="Minimal R3XA file",
    authors="JC Passieux",
    date="2024-10-30",
)

specimen = r3xa.add_specimen_setting(
    title="Openhole sample",
    description="Glass-epoxy specimen",
    sizes=[unit(title="width", value=30.0, unit="mm", scale=1.0)],
)

camera = r3xa.add_camera_source(
    title="CCD Camera",
    description="Encoding: 8-bit",
    output_components=1,
    output_dimension="surface",
    output_units=[unit(title="graylevel", value=1.0, unit="gl", scale=1.0)],
    manufacturer="Allied Vision Technologies (AVT)",
    model="Dolphin F-145B",
    image_size=[
        unit(title="width", value=1392, unit="px", scale=1.0),
        unit(title="height", value=1040, unit="px", scale=1.0),
    ],
)

r3xa.add_image_set_list(
    title="graylevel images",
    description="images taken by the CCD camera",
    path="images/",
    file_type="image/tiff",
    data_sources=[camera["id"]],
    time_reference=0.0,
    timestamps=[0.0, 1.0],
    data=["img_0001.tif", "img_0002.tif"],
)

r3xa.validate()
```

## Validation (why it matters)
R3XA is defined by a JSON Schema. Validation ensures:
- **Completeness**: required fields are present.
- **Consistency**: field types and allowed values are respected.
- **Reproducibility**: datasets can be reused by others without guessing missing metadata.

### Full file validation
Validate a complete R3XA file:
```python
r3xa.validate()
```

### Item validation (registry)
Registry items are validated **against their own schema** (e.g. `data_sources/camera`) so they can be reused safely:
```python
from r3xa_api import validate_item
validate_item(camera_item)
```

See also: `validation.md`

## Registry (reusable components)
To avoid rewriting camera/specimen/software definitions, store reusable items in a registry tree:

```
registry/
  settings/
    generic/
    specimen/
  data_sources/
    camera/
    generic/
  data_sets/
    list/
    file/
```

Each file is a single JSON item (not a full R3XA file) that can be loaded and validated individually.

### How to load registry items
```python
from pathlib import Path
from r3xa_api import load_item_path, validate_item

registry_root = Path(__file__).parents[1] / "registry"

# Load reusable items
specimen_base = load_item_path(registry_root, "settings/specimen/openhole_sample")
validate_item(specimen_base)

camera_base = load_item_path(registry_root, "data_sources/camera/avt_dolphin_f145b")
validate_item(camera_base)

pyxel_base = load_item_path(registry_root, "data_sources/generic/pyxel_dic_2d")
validate_item(pyxel_base)
```

### How it maps to the schema
- Path `registry/settings/specimen/*.json` → items with `kind = "settings/specimen"`
- Path `registry/data_sources/camera/*.json` → items with `kind = "data_sources/camera"`
- Path `registry/data_sources/generic/*.json` → items with `kind = "data_sources/generic"`
- Path `registry/data_sets/list/*.json` → items with `kind = "data_sets/list"`
- Path `registry/data_sets/file/*.json` → items with `kind = "data_sets/file"`

### Why sub-validation works
Each registry item is validated against **its own schema definition** (e.g. `data_sources/camera`) rather than the full R3XA schema, which keeps the registry modular and reusable.
