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
pip install -e ".[typed]"          # Pydantic typed models
pip install -e ".[web]"            # FastAPI web UI/API
pip install -e ".[notebook]"       # Marimo notebooks
pip install -e ".[graph_nx]"       # NetworkX + Matplotlib static graph backend
pip install -e ".[dev]"            # pytest and developer tools
```

Graphviz (`dot`) is a **system dependency** for SVG graph generation.

## Bootstrap a contributor environment

For a fresh `.venv`, the fastest bootstrap is:

```bash
python scripts/dev.py setup-dev
```

This command:

- bootstraps `pip`, `setuptools`, and `wheel` inside `.venv`
- installs the editable contributor stack `.[dev,docs,typed,web,notebook,graph_nx]`
  with `--no-build-isolation`
- regenerates `r3xa_api/models.py`
- regenerates `r3xa_api/core.pyi`
- regenerates `docs/specification.md`
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

- `pip install -e ".[dev]"`  
  Core SDK tests and developer tooling.
- `pip install -e ".[docs]"`  
  Adds the Sphinx documentation toolchain.
- `pip install -e ".[dev,typed]"`  
  Adds typed-model tests.
- `pip install -e ".[dev,web]"`  
  Adds web/API tests.
- `pip install -e ".[dev,graph_nx]"`  
  Adds NetworkX + Matplotlib graph backend tests.
- `pip install -e ".[dev,typed,web,graph_nx]"`  
  Gives the full local matrix used for repository maintenance.

If two contributors report different totals, check the installed extras before comparing raw pytest counts.

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
the generated stub file {ghsrc}`r3xa_api/core.pyi`.

How this works:

- {ghsrc}`r3xa_api/core.py` remains the runtime implementation used by Python.
- {ghsrc}`r3xa_api/core.pyi` is a **type stub** read by IDEs and static type checkers.
- {ghsrc}`r3xa_api/py.typed` marks the installed package as shipping official typing
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
  --input examples/artifacts/qi_hu_from_scratch.json \
  --output examples/artifacts/graph_qi \
  --dot \
  --networkx
```

## Clean source archive

- `python scripts/dev.py source-archive` creates `archives/R3XA_API-source.zip` from `git archive`.
- Generated folders (`docs/_build`, `web/node_modules`, caches, build artifacts) are excluded by workflow and `.gitignore`.
