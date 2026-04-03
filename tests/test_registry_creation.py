from pathlib import Path

from r3xa_api import Registry, new_item, save_item_path, unit


def test_save_item_path_creates_valid_registry_camera(tmp_path: Path):
    tree_path = "data_sources/camera/test_generated_camera"
    camera = new_item(
        "data_sources/camera",
        id="ds_cam_test_generated",
        title="Generated test camera",
        description="Registry camera generated during unit test",
        output_components=1,
        output_dimension="surface",
        output_units=[unit(title="graylevel", value=1.0, unit="gl", scale=1.0)],
        manufacturer="Test manufacturer",
        model="Test model",
        image_size=[
            unit(title="width", value=640, unit="px", scale=1.0),
            unit(title="height", value=480, unit="px", scale=1.0),
        ],
    )

    output_path = save_item_path(tmp_path, tree_path, camera)

    assert output_path == tmp_path / "data_sources" / "camera" / "test_generated_camera.json"
    assert output_path.exists()

    registry = Registry(tmp_path)
    loaded = registry.get_validated(tree_path)
    assert loaded["id"] == "ds_cam_test_generated"


def test_registry_wrap_and_save_creates_valid_registry_camera(tmp_path: Path):
    tree_path = "data_sources/camera/test_wrapped_camera"
    camera = new_item(
        "data_sources/camera",
        id="ds_cam_wrapped",
        title="Wrapped test camera",
        description="Registry camera saved through RegistryItem.save()",
        output_components=1,
        output_dimension="surface",
        output_units=[unit(unit="gl")],
        manufacturer="Wrapped manufacturer",
        model="Wrapped model",
        image_size=[
            unit(unit="px"),
        ],
    )

    registry = Registry(tmp_path)
    output_path = registry.wrap(camera, tree_path=tree_path).validate().save()

    assert output_path == tmp_path / "data_sources" / "camera" / "test_wrapped_camera.json"
    assert registry.get_item(tree_path)["id"] == "ds_cam_wrapped"
