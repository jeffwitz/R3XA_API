"""
## R3XA Tutorial 4 - `File` vs `List` data sets
Compare a list of image names with equivalent columns stored in a CSV file.<br>
First **load an existing R3XA file**
"""

from pathlib import Path

import r3xa_api as r3xa

ARTIFACTS = Path(__file__).resolve().parents[3] / "artifacts" / "examples" / "tutorials"
my_file = r3xa.R3XAFile.load(ARTIFACTS / 'tutorial0_r3xa_file.json')
camera = my_file.data_sources[0]

"""
### List data set
Create a data set of type `list` from the image names and timestamps.
"""

image_files = ['img_0000.tif', 'img_0001.tif', 'img_0002.tif', 'img_0003.tif']
timestamps = [0.0, 0.1, 0.2, 0.3]
t0 = r3xa.unit(title="time_reference", value=0.0, unit="s", scale=1.0)

ds_list = r3xa.new_list_data_set(
    id="set-list-tutorial4-images",
    title="visible images (list)",
    description="my graylevel images",
    path="images/",
    data_type="image/tiff",
    parent_data_sources=[camera],
    time_reference=t0,
    timestamps=timestamps,
    values=image_files,
)

"""
**Overwriting the data_sets** of the R3XA document and **Saving to the disk** <br>
_(for adding a data_set, type `my_file.data_sets += [ds_list,]`)_
"""

my_file.data_sets = [ds_list,]
my_file.save(ARTIFACTS / 'tutorial4_list.json')

"""
### File data set <br>
The example CSV is `tutorial4_file.csv` in this artifact directory. It contains
four data rows (no header): timestamp in column 0 and image filename in column 1.
"""

t0 = r3xa.unit(title="time_reference", value=0.0, unit="s", scale=1.0)

images_file = r3xa.data_set_file(
    filename = 'tutorial4_file.csv',
    file_type = 'text/csv',
    delimiter = ';',
    col = 1,
    rows = [0, 3],
)

timestamps = r3xa.data_set_file(
    filename = 'tutorial4_file.csv',
    file_type = 'text/csv',
    delimiter = ';',
    col = 0,
    rows = [0, 3],
)

ds_file = r3xa.new_file_data_set(
    id="set-file-tutorial4-images",
    title="visible images (file)",
    description="my graylevel images",
    path="images/",
    data_type="image/tiff",
    parent_data_sources=[camera],
    time_reference=t0,
    timestamps=timestamps,
    values=images_file,
)

my_file.data_sets = [ds_file,]
my_file.save(ARTIFACTS / 'tutorial4_file.json')
