# R3XA_API

Python SDK, MATLAB binding, and WebUI for creating, validating, and visualising
R3XA metadata documents.

**[Documentation](https://r3xa-api.readthedocs.io/en/latest/)** ·
**[Public WebUI](https://photomechanics.gitlab.io/R3XA_API/)** ·
**[Python quick start](https://r3xa-api.readthedocs.io/en/latest/getting_started.html)**

The GitLab Pages WebUI is a static application. Editing, validation, Registry
item checks, and graph generation run in the browser. It does not upload user
documents to an R3XA backend.

## The three repositories

| Repository | Responsibility |
| --- | --- |
| [R3XA_SPEC](https://gitlab.com/photomechanics/R3XA_SPEC) | Normative JSON Schema for the format. |
| [R3XA_API](https://gitlab.com/photomechanics/R3XA_API) | Python SDK, MATLAB binding, WebUI, derived models and validators. |
| [R3XA_REGISTRY](https://gitlab.com/photomechanics/R3XA_REGISTRY) | Shareable, validated R3XA items. |

R3XA_API packages the published schema from R3XA_SPEC; it does not define an
independent format. The `registry/` folder here is a small bundled example and
test catalogue, separate from the canonical R3XA_REGISTRY repository and from
items stored locally in a user's browser.

## Install the Python SDK

The stable **`2.0.0`** release targets schema `2026.9.24` and is not source
compatible with the 1.x series. Install it from PyPI:

```bash
python -m pip install --upgrade r3xa-api==2.0.0
```

To work on `develop` instead, clone the repository and install it in an
activated virtual environment:

```bash
git clone --branch develop https://gitlab.com/photomechanics/R3XA_API.git
cd R3XA_API
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. Python
3.9 and newer are supported. The standard SDK includes Pydantic and a
bundled Graphviz WebAssembly backend; a system `dot` installation is optional.

## Create a document

```python
from r3xa_api import R3XAFile

document = R3XAFile(
    title="Tensile test",
    description="First specimen",
    authors=[{"name": "A. Example"}],
    date="2026-09-24",
)
light = document.add_generic_setting(
    title="Laboratory lighting",
    description="Diffuse LED illumination",
)
assert document.settings[0] is light

document.validate()
document.save("experiment.json")
document.plot("experiment.svg")
```

The SDK uses schema-generated Pydantic objects. Item references retain object
identity in Python and become IDs in the saved JSON. `validate()` returns
`None` on success and raises on failure.

For a progressive introduction, follow the
[interactive tutorials](https://r3xa-api.readthedocs.io/en/latest/notebooks.html)
in Python, Jupyter, or Marimo. A MATLAB introductory tutorial and larger
torsion and Qi Hu cases are also maintained under `examples/tutorials/` and
`examples/cases/`. Generated JSON and graph outputs are kept separately in
`artifacts/examples/`.

## WebUI and notebooks

Use the [public WebUI](https://photomechanics.gitlab.io/R3XA_API/) directly,
or build the same static site from a source checkout:

```bash
python -m pip install -e ".[web,dev]"
npm ci --prefix r3xa_web
python scripts/dev.py build-static-web
python scripts/dev.py serve-static-web --no-build --port 8080
```

The static files in `dist/r3xa-webui/` can be copied to any HTTP static host.
The FastAPI runtime remains available to contributors:

```bash
python -m pip install -e ".[web]"
python scripts/dev.py run-web --port 8002
```

To launch the tutorial browsers from the repository root, install the matching
extra and start one server:

```bash
python -m pip install -e ".[jupyter]"
jupyter notebook --no-browser --ip=127.0.0.1 --port=8888 --notebook-dir=.
```

```bash
python -m pip install -e ".[marimo]"
marimo edit --host 127.0.0.1 --port 2720
```

See the [WebUI guide](https://r3xa-api.readthedocs.io/en/latest/web.html) and
[tutorial guide](https://r3xa-api.readthedocs.io/en/latest/notebooks.html)
for details. The companion MATLAB binding creates JSON without requiring a
Python runtime inside MATLAB.

## Contribute and verify

```bash
python scripts/dev.py setup-dev
python -m pytest -q
python scripts/dev.py test-static-web
python scripts/dev.py build-docs
```

Work on `develop`; schema changes belong first in R3XA_SPEC. The
[developer workflow](https://r3xa-api.readthedocs.io/en/latest/dev_workflow.html)
explains schema synchronisation, model generation, CI, and WebUI builds.
