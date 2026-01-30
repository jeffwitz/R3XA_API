import json
from pathlib import Path
from r3xa_api import validate


def main() -> None:
    base = Path(__file__).parent
    files = [
        base / "valid_camera_list.json",
        base / "valid_tabular_file.json",
    ]

    for path in files:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        validate(payload)
        print(f"OK: {path.name}")


if __name__ == "__main__":
    main()
