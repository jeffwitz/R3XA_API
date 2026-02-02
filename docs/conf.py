project = "R3XA_API"
author = "R3XA_API"
extensions = ["myst_parser", "sphinxcontrib.mermaid"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
html_title = "R3XA_API"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 3,
    "titles_only": False,
}

import os
import shutil

def _copy_artifacts(app):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    artifacts = os.path.join(root, "examples", "artifacts")
    static_dir = os.path.join(os.path.dirname(__file__), "_static")
    os.makedirs(static_dir, exist_ok=True)
    for name in [
        "graph_qi.svg",
        "graph_qi.html",
        "graph_dic_pipeline.svg",
        "graph_dic_pipeline.html",
    ]:
        src = os.path.join(artifacts, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(static_dir, name))


def setup(app):
    app.connect("builder-inited", _copy_artifacts)
