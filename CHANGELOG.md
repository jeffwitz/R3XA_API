# Changelog

All notable changes to this project will be documented in this file.

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
