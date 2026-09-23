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
    ## R3XA Tutorial 2 - Opening and editing an existing R3XA File
    Opening an existing R3XA File and add attributes, `settings`, `data_sources` or `data_sets`
    """)
    return


@app.cell
def _():
    import r3xa_api as r3xa

    return (r3xa,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **load** an existing R3XA file
    """)
    return


@app.cell
def _(artifacts, r3xa):
    my_file = r3xa.R3XAFile.load(artifacts / 'tutorial0_r3xa_file.json')
    print(my_file)
    return (my_file,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Add missign attributes in the header
    """)
    return


@app.cell
def _(my_file):
    my_file.documentation = 'https://r3xa-spec.readthedocs.io/en/latest/specification.html'
    print(my_file)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Adding a `setting`
    """)
    return


@app.cell
def _(my_file, r3xa):
    specimen = r3xa.new_specimen_setting(
        title="Sample",
        description="Stainless Steel openhole plate",
        sizes=[r3xa.unit('width', 30, 'mm'), r3xa.unit('length', 120, 'mm'), r3xa.unit('hole radius', 8, 'mm')],
        patterning_technique="black and white spray paint",
        )
    my_file.settings.append(specimen)
    print(my_file)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And **save** it again
    """)
    return


@app.cell
def _(artifacts, my_file):
    my_file.save(artifacts / 'tutorial1_r3xa_file.json')
    return


if __name__ == "__main__":
    app.run()
