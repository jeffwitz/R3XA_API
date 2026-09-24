# Use the R3XA WebUI

The [public WebUI on GitLab Pages](https://photomechanics.gitlab.io/R3XA_API/)
is the simplest way to create and inspect a document. It is a static site:
after its assets load, editing, JSON Schema validation, integrity checks,
Registry-item validation, and graph generation run in the browser. It does not
upload your R3XA JSON or experimental files to an application server.

## Create and save a document

1. On the home page choose an experiment profile, or **Generic** for an empty
   document.
2. In **Guided** mode, follow the profile steps. **Create prefilled workflow**
   inserts an illustrative example. Review and replace those values before
   describing a real experiment.
3. Use **Advanced** to add any kind in the current schema; use **Expert** to
   inspect or edit the canonical JSON.
4. Click **Validate**, then **Save JSON** to download the document.

All three modes edit one document. Switching mode does not discard fields.
**Load JSON** imports an existing document; the current draft is also kept in
this browser's local storage. Download a JSON file for a durable copy or to
move it to another browser or computer.

For `data_sets/list`, the folder picker can gather filenames, sort them
naturally, and fill `values` without uploading the selected files. The
form's reference fields select existing items by title; JSON stores their
IDs. Validation points to the fields that need attention.

## Inspect and edit the graph

Open **Schema viewer** to switch between a summary of the schema and the
current draft. Generate a graph with one of two browser backends:

- **Cytoscape.js** (default): pan, zoom, click a node to inspect its fields,
  choose **Edit fields**, and validate changes. Relationship fields offer
  existing document items as choices. After a valid edit the graph is
  regenerated.
- **Graphviz WebAssembly**: create a local SVG that can be saved or included
  in the standalone HTML export.

Graphviz computes the layout for both views. **Document** is the default
palette; **Classic** preserves the earlier colours. The default graph shows
all semantic relationships, including setting context such as `mesh`.
Choose **Dataflow only** for a simpler pipeline. The SVG and standalone HTML
exports are generated in the browser.

## Work with Registry items

The [Registry editor](registry_web.md) creates and validates one reusable
item at a time. Adding an item to the local Registry makes it available as a
template in this browser. It does not publish it to the separate
[R3XA_REGISTRY](https://gitlab.com/photomechanics/R3XA_REGISTRY) repository.
Export the item JSON if you want to share or submit it.

## Run locally or on another static host

From a source checkout with the project dependencies installed:

```bash
python -m pip install -e ".[web,dev]"
npm ci --prefix r3xa_web
python scripts/dev.py build-static-web
python scripts/dev.py serve-static-web --no-build --port 8080
```

Open `http://127.0.0.1:8080/`. The generated `dist/r3xa-webui/` directory
can also be copied to Apache, nginx, or another static file host. The host
does not need Python, Node.js, FastAPI, or a system `dot` executable. See
[Static WebUI build and deployment](static_web.md) for Pages, iframe, CSP,
and build details.

## Run the FastAPI development version

The same HTML and page scripts also work with the server runtime:

```bash
python -m pip install -e ".[web]"
python scripts/dev.py run-web --port 8002
```

Open `http://127.0.0.1:8002/`. This runtime sends validation and graph
requests to its local FastAPI server and offers additional Python graph
backends, including PyVis and Matplotlib. The native Graphviz backend
requires an optional system `dot`; the bundled WebAssembly backend does not.
For endpoint and maintenance details, see
[Developer workflow](dev_workflow.md).
