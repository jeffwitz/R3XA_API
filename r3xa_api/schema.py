import json
import importlib.resources
from copy import deepcopy
from functools import lru_cache
from typing import Optional, Dict, Any


@lru_cache(maxsize=1)
def _load_packaged_schema_cached() -> Dict[str, Any]:
    """Load and cache packaged schema content once per process."""

    schema_path = importlib.resources.files("r3xa_api.resources").joinpath("schema.json")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_schema(path: Optional[str] = None) -> Dict[str, Any]:
    """Load a schema from explicit path or packaged default location."""

    if path:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        return deepcopy(_load_packaged_schema_cached())
    except Exception as exc:
        raise FileNotFoundError(f"Unable to load packaged schema.json ({exc})") from exc


def schema_version(path: Optional[str] = None) -> Optional[str]:
    """Return the schema version constant declared in loaded schema."""

    schema = load_schema(path)
    return str(schema.get("properties", {}).get("version", {}).get("const"))
