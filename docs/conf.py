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
    "navigation_depth": 2,
    "titles_only": True,
}
html_extra_path = ["figures", "../IDICS_2024"]
