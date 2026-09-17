import inspect

import pytest
import r3xa_api
from r3xa_api import R3XAFile
from r3xa_api.core import _guided_kind_specs


BASE_EXPORTS = {
    "R3XAFile",
    "R3XAItem",
    "author",
    "new_item",
    "unit",
    "data_set_file",
    "from_model",
    "load_schema",
    "schema_version",
    "validate",
    "integrity_errors",
    "validate_integrity",
    "Registry",
    "RegistryItem",
    "models",
    "typed_available",
}


def test_public_api_surface() -> None:
    exports = set(r3xa_api.__all__)

    assert BASE_EXPORTS <= exports

    # Beyond the base surface, only two families are exported: the standalone
    # item builders and the generated model classes.
    builders = set(r3xa_api.core.GUIDED_BUILDERS)
    models = set(r3xa_api.models.__all__) if r3xa_api.typed_available else set()

    assert exports - BASE_EXPORTS == (builders | models) - BASE_EXPORTS
    assert all(name.startswith("new_") for name in builders)


def test_standalone_builders_mirror_the_guided_helpers() -> None:
    # Every `document.add_x(...)` has a `new_x(...)` building the same item
    # without a document, so a setting or a source can exist on its own.
    for kind, spec in _guided_kind_specs().items():
        helper = spec["helper_name"]
        builder = "new_" + helper[len("add_"):]
        assert hasattr(R3XAFile, helper)
        assert callable(getattr(r3xa_api, builder))
        assert r3xa_api.core.GUIDED_BUILDERS[builder] == kind


def test_generated_models_are_exported_at_package_level() -> None:
    # Reachable without going through the `models` module, which is where
    # users look for them first.
    for name in ("CameraSource", "SpecimenSetting", "FileDataSet", "R3XADocument"):
        assert getattr(r3xa_api, name) is getattr(r3xa_api.models, name)
        assert name in r3xa_api.__all__


def test_web_helpers_not_exported_from_top_level() -> None:
    assert not hasattr(r3xa_api, "build_validation_report")
    assert not hasattr(r3xa_api, "build_schema_summary")


def test_compat_helpers_remain_explicitly_importable() -> None:
    from r3xa_api import load_item_path, load_registry, merge_item, save_item_path, validate_item

    assert callable(load_item_path)
    assert callable(save_item_path)
    assert callable(validate_item)
    assert callable(load_registry)
    assert callable(merge_item)


def test_web_helpers_still_available_from_webcore() -> None:
    from r3xa_api.webcore import build_schema_summary, build_validation_report

    assert callable(build_validation_report)
    assert callable(build_schema_summary)


def test_typed_available_flag_remains_module_attribute() -> None:
    assert hasattr(r3xa_api, "_TYPED_AVAILABLE")


@pytest.mark.parametrize("kind,spec", sorted(_guided_kind_specs().items()))
def test_guided_helper_contract(kind: str, spec: dict[str, object]) -> None:
    method = getattr(R3XAFile, spec["helper_name"])
    assert callable(method), kind
    signature = inspect.signature(method)
    for field in spec["required"]:
        assert field in signature.parameters, (kind, field)
    assert any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    ), kind
