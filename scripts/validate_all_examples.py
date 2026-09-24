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
    repository_root = script_dir.parent
    fixtures_dir = repository_root / "tests" / "fixtures" / "documents"
    artifacts_dir = repository_root / "artifacts" / "examples"
    paths = sorted(fixtures_dir.rglob("*.json"))
    paths.extend(sorted(artifacts_dir.rglob("*.json")))
    for path in paths:
        validate_json(path)


if __name__ == "__main__":
    main()
