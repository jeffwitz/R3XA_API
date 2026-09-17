from pathlib import Path

from r3xa_api import author, R3XAFile, unit

# Anchored on this file so the example writes to examples/artifacts/ whatever
# the working directory, instead of dropping a file in the repository root.
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

r3xa = R3XAFile(
    title="Hello World",
    description="Minimal R3XA file",
    authors=[{"name": "JC Passieux"}],
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
    lens="50mm prime",
    aperture="f/8",
    exposure=unit(title="exposure", value=2.0, unit="ms", scale=1.0),
)

r3xa.add_list_data_set(
    title="graylevel images",
    description="images taken by the CCD camera",
    path="images/",
    data_type="image/tiff",
    parent_data_sources=[camera],
    time_reference=unit(title="time_reference", value=0.0, unit="s", scale=1.0),
    timestamps=[0.0, 1.0],
    values=["zoom-0050_1.tif", "zoom-0070_1.tif"],
)

r3xa.validate()

r3xa.save(ARTIFACTS / "hello-world.json")
