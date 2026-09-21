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

For the binary provenance, wrapper ABI, Python/browser call sequence, packaging
rules, and replacement checklist, see
[`graphviz_wasm_development.md`](graphviz_wasm_development.md).

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
| F | Publish the static site with GitLab Pages | **In progress** |
| G | Complete documentation, deployment notes, and cleanup | **In progress** |

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
non-root path and that both a representative navigation session and a complete
editor/schema/Registry session use only same-origin `GET` requests. The build
also rejects absolute or protocol-relative page and stylesheet resources, and
the static runtime contains no remote or FastAPI API endpoint. The static
validator is also compared with the
Python validation report for valid documents and representative schema
failures (missing required field, empty text, unexpected properties, wrong
constant, wrong type, and an invalid item kind), as well as duplicate-ID
integrity errors. The static report
collapses branch-level `oneOf`/`anyOf` diagnostics so that the result matches
the meaningful Python validation error. The parity assertion compares validity
and the stable `(path, validator)` identity of each error. Common Guided-mode
messages for required, type, constant, enum, pattern, item-count, and
numeric-bound errors are also aligned with the Python report builder.
The technical `schema_path` is preserved in both reports, but it may point to
the resolved `$ref` target in Ajv and to the referring location in
`jsonschema`; consumers should use `path` and `validator` as the portable
error identity.

The browser qualification also covers Guided → Advanced → Expert transitions,
local JSON import and persistence across reload, natural sorting of selected
directory files, both graph palettes, fullscreen display, standalone HTML and
SVG downloads, and English/French switching. One-shot `new=1` and `prefill=1`
launch URLs are consumed after use so a browser reload does not recreate or
discard the document unexpectedly.

The first Registry safety lot is now implemented in both runtimes: loading a
Registry JSON item preserves its values and identifier exactly, while example
completion is an explicit action with a proposed-value preview and user
confirmation. Resetting an item or changing its kind/profile also asks for
confirmation when unsaved changes would be discarded. Browser regression tests
cover imported partial items in the FastAPI and static runtimes. The shared ID
migration utility also refuses ambiguous duplicate-ID migrations and reports
the conflicting IDs without rewriting their references. Dependency-closure
insertion is also implemented: using a local template copies its local upstream
objects, generates new IDs, and remaps the relationships. Missing and cyclic
dependency paths are rejected. Local Registry storage is now versioned, legacy
arrays are migrated, and corrupt storage is reported without being overwritten.
Registry examples are now loaded from the shared UI catalogue rather than
hard-coded in `registry.js`. The build validates that every schema kind has a
meaningful example summary, that configured example fields exist in the
schema-derived catalogue, and that the declared completion strategy is
explicit. The FastAPI and static runtimes therefore use the same examples.

Registry validation is now direct per-kind validation in the static runtime.
The build compiles an Ajv standalone validator for every `settings/*`,
`data_sources/*`, and `data_sets/*` definition and exposes a dispatcher keyed
by the item `kind`. A Registry fragment is no longer embedded in a synthetic
full R3XA document, so document-level fields and integrity checks cannot
produce false Registry errors. The static parity test validates every checked-
in Registry example against both the Python item validator and the generated
JavaScript validators, plus an invalid type case.

Static runtime-loaded assets are cache-consistent: the generated build ID is
derived from the Git revision and a content digest of the schema, UI resources,
static assets, and build script. HTML, catalogue fetches, validator imports,
and Graphviz imports all use that same version query. `build-info.json` exposes
both the revision and the content-aware build ID for deployment diagnostics.

The static Schema page no longer depends on the third-party JSON viewer. It
uses an internal text-only collapsible tree, and Graphviz SVG is parsed through
a local allowlist before being inserted into the page. Interactive PyVis output
is sandboxed without `allow-same-origin`. Hostile JSON-key/value and SVG tests
are included in the static browser qualification.

## Phase F — GitLab Pages

The CI now has separate `static-web-build` and `static-web-test` jobs. The
build job installs the Python build dependencies and the local JavaScript
dependencies, produces `dist/r3xa-webui/`, and stores both the directory and a
short-SHA zip as artifacts. The test job runs the canonical static build and
browser qualification with system Chromium.

The same explicit pipeline also runs `registry-sync`. This job checks out the
canonical `R3XA_REGISTRY` repository and validates all of its items against the
schema and SDK from the current API branch. The bundled `R3XA_API/registry/`
directory remains a small offline example/test catalogue; it is not a second
published Registry.

The `static-pages` job publishes only the generated `dist/r3xa-webui/`
directory and is restricted to the default branch when the pipeline is
explicitly started or requested with `[ci run]`. It explicitly waits for the
Python matrix, schema sync, canonical Registry sync, documentation, FastAPI
browser checks, and static browser checks before publishing. Ordinary pushes
remain subject to the repository's CI execution policy. The build is
independent of GitLab and can be copied to another static host.

Development work continues on `develop`; publication is made from the
validated default/release branch according to the repository CI policy. The
static site must support direct navigation to `/edit/`, `/schema/`, and
`/registry/` below a Pages subpath without server rewrites.

Iframe integration is documented and tested separately. GitLab response headers
such as `X-Frame-Options` and `Content-Security-Policy` must be checked before
claiming that the hosted Pages URL is embeddable. If GitLab hosting prevents an
iframe, the same static artefact remains deployable on PhotoMechanics hosting.

As of 2026-09-21, the project Pages API reports the configured domain
`https://r3xa-api-ff00f6.gitlab.io` but no Pages deployment. A request to that
domain redirects to GitLab authentication, so the application response and
its final `X-Frame-Options`/CSP headers cannot yet be qualified. This is a
deployment/quota state, not evidence that the static artefact is broken. Do
not mark Phase F complete until a successful default-branch Pages pipeline
serves the generated site anonymously.

## Local build and deployment

Install the build-time dependencies and create the site from the repository
root:

```bash
npm ci --prefix web
python scripts/dev.py build-static-web
```

The generated `dist/r3xa-webui/` directory is the complete deployment unit.
For a local static smoke test, serve that directory with any ordinary static
HTTP server:

```bash
cd dist/r3xa-webui
python -m http.server 8080
```

The build toolchain is pinned to Node.js `22.23.0` (`web/.node-version` and
`web/package.json`). CI uses the matching `node:22.23.0-bookworm-slim` image;
the Python environment used by the build and browser qualification is created
inside that image. This keeps the generated validator and static bundles
reproducible without adding Node.js to the runtime deployment.

The serving machine does not need `r3xa-api`, FastAPI, Node.js, `dot`, or
Graphviz installed. Node.js and Python are needed only to build the artefact
or to use Python as the local file server. The canonical checks are:

```bash
python scripts/dev.py test-static-web
```

The GitLab Pages job publishes the same content that is stored as the
`static-web-build` artifact. After a successful default-branch pipeline, copy
the URL shown in **Deploy → Pages**; it is also available to the job as
`CI_PAGES_URL`. The URL may include a project subpath, which is why the build
uses relative asset and navigation paths.

## GitHub Pages preview

For a hosted smoke test independent of the GitLab runner quota, the current
`develop` branch is also published temporarily on GitHub Pages:

```text
https://jeffwitz.github.io/R3XA_API/
```

The workflow is `.github/workflows/pages.yml`. It builds the same
`dist/r3xa-webui/` artefact with Python and Node.js, then deploys it with
GitHub Pages Actions. On 2026-09-21, the first run completed successfully and
was checked in a real browser: the Schema viewer loaded, Graphviz WebAssembly
produced an SVG, and no `/api/*` or third-party requests were made. The root
and `/schema/` pages returned HTTP 200, with no `X-Frame-Options` or restrictive
`frame-ancestors` header observed. This validates the static site on GitHub
Pages, but does not yet qualify GitLab Pages or replace the GitLab deployment
configuration.

## Iframe integration

The published site can be embedded when the selected host permits framing:

```html
<iframe
  src="https://<pages-host>/<project-path>/edit/"
  title="R3XA Web Editor"
  loading="lazy"
  style="width:100%;height:85vh;border:0;">
</iframe>
```

If a sandbox is required, start with only the permissions needed by the host
and test them explicitly:

```html
<iframe
  src="https://<pages-host>/<project-path>/edit/"
  title="R3XA Web Editor"
  sandbox="allow-scripts allow-same-origin allow-downloads allow-forms allow-modals"
  style="width:100%;height:85vh;border:0;">
</iframe>
```

The editor falls back to a regular browser download when the File System
Access API is unavailable, including in many cross-origin iframe contexts.
GitLab Pages response headers are controlled by the hosting service. Before
promising iframe support, inspect the deployed URL:

```bash
curl -I "https://<pages-host>/<project-path>/"
```

Check `X-Frame-Options` and the `Content-Security-Policy` `frame-ancestors`
directive. If they prevent framing, deploy the same `dist/r3xa-webui/`
directory on a PhotoMechanics-controlled static host instead.

## Runtime security and privacy

The static runtime has no account, database, upload endpoint, telemetry, CDN,
or remote validation service. Once its local assets are loaded, the R3XA
document is edited, validated, graphed, and exported in the browser. Drafts
are stored in origin-scoped `localStorage`; experimental files selected for a
list dataset contribute only their names or relative paths and are not
uploaded.

For a controlled static host, a restrictive starting policy is:

```text
default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; frame-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'
```

`wasm-unsafe-eval` is the only deliberate relaxation and should be retained
only if the Graphviz WebAssembly graph is enabled. Verify the final policy on
the deployed host with the browser graph test. The static graph runtime is
intentionally Graphviz WebAssembly/SVG only; PyVis and Matplotlib remain
available in the FastAPI runtime.

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
- Extended Phase E browser coverage to the shared editor workflows: mode
  transitions, local import/reload persistence, directory selection, palette
  switching, fullscreen, standalone/SVG export, and language switching. Fixed
  launch-action URLs so `new=1` and `prefill=1` are applied only once.
- Added browser parity coverage for schema and duplicate-ID integrity errors,
  and made Registry validation assert same-origin GET-only resource usage.
- Added local two-origin iframe coverage for Guided loading, validation,
  localStorage, Graphviz SVG rendering, sandbox attributes, and download
  fallback. This does not replace the hosted Pages check.

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

- The static graph runtime now uses the exact same
  `r3xa_api/resources/graphviz/graphviz-12.2.1.wasm` WASI module as the
  Python `graphviz-wasm` backend. The static build copies this binary
  into `assets/` and the browser adapter provides the minimal WASI imports
  needed by the exported Graphviz ABI.
- Ported the shared graph model and DOT generation to browser JavaScript. The
  browser uses the same node roles, relationship directions, labels, and
  palettes as the Python Graphviz backend.
- The Python palette table is exported as `graph-palettes.json`, so static
  rendering does not maintain a second hand-written colour table.
- Graphviz is loaded lazily by `runtime-static.js` only after the user requests
  a graph. The static runtime exposes Graphviz SVG as its supported backend;
  PyVis and Matplotlib remain available through the FastAPI runtime. The npm
  package `@viz-js/viz` is no longer required: there is one versioned Graphviz
  WebAssembly binary shared by Python and the browser build.
- Added Node, static-build, and Chromium browser coverage for local SVG
  rendering and the absence of `/api/*` requests.

Phase D acceptance is complete: the shared Graphviz WASI binary is copied
byte-for-byte into the static artefact, Graphviz is loaded lazily, local SVG
rendering works in Chromium, palette data comes from the Python source, and a
failed WebAssembly load produces a graph-specific error without disabling the
editor.
Phase E browser qualification, zero-network checks, and schema/integrity status
parity are now covered by the local test suite. The remaining Phase E work is
the final normalized user-facing error wording review and any gaps found during
the hosted smoke test. The parity tests intentionally compare portable error
identity (`path`, `validator`) and controlled user messages; `schema_path` may
differ when Ajv resolves a `$ref` to its target while Python reports the
referring schema location.

### Phase F progress

- Added GitLab CI jobs for static build, static browser qualification, and
  Pages publication. The Pages job consumes the same build artifact that is
  available for download and publishes it at the root of the Pages site.
- GitLab CI lint accepted the Pages configuration. The first explicit pipeline
  (`2859601291`, commit `161b6b8`) could not start its jobs because GitLab
  rejected them with `ci_quota_exceeded`; a successful hosted smoke test still
  requires available runner quota.

### Phase G progress

- Added operational documentation for local static deployment, GitLab Pages,
  subpath hosting, iframe embedding and sandbox permissions, CSP/WebAssembly,
  privacy, local storage, and the distinction between browser and server graph
  backends. A hosted Pages smoke test remains before closing this phase.

### Phase H: i18n, accessibility, and CSP

The generated pages now carry the English/French UI catalogue and update the
Registry and Schema viewer controls without a server round trip. Validation and
graph containers use live status regions, schema tree folders are keyboard
operable, and graph action buttons are hidden through CSS classes rather than
inline styles.

Static pages are designed for a restrictive same-origin Content Security
Policy. A host should configure the policy with only the deliberate
`wasm-unsafe-eval` relaxation required by the bundled Graphviz WebAssembly
renderer. No inline event handlers, inline page styles, CDN assets, or
third-party telemetry are used. The policy still needs to be verified on the
final GitLab Pages host, especially together with iframe headers and the
browser's WebAssembly policy. Local Playwright coverage applies this policy as
a response header and exercises the editor and Graphviz SVG path; hosted
qualification remains separate.
