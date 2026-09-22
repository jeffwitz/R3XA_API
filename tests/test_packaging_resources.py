from importlib import resources


def test_schema_resources_are_available_as_a_real_package() -> None:
    resource_root = resources.files("r3xa_api.resources")
    assert resource_root.joinpath("schema.json").is_file()
    assert resource_root.joinpath("ui/messages.json").is_file()
    assert resource_root.joinpath("graphviz/graphviz-12.2.1.wasm").is_file()
