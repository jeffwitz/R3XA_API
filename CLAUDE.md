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
GET-only navigation, local-only asset checks, schema-validation parity cases,
and the main static editor workflows (mode changes, local import/persistence,
directory selection, graph palettes, fullscreen, standalone export, and i18n).

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
WebUI initiative. A detailed audit performed on 2026-09-18 concluded that the
architecture is sound and the static application is feature-complete locally,
but it is not yet production-qualified. In particular, the Registry editor
must become non-destructive and reference-safe before it is recommended for
real scientific metadata.

The work below is the authoritative prioritized handoff. Implement it in the
listed order and keep one coherent commit per numbered lot.

### Priority 0: data safety and browser security

#### 1. Stop silently enriching imported Registry items

Status: implemented in the current working tree. Keep the regression tests and
do not reintroduce automatic enrichment when extending the Registry editor.

`web/static/registry.js` currently calls `enrichLoadedDraft()` when a draft or
file is loaded. It uses `completeExampleValue()` to populate missing or blank
fields with plausible example values and may also replace legacy IDs. This is
useful when explicitly creating an example, but it is unsafe for imported
scientific metadata because opening an item can fabricate values without a
user action.

Required behavior:

- loading a JSON item must preserve it byte-for-data-equivalent apart from
  harmless JSON parsing/serialization differences;
- keep a clear `Create example` action for complete illustrative items;
- add an explicit `Complete missing fields from example` action, with a preview
  of every proposed value and a confirmation before applying it;
- do not confuse example values with values supplied by the user;
- protect kind/profile changes, reset, removal, and replacement with a dirty
  state and confirmation when data would be discarded;
- cover both the FastAPI and static runtimes with browser tests.

Suggested commit:

```text
fix(web): stop mutating imported registry items
```

#### 2. Make ID migration reference-safe

Status: implemented in the current working tree. The shared browser utility
now leaves documents containing duplicate IDs unchanged and reports the
ambiguity instead of guessing a reference target. Keep the duplicate-ID tests
when changing migration behavior.

`normalizeDocumentIds()` in `web/static/app.js` and the local Registry
normalization currently build a simple `old ID -> new ID` map. If two objects
share the same old ID, the second replacement wins and references can silently
be redirected to the wrong object.

Required implementation:

1. extract a shared ID utility used by the document editor and Registry;
2. inventory and count all IDs before modifying anything;
3. migrate automatically only noncanonical IDs that are unique;
4. never guess how to rewrite a reference to a duplicated ID;
5. report ambiguous IDs and let the user resolve them;
6. retain a recoverable copy of the document before an explicit migration;
7. test unique legacy IDs, duplicated IDs, cross-section references, missing
   references, and preservation of already canonical IDs.

Suggested commit:

```text
fix(web): make identifier migration reference-safe
```

#### 3. Clone complete Registry dependency closures

Status: implemented in the current working tree. Local template insertion now
resolves dependencies, remaps cloned IDs, previews multi-object insertions, and
rejects missing, ambiguous, or cyclic dependencies. Preserve the closure tests
when changing Registry insertion behavior.

The insertion code must keep the dependency graph intact. Relationship fields
such as `parent_data_sources`, `input_data_sets`, and
`attached_data_sources` must point to the newly cloned IDs rather than the
local Registry IDs.

Required behavior:

- recursively resolve all referenced local Registry items;
- calculate and display the complete insertion set before changing the
  document (`This will add N objects`);
- clone dependencies in a deterministic topological order;
- allocate new canonical IDs and remap every internal reference;
- detect cycles and missing dependencies and show an actionable error;
- apply the insertion atomically, then run schema and integrity validation;
- add tests for a source/data-set chain, shared dependencies, missing
  dependencies, cycles, and ID remapping.

Suggested commit:

```text
feat(web): clone local registry dependency closures
```

#### 4. Remove unsafe rendering paths

Status: implemented in the current working tree for the static/schema path.
The third-party JSON viewer and its vendored runtime are removed. The Schema
page now renders a collapsible JSON tree with `textContent`, and Graphviz SVG
responses are parsed and sanitized before insertion. PyVis content is placed
in a sandboxed iframe with scripts enabled but without same-origin access.
Hostile JSON and SVG browser tests cover the static runtime.

The server and static pages share this JavaScript renderer; keep the hostile
input tests when changing graph or schema display behavior.

Remaining work is to extend the hostile-input matrix to every backend and to
audit any future HTML-producing feature before it is inserted into the DOM.

- replace the third-party JSON viewer with a small internal tree renderer that
  writes all imported keys and values through `textContent`;
- preserve filtering, collapsible object/array nodes, and current-draft/schema
  selection without relying on unsafe HTML;
- test malicious keys and values containing tags, event handlers, SVG payloads,
  and script-like strings;
- verify that Graphviz labels are escaped or sanitize the returned SVG with a
  strict allowlist before insertion;
- sandbox the PyVis iframe without `allow-same-origin` if its functionality can
  be preserved;
- run the hostile-document scenarios in both runtimes.

Suggested commit:

```text
fix(web): harden JSON and graph rendering
```

### Priority 1: Registry model and static-runtime parity

#### 5. Version and manage local Registry storage

Status: implemented in the current working tree. Local Registry data now uses
a versioned envelope, migrates the legacy array format, reports corrupt
storage, handles write failures, and normalizes title uniqueness. The remaining
CRUD and collection import/export improvements can build on this format.

The storage key `r3xaLocalRegistryItems` now contains the versioned envelope;
legacy raw arrays are accepted only for one-time migration. Corrupt JSON is
reported without replacement, write failures are surfaced, and title
uniqueness is normalized.

Use a versioned envelope such as:

```json
{
  "format_version": 1,
  "schema_version": "...",
  "updated_at": "...",
  "items": []
}
```

Required implementation:

- migrate the legacy array format once without data loss;
- preserve corrupt raw storage for recovery/export instead of erasing it;
- show explicit parse and quota errors;
- normalize title uniqueness using trim, Unicode normalization, and
  case-insensitive comparison;
- keep global ID uniqueness strict;
- provide Edit/Load, Duplicate with a new ID, Export item, and Remove with
  confirmation;
- provide import/export of the complete local Registry;
- display schema-version compatibility and invalid-item status;
- test migration, corruption, quota failure, duplicate title variants,
  duplicate IDs, and all CRUD actions.

Suggested commit:

```text
feat(web): version and manage local registry storage
```

#### 6. Generate Registry examples from UI resources

Status: implemented in the current working tree. Registry kind summaries,
unit examples, field examples, array examples, and numeric examples now live
in `r3xa_api/resources/ui/registry_examples.json`. The Python UI catalogue
loads and validates this resource, and both server and static runtimes expose
it through the same `ui-catalog` payload. `registry.js` now consumes the
resource and keeps only schema-driven completion logic.

The resource declares an explicit `schema-driven` completion strategy: every
known kind must have a meaningful item summary, while the remaining fields are
filled from the schema and the shared example tables. Unknown kinds or example
field names fail the catalogue build instead of silently falling back.

Required implementation:

- move examples to a resource such as
  `r3xa_api/resources/ui/registry_examples.json`, or an equivalent UI-catalogue
  extension;
- expose the generated examples identically through server and static
  runtimes;
- validate at build time that every known kind has either a complete example
  or an explicit generic strategy;
- reject unknown example fields;
- validate every example against its item schema;
- reject empty values and placeholder text except intentionally empty
  relationship arrays;
- make `registry.js` consume the catalogue without knowing individual kinds;
- test meaningful example values for each kind, not merely that values are
  nonempty.

The remaining qualification work is to expand the resource validation to
schema-valid complete payload snapshots if the Registry example policy later
requires examples to be independently loadable without completion.

Suggested commit:

```text
refactor(web): generate registry examples from UI resources
```

#### 7. Compile real per-kind Registry validators

Status: implemented in the current working tree. The static build now emits a
standalone Ajv validator for every supported Registry `kind`, and
`runtime-static.js` dispatches directly to that validator without creating a
synthetic full document. The generated module also exposes the supported kind
list and preserves Ajv's technical errors for report normalization.

The server runtime continues to validate the matching schema definition
directly through `r3xa_api.registry.validate_item`; both runtimes therefore
exercise the same per-kind contract.

Required implementation:

- compile Ajv standalone validators for every supported `kind` during the
  static build, directly from the schema definitions;
- expose one dispatch API keyed by `item.kind`, while retaining an explicit
  kind override where appropriate;
- do not wrap fragments in a fake R3XA document;
- normalize static and server reports to the same shape:
  `path`, `validator`, `message`, `user_message`, and `schema_path`;
- keep the raw technical error available in Expert mode;
- test all valid examples and invalid required/type/enum/const/range cases
  against both Python and JavaScript validators.

The remaining qualification work is to expand report-parity cases for every
schema keyword and to keep the generated validator synchronized with the
schema build.

Suggested commit:

```text
feat(web): generate per-kind registry validators
```

#### 8. Make static asset versioning atomic

Status: implemented in the current working tree. Static runtime fetches and
dynamic imports now carry the same build version as the HTML runtime script.
The build ID combines the checked-out revision with a content digest of the
schema, UI resources, static assets, and build script, so local dirty builds
cannot accidentally reuse the cache key of a different WebUI.

`build-info.json` records both the Git revision and the content-aware build
ID. Keep this invariant when adding new runtime-loaded assets.

Required implementation:

- prefer content-hashed asset names with a generated manifest;
- if that is disproportionate, append a generated build ID to every static
  `fetch()` and dynamic import, not only HTML scripts;
- read the project version directly from `pyproject.toml`;
- include dirty-worktree/content information in local build IDs so two
  different builds cannot share one cache key;
- add a test proving that all dynamically loaded assets are tied to the same
  build identifier;
- generate and include `THIRD_PARTY_NOTICES.txt` for Ajv, Graphviz/Viz.js, and
  all other shipped runtime assets.

Suggested commit:

```text
fix(web): make static assets cache-consistent
```

#### 9. Complete i18n, accessibility, and strict CSP compatibility

Implemented in the current lot:

- moved the Registry, Schema viewer, graph, validation, storage, and standalone
  export UI strings into the bilingual UI message catalogue;
- added English/French browser coverage for Registry and Schema viewer controls;
- added translated placeholders, option labels, accessible status regions, and
  keyboard labels for the schema tree;
- removed template inline handlers/styles and replaced graph visibility changes
  with CSS classes;
- removed inline page handlers/styles and documented a restrictive same-origin
  CSP policy for static hosts, with only the `wasm-unsafe-eval` allowance
  required by Graphviz WebAssembly;
- added static-build assertions preventing inline handlers/styles and browser
  coverage for the local translated controls;
- added a Playwright smoke test that applies the documented strict CSP response
  header and exercises editor loading plus local Graphviz WebAssembly/SVG.

Remaining follow-up:

- audit less visible generated field labels and standalone-export markup for
  complete translation coverage;
- qualify the same CSP through a hosted GitLab Pages smoke test and document
  any host-specific WebAssembly or iframe header requirements;
- the existing validation error controls already focus and scroll to the
  corresponding field; keep that behavior covered when validation rendering
  changes.

Suggested commit:

```text
feat(web): complete i18n accessibility and CSP support
```

### Priority 2: qualification and deployment

#### 10. Share runtime qualification and add missing tests

The Python Playwright coverage is valuable, but server and static suites are
not fully shared. `web/package.json` still has no real JavaScript unit suite,
and pure functions such as ID migration, local storage, report normalization,
and graph-model construction are tested mainly through the browser.

Required implementation:

Progress in the current lot:

- added a Node `node:test` suite for the browser graph model, DOT semantics,
  canonical ID migration, relationship remapping, and local Registry storage;
- made `npm test --prefix web` a required step of the static build CI job;
- kept the existing static browser checks for no `/api/*`, no POST, no remote
  assets, schema/integrity parity, hostile JSON/SVG, Registry validation, and
  graph export.

- use the built-in Node `node:test` runner unless a stronger dependency is
  justified;
- split pure utilities into importable `.mjs` modules;
- parameterize common Playwright scenarios to run against both FastAPI and
  static base URLs;
- preserve runtime-specific tests only where behavior genuinely differs;
- compare the JavaScript and Python graph models for node IDs, edges, node
  categories, initial/intermediate/final status, and palette style keys;
- keep the full static acceptance test that rejects `/api/*`, POST requests,
  and third-party domains;
- add a two-origin iframe test covering load, Guided editing, validation,
  localStorage, graph rendering, and download fallback;
- test the documented sandbox attributes separately;
- run cache, CSP, malicious JSON, and local Registry dependency scenarios.

Suggested commit:

```text
test(web): share static and server qualification
```

#### 11. Finish Phase F GitLab Pages

After priorities 0 and 1 are complete and the full local suite is green:

1. trigger an explicit `develop` pipeline when GitLab runner quota or a private
   runner is available;
2. do not merge to `main` until all existing Python, schema-sync, docs,
   FastAPI, static build, static browser, and package jobs pass;
3. build the downloadable static ZIP from the exact CI artefact;
4. promote to `main` only through the agreed project workflow;
5. run the default-branch Pages job;
6. smoke-test Home, Editor, Schema, Registry, validation, both graph palettes,
   JSON/SVG/HTML export, and French/English on the hosted URL;
7. inspect `X-Frame-Options`, `Content-Security-Policy`, and `frame-ancestors`
   with `curl -I`;
8. test the real GitLab Pages URL in a cross-origin iframe;
9. if GitLab.com headers forbid embedding, document deployment of the exact
   same `dist/r3xa-webui/` artefact on the PhotoMechanics server.

#### 12. Complete Phase G documentation

Update `docs/static_web.md`, `docs/web.md`, the README, and this handoff after
the hosted smoke test. Record the actual Pages URL, tested iframe result,
required CSP, build artefact name, privacy guarantees, supported browsers,
known WebAssembly limitation, storage migration policy, and manual deployment
procedure. Do not describe Pages or iframe support as validated before the
hosted checks have actually passed.

## Implementation constraints for the remaining work

- Work on `develop`; do not develop directly on `main`.
- Preserve one canonical R3XA JSON document across Guided, Advanced, Expert,
  server, and static views.
- Preserve both FastAPI and static runtimes until parity is demonstrated.
- Do not modify generated `dist/` output directly or commit local build caches.
- Do not add a frontend framework or a second schema/document model.
- Do not mutate user data without an explicit, reviewable user action.
- Keep schema-derived knowledge in generated catalogues rather than hardcoding
  kinds in JavaScript.
- Add targeted tests with each fix; never relax an assertion merely to make a
  pipeline green.
- Update this file and `docs/static_web.md` in the same commit whenever phase
  status, architecture, commands, or known limitations change.
- Do not merge, tag, release, or deploy unless explicitly requested.

For each numbered lot, run targeted tests first and finish with:

```bash
.venv/bin/python scripts/dev.py test-static-web
.venv/bin/python -m pytest -q tests/web/test_browser.py
.venv/bin/python -m pytest -q
```

If a full suite is blocked by infrastructure, record the exact blocked command
and retain the successful targeted results. A GitLab `ci_quota_exceeded`
failure is not evidence that the code passed or failed.

## Audit baseline (2026-09-18)

The audit that produced the plan above established this local baseline:

- `python scripts/dev.py test-static-web`: **33 passed** after running outside
  the restricted socket sandbox; this includes the static build, Ajv parity,
  local Graphviz/WASM, and 28 Playwright scenarios;
- `python -m pytest -q tests/web/test_browser.py`: **22 passed** for the
  FastAPI WebUI;
- the worktree remained clean during the audit;
- the latest explicitly requested `develop` pipeline at the time was pipeline
  `2859601291` on commit `161b6b8`; every job was rejected before execution
  with `ci_quota_exceeded`, so it provides no code-test result;
- local static runtime behavior is therefore verified, while hosted Pages,
  strict CSP, cross-origin iframe behavior, reference-safe Registry insertion,
  and non-destructive Registry imports remain unqualified.

The current overall assessment is:

- **Static architecture:** approved; do not rewrite it.
- **Static local feature set:** working and well covered for its current scope.
- **Static production deployment:** not yet qualified.
- **Registry editor:** useful, but not yet safe enough for unreviewed real
  scientific metadata because of silent enrichment and incomplete dependency
  cloning.
- **Recommended strategy:** finish the focused safety/parity lots above rather
  than introducing React, a second UI, or a new backend.

## Current known limitations

- The static build requires Node.js and `npm ci --prefix web` at build time;
  the generated site does not require Node.js at runtime.
- The static graph bundle is deliberately loaded only after `Generate graph`.
- The Schema viewer uses a text-only JSON tree and sanitizes returned SVG before
  inserting it; keep hostile JSON/SVG browser coverage in place.
- Example completion is now explicit and confirmed by the user; future changes
  must not reintroduce enrichment during import, reload, or initial draft
  loading.
- Local Registry templates with dependencies are still cloned one item at a
  time and may retain dangling references until dependency-closure insertion
  is implemented.
- The shared ID utility now prevents ambiguous duplicate-ID migrations and
  reports the conflicting IDs to the user.
- Static Registry item validation uses generated per-kind Ajv validators.
- Static asset cache busting is tied to the content-aware build identifier for
  catalogues and dynamically imported bundles.
- Cross-origin iframe behavior and the final host's strict CSP headers still
  require automated qualification on GitLab Pages or a PhotoMechanics host.
- GitLab Pages publication is configured but still needs a successful GitLab
  pipeline and hosted smoke test. An explicit validation pipeline
  (`2859601291`, commit `161b6b8`) was created but all jobs were rejected with
  GitLab's `ci_quota_exceeded` runner failure before execution; this is an
  infrastructure quota issue, not a reported test or YAML error. Complete
  error-report parity and the hosted smoke test remain open.

## Useful checks

```bash
python scripts/dev.py build-docs
python -m pytest -q --ignore=tests/web/test_browser.py
python -m pytest -q tests/web/test_browser.py
```
