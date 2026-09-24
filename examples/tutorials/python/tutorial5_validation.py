"""
## R3XA Tutorial 5 - Validation of `R3XAFile` and `R3XAItem`
First load an existing R3XA file
"""

from pathlib import Path

import r3xa_api as r3xa
import jsonschema

ARTIFACTS = Path(__file__).resolve().parents[3] / "artifacts" / "examples" / "tutorials"
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

"""
**Inspecting a validation error**

Validation raises a useful error when the document does not match the schema.
This deliberately invalid copy does not alter the valid example loaded above.
"""

invalid_file = r3xa.R3XAFile.from_dict(my_file.to_dict())
invalid_file.date = "2026-02-31"
try:
    invalid_file.validate()
except jsonschema.exceptions.ValidationError as error:
    print(error)
