import json
from pathlib import Path
from r3xa_api import validate


def validate_json(path: Path) -> None:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    validate(payload)
    print(f"OK: {path.name}")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    examples_dir = script_dir.parent

    # Generate complex examples first
    import importlib.util

    for script in ["complex_dic_pipeline.py", "complex_dic_pipeline_registry.py"]:
        spec = importlib.util.spec_from_file_location("_tmp", script_dir / script)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

    # Validate static examples
    for path in [
        examples_dir / "valid_camera_list.json",
        examples_dir / "valid_tabular_file.json",
        examples_dir / "artifacts" / "dic_pipeline.json",
        examples_dir / "artifacts" / "dic_pipeline_registry.json",
    ]:
        validate_json(path)


if __name__ == "__main__":
    main()
