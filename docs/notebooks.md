# Tutorials — Jupyter and Marimo

The repository contains parallel Python, Jupyter, Marimo, and MATLAB examples.
This page is the main entry point for running the interactive tutorials and the
larger torsion and Qi Hu case studies.

:::{important}
Install **R3XA_API itself** in the same virtual environment as the notebook
runtime. Installing only Jupyter or Marimo gives you the notebook application,
but not the current R3XA schema, Python API, bundled Graphviz WebAssembly
runtime, or the generated helpers used by these examples.

Run the commands below from the repository root:

```bash
python -m pip install -e ".[jupyter]"       # Jupyter tutorials and cases
python -m pip install -e ".[marimo]"        # Marimo tutorials and cases
```

You can install both extras at once with
`python -m pip install -e ".[jupyter,marimo]"`. The files
`requirements-jupyter.txt` and `requirements-marimo.txt` are dependency-only
shortcuts; use them **after** `pip install -e .` if you prefer that workflow.
:::

If you want to understand the library by running a real workflow, start here.

This page explains how to run the **base DIC notebook** with a real Python runtime.

The base interactive Marimo notebook source is:
- {glsrc}`examples/notebooks/dic_base_marimo.py`

The converted tutorial notebooks are:
- {glsrc}`examples/tutorials/jupyter/tutorial0_basic.ipynb`
- {glsrc}`examples/tutorials/jupyter/tutorial1_printing_and_plotting.ipynb`
- {glsrc}`examples/tutorials/jupyter/tutorial2_edit_r3xafile.ipynb`
- {glsrc}`examples/tutorials/jupyter/tutorial3_build_use_predefined_items.ipynb`
- {glsrc}`examples/tutorials/jupyter/tutorial4_file_vs_list.ipynb`
- {glsrc}`examples/tutorials/jupyter/tutorial5_validation.ipynb`

Their Marimo counterparts are in {glsrc}`examples/tutorials/marimo/` and the
scientific case conversions are in {glsrc}`examples/cases/`.

## Scientific case studies

These larger examples are presented in all currently supported interactive
Python forms and also have MATLAB entry points:

- **Large-rotation torsion** — {glsrc}`examples/cases/torsion/example.py`,
  {glsrc}`examples/cases/torsion/example.ipynb`,
  {glsrc}`examples/cases/torsion/marimo/example.py`, and
  {glsrc}`examples/cases/torsion/example.m`.
- **Qi Hu thermography** — {glsrc}`examples/cases/qi_hu/example.py`,
  {glsrc}`examples/cases/qi_hu/example.ipynb`,
  {glsrc}`examples/cases/qi_hu/marimo/example.py`, and
  {glsrc}`examples/cases/qi_hu/example.m`.

Both cases validate their document and generate a Graphviz SVG. The Jupyter
and Marimo versions display that graph inline, which makes them useful for
checking the references and data flow while following the construction.

Notebook features:
- **Load JSON from PC** (upload button)
- **Export JSON to PC** (download button)
- **Generate Graphviz SVG graph** + **Export graph SVG to PC**

---

## 1) Start the local notebook servers

Always start these commands from the repository root. This is important: the
workspace browsers then expose both `examples/tutorials/` and
`examples/cases/`, and the relative artifact paths used by the notebooks work
as documented.

### Jupyter

```bash
jupyter notebook --no-browser --ip=127.0.0.1 --port=8888 --notebook-dir=.
```

Open the URL printed by Jupyter, normally
`http://127.0.0.1:8888/tree`. Select a notebook under
`examples/tutorials/jupyter/`, or a complete case under
`examples/cases/<case>/`.

### Marimo

```bash
marimo edit --host 127.0.0.1 --port 2720
```

Open `http://127.0.0.1:2720`. The Marimo workspace browser exposes the six
tutorial applications and the case applications under
`examples/cases/*/marimo/`. To open the base DIC application directly, use:

```bash
python scripts/dev.py notebook-dic --port 2720
```

If a port is already in use, choose another free port in both the command and
the URL, for example `--port 2721`.

## 2) Local interactive validation

### Graphviz requirement

The notebook uses the bundled Graphviz WebAssembly module through the standard
`wasmtime` dependency, so no system installation is required. The native
`dot` executable remains optional if you want to use the explicit native
`graphviz` backend elsewhere.

### What to validate
In the notebook:
1. Run all cells.
2. Check the validation callout confirms payload is valid.
3. Click **Load JSON from PC** and select an existing `.json` file (optional).
4. Confirm the status callout says the uploaded file was loaded and validated.
5. Click **Export JSON to PC**.
6. Click **Generate Graphviz SVG**.
7. Click **Export graph SVG to PC**.
8. Optional repository save:
   ```python
   save_document()
   ```
9. Confirm that `examples/artifacts/dic_pipeline_notebook.json` exists.

---

## 3) MyBinder (public interactive run)

Open:
- [Launch notebook on MyBinder](https://mybinder.org/v2/gl/photomechanics%2FR3XA_API/v2.0.0rc5?urlpath=proxy/2718/)

How it works in this repository:
- Dependencies come from `binder/requirements.txt`.
- System packages come from `binder/apt.txt` (`graphviz` is installed).
- Binder startup runs `binder/start`, which launches:
  `marimo edit examples/notebooks/dic_base_marimo.py --port 2718`.
- Binder then proxies to Marimo at `/proxy/2718/`.

Notes:
- First launch can take 2-5 minutes (image build).
- If the page is blank during startup, wait and refresh once.
