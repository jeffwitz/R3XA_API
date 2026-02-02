import json
from r3xa_api import R3XAFile, Registry, merge_item

registry = Registry("registry")

camera_base = registry.get_validated("data_sources/camera/avt_dolphin_f145b")

# Override ID and description for a specific experiment
camera = merge_item(camera_base, id="ds_cam_exp01", description="CCD Camera (exp01)")

specimen = registry.get_validated("settings/specimen/openhole_sample")

r3xa = R3XAFile(
    title="Experiment with registry items",
    description="Using registry items to build an R3XA file",
    authors="R3XA API",
    date="2024-10-30",
)

r3xa.settings.append(specimen)
r3xa.data_sources.append(camera)

# Minimal dataset (filled by user later)
image_template = registry.get_validated("data_sets/list/camera_images_template")
image_dataset = merge_item(
    image_template,
    id="dset_images_exp01",
    data_sources=[camera["id"]],
    timestamps=[0.0, 1.0, 2.0],
    data=["img_0001.tif", "img_0002.tif", "img_0003.tif"],
)

r3xa.data_sets.append(image_dataset)

r3xa.validate()
r3xa.save("registry_example.json")

print(json.dumps(r3xa.to_dict(), indent=2))
