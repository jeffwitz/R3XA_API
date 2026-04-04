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
pip install -e ".[typed]"          # Pydantic typed models
pip install -e ".[web]"            # FastAPI web UI/API
pip install -e ".[notebook]"       # Marimo notebooks
pip install -e ".[graph_nx]"       # NetworkX + Matplotlib static graph backend
pip install -e ".[dev]"            # pytest and developer tools
```

Graphviz (`dot`) is a **system dependency** for SVG graph generation.

## Test matrix

The exact number of collected tests depends on the optional extras installed in the active `.venv`.

- `pip install -e ".[dev]"`  
  Core SDK tests and developer tooling.
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

From project root:

```bash
make generate-models
make generate-stubs
make generate-spec
make clean-artifacts
make source-archive
```

### Schema-driven stubs

The guided helper methods on `R3XAFile` are reflected for static tooling through
the generated stub file [r3xa_api/core.pyi](https://github.com/jeffwitz/R3XA_API/blob/develop/r3xa_api/core.pyi).

How this works:

- [r3xa_api/core.py](https://github.com/jeffwitz/R3XA_API/blob/develop/r3xa_api/core.py) remains the runtime implementation used by Python.
- [r3xa_api/core.pyi](https://github.com/jeffwitz/R3XA_API/blob/develop/r3xa_api/core.pyi) is a **type stub** read by IDEs and static type checkers.
- [r3xa_api/py.typed](https://github.com/jeffwitz/R3XA_API/blob/develop/r3xa_api/py.typed) marks the installed package as shipping official typing
  information.
- This improves completion and signature awareness for schema-driven guided
  helpers without changing runtime behavior.

Regenerate it after schema changes with:

```bash
make generate-stubs
```

This does not change runtime behavior. It refreshes the static API description
used by IDEs and type checkers. If the runtime helpers change but
`r3xa_api/core.pyi` is not regenerated, editors may show stale signatures even
though the package still runs.

### Test commands

```bash
./.venv/bin/pytest -q
./.venv/bin/pytest -q tests/webcore/test_graph_backends.py tests/webcore/test_graph_networkx.py
```

### Graph generation checks

```bash
./.venv/bin/python examples/python/graph_r3xa.py \
  --input examples/artifacts/dic_pipeline.json \
  --output examples/artifacts/graph_dic_pipeline \
  --dot \
  --networkx
```

```bash
./.venv/bin/python examples/python/graph_r3xa.py \
  --input examples/artifacts/qi_hu_from_scratch.json \
  --output examples/artifacts/graph_qi \
  --dot \
  --networkx
```

## Clean source archive

- `make source-archive` creates `archives/R3XA_API-source.zip` from `git archive`.
- Generated folders (`docs/_build`, `web/node_modules`, caches, build artifacts) are excluded by workflow and `.gitignore`.
