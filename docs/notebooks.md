# Notebooks (Marimo)

This page explains how to run the **base DIC notebook** with a real Python runtime.

Notebook source:
- `examples/notebooks/dic_base_marimo.py`

Notebook features:
- **Load JSON from PC** (upload button)
- **Export JSON to PC** (download button)
- **Generate Graphviz SVG graph** + **Export graph SVG to PC**

---

## 1) Local test (interactive editor)

### Install notebook dependencies
```bash
./.venv/bin/pip install -r requirements-notebook.txt
```

### Graphviz requirement

The notebook renders graphs as SVG with Graphviz.
The Python requirements are **not enough** on their own: the Graphviz executable `dot` must also be installed on the system.

- Linux: `sudo apt-get install graphviz`
- macOS: `brew install graphviz`
- Windows: install from <https://graphviz.org/download/> and ensure `dot` is in `PATH`

Quick check:

```bash
dot -V
```

### Start Marimo
```bash
./.venv/bin/marimo edit examples/notebooks/dic_base_marimo.py
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
- [Launch notebook on MyBinder](https://mybinder.org/v2/gh/jeffwitz/R3XA_API/v1.4.4?urlpath=proxy/2718/)

How it works in this repository:
- Dependencies come from `binder/requirements.txt`.
- System packages come from `binder/apt.txt` (`graphviz` is installed).
- Binder startup runs `binder/start`, which launches:
  `marimo edit examples/notebooks/dic_base_marimo.py --port 2718`.
- Binder then proxies to Marimo at `/proxy/2718/`.

Notes:
- First launch can take 2-5 minutes (image build).
- If the page is blank during startup, wait and refresh once.
