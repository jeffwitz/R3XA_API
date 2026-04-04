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
python -m venv .venv
```

Activate it:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Then upgrade `pip`:

```bash
python -m pip install --upgrade pip
```

Once the environment is activated, the documented `python ...` commands are the
same across Linux, macOS, and Windows.

Bootstrap the full contributor environment with one command:

```bash
python scripts/dev.py setup-dev
```

This installs the editable contributor stack (`dev`, `docs`, `typed`, `web`,
`notebook`, `graph_nx`) and regenerates the schema-derived artifacts tracked in
the repository. The bootstrap uses `pip install --no-build-isolation -e ...`
so it works cleanly inside an already-created project `.venv` without trying to
re-resolve build tooling from the network. On a fresh Python 3.12+ virtual
environment, it first bootstraps `pip`, `setuptools`, and `wheel`, because
editable installs using the setuptools backend cannot start without them.

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

Guided helper methods now exist for every schema kind using a consistent naming rule:

```python
add_<kind>_setting(...)
add_<kind>_source(...)
add_<kind>_data_set(...)
```

Examples:
- `add_testing_machine_setting(...)`
- `add_load_cell_source(...)`
- `add_generic_data_set(...)`

Legacy aliases remain available for datasets:
- `add_image_set_list(...)`
- `add_image_set_file(...)`

## Common workflows
For most users, the public API now boils down to three entry points:

1. **Create a new file from scratch**
   - `R3XAFile(...)`
   - `add_<kind>_setting/source/data_set(...)`
   - `validate()` / `save(...)`

2. **Load, edit, and save an existing file**
   - `R3XAFile.load(...)`
   - `set_header(...)`
   - `save(...)`

3. **Load, edit, and save a reusable registry item**
   - `Registry.load(...)` for plain dict access
   - `Registry.get_item(...)` for a `RegistryItem` wrapper
   - `RegistryItem.merge(...)`
   - `RegistryItem.validate()` / `RegistryItem.save(...)`

Example:

```python
from r3xa_api import Registry

registry = Registry("registry")
camera = registry.get_item("data_sources/camera/avt_dolphin_f145b")
camera = camera.merge(description="Camera used in experiment 01")
camera.save("camera_exp01.json")
```

Recommended import surface:

```python
from r3xa_api import R3XAFile, Registry, RegistryItem, new_item, unit, validate
```

Advanced compatibility helpers still exist, but they are no longer the recommended entry point
and are intentionally excluded from `r3xa_api.__all__`:

```python
from r3xa_api import load_item_path, save_item_path, validate_item, merge_item
```

Registry naming rule:
- prefer `load(...)` / `load_validated(...)` for file-backed registry access
- keep `get(...)` / `get_validated(...)` as compatibility aliases

Stability policy:
- symbols shown in `docs/api.md` are the public SDK contract for the 1.x series
- compatibility helpers remain importable during the 1.x series and will not be removed before `2.0`
- guided helpers (`add_<kind>_setting/source/data_set`) are part of that public contract and are tested against the schema
- details not documented in `docs/api.md` remain internal and may evolve more freely

See `STABILITY.md` for the compact policy.

## Documentation
- `docs/overview.md`
- `docs/api.md`
- `docs/examples.md`
- `docs/notebooks.md`
- `docs/validation.md`
- `docs/qi_case.md`
- `docs/matlab.md`
- `docs/engineering_contract.md`

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
python scripts/dev.py generate-models
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
python scripts/dev.py notebook-dic
```

Notebook graph output uses Graphviz SVG (`dot` executable required).

Optional static export (no backend):
```bash
python scripts/dev.py notebook-dic-export
```

Run on MyBinder (no local install):
- Launch URL: `https://mybinder.org/v2/gh/jeffwitz/R3XA_API/v1.5.0?urlpath=proxy/2718/`
- Binder builds Python dependencies from `binder/requirements.txt`.
- Binder installs system packages from `binder/apt.txt` (includes `graphviz` / `dot`).
- Marimo starts automatically through `binder/start`.
- First launch can take a few minutes (cold start).

## Web UI (v0)
Install extras and run a minimal FastAPI shell:
```bash
pip install -e ".[web,dev]"
python scripts/dev.py run-web --port 8002
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
- Load an item as a `RegistryItem` with `Registry.get_item(...)`.
- Reuse and override an existing item with `RegistryItem.merge(...)`.
- Save it back with `RegistryItem.save(...)` or `RegistryItem.save_to(...)`.

## Examples
- Minimal create/save: `examples/python/basic_create.py`
- From scratch pipeline: `examples/python/complex_dic_pipeline.py`
- Registry pipeline: `examples/python/complex_dic_pipeline_registry.py`
- Registry item creation: `examples/python/create_registry_camera.py`
- Graph export tool: `examples/python/graph_r3xa.py`
- Full file load/edit/save: `examples/python/load_edit_save.py`
- Literal Qi Hu reconstruction: `examples/python/qi_hu_from_json_literal.py`
- Qi Hu from scratch: `examples/python/qi_hu_from_scratch.py`
- Registry discovery and merge: `examples/python/registry_discovery.py`
- Registry loading and override basics: `examples/python/registry_usage.py`
- Typed (Pydantic) pipeline: `examples/python/typed_dic_pipeline.py`
- Validate all: `examples/python/validate_all.py`
- Validate static example JSON: `examples/python/validate_examples.py`

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
- Bootstrap the full contributor environment: `python scripts/dev.py setup-dev`
- Generate typed models after schema updates: `python scripts/dev.py generate-models`
- Regenerate IDE/type-checker stubs for guided helpers: `python scripts/dev.py generate-stubs`
- Regenerate schema spec markdown: `python scripts/dev.py generate-spec`
- Build the HTML docs: `python scripts/dev.py build-docs`
- Clean generated artifacts before packaging: `python scripts/dev.py clean-artifacts`
- Build clean source zip from git tracked files: `python scripts/dev.py source-archive`
- Full test run: `python -m pytest -q`

`python scripts/dev.py ...` is the canonical cross-platform workflow.

`setup-dev` is the fastest way to provision a fresh contributor `.venv`. If you
only want the dependencies without the regeneration steps, the equivalent install is:

```bash
pip install -e ".[dev,docs,typed,web,notebook,graph_nx]"
```

Test totals depend on installed extras:
- `.[dev]` covers the core SDK suite
- `.[docs]` adds the Sphinx documentation toolchain
- `.[typed]` adds typed-model tests
- `.[web]` adds web/API tests
- `.[graph_nx]` adds the NetworkX static graph backend tests

## Artifacts
- Demonstrators generated by examples: `examples/artifacts/dic_pipeline.json`, `examples/artifacts/dic_pipeline_registry.json`

## Notes
- The schema is embedded from the upstream R3XA project.
- This package does not depend on any GUI libraries.
