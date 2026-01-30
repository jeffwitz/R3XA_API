#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "${VENV_PY}" ]]; then
  echo "Virtualenv not found at ${ROOT_DIR}/.venv. Create it first." >&2
  exit 1
fi

"${VENV_PY}" -m sphinx -b html "${ROOT_DIR}/docs" "${ROOT_DIR}/docs/_build/html"
