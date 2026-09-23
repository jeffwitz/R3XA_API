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
    ## R3XA Tutorial 0 - creating, plotting and saving a first basic R3XA file
    First load the R3XA API python package
    """)
    return


@app.cell
def _():
    import r3xa_api as r3xa

    return (r3xa,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Header
    _Contains the general information used to identify and document the dataset, such as its title, description, version, authors, and date + other optional attributes._

    One of the main attributes of the `header` of R3XA file is the list of authors. <br>
    Let's first create an author object:
    """)
    return


@app.cell
def _(r3xa):
    josiah = r3xa.author(
        'J. S. Carberry',
        'Brown University',
        'https://orcid.org/0000-0002-1825-0097'
        )
    return (josiah,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Then creating a new R3XA file required to fill the `header` information:
    """)
    return


@app.cell
def _(josiah, r3xa):
    my_file = r3xa.R3XAFile(
        title="R3XA first tutorial",
        description="Minimal example of a R3XA file",
        authors=[josiah],
        date="2026-09-16"
        )
    return (my_file,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    After the header information, 3 lists must be filled:
    1. Settings
    2. Data_Sources
    3. Data_sets

    ### 1. Settings
    _`settings` is a list of devices not directly generating data but describing the experimental context, including the test specimen, testing machines, equipment, and conditions used during the experiment (ex: testing machine, light, environment chamber...)._

     Adding a new `setting`, here a spot light.
    """)
    return


@app.cell
def _(my_file):
    light = my_file.add_generic_setting(
        title='Spot light',
        description='Spotlight MultiLed',
        documentation='MULTILED_QX.pdf',
        power='fullgaz'
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2. Data Sources
    _`data_sources` is a list of sensors or analysis tools that directly generate or calculate data, including the sensors, cameras, or analysis methods used and their characteristics._

    Adding a new `data_source` of type camera
    """)
    return


@app.cell
def _(my_file, r3xa):
    camera = my_file.add_camera_source(
        title="CCD Camera",
        description="",
        output_components=1,
        output_dimension="surface",
        output_units=[r3xa.unit(unit="gl")],
        manufacturer="Allied Vision Technologies (AVT)",
        model="Dolphin F-145B",
        image_size=[
            r3xa.unit(title="width", value=1392, unit="px"),
            r3xa.unit(title="height", value=1040, unit="px"),
        ]
    )
    return (camera,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3. Data sets
    _`data_sets` is a list of datasets describing how and where the data are stored, their unit and format, linking the data files to the source that produced them and, when needed, to their time references._

    Adding a new `data_set` example as a list of digital images
    """)
    return


@app.cell
def _(camera, my_file, r3xa):
    image_files = ['img_0000.tif', 'img_0001.tif', 'img_0002.tif']
    timestamps = [1.0, 1.5, 2]

    images = my_file.add_list_data_set(
        title="visible images",
        description="my graylevel images",
        path="images/",
        data_type="image/tiff",
        parent_data_sources=[camera],
        time_reference=r3xa.unit(title="time_reference", value=0.0, unit="s", scale=1.0),
        timestamps=timestamps,
        values=image_files,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Saving R3XA files
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To **save a R3XA file** to the disk
    """)
    return


@app.cell
def _(artifacts, my_file):
    my_file.save(artifacts / 'tutorial0_r3xa_file.json')
    return


if __name__ == "__main__":
    app.run()
