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
validator. Phase C is complete: static document, Registry, and integrity
validation work locally. Phase D is complete: Graphviz WebAssembly is bundled
at build time, loaded lazily, and covered by successful and failure-path browser
tests. Phase E is now in progress. The current HEAD includes the resilient
schema viewer and the explicit
`Graphviz WebAssembly` backend label, non-root subpath hosting, same-origin
GET-only navigation, schema-validation parity cases, and the main static
editor workflows (mode changes, local import/persistence, directory selection,
graph palettes, fullscreen, standalone export, and i18n).

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

## Resume checklist

The next agent should start on `develop`, verify the worktree, and run:

```bash
git status -sb
npm ci --prefix web
.venv/bin/python scripts/dev.py test-static-web
```

The static site can be tested manually with:

```bash
.venv/bin/python scripts/dev.py serve-static-web --port 8080
```

Open `http://127.0.0.1:8080/`, create or load a document, then use
`Schema viewer` → `Generate graph`. The plain Python process only serves files;
Graphviz rendering runs in the browser. Stop it with `Ctrl+C`.

## Remaining work

Do not treat the current static graph success as completion of the whole static
WebUI initiative. The following work remains, in this order:

1. **Complete Phase E:** add full Python/JavaScript validation parity fixtures,
   including integrity errors and normalized error reports, and close any
   remaining static-only workflow gaps found by browser qualification.
2. **Add the zero-network acceptance checks:** browser tests must fail on
   `/api/*`, POST requests carrying documents, third-party resources, CDNs,
   telemetry, or remote graph/validation services. Keep all runtime assets,
   including validator and WASM code, local to the static origin.
3. **Implement Phase F GitLab Pages:** add `static-web-build`, `static-web-test`,
   and Pages jobs to `.gitlab-ci.yml` without removing the existing Python,
   docs, package, or FastAPI jobs. Publish `dist/r3xa-webui/` and expose the
   same directory as a downloadable CI artefact. Keep publication on the
   validated publication branch according to the current CI policy.
4. **Complete Phase G documentation:** document static deployment, subpath
   hosting, iframe headers and sandbox permissions, CSP/WebAssembly needs,
   privacy guarantees, known limitations, and the difference between static
   Graphviz WebAssembly and the server-side PyVis/Matplotlib backends.

## Current known limitations

- The static build requires Node.js and `npm ci --prefix web` at build time;
  the generated site does not require Node.js at runtime.
- The static graph bundle is deliberately loaded only after `Generate graph`.
- The static Schema viewer falls back to a native JSON `<pre>` when the bundled
  JSON viewer cannot display a complex draft, including `null` values.
- GitLab Pages publication, the broader zero-CDN/zero-API acceptance suite,
  and complete integrity/error-report parity are not implemented yet.

## Useful checks

```bash
python scripts/dev.py build-docs
python -m pytest -q --ignore=tests/web/test_browser.py
python -m pytest -q tests/web/test_browser.py
```
