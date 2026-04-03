from r3xa_api import R3XAFile, Registry, unit

registry = Registry("registry")

# Load reusable items
specimen_base = registry.get_item("settings/specimen/openhole_sample")
camera_base = registry.get_item("data_sources/camera/avt_dolphin_f145b")
pyxel_base = registry.get_item("data_sources/generic/pyxel_dic_2d")

# Customize for this experiment
specimen = specimen_base.merge(id="set_spec_exp01")

camera = camera_base.merge(
    id="ds_cam_exp01",
    description="CCD Camera (exp01)",
    standoff_distance=unit(title="standoff", value=0.5, unit="m", scale=1.0),
)

# Header
r3xa = R3XAFile(
    title="Open-hole tensile test with DIC (registry)",
    description="Camera acquisition + DIC processing pipeline (registry-based)",
    authors="R3XA API",
    date="2024-10-30",
)

r3xa.settings.append(specimen)
r3xa.data_sources.append(camera)

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
    time_reference=unit(title="time_reference", value=0.0, unit="s", scale=1.0),
    timestamps=timestamps,
    data=image_files,
)

# DIC processing data source (generic from registry)
dic = pyxel_base.merge(
    id="ds_dic_exp01",
    input_data_sets=[images["id"]],
)

r3xa.data_sources.append(dic)

# DIC result dataset (list of result files)
dic_files = [f"dic_{i:04d}.csv" for i in range(num_frames)]

r3xa.add_image_set_list(
    title="DIC displacement fields",
    description="ux, uy per frame",
    path="dic/",
    file_type="text/csv",
    data_sources=[dic["id"]],
    time_reference=unit(title="time_reference", value=0.0, unit="s", scale=1.0),
    timestamps=timestamps,
    data=dic_files,
)

# Validate and save
r3xa.validate()
r3xa.save("examples/artifacts/dic_pipeline_registry.json")
