# Deploy on Railway

This guide describes how to deploy the FastAPI web app on Railway.

## 1) Create the Railway project

1. Go to Railway → **New Project** → **Deploy from GitHub**.
2. Select the `R3XA_API` repository.
3. Choose the branch you want to deploy (typically `main`).

Railway will detect the `Procfile` and start:

```
uvicorn web.app.asgi:app --host 0.0.0.0 --port $PORT
```

## 2) Environment variables

Configure these variables in Railway:

- `R3XA_CORS_ORIGINS`  
  Comma-separated list of allowed origins (e.g. `https://r3xa-api.readthedocs.io`)
- `R3XA_CORS_ALLOW_CREDENTIALS`  
  `0` (default) or `1`
- `R3XA_ENV` (optional)  
  `prod`

If `R3XA_CORS_ORIGINS` is empty, CORS is disabled (secure by default).

## 3) Health check

Once deployed, verify:

- `GET /health` → 200
- `GET /api/schema` → 200

You can find the public URL in the Railway project dashboard.

## 4) Local run

```bash
pip install -e ".[web]"
./.venv/bin/uvicorn web.app.asgi:app --reload --port 8000
```

## Notes

- SVG graph generation requires the Graphviz **`dot`** executable on the server.
- WebSocket endpoints are planned but not enabled yet.
