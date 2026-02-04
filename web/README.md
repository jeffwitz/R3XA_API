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

## Endpoints

- `GET /` home
- `GET /edit` editor
- `GET /schema` schema viewer
- `POST /api/validate`
- `GET /api/schema`
- `GET /api/schema/summary`
