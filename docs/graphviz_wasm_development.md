# Graphviz WebAssembly development

This page documents the Graphviz WebAssembly backend used by R3XA_API. It is
intended for contributors maintaining the graph backends, the Python package,
or the static WebUI. It complements the user-facing installation information
in `README.md` and the operational workflow in `dev_workflow.md`.

## What this component is

The project sometimes refers to the “Graphviz WebAssembly plugin”. Strictly
speaking, it is not a Graphviz plugin. It is a WebAssembly/WASI build of the
Graphviz `dot` engine, wrapped with a small C-compatible R3XA ABI:

```text
R3XA graph model
        ↓
shared DOT generator
        ↓
Graphviz dot compiled for WASI
        ↓
SVG
```

The packaged artifact is:

```text
r3xa_api/resources/graphviz/graphviz-12.2.1.wasm
```

The current artifact is 1,263,220 bytes and has SHA-256:

```text
7e7e38b14253339d9007004039f16ac13b59f6a1dae06cb0f8700f0e93f07d2a
```

The binary is based on the Graphviz 12.2.1 release from the
[upstream Graphviz repository](https://gitlab.com/graphviz/graphviz). It
contains the `dot` layout and SVG rendering path needed by R3XA_API, rather
than a complete native Graphviz installation with every command and plugin.
The upstream Eclipse Public License is shipped next to the binary in
`r3xa_api/resources/graphviz/LICENSE-Graphviz.txt`.

## Why Graphviz and `dot` matter to R3XA

Graphviz is not used only as a final image exporter. Its layout is the common
geometric reference for the R3XA graph backends.

R3XA documents are directed dependency graphs. They contain settings, data
sources, and data sets, with relationships such as:

```text
setting → data source → data set → data source → data set
```

For these graphs, `dot` provides several properties that are difficult to
reproduce consistently with a hand-written layout:

- hierarchical top-to-bottom ranking;
- ordering of nodes within each rank;
- reduction of edge crossings;
- routing of arrows between nodes rather than through node interiors;
- layout that accounts for the size of labels and shapes;
- stable handling of branches, merges, and several independent chains.

The shared Python graph model first creates the R3XA relationships and DOT
labels. `compute_graphviz_positions()` then asks the bundled WASM engine for
positions. NetworkX/Matplotlib and PyVis use those positions, while the
Graphviz backends use the same DOT representation to produce SVG directly. The DOT
model now includes all schema-declared semantic relations by default: solid gray
edges represent dataflow, while dashed ochre edges represent setting/context
relations such as `attached_data_sources` and `mesh`. This semantic graph model is
shared by Graphviz, Graphviz WASM, PyVis, and Matplotlib; `relations="dataflow"`
selects the reduced pipeline view.
Consequently, removing `dot` from the layout path would not merely change the
appearance of one backend: it would make the backends disagree about the
geometry of the same experiment.

The native `graphviz` backend remains useful when a system `dot` is installed,
but it is not a suitable mandatory dependency for distribution. A user would
otherwise need to install a platform-specific executable before the SDK,
notebook, or WebUI could produce the project’s canonical layout.

## Why compile Graphviz to WASI

WASI gives us a portable executable format with a small, explicit system
interface. The same module can be distributed in the Python wheel and copied
into the static WebUI:

```text
Python SDK       → wasmtime → graphviz-12.2.1.wasm
Static WebUI     → browser WebAssembly + local WASI adapter
```

This has practical distribution benefits:

- no system `dot` installation for the default backend;
- no platform-specific Graphviz package manager logic for Linux, macOS, and
  Windows users;
- no subprocess invocation from the Python WebAssembly backend;
- no server or remote rendering service for the static WebUI;
- the Python and browser runtimes use byte-for-byte the same Graphviz engine;
- the static site can be copied to GitLab Pages, Apache, nginx, or another
  ordinary HTTP server;
- the graph engine can be loaded lazily only when the user asks for a graph.

WASI does not mean that Python is embedded in the browser. The browser loads
the local WebAssembly binary directly. Python uses the `wasmtime` package to
instantiate the same binary. The browser adapter implements only the WASI
calls required by this build; it does not provide a general-purpose operating
system or filesystem.

## WebAssembly, WASI, and compiling C

WebAssembly (Wasm) is a portable binary instruction format and execution
environment. A Wasm module has linear memory and explicitly declared imports
and exports. It is not a native executable for Linux, macOS, or Windows, and
it does not automatically have access to a host filesystem, process table, or
network. Those capabilities must be provided by the host runtime.

WASI is the system interface designed for WebAssembly modules that need more
than pure computation. It standardises capabilities such as arguments,
environment variables, file descriptors, clocks, randomness, and filesystem
access. A WASI module can therefore run outside a browser while remaining
isolated from the host. In this project we deliberately provide only the WASI
subset needed by Graphviz; no user files are mounted and no network access is
provided.

The C compilation model is consequently familiar:

```text
C source
  ↓  clang/LLVM with a wasm32-wasi target
Graphviz objects + WASI libc + linker
  ↓
WASI WebAssembly module
  ↓
host runtime: wasmtime or the browser's WebAssembly engine
```

The C code is not translated into JavaScript. The compiler produces Wasm
machine code, while WASI supplies the small platform boundary that C programs
normally obtain from an operating system. This is particularly useful for
Graphviz because its mature C implementation can be reused in a browser and
inside a Python wheel without maintaining three platform-specific native
builds.

### Relation to Python's WebAssembly work

This direction is becoming part of the Python platform and packaging
conversation, but it is important to describe it precisely. There is not one
accepted PEP saying that every Python package should embed arbitrary WASI
binaries. The relevant official work is complementary:

- [PEP 816 — WASI Support](https://peps.python.org/pep-0816/) defines the
  expected WASI/WASI SDK support for CPython releases;
- [PEP 11 — CPython platform support](https://peps.python.org/pep-0011/)
  records WASI as a supported CPython platform, with tier 2 support beginning
  in Python 3.13;
- [PEP 783 — Emscripten Packaging](https://peps.python.org/pep-0783/)
  proposes a `pyemscripten` platform tag for binary packages targeting the
  Emscripten/Pyodide runtime, which is related to WebAssembly but is not the
  WASI target used here;
- [PEP 776 — Emscripten Support](https://peps.python.org/pep-0776/)
  describes CPython's Emscripten port and is likewise distinct from WASI.

The practical conclusion for R3XA_API is narrower and already useful today:
a wheel may ship a WASM file as package data, and a runtime such as `wasmtime`
can execute it portably. Python's increasing first-class support for WebAssembly
makes this approach more conventional, but R3XA_API is not relying on a future
standard packaging tag. The existing wheel uses ordinary package-data rules,
while the static site copies the same local file into its assets.

## The R3XA wrapper ABI

The upstream Graphviz command-line interface is not a convenient library API
for a Python package or a browser. The WASM artifact therefore exposes a thin
wrapper around the Graphviz rendering operation.

The exports used by both runtimes are:

| Export | Role |
|---|---|
| `memory` | Linear WebAssembly memory used for input and output buffers |
| `malloc(size)` | Allocate a buffer inside the module |
| `free(pointer)` | Release a buffer allocated by the module |
| `r3xa_graphviz_render(input, length, output_length)` | Render DOT input and return a pointer to SVG output |
| `r3xa_graphviz_last_error()` | Return a pointer to the last rendering error string |

The call sequence is:

1. Build a UTF-8 DOT string from the R3XA document.
2. Allocate a NUL-terminated input buffer with `malloc`.
3. Allocate a four-byte output-length buffer.
4. Call `r3xa_graphviz_render(input_pointer, input_length, length_pointer)`.
5. Read the returned SVG bytes from `memory`.
6. If the result pointer is null, read `r3xa_graphviz_last_error()` and raise a
   graph-specific error.
7. Release the result, input, and length buffers with `free`.

The Python implementation of this protocol is in
`r3xa_api/webcore/_graph_graphviz_wasm.py`. The browser implementation is in
`web/static/graph-runtime.mjs`. Keeping the ABI small is important: it avoids
duplicating Graphviz’s internal data structures in either runtime.

## What was implemented in R3XA_API

The integration was done in several steps.

### 1. Add a bundled WASI artifact

The Graphviz 12.2.1 WASI binary was added as package data under
`r3xa_api/resources/graphviz/`. The package also includes the upstream license
and provenance README. `pyproject.toml` includes the WASM and documentation
files in the wheel.

### 2. Add the Python runtime adapter

The Python adapter:

- loads the module through `importlib.resources`, so it works from an installed
  wheel;
- creates a `wasmtime.Engine`, `Store`, and WASI configuration;
- defines the WASI imports and instantiates the module;
- passes DOT through the wrapper ABI;
- returns SVG bytes and converts module failures into useful `RuntimeError`
  messages.

The public backend name is `graphviz-wasm`. It is the default graph backend and
does not invoke the system `dot` executable. The native `graphviz` backend is
kept as an explicit alternative.

### 3. Reuse the module in the static WebUI

The static build copies the exact package binary into `dist/r3xa-webui/assets/`
(`scripts/dev.py`, `build-static-web`). The browser adapter:

- fetches only this local asset;
- instantiates it with `WebAssembly.instantiate`;
- supplies the minimal `wasi_snapshot_preview1` functions required by the
  module;
- uses the same wrapper exports and memory protocol as Python;
- returns SVG directly to the existing graph viewer.

The binary is loaded only after the user requests graph generation. If loading
or rendering fails, the editor, validation, import, export, and Registry views
remain usable and the user receives a graph-specific error.

### 4. Keep graph semantics shared

The browser does not implement a second R3XA graph model. The Python and
browser DOT generators use the same relationship conventions, node roles,
labels, and palette data. The current graph roles are:

```text
settings     → hexagon
data_sources → ellipse
data_sets    → rectangle
```

The WASM layout is also used by the Python NetworkX/Matplotlib and PyVis
backends for positioning. This is why the WASM backend is part of the standard
SDK rather than being treated as a WebUI-only convenience.

## Code written specifically for R3XA_API

The Graphviz layout engine itself is not reimplemented in this repository. The
upstream Graphviz release provides the C layout and rendering engine; R3XA_API
adds the integration layer that turns an R3XA document into DOT, executes the
local module, and exposes the result to each consumer.

The repository-specific pieces are:

| Path | Responsibility |
|---|---|
| `r3xa_api/webcore/_graph_core.py` | Builds the R3XA graph model, identifies settings, sources, intermediate objects, and final datasets, and shares palette/role semantics. |
| `r3xa_api/webcore/_graph_graphviz.py` | Builds the Graphviz DOT representation and contains the native Graphviz backend integration. |
| `r3xa_api/webcore/_graph_graphviz_wasm.py` | Python `wasmtime` adapter: loads the packaged module, configures WASI, implements the `malloc`/`free`/render ABI, reads SVG, and extracts Graphviz positions. |
| `web/static/graph-core.mjs` | Browser-side equivalent of the R3XA graph model and DOT generation used by the static WebUI. |
| `web/static/graph-runtime.mjs` | Browser-side WASI adapter: loads the local module, supplies the required `wasi_snapshot_preview1` imports, calls the wrapper exports, and returns SVG. |
| `scripts/dev.py` | Copies the exact packaged WASM bytes into the static distribution and exports the shared graph assets. |
| `pyproject.toml` | Declares `wasmtime` and includes the WASM, license, and provenance files in the Python package. |
| `r3xa_api/resources/graphviz/README.md` | Records upstream Graphviz provenance, the release, the wrapper ABI, and distribution notes. |
| `tests/webcore/test_graph_graphviz_wasm.py` | Verifies the Python WASI backend, its SVG output, and failure behavior. |
| `tests/web/test_static_build.py` and `tests/web/test_static_graph.py` | Verify that the static build contains the exact module and that the browser graph uses the local runtime. |
| `tests/web/test_static_browser.py` | Exercises the static application in a browser, including local graph rendering and graceful failure. |

The file
`r3xa_api/resources/graphviz/graphviz-12.2.1.wasm` is different from the
files above: it is a compiled artifact derived from upstream Graphviz plus the
R3XA wrapper. It is shipped by this repository, but it is not C source written
here.

### Current reproducibility boundary

The source-side reconstruction is now versioned in `tools/graphviz-wasi/`.
That directory contains the R3XA wrapper C source, the CMake link definition,
the pinned Graphviz source commit and archive hash, the pinned WASI SDK
version/hash, and `build.py`, which verifies downloads before compiling. The
canonical command is:

```bash
python scripts/dev.py build-graphviz-wasm
```

This command rebuilds the module into
`r3xa_api/resources/graphviz/graphviz-12.2.1.wasm`. It does not run during
`pip install`: installation consumes the already-built package artifact, while
rebuilding is an explicit maintainer/developer operation.

The output need not be byte-for-byte identical across compiler environments;
the source commit, SDK, target, build flags, exported ABI, output hash, and
Graphviz behavior are the reproducibility contract. The committed artifact's
hash remains recorded so a rebuild can be reviewed deliberately rather than
silently replacing the runtime binary.

### Performance and installation cost

The WASM backend is deliberately measured before it is optimized. The
following local smoke benchmark renders the same QI document repeatedly with
both backends after one warm-up render:

```bash
./.venv/bin/python - <<'PY'
import json
import statistics
import time
from pathlib import Path

from r3xa_api.webcore.graph import generate_svg, generate_svg_wasm

payload = json.loads(
    Path("examples/artifacts/baseline_qi/qi_hu_from_scratch.json").read_text()
)
for name, renderer in (("wasm", generate_svg_wasm), ("native", generate_svg)):
    renderer(payload)
    samples = []
    for _ in range(10):
        started = time.perf_counter()
        renderer(payload)
        samples.append(time.perf_counter() - started)
    print(
        name,
        f"mean_ms={statistics.mean(samples) * 1000:.2f}",
        f"min_ms={min(samples) * 1000:.2f}",
        f"max_ms={max(samples) * 1000:.2f}",
    )
PY
```

On the maintainer workstation on 2026-09-21, this produced approximately
`5.5 ms` per warm WASM render and `54.5 ms` per native render. The first WASM
render took approximately `473 ms` because it included module instantiation;
the first native render took approximately `47 ms`. These are observations
for one document, machine, and Graphviz installation, not performance
guarantees. The native measurement includes launching the system `dot`
process, whereas the warm WASM measurement reuses the loaded module. The
first-render cost matters for UI latency, while repeated renders benefit from
the cached WASM module.

The packaged `wasmtime` installation is currently about `24 MB` in the local
Python environment, and the pure-Python wheel containing the WASM asset is
about `711 KB`. These figures should be rechecked when upgrading wasmtime or
the Graphviz artifact; they are the reason the standard distribution favors a
single ready-to-run WASM backend rather than requiring users to install a
platform-specific `dot` executable.

## Packaging and build flow

The normal Python package contains:

```text
r3xa_api/resources/graphviz/graphviz-12.2.1.wasm
r3xa_api/resources/graphviz/README.md
r3xa_api/resources/graphviz/LICENSE-Graphviz.txt
```

The static build performs a byte-for-byte copy:

```text
resources/graphviz/graphviz-12.2.1.wasm
        ↓
dist/r3xa-webui/assets/graphviz-12.2.1.wasm
```

This is checked by `tests/web/test_static_build.py`. The build must not
download Graphviz from a CDN and must not call a remote rendering service.

The runtime dependencies are deliberately different from the build
dependencies:

| Context | Required runtime |
|---|---|
| Python SDK | `wasmtime` and the packaged WASM file |
| FastAPI WebUI | Python SDK plus FastAPI; graph rendering uses the Python adapter |
| Static WebUI | browser WebAssembly plus the packaged local WASM file |
| Native Graphviz backend | system `dot`, only when explicitly selected |

## Rebuilding or replacing the binary

The repository records the binary provenance and contains the source-side
rebuild toolchain. The artifact is still a versioned binary input to the Python
package: it is not rebuilt automatically by `pip install`, `npm`, or the
normal application build.

Before replacing the module, record all of the following in the merge request
and update this page:

1. Graphviz upstream release and commit/tag.
2. WASI SDK version, compiler, linker, and target triple.
3. Graphviz configuration options and the list of enabled/disabled engines.
4. Wrapper source and the exact ABI implementation.
5. The resulting binary size and SHA-256.
6. The license/provenance files shipped with the artifact.

After replacing it, update the versioned references in:

- `tools/graphviz-wasi/manifest.json` and `tools/graphviz-wasi/build.py`;
- `tools/graphviz-wasi/wrapper.c` and `tools/graphviz-wasi/CMakeLists.txt`;
- `r3xa_api/webcore/_graph_graphviz_wasm.py`;
- `web/static/graph-runtime.mjs`;
- `scripts/dev.py` if the asset filename changes;
- `r3xa_api/resources/graphviz/README.md`;
- the static-build and WASM backend tests.

Do not replace the binary with a different Graphviz build merely because it
produces an SVG. The Python backend, browser backend, and position calculations
must continue to use the same artifact and ABI.

## Validation checklist

Run the focused checks after changing the adapter or the binary:

```bash
./.venv/bin/python -m pytest -q \
  tests/webcore/test_graph_graphviz_wasm.py \
  tests/web/test_static_build.py \
  tests/web/test_static_graph.py

npm test --prefix web
./.venv/bin/python scripts/dev.py build-static-web
```

For browser qualification, also run:

```bash
./.venv/bin/python scripts/dev.py test-static-web
```

The acceptance criteria are:

- Python renders SVG with `backend="graphviz-wasm"` when `dot` is absent from
  `PATH`;
- the static build contains the exact source WASM bytes;
- the browser renders a local SVG without `/api/graph` or third-party network
  requests;
- Graphviz failure does not disable the editor;
- Graphviz and the other backends preserve the same R3XA topology and palette
  semantics.

## Security and licensing

The WASM module is local package/site data, not executable code downloaded at
runtime. The browser still needs a CSP allowing WebAssembly for this feature;
the documented narrow exception is `wasm-unsafe-eval`. No user document is
sent to a validation or graph-rendering service.

The Graphviz license must remain next to the binary in both source and package
distributions. Any future rebuild must preserve the upstream attribution and
update the provenance information before release.
