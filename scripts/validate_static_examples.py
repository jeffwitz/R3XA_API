import json
from pathlib import Path
from r3xa_api import validate


def main() -> None:
    fixtures_dir = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "documents"
    files = [
        fixtures_dir / "valid_camera_list.json",
        fixtures_dir / "valid_tabular_file.json",
    ]

    for path in files:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        validate(payload)
        print(f"OK: {path.name}")


if __name__ == "__main__":
    main()
