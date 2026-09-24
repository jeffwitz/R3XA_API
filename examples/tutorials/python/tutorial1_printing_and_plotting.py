"""
## R3XA Tutorial 1 - Printing and plotting a R3XA File or Items
Opening an existing R3XA File
"""

from pathlib import Path

import r3xa_api as r3xa

ARTIFACTS = Path(__file__).resolve().parents[3] / "artifacts" / "examples" / "tutorials"
my_file = r3xa.R3XAFile.load(ARTIFACTS / 'tutorial0_r3xa_file.json')

"""
### 1. Printing
To print the content of the file in ASCII readable format
"""

print(my_file)

"""
To print the content of an Item in ASCII readable format
"""

camera = my_file.data_sources[0]
print(camera)

"""
Exercise: Try to print() the settings, the data_sets, and also the authors
"""

"""
### 2. Plotting
To plot the structure of a R3XA file as a colored flowchart in Scalable Vector Graphics (SVG) file
"""

my_file.plot(ARTIFACTS / 'tutorial1_image.svg')
