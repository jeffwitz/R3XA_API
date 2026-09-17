# Static WebUI development plan

This document is the persistent development record for the static R3XA WebUI.
It is both the implementation plan and the decision log for the migration. The
goal is to make progress reviewable from the repository, without relying on an
agent session or on undocumented architectural decisions.

## Objective

Provide a second distribution of the WebUI as a self-contained static site:

```text
HTML + CSS + JavaScript + JSON + local runtime assets
```

After the build, the site must run behind a plain static HTTP server, GitLab
Pages, Apache, or nginx. No Python, FastAPI, Node.js, system Graphviz, upload
service, database, telemetry, or third-party CDN may be required at runtime.

The static site must preserve the main user workflows:

- Guided, Advanced, and Expert editing of one canonical R3XA JSON document;
- import and export of R3XA JSON, with local draft persistence;
- schema-driven settings, data sources, data sets, and references;
- JSON Schema validation and R3XA integrity checks in the browser;
- Registry item validation;
- schema browsing and graph generation with the `document` and `classic` palettes;
- English and French internationalisation.

## Architectural decision

The static site is developed **alongside** the FastAPI WebUI first. It does not
replace the server runtime during the migration.

```text
R3XA_SPEC
    ↓
schema.json
    ↓
build-time derived artefacts
    ↓
one UI with two runtime implementations
    ├── runtime-server  → FastAPI `/api/*` routes
    └── runtime-static  → local JSON, JavaScript, and WASM assets
```

Both runtimes edit the same canonical JSON representation. The UI must not
introduce a simplified document model that is later converted into R3XA JSON.
The Python SDK, its validation API, and the FastAPI application remain
supported for development, parity testing, and users who need a server.

The static graph target is local Graphviz-compatible WebAssembly producing SVG.
The Python Graphviz, PyVis, and NetworkX/Matplotlib backends remain available
in the server/Python runtime. Reproducing every Python backend in the browser
is not required for the first static release.

## Scope and non-goals

In scope:

- build-time generation of schema, catalogue, UI, profile, and build metadata;
- a runtime abstraction that hides backend routes from the UI files;
- browser-side validation, integrity checks, and graph rendering;
- static hosting under a subpath, especially GitLab Pages;
- local-only handling of user documents and experimental file names;
- parity and browser tests for server and static runtimes;
- GitLab Pages publication and a downloadable static artefact.

Explicitly out of scope:

- a React, Vue, Angular, or other frontend rewrite;
- Pyodide or Python WebAssembly;
- a second hand-written R3XA schema for JavaScript;
- a parallel business/document model;
- a remote validation or graph-rendering service;
- analytics, telemetry, authentication, database storage, or server uploads;
- removal of the FastAPI runtime during this migration.

## Development phases

| Phase | Goal | Status |
| --- | --- | --- |
| A | Hide server API calls behind a runtime abstraction | **Completed** |
| B | Build static pages and schema-derived JSON artefacts | **Completed** |
| C | Add standalone JavaScript validation and integrity checks | **Completed** |
| D | Add lazy Graphviz WebAssembly SVG rendering | **Completed** |
| E | Test the generated `dist/` with parity and zero-API checks | **In progress** |
| F | Publish the static site with GitLab Pages | Planned |
| G | Complete documentation, deployment notes, and cleanup | Planned |

Each phase must keep the existing Python and server WebUI tests meaningful. A
phase is complete only when its acceptance checks are recorded in this file or
in the corresponding test and CI configuration.

## Phase A — runtime abstraction

The current UI is served by FastAPI and historically calls `/api/*` directly
from several page scripts. The first change removes that coupling without
changing the user-visible behaviour.

The common runtime contract is:

```text
loadSchema()
loadSchemaSummary()
loadSchemaCatalog()
loadUiCatalog()
loadProfiles()
validateDocument(payload)
validateItem(item, kind)
renderGraph(payload, options)
```

The initial implementation is `runtime-server`, which delegates to the
existing FastAPI routes. Later, `runtime-static` will implement the same
contract using generated local assets. Page scripts must call the contract,
not construct `/api/*` URLs themselves.

Phase A acceptance checks:

- no page script contains a direct FastAPI fetch;
- the server runtime preserves response and error behaviour;
- all templates load the runtime before page-specific scripts;
- the existing browser suite remains green;
- the contract test checks the abstraction rather than a particular URL string.

## Phase B — static build

Add the canonical command:

```bash
python scripts/dev.py build-static-web
```

It must produce `dist/r3xa-webui/` containing static pages and local assets,
including:

```text
schema.json
schema-catalog.json
schema-summary.json
ui-catalog.json
build-info.json
```

The Python build may reuse the existing schema and UI catalogue builders. A
profile inconsistent with the schema must fail the build. The generated site
must work from a subdirectory; it must not assume `/` or a project-specific
domain.

## Phase C — browser validation

Use a Draft 2020-12 JavaScript validator, preferably precompiled during the
build. The browser runtime must expose normalized validation reports for the
Guided, Advanced, Expert, and Registry views. R3XA integrity checks must be a
separate pure browser function and run after schema validation.

The first local implementation now compiles the packaged schema with Ajv
standalone during `build-static-web`. Document validation and Registry item
validation use the generated local validator; integrity checking is applied to
complete documents. Report wording is being aligned with the Python reports in
the remaining validation work.

The Python and JavaScript validators must agree at least on valid/invalid
status for representative valid and invalid documents. Required fields, types,
enums, constants, duplicate IDs, broken references, and invalid dates require
explicit parity fixtures.

## Phase D — browser graph

Port the graph domain model, not a layout engine. The browser graph must retain
the R3XA node semantics and the current palettes:

```text
setting     → ochre hexagon
data source → crimson ellipse
data set    → teal rectangle
```

The `document` palette remains the default and `classic` remains available.
Graphviz WebAssembly is loaded only when the user requests a graph. If
WebAssembly is unavailable, editing, validation, import, export, and Registry
work must continue with a clear graph-specific message.

## Phase E — static qualification

Run the same user scenarios against the server and static runtimes where the
behaviour is shared:

- first launch and profile selection;
- Guided → Advanced → Expert transitions without data loss;
- import, validation, and JSON export;
- Registry item validation;
- schema viewer and graph export;
- localStorage draft persistence;
- English/French switching.

The static acceptance test must fail if the browser requests `/api/*`, sends a
document by POST, or loads JavaScript, CSS, fonts, schema, catalogue, or WASM
from a third-party domain.

The current Phase E implementation verifies that generated pages work below a
non-root path and that a representative static navigation session uses only
same-origin `GET` requests. The static validator is also compared with the
Python validation report for valid documents and representative schema
failures (missing required field, wrong constant, and wrong type). Integrity
parity remains a separate follow-up because the JavaScript runtime adds those
semantic checks after schema validation.

## Phase F — GitLab Pages

The Pages job publishes only the generated `dist/r3xa-webui/` directory and
also exposes it as a downloadable CI artefact. The build is independent of
GitLab and can be copied to another static host.

Development work continues on `develop`; publication is made from the
validated default/release branch according to the repository CI policy. The
static site must support direct navigation to `/edit/`, `/schema/`, and
`/registry/` below a Pages subpath without server rewrites.

Iframe integration is documented and tested separately. GitLab response headers
such as `X-Frame-Options` and `Content-Security-Policy` must be checked before
claiming that the hosted Pages URL is embeddable. If GitLab hosting prevents an
iframe, the same static artefact remains deployable on PhotoMechanics hosting.

## Decisions and invariants

- `R3XA_SPEC` remains the normative source of the format.
- `r3xa_api/resources/schema.json` is the input to static artefact generation.
- Python is allowed at build time, never required by the static runtime.
- The canonical browser state is the R3XA JSON document itself.
- The existing FastAPI application stays available during migration.
- No runtime dependency is loaded from a CDN.
- No user document or experimental file is uploaded by the static site.
- No system `dot` executable is required by the static graph runtime.
- The UI remains vanilla JavaScript and uses native browser modules where useful.
- New functionality is added behind tested, small runtime interfaces.

## Definition of done

The initiative is complete only when all of the following are true:

1. `python scripts/dev.py build-static-web` creates a self-contained
   `dist/r3xa-webui/` directory.
2. A plain static HTTP server can serve the application without the R3XA
   Python package, FastAPI, Node.js, or system Graphviz installed on the host.
3. Static validation, integrity checks, Registry validation, and graph SVG
   generation work locally in the browser.
4. The static browser suite verifies parity scenarios, zero API calls, zero
   CDN calls, subpath hosting, and local persistence.
5. GitLab CI builds and publishes Pages from the validated publication branch
   while preserving the existing Python, documentation, packaging, and server
   jobs.
6. `docs/static_web.md` and the deployment documentation explain build, test,
   Pages, iframe, CSP, privacy, and known limitations.

## Progress log

### 2026-09-17

- Recorded the static WebUI architecture and acceptance criteria.
- Chose a parallel migration: FastAPI remains the server runtime while the
  static runtime is built and qualified.
- Completed Phase A: introduced `web/static/runtime.js` as the server runtime
  adapter and routed page metadata, validation, and graph operations through it.
- Verified Phase A with JavaScript syntax checks, 26 WebUI API/contract tests,
  and 16 browser tests.
- Completed the first Phase E qualification batch: added a subpath browser
  test, same-origin/GET-only request assertions, and Python/JavaScript schema
  validation parity cases. The browser suite now covers the WebAssembly
  failure path as well as successful local Graphviz rendering.

### Phase B progress

- Added `python scripts/dev.py build-static-web`.
- The command currently generates the four static pages, local schema/UI
  catalogues, build metadata, a precompiled Ajv validator, and a static runtime
  under
  `dist/r3xa-webui/`.
- Static metadata loading and schema validation are available locally. Static
  integrity checks and Registry validation are also wired; report parity and
  graph rendering remain in phases C and D.

### Phase C progress

- Ajv 2020 standalone compilation is implemented in
  `web/scripts/build-validator.mjs` and runs as part of the static build.
- The static runtime validates documents and Registry fragments without a
  server, then applies local ID/reference/date integrity checks to documents.
- Browser tests cover local document validation, duplicate-ID integrity errors,
  Registry validation, and absence of `/api/*` requests.

### Phase D progress

- Added the local `@viz-js/viz` Graphviz WebAssembly dependency and an esbuild
  step that bundles it into `assets/graph.generated.js` during the static build.
- Ported the shared graph model and DOT generation to browser JavaScript. The
  browser uses the same node roles, relationship directions, labels, and
  palettes as the Python Graphviz backend.
- The Python palette table is exported as `graph-palettes.json`, so static
  rendering does not maintain a second hand-written colour table.
- Graphviz is loaded lazily by `runtime-static.js` only after the user requests
  a graph. The static runtime exposes Graphviz SVG as its supported backend;
  PyVis and Matplotlib remain available through the FastAPI runtime.
- Added Node, static-build, and Chromium browser coverage for local SVG
  rendering and the absence of `/api/*` requests.

Phase D acceptance is complete: Graphviz is loaded lazily, local SVG rendering
works in Chromium, palette data comes from the Python source, and a failed
WebAssembly load produces a graph-specific error without disabling the editor.
The next work is Phase E static qualification and Python/JavaScript parity.
