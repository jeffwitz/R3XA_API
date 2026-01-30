from pathlib import Path
import importlib.util
import json

from r3xa_api import validate


def _run_script(path: Path) -> None:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)


def test_examples_validate_all():
    root = Path(__file__).parents[1]
    examples = root / "examples"

    _run_script(examples / "complex_dic_pipeline.py")
    _run_script(examples / "complex_dic_pipeline_registry.py")

    for path in [
        examples / "valid_camera_list.json",
        examples / "valid_tabular_file.json",
        root / "r3xa.json",
        root / "dic_pipeline.json",
        root / "dic_pipeline_registry.json",
    ]:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        validate(payload)
