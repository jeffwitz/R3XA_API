"""
## R3XA Tutorial 2 - Opening and editing an existing R3XA File
Opening an existing R3XA File and add attributes, `settings`, `data_sources` or `data_sets`
"""

from pathlib import Path

import r3xa_api as r3xa

ARTIFACTS = Path(__file__).resolve().parents[3] / "artifacts" / "examples" / "tutorials"

"""
**load** an existing R3XA file
"""

my_file = r3xa.R3XAFile.load(ARTIFACTS / 'tutorial0_r3xa_file.json')
print(my_file)

"""
Add missing attributes in the document header
"""

my_file.documentation = 'https://r3xa-spec.readthedocs.io/en/latest/specification.html'
print(my_file)

"""
Adding a `setting`
"""

specimen = r3xa.new_specimen_setting(
    id="stg-specimen-tutorial2",
    title="Sample",
    description="Stainless Steel openhole plate",
    sizes=[r3xa.unit('width', 30, 'mm'), r3xa.unit('length', 120, 'mm'), r3xa.unit('hole radius', 8, 'mm')],
    patterning_technique="black and white spray paint",
    )
my_file.settings.append(specimen)
print(my_file)

"""
And **save** it again
"""

my_file.save(ARTIFACTS / 'tutorial2_r3xa_file.json')
