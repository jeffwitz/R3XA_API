from pathlib import Path
import importlib.util
import json
from typing import Iterable

from r3xa_api import validate


def _run_script(path: Path, restore_paths: Iterable[Path] = ()) -> None:
    snapshots: dict[Path, bytes | None] = {}
    for restore_path in restore_paths:
        if restore_path.exists():
            snapshots[restore_path] = restore_path.read_bytes()
        else:
            snapshots[restore_path] = None

    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    try:
        spec.loader.exec_module(module)
    finally:
        for restore_path, content in snapshots.items():
            if content is None:
                if restore_path.exists():
                    restore_path.unlink()
            else:
                restore_path.write_bytes(content)


def test_examples_validate_all():
    root = Path(__file__).parents[1]
    examples = root / "examples"
    examples_python = examples / "python"
    artifacts = examples / "artifacts"

    _run_script(
        examples_python / "complex_dic_pipeline.py",
        restore_paths=[artifacts / "dic_pipeline.json"],
    )
    _run_script(
        examples_python / "complex_dic_pipeline_registry.py",
        restore_paths=[artifacts / "dic_pipeline_registry.json"],
    )

    for path in [
        examples / "valid_camera_list.json",
        examples / "valid_tabular_file.json",
        artifacts / "dic_pipeline.json",
        artifacts / "dic_pipeline_registry.json",
        artifacts / "qi_hu_from_scratch.json",
        artifacts / "qi_hu_from_scratch_matlab.json",
    ]:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        validate(payload)
