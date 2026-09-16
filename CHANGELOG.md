# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- Settings and data sources can be built on their own: `new_testing_machine_setting(...)` mirrors `document.add_testing_machine_setting(...)` for every schema kind, with no document to invent. Add one later with `document.settings += [item]`.
- `new_item()` and `load_item()` return `R3XAItem` instead of a bare dictionary, so building, saving and loading an item all give the same object with `print()`, `validate()` and `save()`.
- `document.print()` lists authors by name rather than dumping their affiliation and ORCID.
- Item listings resolve references to the title they point at - `parent_data_sources`, `input_data_sets`, `attached_data_sources` and `mesh` - discovered from the schema, so a reference added later is resolved too. A standalone item still shows the identifier, having no document to resolve against.
- The `document` palette becomes the default and switches to solid fills with white text and no outline; the previous scheme is available as `palette="classic"`. Its settings fill is a darkened ochre so white text clears the WCAG AA contrast threshold.
- **Schema `2026.9.17`**: identifiers document their flat namespace with `stg-`/`src-`/`set-` examples (no pattern imposed, so existing ids stay valid); data sets gain an optional `data_origin` (`raw` | `derived`); the specimen mesh moves to `settings/specimen.mesh` and `dic_measurement.mesh` now references a setting id; `parent_data_sources` is no longer required on `data_sets/file` and `data_sets/list`.
- **Breaking, schema `2026.9.16`**: `authors` is an array of `{name, affiliation, orcid}` objects and `author_orcids` is removed. The former parallel array could not express "one ORCID per author" in the schema, so the invariant lived in a Python check and any other consumer accepted a mismatched document. It is now structural, and an affiliation became representable.
- Added the `author(name, affiliation=None, orcid=None)` helper, and `r3xa.author(...)` on the MATLAB side.
- `integrity_errors()` no longer carries the author/ORCID length check: the schema enforces it.
- Items returned by `R3XAFile` are now `R3XAItem` objects instead of bare dictionaries: they print, validate, save, load, and introspect their schema fields on their own. `R3XAItem` subclasses `dict`, so existing code treating items as dictionaries is unaffected.
- `R3XAFile` gains `summary()`/`print()` for the header and item titles, and `plot()` to render the item graph through the Graphviz, PyVis or NetworkX backends.
- Graph rendering accepts a `palette` argument, applied identically by every backend: `"default"`, or `"document"` for J-C. Passieux's ochre/crimson/teal scheme.
- `print(document)` and `print(item)` now show the same listing as `.print()`; `repr()` stays compact so collections remain readable.
- Generated model classes carry a docstring built from the schema (field type, description, required flag, permitted values) and are exported from `r3xa_api` directly when the `typed` extra is installed.
- `print()` renders values the way they read: units collapse to `1392 px`, constrained scalars and enumerations no longer leak their internal representation.
- Tests: guard the vendored schema against drift from `R3XA_SPEC`, and check that `r3xa_api/models.py` still matches the schema it is generated from.
- CI: add a `schema-sync` job that compares the packaged schema against a fresh `R3XA_SPEC` clone.

## [2.0.0rc1] - 2026-09-16
- Release candidate for the breaking R3XA schema/API line based on schema `2026.9.8`.
- Breaking schema alignment: authors are arrays, dataset provenance uses `parent_data_sources`, settings use `attached_data_sources`, dataset payloads use `data_type` and `values`, and file ranges use `col`/`rows`.
- No source or document compatibility with the pre-2.0 schema is provided on `develop`; migrate existing documents before using this release candidate.
- CI: validate the installed wheel with the current array-based `authors` header.

## [1.6.0.dev0] - 2026-04-04
- Web UI: harden Guided template review with per-field confirmation, profile-scoped state, dependency-based role recovery, persistent drafts, folder import for file sequences, profile-first home page, French/English interface labels, and browser workflow tests.
- Schema: synchronize non-empty top-level `title`, `description`, and `authors` constraints from `R3XA_SPEC`.
- Start the next development cycle after the `1.5.0` release.
- Documentation: realign the public MyBinder links on `develop` with the latest stable release tag (`v1.5.4`).
- Tests: make `tests/test_dev_cli.py` hermetic by simulating a project-local `.venv` instead of depending on the contributor's real environment.
- MATLAB: add the missing guided helpers, introduce canonical `add_list_data_set(...)` / `add_file_data_set(...)` names, and align the MATLAB reference page with the current v1.5 helper surface.
- Graphs: add a title-only rendering option across Graphviz, PyVis, NetworkX, the graph export script, and the web schema viewer for long datasource/dataset descriptions.

## [1.5.0] - 2026-04-04
- API stability: narrow the recommended top-level surface, add an explicit stability policy, and lock the guided-helper contract with public API tests.
- Documentation structure: expose the current Diátaxis roles more clearly by turning the notebook into the visible tutorial entry point, re-labeling major pages by purpose, and restructuring the main toctree into Tutorials / How-to / Explanation / Reference sections.
- Documentation/examples: fix the validation helper scripts, complete the examples index, clarify advanced compatibility helpers, prefer stable MyBinder links, and document the test matrix by optional extras.
- Documentation: add a public engineering contract page that explains the API and engineering choices from both user and developer perspectives.
- Examples/docs: fix the `qi_hu_from_json_literal.py` SHA-256 guard, add a regression test for the literal Qi Hu export, document shipped registry templates, and align `registry_usage.py` with the preferred `load_validated(...)` registry API.
- Typing: add a generated `r3xa_api/core.pyi` stub plus a `py.typed` marker so schema-driven guided helpers are visible to IDEs and static type checkers.
- Developer docs: explain how the generated `core.pyi` stub, `py.typed`, and the cross-platform `python scripts/dev.py generate-stubs` flow keep IDE signatures aligned with the schema-driven guided helpers.
- Repository hygiene: move internal working notes under `docs/internal/`, archive the PM-IDICS presentation under `docs/archive/`, and keep the public Sphinx build focused on user-facing pages.
- Documentation: realign the public MyBinder links on `develop` with the latest stable release tag (`v1.4.4`).
- Internal planning: refresh `docs/internal/PLAN_ACTION_API_ERGO.md` so completed ergonomics work and remaining v2 topics are tracked accurately.
- Documentation/meta: update Binder links to `v1.4.7`, clarify repository locations, quote the web extra install command, and refresh `docs/internal/PLAN_ACTION_HORS_SCHEMA.md`.
- Validation: lock `examples/essai-torsion.json` behind an automated validation test and update the internal traceability report now that the schema accepts the resolved generic-source fields.
- Developer tooling: replace the old shell wrappers and `Makefile` entry points with the cross-platform `python scripts/dev.py ...` runner, add `setup-dev` for one-shot contributor bootstrap, and verify the workflow from a fresh clone.

## [1.4.0] - 2026-04-03
- Start the next development cycle after the `1.3.0` release.
- API ergonomics: add `R3XAFile.load(...)`, `R3XAFile.loads(...)`, `R3XAFile.dump(...)`, and make `save(...)` validate by default.
- Registry ergonomics: add `Registry.load(...)`, `load_validated(...)`, `list(...)`, `iter_items(...)`, and `merge(...)`.
- Documentation: add a formal API ergonomics action plan and document the new load/edit/save and registry discovery workflows.
- Examples: add runnable `load_edit_save.py` and `registry_discovery.py` scripts to showcase the new ergonomic API entry points.
- Schema: allow optional `uncertainty` on `data_sources/generic` and sync the packaged runtime schema from `R3XA_SPEC`.
- Schema/API consistency: normalize `settings/generic.documentation` to lowercase `documentation` across the source schema, packaged schema, typed models, docs, and the torsion example.
- Core API: align `unit()` with the schema so only `unit` is required and generate guided helpers for all schema kinds, while keeping the image-set aliases.
- Tooling/tests: make `make generate-spec` use a configurable Python executable and extend coverage for the new helper layer and torsion validation.

## [1.3.3] - 2026-04-03
- Schema: allow optional `uncertainty` on `data_sources/generic`.
- Packaging: sync `r3xa_api/resources/schema.json` with the generated runtime schema from `R3XA_SPEC`.
- Documentation: regenerate the local API specification to reflect the generic data source update.
- Tests: lock the new generic `uncertainty` support with a targeted validation test.

## [1.3.2] - 2026-04-03
- Examples: add runnable `load_edit_save.py` and `registry_discovery.py` scripts to showcase the new ergonomic API entry points.

## [1.3.1] - 2026-04-03
- API ergonomics: add `R3XAFile.load(...)`, `R3XAFile.loads(...)`, `R3XAFile.dump(...)`, and make `save(...)` validate by default.
- Registry ergonomics: add `Registry.load(...)`, `load_validated(...)`, `list(...)`, `iter_items(...)`, and `merge(...)`.
- Documentation: add a formal API ergonomics action plan and document the new load/edit/save and registry discovery workflows.

## [1.3.0] - 2026-04-02
- Registry: add `save_item(...)`, `save_item_path(...)`, and `Registry.save(...)` to generate, validate, and write reusable registry entries directly from the Python API.
- Examples: add `examples/python/create_registry_camera.py` plus a validated camera example stored under `registry/data_sources/camera/`.
- Documentation: explain the registry creation workflow in the API, overview, and examples pages.

## [1.2.2] - 2026-03-31
- Documentation: point the public MyBinder notebook link to a stable tagged release instead of the moving `develop` branch.

## [1.2.1] - 2026-03-31
- Documentation: add a homepage installation matrix for core, typed, web, notebook, graph fallback, and full contributor setups.
- Documentation: make the local `.venv` workflow explicit and show how to create and activate it.
- Documentation: highlight that SVG graph generation requires the Graphviz executable `dot`, not just the Python package.

## [1.2.0] - 2026-03-31
- Typed models: add generated Pydantic workflow, direct typed item insertion in `R3XAFile`, and a runnable typed DIC pipeline example.
- Graphs: refactor web graph rendering into dedicated backends, extend non-regression coverage, and add NetworkX/Matplotlib fallback rendering.
- Notebook: add Binder-ready Marimo workflow with Graphviz-backed SVG rendering.
- Docs and tooling: add developer workflow guidance, Railway deployment notes, and repository hygiene targets for clean source archives.

## [1.1.0] - 2026-03-31
- Web UI: add fullscreen SVG graph viewing with zoom, pan, and Escape-to-close support.
- Web UI: improve graph action visibility so fullscreen and save controls appear only when relevant.
- Web UI: refine home page guidance and header branding for clearer navigation.
- Packaging: freeze the current `main` branch as the first post-`1.0.0` minor release.

## [1.0.0] - 2026-02-04
- First complete release (API + web UI + docs + examples).
- Web UI: editor, schema viewer, SVG graph generation.
- Notes: Graphviz `dot` required for SVG; JS viewer is vendored (no npm install).

## [0.1.0] - 2026-01-30
- Initial SDK release with core API, registry utilities, examples, and docs.
