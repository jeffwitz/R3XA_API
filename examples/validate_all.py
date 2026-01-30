import json
from pathlib import Path
from r3xa_api import validate


def validate_json(path: Path) -> None:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    validate(payload)
    print(f"OK: {path.name}")


def main() -> None:
    base = Path(__file__).parent

    # Generate complex examples first
    import importlib.util

    for script in ["complex_dic_pipeline.py", "complex_dic_pipeline_registry.py"]:
        spec = importlib.util.spec_from_file_location("_tmp", base / script)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

    # Validate static examples
    for path in [
        base / "valid_camera_list.json",
        base / "valid_tabular_file.json",
        Path(__file__).parents[1] / "r3xa.json",
        Path("dic_pipeline.json"),
        Path("dic_pipeline_registry.json"),
    ]:
        validate_json(path)


if __name__ == "__main__":
    main()
