import json
import importlib.resources
from typing import Optional, Dict, Any


def load_schema(path: Optional[str] = None) -> Dict[str, Any]:
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    schema_path = importlib.resources.files("r3xa_api.resources").joinpath("schema.json")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def schema_version(path: Optional[str] = None) -> Optional[str]:
    schema = load_schema(path)
    return str(schema.get("properties", {}).get("version", {}).get("const"))
