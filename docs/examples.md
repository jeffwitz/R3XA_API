# R3XA examples

The maintained source examples are organized into two groups:

- **Tutorials** introduce the Python object-first API progressively. Start at
  [Interactive tutorials](notebooks.md).
- **Cases** are fuller scientific workflows that can be adapted to experiments.
  See {glsrc}`examples/cases/README.md` and the
  [Qi Hu case study](qi_case.md).

The same tutorial and case sources are provided in Python, Jupyter, Marimo, or
MATLAB where applicable. Install R3XA_API with the appropriate optional
notebook extra before launching Jupyter or Marimo; the package supplies the
current schema and Graphviz WebAssembly backend.

Run Python cases from the repository root:

```bash
python examples/cases/torsion/example.py
python examples/cases/qi_hu/example.py
```

Generated JSON and graph files are kept separately from source code under
`artifacts/examples/`. These outputs include test fixtures and graph baselines;
they are validated against the current schema by the test suite.

The graph command-line example is maintained in
{glsrc}`scripts/graph_r3xa.py`. The independent
[R3XA_REGISTRY](https://gitlab.com/photomechanics/R3XA_REGISTRY) repository is
the source of shareable Registry items; the bundled Registry examples are
validated against the current schema and API.
