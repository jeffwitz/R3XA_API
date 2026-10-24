import marimo

__generated_with = "0.20.2"
app = marimo.App(width="full")


@app.cell
def _():
    from html import escape
    from pathlib import Path

    import marimo as mo
    from r3xa_api import R3XAFile

    repo_root = Path(__file__).resolve().parents[3]
    source = repo_root / "tests" / "fixtures" / "documents" / "essai-torsion.json"
    return R3XAFile, escape, mo, repo_root, source


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Explore an existing R3XA document

    This independent tutorial opens the existing torsion-test JSON. It does
    not require you to run tutorials 0–5. The graph is read-only; click a
    node to inspect its fields, or double-click a data node to focus on its
    neighbours.
    """)
    return


@app.cell
def _(R3XAFile, source):
    document = R3XAFile.load(source)
    document.validate()
    print(f"Loaded: {document.title} ({len(document.data_sources)} sources, {len(document.data_sets)} sets)")
    return (document,)


@app.cell
def _(document, escape, mo, repo_root):
    output = repo_root / "artifacts" / "examples" / "tutorials" / "torsion_cytoscape.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    html_path = document.plot(output, backend="cytoscape", include_description=False)
    markup = escape(html_path.read_text(encoding="utf-8"), quote=True)
    mo.Html(
        '<iframe title="Interactive R3XA torsion graph" sandbox="allow-scripts" '
        'style="width:100%;height:760px;border:1px solid #d7dfe8;border-radius:8px" '
        f'srcdoc="{markup}"></iframe>'
    )
    return (html_path,)


@app.cell(hide_code=True)
def _(html_path, mo, repo_root):
    mo.md(f"""
    The same standalone HTML is saved at `{html_path.relative_to(repo_root)}`.
    """)
    return


if __name__ == "__main__":
    app.run()
