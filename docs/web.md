# Web UI (R3XA_API)

This section documents the optional web UI included in the repository.

## Architecture choices

The web UI is split into two layers:

- **`r3xa_api/webcore/`**: pure Python helpers used by the web API (validation reports, schema summary, SVG graph generation).
- **`web/`**: FastAPI app + HTML/JS/CSS templates and static assets.

This keeps the **core API** (`r3xa_api`) as the single source of truth, while the web UI remains a thin consumer of that API.

## Install & run

From the project root (using the `.venv` convention):

```bash
pip install -e .[web,dev]
./.venv/bin/uvicorn web.app.main:app --reload --port 8002
```

Open: `http://127.0.0.1:8002/`

> Note: SVG graph generation requires the **Graphviz executable** (`dot`) to be installed on your system.

## What you can do

- **Editor** (`/edit`)
  - Edit a JSON draft (header + settings + data_sources + data_sets).
  - Validate the JSON (inline report).
  - Save/load JSON to/from disk.
  - Draft state is stored locally (browser storage).
- **Schema viewer** (`/schema`)
  - Inspect the schema summary or the current draft.
  - Generate an SVG graph from the current draft.

## API endpoints

- `POST /api/validate` → validation report
- `GET /api/schema` → raw schema
- `GET /api/schema/summary` → schema summary
- `POST /api/graph` → SVG graph (Graphviz)
