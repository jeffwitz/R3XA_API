import os

project = "R3XA_API"
author = "R3XA_API"
extensions = ["myst_parser", "sphinxcontrib.mermaid"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "internal/*"]
html_theme = "sphinx_rtd_theme"
html_title = "R3XA_API"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "titles_only": False,
    "includehidden": True,
}
html_extra_path = ["figures", "archive/PM_IDICS_2024"]

_rtd_version = os.environ.get("READTHEDOCS_VERSION", "develop")
if _rtd_version == "latest":
    _rtd_version = "develop"
elif _rtd_version == "stable":
    _rtd_version = "main"

github_base = f"https://github.com/jeffwitz/R3XA_API/blob/{_rtd_version}"

myst_substitutions = globals().get("myst_substitutions", {})
myst_substitutions.update({
    "github_base": github_base,
})

# Force a global, uniform sidebar on every page (no local overrides)
html_sidebars = {
    "**": [
        "globaltoc.html",
        "relations.html",
        "sourcelink.html",
        "searchbox.html",
    ]
}
