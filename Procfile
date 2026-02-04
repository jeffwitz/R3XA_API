web: sh -c 'command -v dot >/dev/null 2>&1 || (apt-get update && apt-get install -y graphviz); PYTHONPATH=/app python -m uvicorn web.app.asgi:app --host 0.0.0.0 --port ${PORT:-8080}'
