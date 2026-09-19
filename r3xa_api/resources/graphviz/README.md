# Bundled Graphviz WebAssembly

`graphviz-12.2.1.wasm` is a WASI build of Graphviz 12.2.1. It provides the
`dot` layout engine and SVG renderer through the small R3XA wrapper ABI used by
`r3xa_api.webcore._graph_graphviz_wasm`.

The module is a standard runtime resource. The `graphviz-wasm` backend uses it
through the standard `wasmtime` dependency and is the default. The native
`graphviz` backend remains available when the system `dot` executable is
installed.

The Graphviz source is available from the [Graphviz source repository](https://gitlab.com/graphviz/graphviz),
and Graphviz is distributed under the Eclipse Public License 1.0. The bundled
module was built from the 12.2.1 release with the WASI SDK and contains only
the `dot` layout and SVG output path required by R3XA.

The upstream license text is included as `LICENSE-Graphviz.txt` beside the
module.
