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
    ## R3XA Tutorial 4 - `File` vs `List` data_sets
    List and File are the two main data_set types. How does it work ?<br>
    First **load an existing R3XA file**
    """)
    return


@app.cell
def _(artifacts):
    import r3xa_api as r3xa
    my_file = r3xa.R3XAFile.load(artifacts / 'tutorial0_r3xa_file.json')
    camera = my_file.data_sources[0]
    return artifacts, camera, my_file, r3xa


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### List data source
    Creating a data_source of type 'list' require to first create the lists
    """)
    return


@app.cell
def _(camera, r3xa):
    image_files = ['img_0000.tif', 'img_0001.tif', 'img_0002.tif', 'img_0003.tif']
    _timestamps = [0.0, 0.1, 0.2, 0.3]
    _t0 = r3xa.unit(title='time_reference', value=0.0, unit='s', scale=1.0)
    ds_list = r3xa.new_list_data_set(title='visible images (list)', description='my graylevel images', path='images/', data_type='image/tiff', parent_data_sources=[camera], time_reference=_t0, timestamps=_timestamps, values=image_files)
    return (ds_list,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Overwriting the data_sets** of the R3XA document and **Saving to the disk** <br>
    _(for adding a data_set, type `my_file.data_sets += [ds_list,]`)_
    """)
    return


@app.cell
def _(artifacts, ds_list, my_file):
    my_file.data_sets = [ds_list,]
    my_file.save(artifacts / 'tutorial3_list.json')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### File data source <br>
    Let's now build the same data_set but with type file. Have a look at the CSV file
    """)
    return


@app.cell
def _(camera, r3xa):
    _t0 = r3xa.unit(title='time_reference', value=0.0, unit='s', scale=1.0)
    images_file = r3xa.data_set_file(filename='tutorial3_file.csv', file_type='text/csv', delimiter=';', col='1', rows=[1, 5])
    _timestamps = r3xa.data_set_file(filename='tutorial3_file.csv', file_type='text/csv', delimiter=';', col='0', rows=[1, 5])
    ds_file = r3xa.new_file_data_set(title='visible images (file)', description='my graylevel images', path='images/', data_type='image/tiff', parent_data_sources=[camera], time_reference=_t0, timestamps=_timestamps, values=images_file)
    return (ds_file,)


@app.cell
def _(artifacts, ds_file, my_file):
    my_file.data_sets = [ds_file,]
    my_file.save(artifacts / 'tutorial3_file.json')
    return


if __name__ == "__main__":
    app.run()
