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
    ## R3XA Tutorial 5 - Validation or `R3XAFile` and `R3XAItem`
    First load an existing R3XA file
    """)
    return


@app.cell
def _(artifacts):
    import r3xa_api as r3xa
    my_file = r3xa.R3XAFile.load(artifacts / 'tutorial0_r3xa_file.json')
    print(my_file)
    return (my_file,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Validating a R3XAFile** <br>
    _Returns the item is validation is ok_
    """)
    return


@app.cell
def _(my_file):
    my_file.validate()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Validating a R3XAItem.setting** <br>
    """)
    return


@app.cell
def _(my_file):
    light = my_file.settings[0]
    light.validate()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Validating a R3XAItem.data_source** <br>
    """)
    return


@app.cell
def _(my_file):
    camera = my_file.data_sources[0]
    camera.validate()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Validating a R3XAItem.data_set** <br>
    """)
    return


@app.cell
def _(my_file):
    images = my_file.data_sets[0]
    images.validate()
    return


if __name__ == "__main__":
    app.run()
