# R3XA Web (v0)

Minimal FastAPI shell wired to the `r3xa_api.webcore` contracts.

## Install

```bash
pip install -e .[web,dev]
```

## Run

```bash
uvicorn web.app.main:app --reload
```

Notes:
- SVG graph generation requires the **Graphviz executable** (`dot`) installed on the system.
- The schema viewer JS is vendored; **no `npm install` is required** for normal use.

## Branding

Place the Photomeca logo at:

```
web/static/photomeca-logo.png
```

It will be displayed in the top bar if present.

## Endpoints

- `GET /` home
- `GET /edit` editor
- `GET /schema` schema viewer
- `POST /api/validate`
- `GET /api/schema`
- `GET /api/schema/summary`
