# Tutorials — Jupyter and Marimo

The repository contains parallel Python, Jupyter, Marimo, and MATLAB examples.
Install Jupyter with `pip install -r requirements-jupyter.txt`, or install
Marimo with `pip install -r requirements-marimo.txt`, then follow
`examples/tutorials/README.md`.

This page is the main **learn-by-doing tutorial entry point** for the project.
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

Notebook features:
- **Load JSON from PC** (upload button)
- **Export JSON to PC** (download button)
- **Generate Graphviz SVG graph** + **Export graph SVG to PC**

---

## 1) Local test (interactive editor)

### Install notebook dependencies
```bash
python -m pip install -r requirements-marimo.txt
```

For the converted Jupyter tutorials instead, install
`python -m pip install -r requirements-jupyter.txt`.

### Graphviz requirement

The notebook uses the bundled Graphviz WebAssembly module through the standard
`wasmtime` dependency, so no system installation is required. The native
`dot` executable remains optional if you want to use the explicit native
`graphviz` backend elsewhere.

### Start Marimo
```bash
marimo edit
```

Run this command from the repository root. The Marimo workspace browser then
exposes both `examples/tutorials/marimo/` and the case applications under
`examples/cases/*/marimo/`. To launch the base DIC notebook directly, use:

```bash
python scripts/dev.py notebook-dic
```

Then open the URL printed by Marimo (usually `http://127.0.0.1:2718`).

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

## 2) MyBinder (public interactive run)

Open:
- [Launch notebook on MyBinder](https://mybinder.org/v2/gl/photomechanics%2FR3XA_API/v2.0.0rc4?urlpath=proxy/2718/)

How it works in this repository:
- Dependencies come from `binder/requirements.txt`.
- System packages come from `binder/apt.txt` (`graphviz` is installed).
- Binder startup runs `binder/start`, which launches:
  `marimo edit examples/notebooks/dic_base_marimo.py --port 2718`.
- Binder then proxies to Marimo at `/proxy/2718/`.

Notes:
- First launch can take 2-5 minutes (image build).
- If the page is blank during startup, wait and refresh once.
