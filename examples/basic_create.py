from r3xa_api import R3XAFile, unit

r3xa = R3XAFile(
    title="Hello World",
    description="Minimal R3XA file",
    authors=["JC Passieux"],
    date="2024-10-30",
)

r3xa.add_specimen_setting(
    title="Openhole sample",
    description="Glass-epoxy specimen",
    sizes=[unit(title="width", value=30.0, unit="mm", scale=1.0)],
)

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
    field_of_view=[
        unit(title="width", value=120.0, unit="mm", scale=1.0),
        unit(title="height", value=90.0, unit="mm", scale=1.0),
    ],
    focal_length=unit(title="focal_length", value=25.0, unit="mm", scale=1.0),
    standoff_distance=unit(title="standoff", value=0.5, unit="m", scale=1.0),
    noise=unit(title="noise", value=1.0, unit="gl", scale=1.0),
    lens="50mm prime",
    aperture="f/8",
    exposure=unit(title="exposure", value=2.0, unit="ms", scale=1.0),
)

r3xa.add_image_set_list(
    title="graylevel images",
    description="images taken by the CCD camera",
    path="images/",
    file_type="image/tiff",
    data_sources=[camera["id"]],
    time_reference=0.0,
    timestamps=[0.0, 1.0],
    data=["zoom-0050_1.tif", "zoom-0070_1.tif"],
)

r3xa.validate()

r3xa.save("hello-world.json")
