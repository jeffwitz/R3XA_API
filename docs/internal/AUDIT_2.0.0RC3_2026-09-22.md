# Audit R3XA_API — develop (2.0.0rc3)

**Date:** 22 September 2026  
**Scope:** `R3XA_API/develop`, version `2.0.0rc3`, schema `2026.9.18`  
**Purpose:** preserve the complete audit as a reference for the corrective work leading to `2.0.0`.

## Verdict

The code has matured significantly since the 1.5.3 audit. It now relies on a single object model generated from the schema and on a serverless static WebUI. The test suite is real and was fully green in the audited environment. **It is not ready for a final 2.0.0 release**, for three verified reasons:

1. The wheel cannot be imported under Python 3.9, although `requires-python = ">=3.9"`.
2. CI is triggered neither on pushes nor on merge requests. According to `CLAUDE.md`, the latest develop pipeline was entirely rejected (`ci_quota_exceeded`).
3. Scientifically, a document the user has not filled in is declared “valid”: guided-profile example values and the `scale=1.0` added by default to every unit pass validation.

The third point is the most serious for a tool whose purpose is traceability. It is not a style issue: the software can produce false metadata and mark it valid.

## Scope and measurements

The analysis covers the `develop` archive supplied on 22 September, version `2.0.0rc3`, schema `2026.9.18`. The Python package is approximately 6,900 lines and the WebUI JavaScript approximately 5,400 lines. MATLAB was not executed for the original audit because no license was available at that time.

| Control | Result |
|---|---|
| Core + Web API pytest (3.9 editable, 3.10, 3.11, 3.13) | 211 passed, 2 skipped (3.9: 147 outside WebUI) |
| Coverage (`r3xa_api` + `web`, 3.11) | 88% of statements; `graphviz_setup` 36%, `reports` 55%, `_graph_core` 74% |
| `dev.py test-static-web` (static build + Playwright) | 47 passed |
| `tests/web/test_browser.py` (FastAPI + Chromium) | 21 passed (22 announced in `CLAUDE.md`) |
| `npm test` (Node.js) | 8 passed |
| Sphinx `-W` | Builds without warnings |
| Installed wheel, Python 3.13 | Import, validation and SVG WASM work |
| Installed wheel, Python 3.9 | **Import failure** (`FileNotFoundError` on `schema.json`) |
| mypy (not configured in the project) | 23 errors, including 4 in the published `core.pyi` stub |
| Ruff bug rules (`F`, `B`) | 8 findings besides unused imports; no linter configured |
| SHA-256 of `graphviz-12.2.1.wasm` | Matches the documented value |

The behaviours cited below were reproduced by scripts or in Chromium; they are not inferred solely from code reading. Untested points are explicitly identified.

## Scientific evaluation

The criterion used was: an R3XA file declared valid must contain only what the experimenter has asserted, remain unambiguous to a machine, and remain interpretable years later. Two findings violate the first point and are the most serious findings of this audit.

### S1 — Critical: example values are validated as data

The `dic_2d` profile pre-fills the author `R3XA Team`, the date `2026-09-01`, dimensions of 50 / 12.5 / 1 mm, and `manufacturer: "Not specified"`. Without any modification, this document passes `/api/validate` with `valid: true`, and nothing in the JSON distinguishes these values from user input. The `CHANGELOG` entry `1.6.0.dev0` announces “per-field confirmation”, but no such mechanism was found in the current `app.js`.

**Proposed correction:** display examples as *placeholders* rather than values, or mark every unconfirmed value and block export while any remain. Reject sentinel strings such as `Not specified` on required fields.

### S2 — Critical: `scale` is scientifically unusable

The schema defines `scale` as a factor relative to the standard system. However, examples, profiles and registry entries contain 62 occurrences of units with `scale: 1.0`, including mm, cm, ms and MPa·m^0.5. `unit()` in Python and `r3xa.unit()` in MATLAB write `scale=1.0` by default, thereby asserting a factor the user never supplied. Symbols are free-form and heterogeneous (`px`/`pixel`, `N*m`/`Pa.m^(1/2)`).

**Proposed correction:** decide in `R3XA_SPEC` whether to remove `scale` or define it precisely; correct all examples; adopt UCUM codes or QUDT IRIs; use `scale=None` by default in the SDK.

### S3 — Major: schema defaults are written into the file

`data_set_file(filename=..., col=1, rows=[0, None])` serializes `delimiter: ";"` even when the user did not provide it.

**Proposed correction:** serialize only explicitly set fields (`exclude_unset`) and let the consumer apply schema defaults.

### S4 — Major: documents have no version persistence

`version` is a `const`: a document created with schema `2026.9.17` is rejected by schema `2026.9.18`. Four versions were published in September (9.8, 9.16, 9.17, 9.18), the schema has no `$id`, and no migration tool exists. `STABILITY.md` says to “migrate explicitly”. A file deposited today with experimental data will be invalid after the next version.

**Proposed correction:** publish every schema version at a stable `$id`, validate a document against the version it declares, and provide a migrator between successive versions, tested on the examples.

### S5 — Major: a reference becomes stale after an ID is renamed

In memory, `ds.parent_data_sources` points to the new ID and `doc.integrity_errors()` returns an empty list. However, `to_dict()` emits the old ID and `doc.validate()` fails on an unknown reference. The two integrity checks contradict one another, while `save(validate=False)` writes the dangling reference without reporting it.

**Proposed correction:** resolve the ID at serialization time from the retained object, and keep only one integrity check operating on the JSON representation.

### S6 — Major: the SDK does not exactly follow the normative schema

The schema accepts an additional key in `unit` because it does not define `additionalProperties: false`, while `R3XAFile.from_dict()` rejects it with 20 Pydantic errors. Conversely, `doc.settings.append(camera)` and `doc.data_sources.append(duplicate)` are accepted without error; only `add()` checks duplicate IDs. This conflicts with the invariant that `R3XA_SPEC` is the sole authority.

**Proposed correction:** align `extra` with `additionalProperties` definition by definition; check `kind` and ID uniqueness in `R3XACollection`.

### S7 — Moderate: missing FAIR metadata

There is no checksum (for example SHA-256) for referenced files, making it impossible to verify that a referenced file is the one described. Nothing records the generating software or version. ORCID has neither a pattern nor a checksum, `license` is free text, and `uncertainty` is a simple unit without a type distinguishing standard uncertainty from expanded uncertainty or a coverage factor *k*.

**Proposed corrections for `R3XA_SPEC`:** checksum per file, a generator block, SPDX identifiers, and typed uncertainty in the sense of GUM.

### S8 — Moderate: non-compliant and non-reproducible MATLAB IDs

`random_id` generates 24 letters through `randi`, without the canonical `stg-`/`src-`/`set-` prefix. MATLAB initializes its random generator with the same seed at each startup, so two fresh sessions generate the same sequence of IDs.

The current binding now uses Java UUIDs and kind-specific prefixes. The
repository includes `matlab/test_smoke.m`, which also checks UTF-8 file output.
It was executed successfully with MATLAB R2025b Update 3 and a local MATLAB
license on 23 September 2026. This closes the local qualification gap; a
licensed MATLAB runner is still not assumed in the shared CI.

**Proposed correction:** generate IDs from a UUID (`java.util.UUID` or `matlab.lang.internal.uuid`) and add the canonical prefix without relying on the global random generator.

### Scientific strengths

- The schema is copied byte-for-byte from a pinned `R3XA_SPEC` commit and checked in CI.
- Dates are checked as real calendar dates.
- The WebUI ID migration refuses to guess when an ID is duplicated.

## Software engineering evaluation

The architecture is sound. The defects are concentrated in areas not exercised by local tests: the installed wheel, CI, published type information and the MATLAB binding.

### G1 — Critical: the wheel is broken under Python 3.9

`r3xa_api/resources/__init__.py` exists in the sources, but `packages = [...]` does not list `r3xa_api.resources`. It is therefore not embedded in the wheel, and `importlib.resources.files()` fails under Python 3.9 for this package that has become a namespace. The CI matrix cannot detect this because it installs editable packages, and the package job tests the wheel only under 3.12.

**Proposed correction:** use `packages.find`, stop treating Python 3.9 as unsupported without an explicit decision, and test the installed wheel on every matrix version.

### G2 — Critical: CI does not protect the branch daily

The current `workflow: rules` starts a pipeline only on manual/API triggers, release-candidate tags, or commit messages containing `[ci run]`. Pushes and merge requests do not start a pipeline. A final tag does not match the current regex, so the tag/version check will not run for the actual release. According to `CLAUDE.md`, the latest develop pipeline was rejected for quota. `registry-sync` follows `main` (a moving reference), contrary to the project rule requiring a pinned reference. There is no lint or type-check job.

**Proposed correction:** establish a lightweight MR pipeline (Python 3.10/3.13 tests plus wheel), use a private runner (LaMcube or PhotoMecA), cover final tags with the regex, pin `registry-sync`, and add Ruff plus mypy.

### G3 — Major: published type information is inaccurate

The package declares `py.typed`, but `core.pyi` redefines its own `R3XAItem`, which mypy sees as distinct from the class in `model_base`. Mypy reports 23 errors overall, including four in the published stub. In the stub, `R3XAFile.to_dict(self)` lacks `exclude_none`, `validate(self)` lacks `schema`, and `version` is typed as `Optional[str]` instead of the generated `Literal`. Registry signatures accept `R3XAItem` while advertising `Mapping`.

**Proposed correction:** generate the stub from the actual signatures, then run `stubtest` and mypy in CI.

### G4 — Major: a top-level `web` package is installed into site-packages

The distribution installs 26 files in a top-level `web` package, creating a collision with any distribution that already provides `web`, such as `web.py`.

**Proposed correction:** rename it to `r3xa_api.webui` or `r3xa_web`.

### G5 — Major: `validated=False` does nothing in Registry

`load_item` calls `R3XAItem.from_dict` with `validate=True`. Consequently, `get_item(..., validated=False)` raises on an incomplete item that should be loadable for repair. Validated paths are also validated twice.

**Proposed correction:** propagate the flag through `from_dict` and add a test loading an invalid item with `validated=False`.

### G6 — Moderate: the API does not match its documentation

`repr()` returns the complete multi-line record, up to 21 lines for a one-source list, while `docs/api.md` and the changelog announce a compact representation. `R3XAFile.merge()` raises `ValueError`. `to_model()` validates and then returns `self`. `typed_available` and aliases `get`/`get_validated` remain in a major version that breaks compatibility.

**Proposed correction:** use the 2.0 break to simplify and restore the documented representation.

### G7 — Moderate: the reference model is unnecessarily complex

Each reference is stored twice (the ID and the object), and `__getattribute__` is overridden on every access. This is the direct origin of S5; the measured cost is negligible, approximately 0.9 µs per access.

**Proposed correction:** store only the object or only the ID, and derive the other representation during serialization.

### G8 — Moderate: FastAPI is exposed without safeguards

`POST /api/graph` renders an unvalidated payload without a body-size limit or a timeout on `dot`; the WASM execution has no fuel or epoch limit. When deployed publicly (the supplied Railway configuration), this is vulnerable to a trivial denial of service. An item without an ID causes a 500. `create_app()` is instantiated twice during ASGI import.

**Proposed correction:** validate before rendering, bound body size and execution time, or remove FastAPI once static parity is established.

### G9 — Moderate: license notices are missing

The static site redistributes `graphviz-12.2.1.wasm` (EPL-1.0), generated Ajv code and Cytoscape (MIT), but contains no `THIRD_PARTY_NOTICES`. Lot 8 of `CLAUDE.md` requires this and is marked as completed, but the file is absent from the build. `r3xa_web/package.json` declares ISC for a project declared GPL-2.0-or-later.

**Proposed correction:** generate notices in the build and test their presence. State explicitly that the WASM program is a separate EPL/GPL aggregate.

### G10 — Moderate: MATLAB is never executed in CI

Its 18 guided helpers, one per schema kind, are handwritten, and CI validates only a committed JSON file. Drift after a schema change can therefore go unnoticed. `fopen(filepath, "w")` followed by `fwrite(..., "char")` without explicit UTF-8 encoding risks altering µm, °C and accented names on Windows.

**Proposed correction:** add an Octave CI job, use `fopen(..., "w", "n", "UTF-8")`, and generate helpers from the schema.

### G11 — Minor: repository hygiene

The repository contains 28 MB of Marimo exports (677 generated JavaScript bundles) in `docs/figures`, four copies of the 3,755-line Qi Hu JSON, and internal DOCX/PDF files. `DEMANDES_JC.md`, containing a video-conference link, is at the root of a public repository. There is no linter or formatter configuration.

**Proposed correction:** remove exports and internal notes from the source repository, or use Git LFS/Pages; add `[tool.ruff]`.

The use of `exec()` by guided helpers remains acceptable. However, 2.0 is a good time to replace it with `inspect.Signature`: it provides the same introspection without generating code as strings.

## Points to preserve

- **One source of truth.** Models, stubs, specification and UI catalogues derive from the schema, and tests detect drift between `models.py` and `schema.json`.
- **A well-designed static WebUI.** No remote runtime dependency, strict CSP tested, hostile JSON and SVG covered, Ajv validators by kind, Python/JavaScript validation parity, and content-dependent build IDs.
- **Traceable Graphviz WASM.** The binary is pinned and hashed, and the same WASI-compiled Graphviz binary is used in Python and the browser.
- **Substantial tests.** 287 tests overall, including 62 Playwright scenarios covering both runtimes, and 88% coverage.
- **Registry data-safety fixes.** No enrichment at import, cautious ID migration, and dependency closure.
- **Abundant, up-to-date documentation.** Sphinx builds without warnings.

## Prioritized action plan

The rejection criteria are operational: each lot is complete when the stated test exists and passes.

### Blocking for a final 2.0.0

1. **G1 — packaging.** The installed wheel imports and validates on every matrix version.
2. **G2 — CI.** A pipeline runs on every MR targeting `develop`, and the final tag triggers the tag/version check.
3. **S1 — example values.** A document generated from a profile without modification is refused at export or marked as unconfirmed, with a Playwright test in both runtimes.
4. **S2 + S3 — do not write what the user did not state.** `unit(unit="mm", value=30).to_dict()` must not contain `scale`, and `data_set_file(...)` must not contain `delimiter` unless it was supplied. The semantics of `scale` must be decided with JC in `R3XA_SPEC`.
5. **S5 — references.** Renaming a source ID after linkage must produce coherent JSON, with one integrity check remaining.

### Before broad release

6. **S4 — versions.** Add a `$id` per schema version, validate according to the declared version, and provide a migrator from `2026.9.x` to `2026.9.18`, tested on the 1.x examples.
7. **G3 + G4 + G5 + S6.** Make the stub faithful, verify it with `stubtest`, rename the web package, fix the `validated` flag, and align strictness with the schema.
8. **G9.** Add `THIRD_PARTY_NOTICES` to the static build and test it.

### Afterwards

9. **S7.** Propose file checksums, generator metadata, ORCID validation, SPDX and typed uncertainty in the schema.
10. **G6, G7, G8, G10, G11, S8.** Simplify the API and references, add FastAPI safeguards or remove FastAPI, add the Octave job, fix MATLAB identifiers, and reduce repository weight.

## Decisions for the working group

The working group must decide:

- the semantics and default behaviour of `scale`;
- the compatibility and migration policy between schema versions;
- whether Python 3.9 remains supported.

The working decision for this hardening phase is to leave `scale` unchanged
and explicitly defer S2. S7 (additional FAIR metadata proposals) is also out
of scope for this release. Until the schema-version policy is recorded in
`R3XA_SPEC` and reflected back into `R3XA_API`, this audit remains the baseline
for the 2.0.0 hardening work.

## Status and interpretation after the audit

### S1 clarification: profiles are intentional example templates

The initial S1 recommendation to replace profile values with placeholders is
not the intended WebUI design. A non-generic profile is deliberately a complete,
realistic example that the user can reuse as a starting point. If the user
explicitly chooses “Start from this example”, exporting a valid document is
legitimate; the values are not silently presented as measurements from the
user's experiment.

The corrective action is therefore presentation, not removal of the examples:

- the Home profile cards say that they start from a complete illustrative
  example;
- the Guided editor displays an “Example template” banner naming the selected
  profile;
- the banner states that every value remains editable and must be adapted to
  the real experiment;
- the Generic profile remains the explicit empty, schema-driven workflow.

This resolves the ambiguity identified by S1 without adding per-field
confirmation badges or blocking valid example documents. A future audit should
distinguish an intentionally selected template from an unannounced fabricated
default.

### Corrections started after the audit

- **G1:** `r3xa_api.resources` is now packaged explicitly, the wheel smoke
  check includes the schema resource, and a regression test checks resource
  access through `importlib.resources`. The wheel was rebuilt locally and its
  schema, UI catalogue and Graphviz WASM resources were verified. CI now has an
  installed-wheel smoke matrix for Python 3.9–3.13, subject to the project's
  explicit/manual pipeline policy.
- **G5:** `load_item`, `load_item_path`, `Registry.get`, and `Registry.load`
  now accept a validation switch. `Registry.get_item(validated=False)` really
  loads incomplete items without validating them, while validated paths avoid
  the previous duplicate validation. A regression test covers repair loading.
- **S3:** the public `data_set_file()` helper no longer serializes the schema's
  implicit delimiter when the caller did not provide one; an explicit
  delimiter is preserved and both behaviours are tested.
- **S5:** renaming a document-bound item now updates the retained wire IDs of
  its references. A regression test verifies object identity, integrity and
  serialized JSON after a source rename.
- **G9:** the static distribution now contains `THIRD_PARTY_NOTICES.txt` and
  the complete Graphviz license text, with a build test covering Ajv,
  Cytoscape and Graphviz notices. The WebUI package metadata now declares the
  project license consistently.
- **G3:** the generated `core.pyi` now re-exports the shared
  `r3xa_api.model_base.R3XAItem` instead of defining an incompatible duplicate,
  and the generated `R3XAFile` signatures match the inherited runtime methods.
- **G8:** FastAPI JSON endpoints now reject bodies over the configurable
  `R3XA_MAX_JSON_BODY_BYTES` limit (5 MiB by default), with API regression
  coverage. The Python Graphviz WebAssembly backend now also consumes a
  configurable deterministic fuel budget through `R3XA_GRAPHVIZ_WASM_FUEL`.
  Native `dot` rendering now has a configurable subprocess timeout through
  `R3XA_GRAPHVIZ_NATIVE_TIMEOUT_SECONDS`. The `/api/graph` endpoint validates
  the complete R3XA document, including integrity references, before invoking
  a renderer and returns a structured `422` report for invalid documents.
- **G4:** the WebUI package is now named `r3xa_web` instead of the generic
  top-level `web`. Runtime commands, wheel contents, deployment manifests,
  tests, and documentation were updated; the installed wheel now exposes only
  the non-colliding namespace.
- **S6:** document collections reject direct insertion of an item from
  another schema section and reject duplicate IDs, including when the same
  object is appended directly instead of going through `add_*`. Generated
  Pydantic models now follow the `additionalProperties` policy of every
  settings, data-source, and data-set definition; a generated-model test
  checks the complete schema taxonomy and a code-generation test covers
  explicit `true`, explicit `false`, and the omitted default policy.
- **G6:** `repr(item)` now uses Pydantic's compact representation, while
  `str(item)` and `item.print()` keep the readable multi-line summary.
  `merge()` reconstructs the concrete model class, including `R3XADocument`.
  The redundant `R3XAFile.to_model()` conversion, the meaningless
  `typed_available` flag, and the `Registry.get`/`get_validated` aliases have
  been removed; generated stubs, examples, tests, and documentation now use
  the object-first 2.0 API directly.
- **G7:** bound references now use the object-valued model field as their
  in-memory source of truth. Wire IDs are derived during serialization, so
  renaming a bound item cannot leave stale IDs in `to_dict()`; schema-scoped
  reference metadata remains the source for reference resolution.
- **G2 (partial):** merge-request pipelines now run a lightweight Python
  smoke suite and an installed-wheel smoke test. The full Python matrix,
  lint, browser, static-WebUI, Registry, documentation, and Pages jobs remain
  explicit/manual or release-triggered to avoid consuming the project's
  constrained runner quota. Release and release-candidate tag matching now
  covers both forms, and the Registry synchronization ref is pinned.
- **S6 (continued):** direct collection insertion enforces section and ID
  invariants. The generated base model follows JSON Schema's default
  permissive policy when a definition omits `additionalProperties`, while
  generated definitions with an explicit `false` or `true` policy retain it.
  The complete policy is now checked against the schema copied from
  `R3XA_SPEC`; no local schema edit was made.
- **S8:** MATLAB item creation now generates UUID-based, kind-specific
  `stg-*`, `src-*`, or `set-*` identifiers instead of relying on the repeatable
  global random stream. MATLAB file output now requests UTF-8 explicitly. The
  reusable `matlab/test_smoke.m` qualification passes locally with MATLAB
  R2025b; shared CI remains independent of a proprietary MATLAB runner.
- **G11 (partial):** Ruff is now configured for the maintained Python source
  and tests, with the generated stub files explicitly excluded. The configured
  bug and import checks pass locally and run in the explicit full CI pipeline;
  repository-size and internal-document cleanup remain open.

S2 is intentionally deferred without changing `scale`. S4 is intentionally
deferred because R3XA currently has no external document users; versioned
schema migration can be introduced when that policy becomes necessary. S7 is
intentionally excluded from this release. This repository must not edit the
vendored schema to resolve decisions that belong in `R3XA_SPEC`.
