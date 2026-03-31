# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0.dev0] - 2026-03-31
- Typed models: add generated Pydantic workflow, direct typed item insertion in `R3XAFile`, and a runnable typed DIC pipeline example.
- Graphs: refactor web graph rendering into dedicated backends, extend non-regression coverage, and add NetworkX/Matplotlib fallback rendering.
- Notebook: add Binder-ready Marimo workflow with Graphviz-backed SVG rendering.
- Docs and tooling: add developer workflow guidance, Railway deployment notes, and repository hygiene targets for clean source archives.

## [1.0.0] - 2026-02-04
- First complete release (API + web UI + docs + examples).
- Web UI: editor, schema viewer, SVG graph generation.
- Notes: Graphviz `dot` required for SVG; JS viewer is vendored (no npm install).

## [0.1.0] - 2026-01-30
- Initial SDK release with core API, registry utilities, examples, and docs.
