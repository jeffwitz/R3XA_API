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

## Common developer commands

From project root:

```bash
make generate-models
make generate-spec
make clean-artifacts
make source-archive
```

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
