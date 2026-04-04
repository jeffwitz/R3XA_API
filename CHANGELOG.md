# Changelog

All notable changes to this project will be documented in this file.

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
- Documentation/meta: update Binder links to `v1.4.7`, clarify GitHub as the public repository with GitLab as upstream, quote the web extra install command, and refresh `docs/internal/PLAN_ACTION_HORS_SCHEMA.md`.
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
