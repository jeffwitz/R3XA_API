#!/usr/bin/env bash
set -euo pipefail

pip install -e ".[web]"
uvicorn web.app.asgi:app --reload --port 8000
