from pathlib import Path

import jsonschema

from r3xa_api import load_item, validate_item, load_registry, merge_item, Registry


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

    assert "settings/specimen/openhole_sample" in all_items
    assert all(tree_path.startswith("settings/") for tree_path in specimen_items)
    assert "data_sources/camera/avt_dolphin_f145b" in camera_items
    assert validated_items
    assert validated_items[0][0].startswith("data_sources/camera/")
    assert validated_items[0][1]["kind"] == "data_sources/camera"


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


def test_load_registry_structure():
    root = Path(__file__).parents[1] / "registry"
    reg = load_registry(root)
    assert "settings" in reg
    assert "data_sources" in reg
    assert "data_sets" in reg
    assert "settings/specimen" in reg["settings"]
    assert "data_sources/camera" in reg["data_sources"]
    assert "data_sets/list" in reg["data_sets"]
