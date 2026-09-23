import json
from pathlib import Path
from r3xa_api import validate, validate_item


def validate_json(path: Path) -> None:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict) and isinstance(payload.get("kind"), str):
        validate_item(payload)
    else:
        validate(payload)
    print(f"OK: {path}")


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

    # Validate every committed JSON example and generated artifact. Registry
    # fragments are validated against their kind; complete documents include
    # the document-level integrity checks.
    paths = sorted(examples_dir.glob("*.json"))
    paths.extend(sorted((examples_dir / "artifacts").rglob("*.json")))
    for path in paths:
        validate_json(path)


if __name__ == "__main__":
    main()
