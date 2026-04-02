from pathlib import Path

from r3xa_api import Registry, new_item, save_item_path, unit

registry_root = Path(__file__).parents[2] / "registry"
tree_path = "data_sources/camera/example_generated_camera"

camera = new_item(
    "data_sources/camera",
    id="ds_cam_example_generated",
    title="Example generated camera",
    description="Example registry camera generated with R3XA_API",
    output_components=1,
    output_dimension="surface",
    output_units=[unit(title="graylevel", value=1.0, unit="gl", scale=1.0)],
    manufacturer="Example manufacturer",
    model="Example model",
    image_size=[
        unit(title="width", value=2048, unit="px", scale=1.0),
        unit(title="height", value=1536, unit="px", scale=1.0),
    ],
    focal_length=unit(title="focal_length", value=35.0, unit="mm", scale=1.0),
)

output_path = save_item_path(registry_root, tree_path, camera)

registry = Registry(registry_root)
loaded = registry.get_validated(tree_path)

print(f"Registry item written to: {output_path}")
print(f"Validated kind: {loaded['kind']}")
print(f"Reusable key: {tree_path}")
