# Web UI (R3XA_API)

The current development runtime is the FastAPI WebUI described on this page.
The static WebUI is available as a second runtime from `dist/r3xa-webui/`,
without a Python backend at runtime. Its implementation and deployment status
are tracked in [`static_web.md`](static_web.md).

For deployment without a backend, follow the static build, GitLab Pages, and
iframe instructions in [`static_web.md`](static_web.md).

This section documents the optional web UI included in the repository.

## Architecture choices

The web UI is split into two layers:

- **`r3xa_api/webcore/`**: pure Python helpers used by the web API (validation reports, resolved schema catalogue, UI profiles, schema summary, and the Graphviz, PyVis, and NetworkX/Matplotlib graph backends).
- **`web/`**: FastAPI app + HTML/JS/CSS templates and static assets.

This keeps the **core API** (`r3xa_api`) as the single source of truth, while the web UI remains a thin consumer of that API.

The editor stores one canonical R3XA JSON document. Its Guided, Advanced, and
Expert views are different presentations of that document, not separate data
models. The normative schema is resolved by Python; presentation rules and
experience profiles are independent resources under
`r3xa_api/resources/ui/`. The JavaScript renderer must consume the catalogue
instead of duplicating the R3XA `kind` taxonomy.

## Install & run

The web UI is included in the PyPI package. Install it with:

```bash
python -m pip install "r3xa-api[web]"
python -m uvicorn web.app.asgi:app --host 127.0.0.1 --port 8002
```

From a source checkout, the repository runner is also available:

```bash
python -m pip install -e ".[web,dev]"
python scripts/dev.py run-web --port 8002
```

Open: `http://127.0.0.1:8002/`

The standard installation includes the Python dependencies for the bundled
Graphviz WebAssembly SVG backend. The `web` extra adds FastAPI, interactive
PyVis HTML, and static NetworkX/Matplotlib support. Select `graphviz-wasm` to
render SVG without installing the system `dot` executable.

> Note: the native `graphviz` SVG backend requires the **Graphviz executable** (`dot`).
> The default `graphviz-wasm` backend uses the bundled Graphviz WASI module and
> does not require `dot`.
> The schema viewer JS is vendored; **no `npm install` is required** for normal usage.

### Graphviz requirement

The base package installation includes the Python `graphviz` wrapper, but
`pip install -e ".[web]"` does **not** install the Graphviz executable itself.

> **Windows and macOS users:** no system installation is required for the
> default WebAssembly SVG backend. Install Graphviz only if you explicitly
> select the native `graphviz` backend. Run `r3xa-ensure-graphviz` from the
> activated virtual environment; on Windows it uses WinGet or Chocolatey and
> on macOS it uses Homebrew. Verify the result with `dot -V`.

For `POST /api/graph?backend=graphviz` and native SVG viewer/export to work, `dot` must be available on the system:

- Linux: `sudo apt-get install graphviz`
- macOS: `r3xa-ensure-graphviz` installs it through Homebrew
- Windows: `r3xa-ensure-graphviz` installs it through WinGet, or Chocolatey when WinGet is unavailable

The installer is explicit and only runs when requested. It does not modify the system during a normal package install.
From a source checkout, use `python scripts/dev.py ensure-graphviz` instead.

Quick check:

```bash
dot -V
```

## What you can do

- **Editor** (`/edit`)
  - Start from the home-page choice of experimental workflows.
  - Edit a JSON draft (header + settings + data_sources + data_sets).
  - Use Guided, Advanced, or Expert presentation modes.
  - Choose an experience profile in Guided mode.
  - Validate the JSON (inline report).
  - Save/load JSON to/from disk.
  - Draft state is stored locally (browser storage) and survives a WebUI server restart.
- **Registry editor** (`/registry`)
  - Choose a registry `kind` from the current schema catalogue.
  - Edit the item through a schema-generated form or the synchronized Expert JSON view.
  - Receive local JSON/schema lint feedback and save the item locally.
  - Save valid items as browser-local templates reusable from the document editor; they are never published automatically. The static runtime keeps validation and storage local.
  - See dedicated page: [Registry Web Editor](registry_web.md).
- **Schema viewer** (`/schema`)
  - Inspect the schema summary or the current draft.
  - Generate a graph from the current draft with Graphviz (SVG), PyVis (interactive HTML), or Matplotlib (PNG).
  - Optional: hide node descriptions and keep titles only.
  - Choose the graph palette: **Document** (the R3XA document palette) or **Classic** (the legacy palette).
  - Export a fully inlined standalone HTML report (Graphviz SVG + JSON) shareable without server.

## Editor modes

The editor offers three views over the same JSON document:

- **Guided**: choose an experience profile and follow a checklist of recommended objects. Technical fields are hidden unless they are required by the schema or supplied by the selected example profile; the generic object forms are replaced by the current business step.
- **Advanced**: add any schema-discovered object and edit user-facing fields without opening the raw JSON editor.
- **Expert**: expose every field, including `id`, `kind`, references, and the canonical JSON editor.

The Guided view intentionally shows only the profile checklist and document
actions. The Advanced view shows the schema-driven forms, while the Expert view
also exposes the raw JSON editor. Switching views changes visibility only; it
does not rebuild or discard the canonical document.

Profiles can expose a **Create prefilled workflow** action. It starts a complete
example document whose Guided fields already have editable values, making it
possible to inspect the workflow and validate it immediately before replacing
the illustrative metadata with experimental values. Additional profile values
are displayed as ordinary editable fields. They are examples only: the editor
does not require acknowledgements or block saving, so users can freely adapt
them for demonstrations, tests, or real experiments.

The home page is the normal entry point: it presents the available experiment
profiles before creating a document. Opening `/edit` directly starts with the
Generic profile, so no experimental technique is assumed.

In Guided mode, validation uses short corrective messages such as “Add the
required field” or “Choose one of”. Advanced and Expert modes keep the original
JSON Schema message available for technical diagnosis.

When an error points to a visible field, its message is rendered as a link-like
action. Selecting it scrolls to and focuses the corresponding editor control;
errors for hidden or unknown paths remain readable without being discarded.

Changing mode never rebuilds the document from a simplified model. Fields that a
profile does not display remain in the JSON and are preserved when the user
switches views.

Guided profiles can add a real sequence of steps and business questions. A step
can be conditional on an object or value already present in the document, so a
question only appears when it is relevant. Previous/Next navigation changes the
current view, not the underlying document. The Next button stays disabled until
the current step's explicitly required profile questions are completed; a
kind-specific step also requires its object to exist. Full JSON Schema validation
remains the final authority.

The Generic profile is intentionally not a prefilled experiment. It is the
schema-driven fallback for an experiment that does not match an available
profile, for an expert starting from an empty document, or for a document that
needs a combination of objects not covered by a profile. It asks for the
document metadata and exposes every schema-discovered kind in each collection
step. The **Create prefilled workflow** action is hidden for this profile because
there are no example values to insert.

Opening the Custom profile from the home page starts a new empty document. If it
is selected from a populated experimental workflow, the editor asks for
confirmation before discarding the existing settings, sources, and data sets.
Switching between experimental profiles does not discard the current document.

For `data_sets/list`, the Guided editor offers a folder picker. It reads the
selected filenames from the browser, sorts them naturally (`image_2` before
`image_10`), and replaces the dataset file list. This avoids manually entering
long image sequences.

The interface provides an English/French language switch. Presentation labels
are supplied by `resources/ui/messages.json`; schema validity and profile data
remain independent from translations.

Profile relationships are pre-filled when a Guided object is first created, but
an explicit selection or an explicit empty selection is preserved when later
objects are added. Optional dependencies therefore remain under the user's
control. The available prefilled profiles cover camera
acquisition, tabular measurements, mechanical tests, torsion tests, fatigue tests
with overload, X-ray tomography with DVC, in-situ tensile tests, 2D DIC, and
stereo-DIC workflows. The Stereo-DIC profile uses `settings/stereorig` to
associate two cameras with one stereo rig, then links the left and right image
datasets to stereo-DIC processing. The Generic profile remains available for
free-form schema-driven construction.

The stereo-rig association identifies which cameras belong to the same rig;
it does not by itself encode a timing or lighting-synchronization protocol.

Profiles also describe data dependencies explicitly. When a Guided item is
created, the editor links the corresponding identifiers instead of leaving the
collections as unrelated lists. For example, the **Tensile test with 2D DIC**
profile builds two explicit chains: `Camera → Images → DIC processing →
2D DIC displacement file` and `Universal testing machine → Machine test
files`. Both files are final datasets. The tomography profile extends the same
idea to `Tomograph → Projections → Reconstruction → Volume → DVC → DVC
displacement`. Camera, machine, and specimen are root objects without
antecedents. The data-flow edges remain the schema-defined
`parent_data_sources` and `input_data_sets` identifiers.

Graph exports include settings as root nodes. A dashed edge connects a setting
to each of its `attached_data_sources`, making the machine and specimen
context visible alongside the source/dataset dependency graph.

## Developer contract

The data flow is deliberately one-way for metadata and shared for document state:

```text
schema.json → schema catalogue → UI resources/profiles → JavaScript views
                                         ↘ canonical R3XA JSON ↗
```

`schema.json` defines validity. `r3xa_api/webcore/schema_catalog.py` resolves
schema references and combinators for the frontend. `resources/ui/default.json`
defines presentation levels, while `resources/ui/profiles/*.json` defines
experience-oriented recommendations and steps. A new schema `kind` should be
discoverable in Advanced mode without adding a hardcoded frontend template.

When adding a profile, reference only kinds present in the schema catalogue and
keep business wording in the profile. Profile questions reference schema fields
but may replace their technical label with a user-facing question. The loader
checks these kind, section, field, and step references when the API starts. Do
not duplicate validation rules or create a second document model in JavaScript.

Browser workflows are covered by Playwright tests in `tests/web/test_browser.py`.
Run `python -m pytest -q tests/web/test_browser.py` with Chromium available, or
set `R3XA_CHROMIUM_EXECUTABLE` to its executable path.

## Links

- Source repo: <https://gitlab.com/photomechanics/R3XA_API>
- Original upstream repository: <https://gitlab.com/photomechanics/r3xa>
- Documentation: <https://r3xa-api.readthedocs.io/en/latest/>

## API endpoints

- `POST /api/validate` → validation report
- `GET /api/schema` → raw schema
- `GET /api/schema/summary` → schema summary
- `GET /api/schema/catalog` → resolved schema catalogue for the editor
- `GET /api/ui` → presentation rules and experience profiles
- `GET /api/profiles` → experience profiles only
- `GET /api/graph/backends` → supported graph backend names.
- `POST /api/graph?backend=graphviz&show_description=true&palette=document` → native Graphviz SVG using `dot`.
- `POST /api/graph?backend=graphviz-wasm&show_description=true&palette=document` → Graphviz WebAssembly SVG (standard dependency; no system `dot`).
- `POST /api/graph?backend=pyvis&show_description=true&palette=document` → interactive PyVis HTML.
- `POST /api/graph?backend=matplotlib&show_description=true&palette=document` → static Matplotlib PNG.
- `backend` defaults to `graphviz-wasm`; `palette` accepts `document` (recommended) or `classic` (legacy).
