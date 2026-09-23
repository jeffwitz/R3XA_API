"""
## R3XA Tutorial 3 - Using existing `items`
Saving, loading and using a predefined `setting` or `data_source`
"""

from pathlib import Path

import r3xa_api as r3xa

ARTIFACTS = Path(__file__).resolve().parents[3] / "examples" / "artifacts" / "tutorials"

"""
In the previous tutorials, items (data_source, data_set of setting) were created from a R3XAfile, using for example:<br>
``my_file.add_camera_source(...)`` <br><br>
A new data source can be **created outside a R3XA file** using:<br>
``r3xa.new_camera_source(...)`` <br><br>

with exactly the same arguments
"""

my_torque_sensor = r3xa.new_generic_source(
    title='Dynamic Torque sensor',
    description='Andilog Dynamic Torque sensor. \nCapacity 6Nm. \nResolution : 0,6 mNm',
    output_components=1,
    output_dimension='point',
    output_units=[r3xa.unit('torque', 0, 'N.m'),],
    manufacturer='Andilog',
    model='SPIP TT 6',
    documentation='https://pdf.directindustry.com/pdf/andilog-technologies/andilog-force-torque-measurements/7999-34677.html'
    )

"""
Check its validation of the schema
"""

my_torque_sensor.validate()

"""
And save it to the disk
"""

my_torque_sensor.save(ARTIFACTS / 'tutorial2_andilog_dynamic_torque_sensor.json')

"""
**Loading an existing device** and add it to an existing R3XA File
"""

device = r3xa.R3XAItem.load(ARTIFACTS / 'tutorial2_andilog_dynamic_torque_sensor.json')
my_file = r3xa.R3XAFile.load(ARTIFACTS / 'tutorial1_r3xa_file.json')
my_file.data_sources.append(device)
print(my_file)

my_file.plot(ARTIFACTS / 'tutorial2_image.svg')

"""
Saving a particular item inside a full R3XA file is done like this:
"""

my_file.data_sources[0].save(ARTIFACTS / 'tutorial2_camera.json')
