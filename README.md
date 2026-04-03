# R3XA_API

Minimal Python SDK (no GUI) to create and validate R3XA metadata files.

## Install (editable)
```bash
pip install -e .
```

## Assumed environment
Documentation commands assume a local virtual environment exists at `.venv` (project root).

Create it once from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

On Windows:

```bat
.venv\Scripts\activate
```

## Quick start
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
    field_of_view=[
        unit(title="width", value=120.0, unit="mm", scale=1.0),
        unit(title="height", value=90.0, unit="mm", scale=1.0),
    ],
    focal_length=unit(title="focal_length", value=25.0, unit="mm", scale=1.0),
    standoff_distance=unit(title="standoff", value=0.5, unit="m", scale=1.0),
    lens="50mm prime",
    aperture="f/8",
    exposure=unit(title="exposure", value=2.0, unit="ms", scale=1.0),
)

images = r3xa.add_image_set_list(
    title="graylevel images",
    description="images taken by the CCD camera",
    path="images/",
    file_type="image/tiff",
    data_sources=[camera["id"]],
    time_reference=unit(title="time_reference", value=0.0, unit="s", scale=1.0),
    timestamps=[0.0, 1.0],
    data=["zoom-0050_1.tif", "zoom-0070_1.tif"],
)

r3xa.validate()

r3xa.save("hello-world.json")
```

Load and edit an existing file:

```python
from r3xa_api import R3XAFile

r3xa = R3XAFile.load("hello-world.json")
r3xa.set_header(title="Updated title")
r3xa.save("hello-world-updated.json")
```

## Documentation
- `docs/overview.md`
- `docs/api.md`
- `docs/examples.md`
- `docs/notebooks.md`
- `docs/validation.md`
- `docs/qi_case.md`
- `docs/matlab.md`

## IDE autocompletion (optional)
Typed models are available as an optional extra:

```bash
pip install -e ".[typed]"
```

Models are generated from the JSON schema and keep the dict-based API unchanged:

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

Regenerate typed models after schema updates:

```bash
make generate-models
```

## Marimo notebook (base DIC example)
Install notebook support:
```bash
pip install -e ".[notebook]"
# or
pip install -r requirements-notebook.txt
```

Run the notebook:
```bash
./.venv/bin/marimo edit examples/notebooks/dic_base_marimo.py
```

Notebook graph output uses Graphviz SVG (`dot` executable required).

Optional static export (no backend):
```bash
./.venv/bin/marimo export html examples/notebooks/dic_base_marimo.py -o docs/figures/dic_base_marimo/index.html --force
```

Run on MyBinder (no local install):
- Launch URL: `https://mybinder.org/v2/gh/jeffwitz/R3XA_API/develop?urlpath=proxy/2718/`
- Binder builds Python dependencies from `binder/requirements.txt`.
- Binder installs system packages from `binder/apt.txt` (includes `graphviz` / `dot`).
- Marimo starts automatically through `binder/start`.
- First launch can take a few minutes (cold start).

## Web UI (v0)
Install extras and run a minimal FastAPI shell:
```bash
pip install -e .[web,dev]
./.venv/bin/uvicorn web.app.main:app --reload --port 8002
```
Then open `http://127.0.0.1:8002/`.

Notes:
- SVG graph generation requires the **Graphviz executable** (`dot`) installed on the system:
  - Linux: `sudo apt-get install graphviz` (or your distro equivalent), then `dot -V`
  - macOS: `brew install graphviz`, then `dot -V`
  - Windows: install from <https://graphviz.org/download/>, add `Graphviz\\bin` to `PATH`, then `dot -V`
- The web viewer JS is vendored; **no `npm install` is required** for normal use.

## MATLAB (minimal binding)
MATLAB helpers live in `matlab/` and focus on **JSON generation only**.
Add the folder to the MATLAB path and use `r3xa.R3XAFile`.
## Registry
- Reusable items live in `registry/` (cameras, machines, software, datasets templates).
- Discover items with `Registry.list(...)` / `Registry.iter_items(...)`.
- Reuse and override an existing item with `Registry.merge(...)`.

## Examples
- From scratch pipeline: `examples/python/complex_dic_pipeline.py`
- Registry pipeline: `examples/python/complex_dic_pipeline_registry.py`
- Registry item creation: `examples/python/create_registry_camera.py`
- Typed (Pydantic) pipeline: `examples/python/typed_dic_pipeline.py`
- Validate all: `examples/python/validate_all.py`

## Optional static graph backend (NetworkX + Matplotlib)
Install:
```bash
pip install -e ".[graph_nx]"
```

Generate graph artifacts (Graphviz + PyVis + optional NetworkX image):
```bash
python examples/python/graph_r3xa.py \
  --input examples/artifacts/dic_pipeline.json \
  --output examples/artifacts/graph_dic_pipeline \
  --dot \
  --networkx \
  --networkx-format png
```

## Developer workflow (local)
- Generate typed models after schema updates: `make generate-models`
- Regenerate schema spec markdown: `make generate-spec`
- Clean generated artifacts before packaging: `make clean-artifacts`
- Build clean source zip from git tracked files: `make source-archive`
- Full test run: `./.venv/bin/pytest -q`

## Artifacts
- Demonstrators generated by examples: `examples/artifacts/dic_pipeline.json`, `examples/artifacts/dic_pipeline_registry.json`

## Notes
- The schema is embedded from the upstream R3XA project.
- This package does not depend on any GUI libraries.
