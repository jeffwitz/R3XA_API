# Rebuilding the Graphviz WASI module

This directory contains the source-side build description for the Graphviz
module shipped in `r3xa_api/resources/graphviz/`. It is separate from
`r3xa_api/graphviz_setup.py`, which installs the optional native `dot`
executable and does not build WebAssembly.

## What is pinned

`manifest.json` pins:

- Graphviz `12.2.1`, commit `0a1e625ea287ae55e0db59a470f076f8d79d3c4f`;
- the GitLab source archive URL and SHA-256;
- WASI SDK `27.0`, target `wasm32-wasip1`, and the Linux x86_64 SDK SHA-256;
- the expected package output path.

`wrapper.c` is the R3XA-specific C adapter. It links Graphviz's built-in
`dot`, core, and SVG renderer plugins and exports the small ABI consumed by
the Python `wasmtime` adapter and the static browser runtime.

## Build

On Linux x86_64, the pinned SDK is downloaded and verified automatically:

```bash
python tools/graphviz-wasi/build.py
```

The command downloads only the pinned Graphviz source archive and WASI SDK,
builds the reduced static Graphviz configuration, and writes:

```text
r3xa_api/resources/graphviz/graphviz-12.2.1.wasm
```

For another host, install a compatible WASI SDK and pass its directory:

```bash
python tools/graphviz-wasi/build.py --wasi-sdk /path/to/wasi-sdk-27.0
```

An existing Graphviz checkout can also be supplied after checking out the
manifest commit:

```bash
python tools/graphviz-wasi/build.py \
  --graphviz-source /path/to/graphviz \
  --wasi-sdk /path/to/wasi-sdk-27.0
```

The build requires CMake, a C/C++ build toolchain, and the host-side Bison and
Flex programs required by Graphviz. The compiler is the pinned WASI SDK; the
result is a `wasm32-wasip1` module, not a native executable.

The script prints the resulting SHA-256. Before replacing the committed
artifact, run the Graphviz WASM tests and compare the module exports and output
behavior. A different hash is expected if compiler flags or source changes,
but it must be reviewed rather than silently accepted.

## Scope of the reduced build

The build disables Graphviz CLI programs, dynamic plugin loading, GUI/language
bindings, and optional image/dependency integrations. It keeps the C graph
libraries, the `dot` layout plugin, the core renderer, and the SVG path needed
by R3XA. This keeps the package portable and avoids shipping an entire native
Graphviz installation.

The upstream Graphviz source and license remain authoritative for Graphviz
code. `wrapper.c`, `CMakeLists.txt`, `build.py`, and `manifest.json` are the
R3XA-specific build and ABI layer.
