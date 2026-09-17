# Developer workflow

This page documents the recommended contributor workflow for local development.

## Runtime model for graphs

- **Primary engine:** Graphviz (`dot`) is the reference layout engine for SVG output.
- **Interactive HTML:** PyVis is generated from the same graph model.
- **Fallback behavior:** if Graphviz is unavailable, PyVis falls back to a manual layered layout.
- **Static optional backend:** NetworkX + Matplotlib can generate `png/svg/pdf` artifacts for environments without interactive HTML needs.

## Optional dependency sets

Install only what you need:

```bash
pip install -e .
pip install -e ".[docs]"           # Sphinx + doc extensions
pip install -e ".[web]"            # FastAPI web UI/API
pip install -e ".[notebook]"       # Marimo notebooks
pip install -e ".[graph_nx]"       # NetworkX + Matplotlib static graph backend
pip install -e ".[dev]"            # pytest and developer tools
```

The base installation includes the Python `graphviz` wrapper because graph
generation is used by the SDK, notebook, and web workflows. It cannot install
the system Graphviz executable (`dot`) through `pip`; install that executable
with `r3xa-ensure-graphviz` on macOS/Windows or with the Linux package manager.

Graphviz (`dot`) is a **system dependency** for SVG graph generation.

## Bootstrap a contributor environment

For a fresh `.venv`, the fastest bootstrap is:

```bash
python scripts/dev.py setup-dev
```

This command:

- bootstraps `pip`, `setuptools`, and `wheel` inside `.venv`
- installs the editable contributor stack `.[dev,docs,web,notebook,graph_nx]`
  with `--no-build-isolation`
- regenerates `r3xa_api/models.py`
- regenerates `r3xa_api/core.pyi`
- regenerates `docs/specification.md`

### Schema-driven typed models

The typed models follow the same source-of-truth rule as the rest of the SDK:

```text
R3XA_SPEC/schema-full.json
        ↓
R3XA_API/r3xa_api/resources/schema.json
        ↓
datamodel-code-generator
        ↓
r3xa_api/models.py
        ↓
scripts/postprocess_models.py
```

`datamodel-code-generator` is an external generator pinned to `0.54.0` so that
the checked-in generated output is reproducible across contributor machines.
It is configured to emit Pydantic v2 models. Pydantic provides runtime validation and serialization; it is not the
tool that generates the models from JSON Schema. Pydantic is a runtime dependency
of the object-first SDK, not an optional feature. The generated classes inherit
the shared `R3XAItem` behavior from {glsrc}`r3xa_api/model_base.py`.

Never edit {glsrc}`r3xa_api/models.py` by hand. After a schema change, update the
source schema in `R3XA_SPEC`, propagate it to the API repository, then run:

```bash
python scripts/dev.py generate-models
```

The command regenerates the classes and stable public aliases. Tests in
{glsrc}`tests/test_models.py` cover the ergonomic behavior and ensure that the
generated classes remain usable.
- builds the Sphinx HTML documentation

Use it when you want a ready-to-work contributor environment without running
each regeneration command manually.

The `--no-build-isolation` flag is intentional: it avoids an unnecessary second
packaging environment inside the already-prepared project `.venv`.

The explicit bootstrap of `pip`, `setuptools`, and `wheel` is also intentional:
on fresh Python 3.12+ virtual environments, `setuptools` is not guaranteed to
be present, but editable installs with the setuptools backend require it.

If the dependencies are already installed and you only want to refresh the
generated files, use:

```bash
python scripts/dev.py setup-dev --skip-install
```

If you want the regeneration steps but do not need a full HTML doc build:

```bash
python scripts/dev.py setup-dev --no-build-docs
```

## Test matrix

The exact number of collected tests depends on the optional extras installed in the active `.venv`.

- `pip install -e ".[docs]"`  
  Adds the Sphinx documentation toolchain.
- `pip install -e ".[dev]"`  
  Includes the Pydantic object-model tests.
- `pip install -e ".[dev,web]"`  
  Adds web/API tests.
- `pip install -e ".[dev,graph_nx]"`  
  Adds NetworkX + Matplotlib graph backend tests.
- `pip install -e ".[dev,web,graph_nx]"`  
  Gives the full local matrix used for repository maintenance.

For local graph support, run `r3xa-ensure-graphviz` after installing the package.
In a source checkout, `python scripts/dev.py ensure-graphviz` provides the same
cross-platform helper.

If two contributors report different totals, check the installed extras before comparing raw pytest counts.

GitLab CI runs the full test suite with the `dev`, `web`, and `graph_nx`
extras on Python 3.9 through 3.13, and installs the Graphviz `dot` executable.
A separate quality job builds the documentation with warnings treated as
errors. The package job verifies the wheel contents and runs a smoke test from
an environment where the installed wheel, rather than the source tree, is
imported.

### GitLab CI execution policy

To avoid consuming CI minutes on every push, GitLab CI is created automatically
only for release-candidate tags such as `v2.0.0rc2` or for commits whose
message contains `[ci run]`. A complete pipeline can also be started explicitly
from GitLab with **Run pipeline**, or with `glab pipeline run --branch main`.
Ordinary pushes do not create a pipeline.

## Common developer commands

From project root, use the Python task runner for a cross-platform workflow:

```bash
python scripts/dev.py setup-dev
python scripts/dev.py generate-models
python scripts/dev.py generate-stubs
python scripts/dev.py generate-spec
python scripts/dev.py build-docs
python scripts/dev.py clean-artifacts
python scripts/dev.py source-archive
```

`python scripts/dev.py ...` is the canonical workflow documented for all OSes.
`setup-dev` is the one-shot bootstrap command; the other subcommands stay useful
for targeted day-to-day work.

### Schema-driven stubs

The guided helper methods on `R3XAFile` are reflected for static tooling through
the generated stub file {glsrc}`r3xa_api/core.pyi`.

How this works:

- {glsrc}`r3xa_api/core.py` remains the runtime implementation used by Python.
- {glsrc}`r3xa_api/core.pyi` is a **type stub** read by IDEs and static type checkers.
- {glsrc}`r3xa_api/py.typed` marks the installed package as shipping official typing
  information.
- This improves completion and signature awareness for schema-driven guided
  helpers without changing runtime behavior.

Regenerate it after schema changes with:

```bash
python scripts/dev.py generate-stubs
```

This does not change runtime behavior. It refreshes the static API description
used by IDEs and type checkers. If the runtime helpers change but
`r3xa_api/core.pyi` is not regenerated, editors may show stale signatures even
though the package still runs.

### Test commands

```bash
python -m pytest -q
python -m pytest -q tests/webcore/test_graph_backends.py tests/webcore/test_graph_networkx.py
```

### Graph generation checks

```bash
python examples/python/graph_r3xa.py \
  --input examples/artifacts/dic_pipeline.json \
  --output examples/artifacts/graph_dic_pipeline \
  --dot \
  --networkx
```

```bash
python examples/python/graph_r3xa.py \
  --input examples/artifacts/dic_pipeline.json \
  --output examples/artifacts/graph_dic_pipeline_titles_only \
  --hide-description
```

```bash
python examples/python/graph_r3xa.py \
  --input examples/artifacts/qi_hu_from_scratch.json \
  --output examples/artifacts/graph_qi \
  --dot \
  --networkx
```

## Clean source archive

- `python scripts/dev.py source-archive` creates `archives/R3XA_API-source.zip` from `git archive`.
- Generated folders (`docs/_build`, `web/node_modules`, caches, build artifacts) are excluded by workflow and `.gitignore`.
