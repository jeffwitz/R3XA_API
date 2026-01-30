from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema

from .schema import load_schema


def load_item(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_item_path(root: str | Path, tree_path: str) -> Dict[str, Any]:
    root = Path(root)
    path = root / f"{tree_path}.json"
    return load_item(path)


def _wrap_def(schema: Dict[str, Any], kind: str) -> Dict[str, Any]:
    section, name = kind.split("/", 1)
    return {
        "$ref": f"#/$defs/{section}/{name}",
        "$defs": schema.get("$defs", {}),
    }


def validate_item(item: Dict[str, Any], kind: Optional[str] = None, schema: Optional[Dict[str, Any]] = None) -> None:
    schema = schema or load_schema()
    if kind is None:
        kind = item.get("kind")
    if not kind:
        raise ValueError("Missing kind for item validation")

    item_schema = _wrap_def(schema, kind)
    validator = jsonschema.validators.Draft202012Validator(item_schema)
    errors = sorted(validator.iter_errors(item), key=jsonschema.exceptions.relevance)
    if errors:
        msg = "\n".join([f"- {e.message}" for e in errors])
        raise jsonschema.exceptions.ValidationError(msg)


def load_registry(root: str | Path) -> Dict[str, Dict[str, Dict[str, Any]]]:
    root = Path(root)
    registry: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for section in ["settings", "data_sources", "data_sets"]:
        section_dir = root / section
        if not section_dir.exists():
            continue
        registry[section] = {}
        for kind_dir in section_dir.iterdir():
            if not kind_dir.is_dir():
                continue
            kind = f"{section}/{kind_dir.name}"
            registry[section][kind] = {}
            for path in kind_dir.glob("*.json"):
                registry[section][kind][path.stem] = load_item(path)
    return registry


def merge_item(base: Dict[str, Any], **overrides: Any) -> Dict[str, Any]:
    merged = dict(base)
    merged.update({k: v for k, v in overrides.items() if v is not None})
    return merged


class Registry:
    """Helper to load and validate registry items by tree path."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def get(self, tree_path: str) -> Dict[str, Any]:
        return load_item_path(self.root, tree_path)

    def validate(self, item: Dict[str, Any], kind: Optional[str] = None) -> None:
        validate_item(item, kind=kind)

    def get_validated(self, tree_path: str, kind: Optional[str] = None) -> Dict[str, Any]:
        item = self.get(tree_path)
        self.validate(item, kind=kind)
        return item
