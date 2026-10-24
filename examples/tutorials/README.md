# R3XA tutorials

These tutorials form a progressive introduction to the Python object-first API:

1. create and save a document;
2. print and plot documents and items;
3. edit an existing document;
4. save and reuse standalone items;
5. compare list and file datasets;
6. validate documents and items;
7. open an existing document and explore its graph interactively.

## Prerequisite

Run the commands from the repository root. The plain Python tutorials need
only R3XA_API; install the extra corresponding to an interactive notebook tool
if you want to use Jupyter or Marimo. Installing only a notebook application
does not install R3XA_API, its current schema, or the bundled Graphviz
WebAssembly backend.

```bash
python -m pip install -e .
# For notebooks, choose one extra or install both together.
python -m pip install -e ".[jupyter]"
python -m pip install -e ".[marimo]"
```

The dependency-only files `requirements-jupyter.txt` and
`requirements-marimo.txt` can be used after `python -m pip install -e .`, but
the editable extra commands above are the recommended setup.

## Python scripts

Run the scripts from the repository root, in order:

```bash
python examples/tutorials/python/tutorial0_basic.py
python examples/tutorials/python/tutorial1_printing_and_plotting.py
python examples/tutorials/python/tutorial2_edit_r3xafile.py
python examples/tutorials/python/tutorial3_build_use_predefined_items.py
python examples/tutorials/python/tutorial4_file_vs_list.py
python examples/tutorials/python/tutorial5_validation.py
python examples/tutorials/python/tutorial6_interactive_cytoscape.py
```

The generated JSON, SVG, and interactive HTML files are written to
`artifacts/examples/tutorials/`. They are deliberately kept outside the
source tree.

Interactive notebooks display generated SVG graphs inline: Jupyter uses
`IPython.display.SVG`, while Marimo embeds the SVG markup with `mo.Html`. The
plain Python tutorial 6 loads the same existing torsion document as the two
notebooks and saves `torsion_cytoscape.html`; open that file in a browser to
inspect nodes interactively. It requires neither Jupyter nor Marimo.

## Jupyter notebooks

Install the optional Jupyter support:

```bash
python -m pip install -e ".[jupyter]"
```

Start Jupyter from the repository root so its file browser exposes both the
tutorial notebooks and the notebooks under `examples/cases/`:

```bash
jupyter notebook --no-browser --ip=127.0.0.1 --port=8888 --notebook-dir=.
```

Open the URL printed by Jupyter, normally `http://127.0.0.1:8888/tree`.

Open `examples/tutorials/jupyter/` for the tutorials, or
`examples/cases/<case>/` for a complete scientific case.

The notebooks use the same artifact directory and follow the same progression
as the Python scripts. The notebooks are teaching material; the Python scripts
are the files exercised by the automated smoke tests.

`tutorial6_interactive_cytoscape.ipynb` is independent of the earlier lessons:
it loads `tests/fixtures/documents/essai-torsion.json`, validates it, and shows
the standalone Cytoscape export in an iframe. Start Jupyter from the repository
root as shown above so `/files/` can serve the generated HTML artifact.

## Marimo notebooks

The Jupyter tutorials were converted to Marimo applications without changing
their document-building logic. Install the optional dependency:

```bash
python -m pip install -e ".[marimo]"
# or
python -m pip install -r requirements-marimo.txt
```

Run Marimo from the repository root without passing a notebook filename. This
opens its workspace browser and exposes both tutorial and case applications:

```bash
marimo edit --host 127.0.0.1 --port 2720
```

Open `http://127.0.0.1:2720`. If that port is occupied, choose another free
port with `--port` and use the corresponding URL. The base DIC application can
also be launched directly with:

```bash
python scripts/dev.py notebook-dic --port 2720
```

Select a file under `examples/tutorials/marimo/` or
`examples/cases/<case>/marimo/` from the workspace browser. Passing a single
filename remains useful when opening one application directly:

```bash
marimo edit examples/tutorials/marimo/tutorial0_basic.py
```

`tutorial6_interactive_cytoscape.py` loads the same existing document and
embeds the self-contained HTML in a sandboxed iframe. No notebook server route
or CDN is needed for this graph.

The converted case notebooks are available at
`examples/cases/torsion/marimo/example.py` and
`examples/cases/qi_hu/marimo/example.py`. They are repository-local examples,
so the editable R3XA API installation is intentionally the source of their
dependencies rather than a generated standalone package.

To regenerate the converted Marimo sources (tutorials 0–5 and the cases) after
editing a Jupyter notebook, use the repository command. Tutorial 6 is
hand-maintained because Jupyter and Marimo embed the HTML differently; the
converter deliberately leaves it untouched. Review generated cells before
running them:

```bash
python scripts/dev.py convert-tutorials
```

For a single notebook, the underlying command is:

```bash
marimo convert examples/tutorials/jupyter/tutorial0_basic.ipynb \
  -o examples/tutorials/marimo/tutorial0_basic.py
marimo check examples/tutorials/marimo/tutorial0_basic.py
```

The checked-in Python scripts remain the canonical smoke-test targets because
they can run in the minimal contributor environment without starting a
notebook server.

## MATLAB

The MATLAB binding has a matching minimal tutorial:

```matlab
run('examples/tutorials/matlab/tutorial0_basic.m')
```

It writes `matlab_tutorial0_basic.json` to the same artifact directory. The
MATLAB binding generates JSON; validation can then be performed with the
Python API or the WebUI.

The larger MATLAB case entry points are
`examples/cases/torsion/example.m` and `examples/cases/qi_hu/example.m`.
