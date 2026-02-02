from r3xa_api import R3XAFile, unit

# Header
r3xa = R3XAFile(
    title="Open-hole tensile test with DIC",
    description="Camera acquisition + DIC processing pipeline",
    authors="R3XA API",
    date="2024-10-30",
)

# Settings
specimen = r3xa.add_specimen_setting(
    title="Openhole sample",
    description="Glass-epoxy specimen",
    sizes=[
        unit(title="width", value=30.0, unit="mm", scale=1.0),
        unit(title="thickness", value=2.0, unit="mm", scale=1.0),
    ],
    patterning_technique="white background with black spray paint",
)

# Camera data source (acquisition)
camera = r3xa.add_camera_source(
    title="CCD Camera",
    description="Encoding: 8-bit",
    output_components=1,
    output_dimension="surface",
    output_units=[unit(title="graylevel", value=1.0, unit="gl", scale=1.0)],
    manufacturer="Allied Vision Technologies (AVT)",
    model="Dolphin F-145B",
    image_size=[
        unit(title="width", value=1392, unit="px", scale=1.0),
        unit(title="height", value=1040, unit="px", scale=1.0),
    ],
    focal_length=unit(title="focal_length", value=25.0, unit="mm", scale=1.0),
    standoff_distance=unit(title="standoff", value=0.5, unit="m", scale=1.0),
)

# Image dataset (list)
num_frames = 5
image_files = [f"img_{i:04d}.tif" for i in range(num_frames)]
timestamps = [i * 0.5 for i in range(num_frames)]

images = r3xa.add_image_set_list(
    title="graylevel images",
    description="raw images from CCD camera",
    path="images/",
    file_type="image/tiff",
    data_sources=[camera["id"]],
    time_reference=0.0,
    timestamps=timestamps,
    data=image_files,
)

# DIC processing data source (generic)
dic = r3xa.add_data_source(
    "data_sources/generic",
    title="DIC processing (pyxel)",
    description="2D DIC using pyxel",
    output_components=2,
    output_dimension="surface",
    output_units=[
        unit(title="ux", value=1.0, unit="mm", scale=1.0),
        unit(title="uy", value=1.0, unit="mm", scale=1.0),
    ],
    manufacturer="Pyxel",
    model="pyxel-2d",
    input_data_sets=[images["id"]],
)

# DIC result dataset (list of result files)
dic_files = [f"dic_{i:04d}.csv" for i in range(num_frames)]

r3xa.add_image_set_list(
    title="DIC displacement fields",
    description="ux, uy per frame",
    path="dic/",
    file_type="text/csv",
    data_sources=[dic["id"]],
    time_reference=0.0,
    timestamps=timestamps,
    data=dic_files,
)

# Validate and save
r3xa.validate()
r3xa.save("examples/artifacts/dic_pipeline.json")
