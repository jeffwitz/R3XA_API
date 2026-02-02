# Examples — From Scratch vs Registry

This page shows the **same pipeline** built in two ways:
1) **From scratch** (explicit creation of every item)
2) **Registry‑based** (reuse shared items and override only what changes)

## 1) From scratch
File: `examples/complex_dic_pipeline.py`

Key ideas:
- Define specimen, camera, and DIC source explicitly.
- Generate file names and timestamps via loops.
- Build datasets directly from those lists.

```python
from r3xa_api import R3XAFile, unit

r3xa = R3XAFile(
    title="Open-hole tensile test with DIC",
    description="Camera acquisition + DIC processing pipeline",
    authors="R3XA API",
    date="2024-10-30",
)

specimen = r3xa.add_specimen_setting(
    title="Openhole sample",
    description="Glass-epoxy specimen",
    sizes=[
        unit(title="width", value=30.0, unit="mm", scale=1.0),
        unit(title="thickness", value=2.0, unit="mm", scale=1.0),
    ],
    patterning_technique="white background with black spray paint",
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
    focal_length=unit(title="focal_length", value=25.0, unit="mm", scale=1.0),
    standoff_distance=unit(title="standoff", value=0.5, unit="m", scale=1.0),
)

num_frames = 5
image_files = [f"img_{i:04d}.tif" for i in range(num_frames)]
timestamps = [i * 0.5 for i in range(num_frames)]

images = r3xa.add_image_set_list(
    title="graylevel images",
    description="raw images from CCD camera",
    path="images/",
    file_type="image/tiff",
    data_sources=[camera["id"]],
    time_reference=0.0,
    timestamps=timestamps,
    data=image_files,
)

dic = r3xa.add_data_source(
    "data_sources/generic",
    title="DIC processing (pyxel)",
    description="2D DIC using pyxel",
    output_components=2,
    output_dimension="surface",
    output_units=[
        unit(title="ux", value=1.0, unit="mm", scale=1.0),
        unit(title="uy", value=1.0, unit="mm", scale=1.0),
    ],
    manufacturer="Pyxel",
    model="pyxel-2d",
    input_data_sets=[images["id"]],
)

dic_files = [f"dic_{i:04d}.csv" for i in range(num_frames)]

r3xa.add_image_set_list(
    title="DIC displacement fields",
    description="ux, uy per frame",
    path="dic/",
    file_type="text/csv",
    data_sources=[dic["id"]],
    time_reference=0.0,
    timestamps=timestamps,
    data=dic_files,
)
```

## 2) Registry‑based
File: `examples/complex_dic_pipeline_registry.py`

Key ideas:
- Load reusable items from `registry/`
- Validate each item **by kind**
- Override only what changes (IDs, experiment‑specific values)

```python
from r3xa_api import R3XAFile, Registry, merge_item, unit

registry = Registry("registry")

specimen_base = registry.get_validated("settings/specimen/openhole_sample")
camera_base = registry.get_validated("data_sources/camera/avt_dolphin_f145b")
pyxel_base = registry.get_validated("data_sources/generic/pyxel_dic_2d")

specimen = merge_item(specimen_base, id="set_spec_exp01")
camera = merge_item(
    camera_base,
    id="ds_cam_exp01",
    description="CCD Camera (exp01)",
    standoff_distance=unit(title="standoff", value=0.5, unit="m", scale=1.0),
)

r3xa = R3XAFile(
    title="Open-hole tensile test with DIC (registry)",
    description="Camera acquisition + DIC processing pipeline (registry-based)",
    authors="R3XA API",
    date="2024-10-30",
)

r3xa.settings.append(specimen)
r3xa.data_sources.append(camera)

num_frames = 5
image_files = [f"img_{i:04d}.tif" for i in range(num_frames)]
timestamps = [i * 0.5 for i in range(num_frames)]

images = r3xa.add_image_set_list(
    title="graylevel images",
    description="raw images from CCD camera",
    path="images/",
    file_type="image/tiff",
    data_sources=[camera["id"]],
    time_reference=0.0,
    timestamps=timestamps,
    data=image_files,
)

dic = merge_item(
    pyxel_base,
    id="ds_dic_exp01",
    input_data_sets=[images["id"]],
)
r3xa.data_sources.append(dic)

dic_files = [f"dic_{i:04d}.csv" for i in range(num_frames)]
r3xa.add_image_set_list(
    title="DIC displacement fields",
    description="ux, uy per frame",
    path="dic/",
    file_type="text/csv",
    data_sources=[dic["id"]],
    time_reference=0.0,
    timestamps=timestamps,
    data=dic_files,
)
```

## Outputs
- From scratch: `examples/artifacts/dic_pipeline.json`
- Registry‑based: `examples/artifacts/dic_pipeline_registry.json`

## DIC pipeline graph (from scratch example)
SVG (Graphviz backend):

<img src="graph_dic_pipeline.svg" alt="DIC pipeline graph" />

Interactive HTML (PyVis backend):

<iframe
  src="graph_dic_pipeline.html"
  width="100%"
  height="700"
  style="border:1px solid #ddd;"
  title="DIC pipeline graph (interactive)"
></iframe>
