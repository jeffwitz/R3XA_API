from pathlib import Path

import jsonschema

from r3xa_api import R3XAFile, Registry, RegistryItem, load_item, load_registry, merge_item, unit, validate_item


def test_validate_registry_items():
    root = Path(__file__).parents[1] / "registry"
    items = sorted(root.rglob("*.json"))

    for path in items:
        item = load_item(path)
        validate_item(item)


def test_merge_item_overrides():
    root = Path(__file__).parents[1] / "registry"
    base = load_item(root / "data_sources" / "generic" / "pyxel_dic_2d.json")
    merged = merge_item(base, id="ds_custom", description="custom")
    assert merged["id"] == "ds_custom"
    assert merged["description"] == "custom"


def test_registry_class():
    root = Path(__file__).parents[1] / "registry"
    registry = Registry(root)
    item = registry.get_validated("settings/specimen/openhole_sample")
    assert item["kind"] == "settings/specimen"
    assert registry.load("settings/specimen/openhole_sample")["kind"] == "settings/specimen"
    assert registry.load_validated("settings/specimen/openhole_sample")["kind"] == "settings/specimen"


def test_registry_list_and_iteration():
    root = Path(__file__).parents[1] / "registry"
    registry = Registry(root)

    all_items = registry.list()
    specimen_items = registry.list(section="settings")
    camera_items = registry.list(kind="data_sources/camera")
    validated_items = list(registry.iter_items(kind="data_sources/camera", validated=True))
    wrapped_items = list(registry.iter_items(kind="data_sources/camera", validated=True, wrapped=True))

    assert "settings/specimen/openhole_sample" in all_items
    assert all(tree_path.startswith("settings/") for tree_path in specimen_items)
    assert "data_sources/camera/avt_dolphin_f145b" in camera_items
    assert validated_items
    assert wrapped_items
    assert validated_items[0][0].startswith("data_sources/camera/")
    assert validated_items[0][1]["kind"] == "data_sources/camera"
    assert isinstance(wrapped_items[0][1], RegistryItem)
    assert wrapped_items[0][1].tree_path.startswith("data_sources/camera/")


def test_registry_merge():
    root = Path(__file__).parents[1] / "registry"
    registry = Registry(root)
    merged = registry.merge(
        "data_sources/generic/pyxel_dic_2d",
        id="ds_custom",
        description="custom",
    )

    assert merged["id"] == "ds_custom"
    assert merged["description"] == "custom"
    assert isinstance(merged, RegistryItem)


def test_registry_item_workflow(tmp_path: Path):
    registry = Registry(tmp_path)
    tree_path = "data_sources/camera/test_camera"
    item = RegistryItem(
        {
            "id": "ds_cam_item",
            "kind": "data_sources/camera",
            "title": "Test camera",
            "description": "Wrapped registry item",
            "output_components": 1,
            "output_dimension": "surface",
            "output_units": [{"kind": "unit", "unit": "gl"}],
            "manufacturer": "Test manufacturer",
            "model": "Test model",
            "image_size": [{"kind": "unit", "unit": "px"}],
        },
        registry_root=tmp_path,
        tree_path=tree_path,
    )

    output_path = item.validate().save()

    assert output_path == tmp_path / "data_sources" / "camera" / "test_camera.json"

    loaded = registry.get_item(tree_path)
    assert isinstance(loaded, RegistryItem)
    assert loaded["kind"] == "data_sources/camera"
    assert loaded.path == output_path

    merged = loaded.merge(description="Updated description")
    assert isinstance(merged, RegistryItem)
    assert merged["description"] == "Updated description"

    standalone_output = merged.save(tmp_path / "camera_copy.json")
    assert standalone_output == tmp_path / "camera_copy.json"


def test_registry_item_can_be_appended_to_r3xafile() -> None:
    registry = Registry(Path(__file__).parents[1] / "registry")
    camera = registry.get_item("data_sources/camera/avt_dolphin_f145b")

    r3xa = R3XAFile(
        title="Registry item append",
        description="Append RegistryItem directly to a file",
        authors="R3XA API",
        date="2026-04-03",
    )
    r3xa.data_sources.append(camera)
    r3xa.add_list_data_set(
        title="Images",
        description="Camera image sequence",
        file_type="image/tiff",
        path="images/",
        data_sources=[camera["id"]],
        time_reference=unit(unit="s"),
        timestamps=[0.0],
        data=["img_0000.tif"],
    )

    validate_item(camera)
    assert r3xa.to_dict()["data_sources"][0]["kind"] == "data_sources/camera"


def test_load_registry_structure():
    root = Path(__file__).parents[1] / "registry"
    reg = load_registry(root)
    assert "settings" in reg
    assert "data_sources" in reg
    assert "data_sets" in reg
    assert "settings/specimen" in reg["settings"]
    assert "data_sources/camera" in reg["data_sources"]
    assert "data_sets/list" in reg["data_sets"]
