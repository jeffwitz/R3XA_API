from pathlib import Path

import jsonschema

from r3xa_api import load_item, validate_item, load_registry, merge_item, Registry


def test_validate_registry_items():
    root = Path(__file__).parents[1] / "registry"
    items = [
        root / "settings" / "generic" / "instron_5800.json",
        root / "settings" / "specimen" / "openhole_sample.json",
        root / "data_sources" / "camera" / "avt_dolphin_f145b.json",
        root / "data_sources" / "generic" / "pyxel_dic_2d.json",
        root / "data_sets" / "list" / "camera_images_template.json",
        root / "data_sets" / "file" / "tabular_timeseries_template.json",
    ]

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


def test_load_registry_structure():
    root = Path(__file__).parents[1] / "registry"
    reg = load_registry(root)
    assert "settings" in reg
    assert "data_sources" in reg
    assert "data_sets" in reg
    assert "settings/specimen" in reg["settings"]
    assert "data_sources/camera" in reg["data_sources"]
    assert "data_sets/list" in reg["data_sets"]
