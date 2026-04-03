from pathlib import Path
import importlib.util
import json
from typing import Iterable

from r3xa_api import validate


def _snapshot_paths(paths: Iterable[Path]) -> dict[Path, bytes | None]:
    snapshots: dict[Path, bytes | None] = {}
    for path in paths:
        if path.exists():
            snapshots[path] = path.read_bytes()
        else:
            snapshots[path] = None
    return snapshots


def _restore_paths(snapshots: dict[Path, bytes | None]) -> None:
    for path, content in snapshots.items():
        if content is None:
            if path.exists():
                path.unlink()
        else:
            path.write_bytes(content)


def _run_script(path: Path, restore_paths: Iterable[Path] = ()) -> None:
    snapshots = _snapshot_paths(restore_paths)

    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    try:
        spec.loader.exec_module(module)
        main = getattr(module, "main", None)
        if callable(main):
            main()
    finally:
        _restore_paths(snapshots)


def _run_script_preserving_outputs(path: Path, output_paths: Iterable[Path]) -> dict[Path, bytes | None]:
    snapshots = _snapshot_paths(output_paths)

    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    main = getattr(module, "main", None)
    if callable(main):
        main()
    return snapshots


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
    generated_snapshots: dict[Path, bytes | None] = {}
    try:
        generated_snapshots.update(
            _run_script_preserving_outputs(
                examples_python / "load_edit_save.py",
                output_paths=[artifacts / "dic_pipeline_loaded.json"],
            )
        )
        generated_snapshots.update(
            _run_script_preserving_outputs(
                examples_python / "registry_discovery.py",
                output_paths=[artifacts / "registry_camera_merged.json"],
            )
        )

        for path in [
            examples / "valid_camera_list.json",
            examples / "valid_tabular_file.json",
            examples / "essai-torsion.json",
            artifacts / "dic_pipeline.json",
            artifacts / "dic_pipeline_registry.json",
            artifacts / "dic_pipeline_loaded.json",
            artifacts / "qi_hu_from_scratch.json",
            artifacts / "qi_hu_from_scratch_matlab.json",
        ]:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            validate(payload)

        merged_registry_item = json.loads((artifacts / "registry_camera_merged.json").read_text(encoding="utf-8"))
        assert merged_registry_item["kind"] == "data_sources/camera"
    finally:
        _restore_paths(generated_snapshots)


def test_validation_scripts_run() -> None:
    root = Path(__file__).parents[1]
    examples = root / "examples"
    examples_python = examples / "python"
    artifacts = examples / "artifacts"

    _run_script(examples_python / "validate_examples.py")
    _run_script(
        examples_python / "validate_all.py",
        restore_paths=[
            artifacts / "dic_pipeline.json",
            artifacts / "dic_pipeline_registry.json",
        ],
    )
