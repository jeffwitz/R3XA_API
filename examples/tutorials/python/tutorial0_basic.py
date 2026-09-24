"""
## R3XA Tutorial 0 - creating, plotting and saving a first basic R3XA file
First load the R3XA API python package
"""

from pathlib import Path

import r3xa_api as r3xa

ARTIFACTS = Path(__file__).resolve().parents[3] / "artifacts" / "examples" / "tutorials"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

"""
### Header
_Contains the general information used to identify and document the dataset, such as its title, description, version, authors, and date + other optional attributes._

One of the main attributes of the `header` of R3XA file is the list of authors. <br>
Let's first create an author object:
"""

josiah = r3xa.author(
    'J. S. Carberry',
    'Brown University',
    'https://orcid.org/0000-0002-1825-0097'
    )

"""
Then creating a new R3XA file required to fill the `header` information:
"""

my_file = r3xa.R3XAFile(
    title="R3XA first tutorial",
    description="Minimal example of a R3XA file",
    authors=[josiah],
    date="2026-09-16"
    )

"""
After the header information, 3 lists must be filled:
1. Settings
2. Data_Sources
3. Data_sets

### 1. Settings
_`settings` is a list of devices not directly generating data but describing the experimental context, including the test specimen, testing machines, equipment, and conditions used during the experiment (ex: testing machine, light, environment chamber...)._

 Adding a new `setting`, here a spot light.
"""

light = my_file.add_generic_setting(
    id="stg-generic-tutorial0-light",
    title='Spot light',
    description='Spotlight MultiLed',
    documentation='MULTILED_QX.pdf',
    power='fullgaz'
    )

"""
### 2. Data Sources
_`data_sources` is a list of sensors or analysis tools that directly generate or calculate data, including the sensors, cameras, or analysis methods used and their characteristics._

Adding a new `data_source` of type camera
"""

camera = my_file.add_camera_source(
    id="src-camera-tutorial0-camera",
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

"""
### 3. Data sets
_`data_sets` is a list of datasets describing how and where the data are stored, their unit and format, linking the data files to the source that produced them and, when needed, to their time references._

Adding a new `data_set` example as a list of digital images
"""

image_files = ['img_0000.tif', 'img_0001.tif', 'img_0002.tif']
timestamps = [1.0, 1.5, 2]

images = my_file.add_list_data_set(
    id="set-list-tutorial0-images",
    title="visible images",
    description="my graylevel images",
    path="images/",
    data_type="image/tiff",
    parent_data_sources=[camera],
    time_reference=r3xa.unit(title="time_reference", value=0.0, unit="s", scale=1.0),
    timestamps=timestamps,
    values=image_files,
)

"""
### Saving R3XA files
"""

"""
To **save a R3XA file** to the disk
"""

my_file.save(ARTIFACTS / 'tutorial0_r3xa_file.json')
