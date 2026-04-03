import inspect

import pytest
import r3xa_api
from r3xa_api import R3XAFile
from r3xa_api.core import _guided_kind_specs


def test_public_api_surface() -> None:
    expected_exports = {
        "R3XAFile",
        "new_item",
        "unit",
        "data_set_file",
        "from_model",
        "load_schema",
        "schema_version",
        "validate",
        "Registry",
        "RegistryItem",
        "models",
        "typed_available",
    }

    assert set(r3xa_api.__all__) == expected_exports


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
