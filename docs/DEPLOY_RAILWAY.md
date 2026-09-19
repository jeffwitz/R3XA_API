# Deploy on Railway

This guide describes how to deploy the FastAPI web app on Railway.

## 1) Create the Railway project

1. Go to Railway → **New Project** and connect a repository.
2. Select the `R3XA_API` repository.
3. Choose the branch you want to deploy (typically `main`).

Railway will detect the `Procfile` and start:

```
python -m uvicorn web.app.asgi:app --host 0.0.0.0 --port $PORT
```

If the build system does not install web extras, the included `railway.toml`
and `requirements.txt` force a minimal install of the web dependencies.
The default Graphviz WebAssembly backend does not require a system package;
the native `graphviz` backend remains available when `dot` is installed.

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

- `GET /health` → 200 (root endpoint, not under `/api`)
- `GET /api/schema` → 200

You can find the public URL in the Railway project dashboard.

## 4) Local run

```bash
pip install -e ".[web]"
python scripts/dev.py run-web --app web.app.asgi:app --port 8000
```

## Notes

- The default SVG graph generation uses the bundled WebAssembly backend. Install
  the Graphviz **`dot`** executable only when using the native `graphviz` backend.
- WebSocket endpoints are planned but not enabled yet.
