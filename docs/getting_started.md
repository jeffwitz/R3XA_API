# Start with R3XA

Choose the browser editor if you want to describe an experiment without
installing software. Choose the Python SDK if you want to create documents in
scripts or notebooks. Both produce the same R3XA JSON format defined by
[R3XA_SPEC](https://gitlab.com/photomechanics/R3XA_SPEC).

## Use the browser editor

1. Open the [R3XA WebUI on GitLab Pages](https://photomechanics.gitlab.io/R3XA_API/).
2. Select an experiment profile, or **Generic** for an empty document.
3. Edit the document in Guided, Advanced, or Expert mode. A prefilled profile is
   an *illustrative example*; replace its values with those of your experiment.
4. Validate and download the JSON. Open **Schema viewer** to inspect the
   document and its graph.

The published site uses local browser storage for drafts and locally generated
graphs. The JSON is downloaded to your computer; it is not uploaded for
validation. See [Using the WebUI](web.md) for import, Registry editing, graph
controls, and the distinction between the static and FastAPI versions.

## Use the Python SDK

Install the stable 2.0 SDK, which targets schema `2026.9.24`:

```bash
python -m pip install --upgrade r3xa-api==2.0.0
```

To work with the current `develop` branch instead, install that checkout:

```bash
git clone --branch develop https://gitlab.com/photomechanics/R3XA_API.git
cd R3XA_API
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. Development
may move to a newer schema than the stable release; use the package version
matching the documentation and documents you are working with.

Create a small document:

```python
from r3xa_api import R3XAFile

document = R3XAFile(
    title="Tensile test",
    description="Metadata for the first test specimen",
    authors=[{"name": "A. Example"}],
    date="2026-09-24",
)
document.add_generic_setting(
    title="Laboratory lighting",
    description="Diffuse LED illumination",
)
document.validate()
document.save("tensile-test.json")
```

The generated item is an object in `document.settings`. You can edit it using
attributes, and references between objects are stored as IDs when saving JSON.
The bundled Graphviz WebAssembly backend lets `document.plot("test.svg")`
produce an SVG without installing the system `dot` executable.

## Continue

- [Interactive tutorials](notebooks.md): learn the object-first API in six
  steps, in Python, Jupyter, Marimo, or MATLAB.
- [Qi Hu case study](qi_case.md): inspect a larger scientific pipeline.
- [Python recipes](examples.md): load/edit/save, use the Registry, and export
  graphs.
- [API reference](api.md) and [generated specification](specification.md):
  exact methods and schema fields.

The shareable items in [R3XA_REGISTRY](https://gitlab.com/photomechanics/R3XA_REGISTRY)
are separate from the browser's local Registry. The `registry/` directory in
this repository is a small bundled example and test catalogue.
