"""
## R3XA Tutorial 5 - Validation or `R3XAFile` and `R3XAItem`
First load an existing R3XA file
"""

from pathlib import Path

import r3xa_api as r3xa

ARTIFACTS = Path(__file__).resolve().parents[3] / "examples" / "artifacts" / "tutorials"
my_file = r3xa.R3XAFile.load(ARTIFACTS / 'tutorial0_r3xa_file.json')
print(my_file)

"""
**Validating a R3XAFile** <br>
`validate()` returns `None` when validation succeeds and raises when it fails.
"""

my_file.validate()

"""
**Validating a R3XAItem.setting** <br>
"""

light = my_file.settings[0]
light.validate()

"""
**Validating a R3XAItem.data_source** <br>
"""

camera = my_file.data_sources[0]
camera.validate()

"""
**Validating a R3XAItem.data_set** <br>
"""

images = my_file.data_sets[0]
images.validate()
