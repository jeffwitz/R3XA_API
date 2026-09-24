# Interactive tutorials

The six tutorials teach the Python object-first API in order. Each has a
plain Python script, a Jupyter notebook, and a Marimo application. Start with
tutorial 0; the later lessons reuse documents written to
`artifacts/examples/tutorials/`.

| Step | Topic | What you do |
| --- | --- | --- |
| 0 | Create a document | Add items, validate, plot, and save JSON. |
| 1 | Inspect and plot | Print a document and its items; display the SVG graph. |
| 2 | Edit a document | Load the saved JSON, modify it, and save it again. |
| 3 | Reuse items | Save an item separately and insert it in a document. |
| 4 | File or list dataset | Describe tabular data and file sequences. |
| 5 | Validate | Check documents and individual items. |

The maintained files and their output paths are listed in
{glsrc}`examples/tutorials/README.md`. The MATLAB binding has a matching
[introductory tutorial](matlab.md); the larger [scientific cases](qi_case.md)
also have MATLAB entry points.

## Install the notebook runtime

Start from the repository root in an activated virtual environment containing
the current R3XA_API checkout. Install the extra for the interface you want:

```bash
python -m pip install -e ".[jupyter]"
python -m pip install -e ".[marimo]"
```

You can install both with `python -m pip install -e ".[jupyter,marimo]"`.
Installing only Jupyter or Marimo without R3XA_API will not provide the
current schema, generated models, and bundled Graphviz WebAssembly backend.
For the initial checkout and environment setup, see [Start with R3XA](getting_started.md).

## Open Jupyter

```bash
jupyter notebook --no-browser --ip=127.0.0.1 --port=8888 --notebook-dir=.
```

Open the URL printed by Jupyter, normally `http://127.0.0.1:8888/tree`.
Browse to `examples/tutorials/jupyter/` and open
`tutorial0_basic.ipynb`. The torsion and Qi Hu notebooks are under
`examples/cases/`.

## Open Marimo

```bash
marimo edit --host 127.0.0.1 --port 2720
```

Open `http://127.0.0.1:2720`. Starting Marimo without a notebook filename
shows its workspace browser, where you can choose a tutorial under
`examples/tutorials/marimo/` or a case under `examples/cases/`. To open the
separate base DIC application directly, use
`python scripts/dev.py notebook-dic --port 2720`.

Both notebook formats display generated SVG graphs inline. Their Python
scripts save the same JSON and SVG files under `artifacts/examples/`. The
standard graph backend uses bundled Graphviz WebAssembly; a system `dot`
installation is unnecessary. If either port is busy, use another port in the
command and URL.

## Run without a notebook server

```bash
python examples/tutorials/python/tutorial0_basic.py
```

Continue with tutorials 1 through 5 in the same directory. For a complete
experimental pipeline, continue with the [Qi Hu case study](qi_case.md) or
{glsrc}`examples/cases/torsion/example.py`.
