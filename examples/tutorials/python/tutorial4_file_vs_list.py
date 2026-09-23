"""
## R3XA Tutorial 4 - `File` vs `List` data_sets
List and File are the two main data_set types. How does it work ?<br>
First **load an existing R3XA file**
"""

from pathlib import Path

import r3xa_api as r3xa

ARTIFACTS = Path(__file__).resolve().parents[3] / "examples" / "artifacts" / "tutorials"
my_file = r3xa.R3XAFile.load(ARTIFACTS / 'tutorial0_r3xa_file.json')
camera = my_file.data_sources[0]

"""
### List data source
Creating a data_source of type 'list' require to first create the lists
"""

image_files = ['img_0000.tif', 'img_0001.tif', 'img_0002.tif', 'img_0003.tif']
timestamps = [0.0, 0.1, 0.2, 0.3]
t0 = r3xa.unit(title="time_reference", value=0.0, unit="s", scale=1.0)

ds_list = r3xa.new_list_data_set(
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
my_file.save(ARTIFACTS / 'tutorial3_list.json')

"""
### File data source <br>
Let's now build the same data_set but with type file. Have a look at the CSV file
"""

t0 = r3xa.unit(title="time_reference", value=0.0, unit="s", scale=1.0)

images_file = r3xa.data_set_file(
    filename = 'tutorial3_file.csv',
    file_type = 'text/csv',
    delimiter = ';',
    col = '1',
    rows = [1, 5],
)

timestamps = r3xa.data_set_file(
    filename = 'tutorial3_file.csv',
    file_type = 'text/csv',
    delimiter = ';',
    col = '0',
    rows = [1, 5],
)

ds_file = r3xa.new_file_data_set(
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
my_file.save(ARTIFACTS / 'tutorial3_file.json')
