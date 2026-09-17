# Agent handoff notes

## Current development strategy

The project is migrating the WebUI to a static distribution while preserving
the existing FastAPI WebUI during the transition. Work is performed on
`develop`; publication and release promotion are handled separately after
validation.

The complete plan, decision log, phase status, and acceptance criteria are in
[`docs/static_web.md`](docs/static_web.md). The contributor workflow contains
the short operational summary in [`docs/dev_workflow.md`](docs/dev_workflow.md).

The architectural invariants are:

- `R3XA_SPEC` and the packaged `schema.json` remain the normative format source;
- the browser edits one canonical R3XA JSON document in every UI mode;
- Python may generate derived catalogues and validators at build time, but the
  static site must not require Python, FastAPI, Node.js, or system Graphviz at
  runtime;
- the static WebUI is a second runtime, not a replacement during migration;
- no schema taxonomy or parallel document model may be duplicated by hand in
  the frontend;
- runtime dependencies must be local; no CDN, telemetry, or document upload.

## Static WebUI phases

Phase A is complete: `web/static/runtime.js` provides the server runtime
adapter, and page scripts use `window.R3XARuntime` instead of direct `/api/*`
calls. Phase B is complete: `python scripts/dev.py build-static-web` generates
static pages, local schema/UI artefacts, build metadata, and a precompiled Ajv
validator. Phase C is in progress: static document, Registry, and integrity
validation work locally. Later phases cover report parity, local Graphviz
WebAssembly, zero-API checks, and GitLab Pages publication.

## Working rules

- Keep each coherent development phase in its own commit.
- Update `docs/static_web.md` progress and decisions in the same commit as the
  corresponding implementation.
- Do not commit generated build directories or local caches unless explicitly
  required by the repository.
- Preserve the FastAPI runtime and its tests until static-runtime parity is
  demonstrated.
- Run targeted tests first, then the broader suite and documentation build
  before handing off a phase.

## Useful checks

```bash
python scripts/dev.py build-docs
python -m pytest -q --ignore=tests/web/test_browser.py
python -m pytest -q tests/web/test_browser.py
```
