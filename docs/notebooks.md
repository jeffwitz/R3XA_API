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

## 2) Local test (static export, no Python backend)

Export as static WASM notebook:
```bash
./.venv/bin/marimo export html-wasm \
  examples/notebooks/dic_base_marimo.py \
  -o docs/figures/dic_base_marimo \
  --mode run
```

Serve locally:
```bash
python -m http.server --directory docs/figures/dic_base_marimo 8010
```

Open:
- `http://127.0.0.1:8010`

This is the same deployment model used for static hosting platforms.

---

## 3) Publish on GitHub Pages

GitHub Pages can host the exported Marimo notebook because it is static HTML + assets.

### Recommended workflow
1. Export:
   ```bash
   ./.venv/bin/marimo export html-wasm \
     examples/notebooks/dic_base_marimo.py \
     -o docs/figures/dic_base_marimo \
     --mode run
   ```
2. Commit the exported folder `docs/figures/dic_base_marimo/`.
3. Push to the branch used by Pages (`main` or `gh-pages`, depending on your repository settings).
4. In GitHub: `Settings -> Pages`, confirm the configured source branch/folder.

### Resulting URL
- **Project Pages**: `https://<user>.github.io/<repo>/figures/dic_base_marimo/`
- **User Pages**: `https://<user>.github.io/dic_base_marimo/` (if published at site root)

Use the URL corresponding to your Pages configuration.

### Note for static hosting
GitHub Pages is static hosting. JSON load/export works well in static mode.
For graph generation, prefer using the notebook locally (`marimo edit`) and exporting the generated HTML graph.

---

## Notes

- No Jupyter server is required for static mode.
- Static mode is ideal for low-CPU demos and sharing.
- For editable notebooks, keep using `marimo edit` locally.
