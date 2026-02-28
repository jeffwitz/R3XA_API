# Notebooks (Marimo)

This page explains how to test the **base DIC notebook** locally and how to share a static HTML export.

Notebook source:
- `examples/notebooks/dic_base_marimo.py`

Notebook features:
- **Load JSON from PC** (upload button)
- **Export JSON to PC** (download button)
- **Generate PyVis HTML graph** + **Export graph HTML to PC**

---

## 1) Local test (interactive editor)

### Install notebook dependencies
```bash
./.venv/bin/pip install -r requirements-notebook.txt
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
6. Click **Generate PyVis HTML graph**.
7. Click **Export graph HTML to PC**.
8. Optional repository save:
   ```python
   save_document()
   ```
9. Confirm that `examples/artifacts/dic_pipeline_notebook.json` exists.

---

## 2) Local static export

Export as static HTML notebook:
```bash
./.venv/bin/marimo export html \
  examples/notebooks/dic_base_marimo.py \
  -o docs/figures/dic_base_marimo/index.html \
  --force
```

Open directly:
```bash
xdg-open docs/figures/dic_base_marimo/index.html
```

Or serve locally:
```bash
python -m http.server --directory docs 8010
```
Then open `http://127.0.0.1:8010/figures/dic_base_marimo/`.

---

## Notes

- No Jupyter server is required for static mode.
- Static mode is ideal for low-CPU demos and sharing.
- For editable notebooks, keep using `marimo edit` locally.
- `html-wasm` is not used here because it does not reliably import this local package (`r3xa_api`).

---

## 3) MyBinder (public interactive run)

Open this URL:

`https://mybinder.org/v2/gh/jeffwitz/R3XA_API/develop?urlpath=proxy/2718/`

How it works in this repository:
- Dependencies come from `binder/requirements.txt`.
- Binder startup runs `binder/start`, which launches:
  `marimo edit examples/notebooks/dic_base_marimo.py --port 2718`.
- Binder then proxies to Marimo at `/proxy/2718/`.

Notes:
- First launch can take 2-5 minutes (image build).
- If the page is blank during startup, wait and refresh once.
