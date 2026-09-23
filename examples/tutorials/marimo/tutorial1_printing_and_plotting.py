import marimo

__generated_with = "0.20.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    from pathlib import Path

    artifacts = Path(__file__).resolve().parents[3] / "examples" / "artifacts" / "tutorials"
    return artifacts, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## R3XA Tutorial 1 - Printing and plotting a R3XA File or Items
    Opening an existing R3XA File
    """)
    return


@app.cell
def _(artifacts):
    import r3xa_api as r3xa
    my_file = r3xa.R3XAFile.load(artifacts / 'tutorial0_r3xa_file.json')
    return (my_file,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1. Printing
    To print the content of the file in ASCII readable format
    """)
    return


@app.cell
def _(my_file):
    print(my_file)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To print the content of an Item in ASCII readable format
    """)
    return


@app.cell
def _(my_file):
    camera = my_file.data_sources[0]
    print(camera)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Exercise: Try to print() the settings, the data_sets, and also the authors
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2. Plotting
    To plot the structure of a R3XA file as a colored flowchart in Scalable Vector Graphics (SVG) file
    """)
    return


@app.cell
def _(artifacts, mo, my_file):
    svg_path = my_file.plot(artifacts / 'tutorial0_image.svg')
    mo.Html(
        '<div class="r3xa-inline-graph">'
        + svg_path.read_text(encoding='utf-8')
        + '</div>'
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The SVG is displayed inline above and also saved in the artifacts directory.
    """)
    return


if __name__ == "__main__":
    app.run()
