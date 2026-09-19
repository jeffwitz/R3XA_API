# R3XA Web (v0)

FastAPI editor wired to schema-derived `r3xa_api.webcore` contracts.

## Install

```bash
python -m pip install "r3xa-api[web]"
```

## Run

```bash
python -m uvicorn web.app.asgi:app --reload
```

When working from a source checkout, `pip install -e ".[web,dev]"` remains
available.

Notes:
- The default SVG graph generation uses bundled Graphviz WebAssembly; the
  **Graphviz executable** (`dot`) is only needed for the explicit native backend.
- `r3xa-ensure-graphviz` can install `dot` through Homebrew on macOS or
  WinGet/Chocolatey on Windows.
- The schema viewer JS is vendored; **no `npm install` is required** for normal use.
- The editor keeps one canonical R3XA JSON document across Guided, Advanced, and Expert modes.
- Schema kinds come from `GET /api/schema/catalog`; UI presentation and profiles come from `GET /api/ui`.

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
- `GET /api/schema/catalog`
- `GET /api/ui`
- `GET /api/profiles`
