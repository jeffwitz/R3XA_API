# MATLAB binding reference (minimal)

This page is mostly **reference documentation** for the MATLAB binding.
Use it when you need the exact supported scope and MATLAB call patterns.

This binding focuses **only on generating R3XA JSON** from MATLAB.  
No graph generation, no GUI dependencies, and no Python packages required inside MATLAB.

## Install (MATLAB path)
Add the `matlab/` folder to your MATLAB path:
```matlab
addpath(genpath('path/to/R3XA_API/matlab'));
```

## Quick start
```matlab
import r3xa.*

r3xa_file = R3XAFile( ...
    "title", "Hello World", ...
    "description", "Minimal R3XA file", ...
    "authors", "JC Passieux", ...
    "date", "2024-10-30" ...
);

specimen = r3xa_file.add_specimen_setting( ...
    "Openhole sample", ...
    "Glass-epoxy specimen", ...
    "sizes", {unit("width", 30.0, "mm", 1.0)} ...
);

camera = r3xa_file.add_camera_source( ...
    "CCD Camera", ...
    "Encoding: 8-bit", ...
    1, ...
    "surface", ...
    {unit("graylevel", 1.0, "gl", 1.0)}, ...
    "Allied Vision Technologies (AVT)", ...
    "Dolphin F-145B", ...
    {unit("width", 1392, "px", 1.0), unit("height", 1040, "px", 1.0)}, ...
    "field_of_view", {unit("width", 120.0, "mm", 1.0), unit("height", 90.0, "mm", 1.0)}, ...
    "focal_length", unit("focal_length", 25.0, "mm", 1.0), ...
    "standoff_distance", unit("standoff", 0.5, "m", 1.0), ...
    "lens", "50mm prime", ...
    "aperture", "f/8", ...
    "exposure", unit("exposure", 2.0, "ms", 1.0) ...
);

images = r3xa_file.add_list_data_set( ...
    "graylevel images", ...
    "images taken by the CCD camera", ...
    "image/tiff", ...
    {camera.id}, ...
    unit("time_reference", 0.0, "s", 1.0), ...
    [0.0, 1.0], ...
    {"zoom-0050_1.tif", "zoom-0070_1.tif"}, ...
    "path", "images/" ...
);

r3xa_file.save("hello-world.json");
```

## MATLAB vs Python helper signatures
The MATLAB binding currently keeps a small handwritten helper layer. It is intentionally close to the
Python API, but not identical.

General rule:

- schema-required fields are positional in MATLAB helpers
- optional fields go through trailing name/value arguments (`varargin`)
- low-level methods remain available for every kind:
  - `add_setting(kind, ...)`
  - `add_data_source(kind, ...)`
  - `add_data_set(kind, ...)`

In particular, `add_camera_source(...)` is stricter in MATLAB:

- Python guided helper:
  - `add_camera_source(title, output_components, output_dimension, output_units, image_size, **extra)`
- MATLAB helper:
  - `add_camera_source(title, description, output_components, output_dimension, output_units, manufacturer, model, image_size, ...)`

So `description`, `manufacturer`, and `model` are positional in MATLAB, while they stay optional
schema fields passed through `**extra` in Python.

When switching from Python to MATLAB, use the MATLAB examples in this page as the reference call signature.

## `unit()` signature difference

Python `unit()` requires only the `unit` keyword:

```python
unit(unit="mm")
unit(title="width", value=30.0, unit="mm")
```

MATLAB `unit()` keeps `title`, `value`, and `unit_name` as positional parameters:

```matlab
r3xa.unit("width", 30.0, "mm")
r3xa.unit("width", 30.0, "mm", 1.0)
```

This divergence is intentional. MATLAB does not support keyword-only arguments, and changing the
existing signature would break current MATLAB scripts.

## What is implemented
- `r3xa.R3XAFile` constructor, header editing, JSON serialization, and save
- Low-level item builders:
  - `add_setting(kind, ...)`
  - `add_data_source(kind, ...)`
  - `add_data_set(kind, ...)`
- Guided settings helpers:
  - `add_generic_setting(...)`
  - `add_specimen_setting(...)`
  - `add_stereorig_setting(...)`
  - `add_testing_machine_setting(...)`
- Guided data source helpers:
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
- Guided data set helpers:
  - `add_file_data_set(...)`
  - `add_generic_data_set(...)`
  - `add_list_data_set(...)`
- Legacy MATLAB aliases:
  - `add_image_set_list(...)`
  - `add_image_set_file(...)`
- Core helper functions:
  - `r3xa.new_item`
  - `r3xa.unit`
  - `r3xa.data_set_file`
  - `r3xa.ensure_data_set_file`
- `r3xa.schema_version` (reads `r3xa_api/resources/schema.json`)

## Legacy aliases

The canonical data set helper names now match the Python API:

- `add_list_data_set(...)`
- `add_file_data_set(...)`

For backward compatibility, the legacy MATLAB names remain available:

- `add_image_set_list(...)`
- `add_image_set_file(...)`

`add_image_set_list(...)` keeps the historical positional `path` argument. Use it only when you need
to preserve existing MATLAB scripts unchanged.

## What is intentionally omitted
- Graph generation backends
- JSON schema validation
- Registry tooling
- JSON loading / `from_dict()`
