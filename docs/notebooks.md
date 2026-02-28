# Notebooks (Marimo)

This page explains how to test the **base DIC notebook** locally and how to publish a static version on **GitHub Pages**.

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

## 3) Publish on GitHub Pages

GitHub Pages can host this notebook as a regular static HTML page.

### Recommended workflow
1. Export:
   ```bash
   ./.venv/bin/marimo export html \
     examples/notebooks/dic_base_marimo.py \
     -o docs/figures/dic_base_marimo/index.html \
     --force
   ```
2. Commit the exported file `docs/figures/dic_base_marimo/index.html`.
3. Push to the branch used by Pages (`main` or `gh-pages`, depending on your repository settings).
4. In GitHub: `Settings -> Pages`, confirm the configured source branch/folder.

### Resulting URL
- **Project Pages**: `https://<user>.github.io/<repo>/figures/dic_base_marimo/`
- **User Pages**: `https://<user>.github.io/dic_base_marimo/` (if published at site root)

Use the URL corresponding to your Pages configuration.

### Why not `html-wasm` here
`html-wasm` runs Python in-browser and cannot import this local package (`r3xa_api`) reliably from GitHub Pages.
For this project, `marimo export html` is the stable option.

---

## Notes

- No Jupyter server is required for static mode.
- Static mode is ideal for low-CPU demos and sharing.
- For editable notebooks, keep using `marimo edit` locally.

---

## 4) MyBinder (public interactive run)

Open this URL:

`https://mybinder.org/v2/gh/jeffwitz/R3XA_API/HEAD?urlpath=proxy/2718/`

How it works in this repository:
- Dependencies come from `binder/requirements.txt`.
- Binder startup runs `binder/start`, which launches:
  `marimo edit examples/notebooks/dic_base_marimo.py --port 2718`.
- Binder then proxies to Marimo at `/proxy/2718/`.

Notes:
- First launch can take 2-5 minutes (image build).
- If the page is blank during startup, wait and refresh once.
