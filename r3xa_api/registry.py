from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

import jsonschema

from .schema import load_schema


def _coerce_item_payload(item: Mapping[str, Any] | RegistryItem) -> Dict[str, Any]:
    """Return a plain dictionary payload for registry helpers."""

    if isinstance(item, RegistryItem):
        return item.to_dict()
    return dict(item)


def load_item(path: str | Path) -> Dict[str, Any]:
    """Load a JSON registry item from disk."""

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_item(
    path: str | Path,
    item: Mapping[str, Any] | RegistryItem,
    *,
    validate: bool = True,
    kind: Optional[str] = None,
) -> Path:
    """Validate then save a registry item to a JSON file."""

    payload = _coerce_item_payload(item)
    if validate:
        validate_item(payload, kind=kind)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_item_path(root: str | Path, tree_path: str) -> Dict[str, Any]:
    """Load a registry item addressed as section/kind/name."""

    root = Path(root)
    path = root / f"{tree_path}.json"
    return load_item(path)


def save_item_path(
    root: str | Path,
    tree_path: str,
    item: Mapping[str, Any] | RegistryItem,
    *,
    validate: bool = True,
    kind: Optional[str] = None,
) -> Path:
    """Validate then save a registry item addressed as `section/kind/name`."""

    root = Path(root)
    inferred_kind = kind
    if inferred_kind is None:
        parts = tree_path.split("/")
        if len(parts) >= 2:
            inferred_kind = "/".join(parts[:2])

    path = root / f"{tree_path}.json"
    return save_item(path, item, validate=validate, kind=inferred_kind)


def _wrap_def(schema: Dict[str, Any], kind: str) -> Dict[str, Any]:
    """Wrap a `$defs` item into a standalone schema root for validation."""

    section, name = kind.split("/", 1)
    return {
        "$ref": f"#/$defs/{section}/{name}",
        "$defs": schema.get("$defs", {}),
    }


def validate_item(
    item: Mapping[str, Any] | RegistryItem,
    kind: Optional[str] = None,
    schema: Optional[Dict[str, Any]] = None,
) -> None:
    """Validate a registry item against its `$defs` entry."""

    item = _coerce_item_payload(item)
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
    """Load all JSON entries from a registry tree."""

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


def merge_item(base: Mapping[str, Any] | RegistryItem, **overrides: Any) -> Dict[str, Any]:
    """Return a shallow-merged item while ignoring `None` override values."""

    merged = dict(_coerce_item_payload(base))
    merged.update({k: v for k, v in overrides.items() if v is not None})
    return merged


class RegistryItem(MutableMapping[str, Any]):
    """Dictionary-like wrapper for a single registry item with item-level helpers."""

    def __init__(
        self,
        payload: Mapping[str, Any],
        *,
        registry_root: str | Path | None = None,
        tree_path: str | None = None,
    ) -> None:
        self._payload = dict(payload)
        self.registry_root = Path(registry_root) if registry_root is not None else None
        self.tree_path = tree_path

    def __getitem__(self, key: str) -> Any:
        return self._payload[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._payload[key] = value

    def __delitem__(self, key: str) -> None:
        del self._payload[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._payload)

    def __len__(self) -> int:
        return len(self._payload)

    def __repr__(self) -> str:
        return (
            f"RegistryItem(kind={self.kind!r}, tree_path={self.tree_path!r}, "
            f"keys={sorted(self._payload.keys())!r})"
        )

    @property
    def kind(self) -> Optional[str]:
        """Return the embedded schema kind if present."""

        return self._payload.get("kind")

    @property
    def path(self) -> Optional[Path]:
        """Return the bound registry file path when both root and tree path are known."""

        if self.registry_root is None or self.tree_path is None:
            return None
        return self.registry_root / f"{self.tree_path}.json"

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dictionary copy of the payload."""

        return dict(self._payload)

    def bind(
        self,
        *,
        registry_root: str | Path | None = None,
        tree_path: str | None = None,
    ) -> RegistryItem:
        """Return a copy bound to a registry root and/or tree path."""

        return RegistryItem(
            self._payload,
            registry_root=self.registry_root if registry_root is None else registry_root,
            tree_path=self.tree_path if tree_path is None else tree_path,
        )

    def validate(self, kind: Optional[str] = None, schema: Optional[Dict[str, Any]] = None) -> RegistryItem:
        """Validate the current item payload and return `self`."""

        validate_item(self._payload, kind=kind, schema=schema)
        return self

    def merge(self, **overrides: Any) -> RegistryItem:
        """Return a shallow-merged copy while preserving registry binding."""

        return RegistryItem(
            merge_item(self._payload, **overrides),
            registry_root=self.registry_root,
            tree_path=self.tree_path,
        )

    def save(
        self,
        path: str | Path | None = None,
        *,
        validate: bool = True,
        kind: Optional[str] = None,
    ) -> Path:
        """Save to a raw JSON file path or back to the bound registry location."""

        if path is None:
            if self.registry_root is None or self.tree_path is None:
                raise ValueError("RegistryItem.save() needs a file path or a bound registry tree path")
            return save_item_path(self.registry_root, self.tree_path, self._payload, validate=validate, kind=kind)
        return save_item(path, self._payload, validate=validate, kind=kind)

    def save_to(
        self,
        registry: Registry | str | Path,
        tree_path: str | None = None,
        *,
        validate: bool = True,
        kind: Optional[str] = None,
    ) -> Path:
        """Save into a registry root with an explicit or bound tree path."""

        registry_root = registry.root if isinstance(registry, Registry) else Path(registry)
        resolved_tree_path = tree_path or self.tree_path
        if resolved_tree_path is None:
            raise ValueError("RegistryItem.save_to() needs an explicit tree_path when the item is not bound")
        return save_item_path(registry_root, resolved_tree_path, self._payload, validate=validate, kind=kind)


class Registry:
    """Helper to load and validate registry items by tree path."""

    def __init__(self, root: str | Path):
        """Create a registry helper rooted at a local directory."""

        self.root = Path(root)

    def get(self, tree_path: str) -> Dict[str, Any]:
        """Load an item from `section/kind/name` path."""

        return load_item_path(self.root, tree_path)

    def load(self, tree_path: str) -> Dict[str, Any]:
        """Alias for `get()` with a more discoverable name."""

        return self.get(tree_path)

    def wrap(self, item: Mapping[str, Any], tree_path: str | None = None) -> RegistryItem:
        """Wrap a plain item payload into a bound `RegistryItem`."""

        return RegistryItem(item, registry_root=self.root, tree_path=tree_path)

    def get_item(self, tree_path: str, *, validated: bool = True, kind: Optional[str] = None) -> RegistryItem:
        """Load a registry item and return it as a `RegistryItem` wrapper."""

        item = self.get_validated(tree_path, kind=kind) if validated else self.get(tree_path)
        return RegistryItem(item, registry_root=self.root, tree_path=tree_path)

    def save(
        self,
        tree_path: str,
        item: Mapping[str, Any] | RegistryItem,
        *,
        validate: bool = True,
        kind: Optional[str] = None,
    ) -> Path:
        """Validate then save an item to `section/kind/name` path."""

        return save_item_path(self.root, tree_path, item, validate=validate, kind=kind)

    def validate(self, item: Mapping[str, Any] | RegistryItem, kind: Optional[str] = None) -> None:
        """Validate an item using explicit `kind` or embedded `item.kind`."""

        validate_item(item, kind=kind)

    def get_validated(self, tree_path: str, kind: Optional[str] = None) -> Dict[str, Any]:
        """Load then validate a registry item in one call."""

        item = self.get(tree_path)
        self.validate(item, kind=kind)
        return item

    def load_validated(self, tree_path: str, kind: Optional[str] = None) -> Dict[str, Any]:
        """Alias for `get_validated()` with a more discoverable name."""

        return self.get_validated(tree_path, kind=kind)

    def list(self, section: Optional[str] = None, kind: Optional[str] = None) -> list[str]:
        """List available registry tree paths, optionally filtered by section or kind."""

        if kind is not None:
            if "/" not in kind:
                raise ValueError("kind filter must look like 'section/name'")
            if section is not None and not kind.startswith(f"{section}/"):
                raise ValueError("section and kind filters are inconsistent")

            kind_dir = self.root / kind
            if not kind_dir.exists():
                return []
            return sorted(f"{kind}/{path.stem}" for path in kind_dir.glob("*.json"))

        sections = [section] if section is not None else ["settings", "data_sources", "data_sets"]
        tree_paths: list[str] = []
        for current_section in sections:
            section_dir = self.root / current_section
            if not section_dir.exists():
                continue
            for kind_dir in sorted(path for path in section_dir.iterdir() if path.is_dir()):
                tree_paths.extend(
                    sorted(f"{current_section}/{kind_dir.name}/{path.stem}" for path in kind_dir.glob("*.json"))
                )
        return tree_paths

    def iter_items(
        self,
        section: Optional[str] = None,
        kind: Optional[str] = None,
        *,
        validated: bool = False,
        wrapped: bool = False,
    ) -> Iterator[tuple[str, Dict[str, Any] | RegistryItem]]:
        """Iterate over registry items, optionally validated and/or wrapped."""

        for tree_path in self.list(section=section, kind=kind):
            if wrapped:
                item = self.get_item(tree_path, validated=validated)
            else:
                item = self.get_validated(tree_path) if validated else self.get(tree_path)
            yield tree_path, item

    def merge(self, tree_path: str, **overrides: Any) -> RegistryItem:
        """Load a registry item and return a shallow merged copy with overrides."""

        return self.get_item(tree_path, validated=True).merge(**overrides)
