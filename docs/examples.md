# Python recipes

Use this page when you already know the basic R3XA object model and need a
specific workflow. For lessons in sequence, see
[Interactive tutorials](notebooks.md). Run the commands below from an
activated environment in the repository root; generated JSON and graphs go to
`examples/artifacts/`.

## Create a DIC pipeline

The two maintained scripts build the same kind of document in different ways:

| Task | Run |
| --- | --- |
| Define every item in Python | `python examples/python/complex_dic_pipeline.py` |
| Reuse bundled item templates | `python examples/python/complex_dic_pipeline_registry.py` |

The second script reads the small `registry/` catalogue bundled with this
repository. The independent
[R3XA_REGISTRY](https://gitlab.com/photomechanics/R3XA_REGISTRY) repository
is the source for shareable Registry items; it is validated by API CI.

## Load and update a document

```python
from r3xa_api import R3XAFile

document = R3XAFile.load("experiment.json")
document.title = "Updated experiment"
document.validate()
document.save("experiment-updated.json")
```

See {glsrc}`examples/python/load_edit_save.py` for a runnable version.

## Reuse or create an item

Use `Registry.load(...)` to obtain a generated Python object, or
`Registry.get_item(...)` when you need a wrapper bound to its Registry path.
The maintained examples are:

- {glsrc}`examples/python/registry_discovery.py`: list and merge entries;
- {glsrc}`examples/python/registry_usage.py`: load and override a template;
- {glsrc}`examples/python/create_registry_camera.py`: create and save a
  camera item.

In the browser, the [Registry editor](registry_web.md) stores new templates
only in your browser until you export them. It does not publish them to
`R3XA_REGISTRY`.

## Export a graph

```python
from r3xa_api import R3XAFile

document = R3XAFile.load("experiment.json")
document.plot("experiment.svg", palette="document")
```

The standard `graphviz-wasm` backend uses the bundled Graphviz binary.
Pass `backend="graphviz"` only when you want the optional system `dot`.
Use `backend="matplotlib"` for Matplotlib SVG or
`backend="pyvis"` for interactive HTML when the corresponding extras are
installed. The {glsrc}`examples/python/graph_r3xa.py` script demonstrates
multi-backend export, including optional DOT output.

## Run a scientific case

- Torsion: `python examples/cases/torsion/example.py`
- Qi Hu thermography: `python examples/cases/qi_hu/example.py`

Each case also has Jupyter, Marimo, and MATLAB forms. See
[Qi Hu case study](qi_case.md) and {glsrc}`examples/cases/README.md` for
the files and outputs.

Earlier recipes are kept under {glsrc}`examples/archive/` for comparison,
outside the recommended path. The generated examples and graph baselines in
`examples/artifacts/` are test and illustration artefacts, not source code.
