# Notebooks (Marimo)

This page explains how to test the **base DIC notebook** locally and how to publish a static version on **GitHub Pages**.

Notebook source:
- `examples/notebooks/dic_base_marimo.py`

Notebook features:
- **Load JSON from PC** (upload button)
- **Export JSON to PC** (download button)
- **Generate Graphviz SVG** + **Export SVG to PC**

---

## 1) Local test (interactive editor)

### Install notebook dependencies
```bash
./.venv/bin/pip install -r requirements-notebook.txt
```

Install Graphviz executable (`dot`) on your system:
- Linux: `sudo apt-get install graphviz`
- macOS: `brew install graphviz`
- Windows: install from `https://graphviz.org/download/` and add `Graphviz\\bin` to `PATH`

### Start Marimo
```bash
./.venv/bin/marimo edit examples/notebooks/dic_base_marimo.py
```

Then open the URL printed by Marimo (usually `http://127.0.0.1:2718`).

### What to validate
In the notebook:
1. Run all cells.
2. Check the validation callout confirms payload is valid.
3. Click **Load JSON from PC** and load an existing `.json` file (optional).
4. Click **Export JSON to PC**.
5. Click **Generate Graphviz SVG**.
6. Click **Export SVG to PC**.
7. Optional repository save:
   ```python
   save_document()
   ```
8. Confirm that `examples/artifacts/dic_pipeline_notebook.json` exists.

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

### Important note for Graphviz on GitHub Pages
GitHub Pages is static hosting, so there is no native `dot` executable in-browser.
- JSON load/export buttons work in static mode.
- The Graphviz generation button may fail in static mode depending on runtime capabilities.

Recommended approach:
1. Generate SVG locally (where `dot` is installed).
2. Export and commit the produced SVG file.
3. Share that SVG along with the notebook page.

---

## Notes

- No Jupyter server is required for static mode.
- Static mode is ideal for low-CPU demos and sharing.
- For editable notebooks, keep using `marimo edit` locally.
