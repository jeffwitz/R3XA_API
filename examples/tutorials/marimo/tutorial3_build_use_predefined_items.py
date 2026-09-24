import marimo

__generated_with = "0.20.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    from pathlib import Path

    artifacts = Path(__file__).resolve().parents[3] / "artifacts" / "examples" / "tutorials"
    return artifacts, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## R3XA Tutorial 3 - Using existing `items`
    Saving, loading and using a predefined `setting` or `data_source`
    """)
    return


@app.cell
def _():
    import r3xa_api as r3xa

    return (r3xa,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In earlier tutorials, data sources, data sets, and settings were created from an R3XA file, for example:<br>
    ``my_file.add_camera_source(...)`` <br><br>
    A new data source can be **created outside a R3XA file** using:<br>
    ``r3xa.new_camera_source(...)`` <br><br>

    with exactly the same arguments
    """)
    return


@app.cell
def _(r3xa):
    my_torque_sensor = r3xa.new_generic_source(
        id="src-generic-tutorial3-torque-sensor",
        title='Dynamic Torque sensor',
        description='Andilog Dynamic Torque sensor. \nCapacity 6Nm. \nResolution : 0,6 mNm',
        output_components=1,
        output_dimension='point',
        output_units=[r3xa.unit('torque', 0, 'N.m'),],
        manufacturer='Andilog',
        model='SPIP TT 6',
        documentation='https://pdf.directindustry.com/pdf/andilog-technologies/andilog-force-torque-measurements/7999-34677.html'
        )
    return (my_torque_sensor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Check its validation of the schema
    """)
    return


@app.cell
def _(my_torque_sensor):
    my_torque_sensor.validate()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And save it to the disk
    """)
    return


@app.cell
def _(artifacts, my_torque_sensor):
    my_torque_sensor.save(artifacts / 'tutorial3_andilog_dynamic_torque_sensor.json')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Loading an existing device** and add it to an existing R3XA File
    """)
    return


@app.cell
def _(artifacts, r3xa):
    device = r3xa.R3XAItem.load(artifacts / 'tutorial3_andilog_dynamic_torque_sensor.json')
    my_file = r3xa.R3XAFile.load(artifacts / 'tutorial2_r3xa_file.json')
    my_file.data_sources.append(device)
    print(my_file)
    return (my_file,)


@app.cell
def _(artifacts, mo, my_file):
    svg_path = my_file.plot(artifacts / 'tutorial3_image.svg')
    mo.Html(
        '<div class="r3xa-inline-graph">'
        + svg_path.read_text(encoding='utf-8')
        + '</div>'
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Saving a particular item inside a full R3XA file is done like this:
    """)
    return


@app.cell
def _(artifacts, my_file):
    my_file.data_sources[0].save(artifacts / 'tutorial3_camera.json')
    return


if __name__ == "__main__":
    app.run()
