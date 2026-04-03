from __future__ import annotations

import json
import inspect
import random
import string
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Union

from .schema import load_schema, schema_version
from .typed import from_model
from .validate import validate


def _random_id(n: int = 24) -> str:
    """Generate a lowercase identifier suitable for JSON object ids."""

    chars = string.ascii_lowercase
    return "".join(random.choice(chars) for _ in range(n))


def new_item(kind: str, **fields: Any) -> Dict[str, Any]:
    """Create a schema item with default `id` and `kind` if missing."""

    item = dict(fields)
    item.setdefault("id", _random_id())
    item.setdefault("kind", kind)
    return item


def unit(
    title: Optional[str] = None,
    value: Optional[float] = None,
    unit: Optional[str] = None,
    scale: Optional[float] = 1.0,
    **extra: Any,
) -> Dict[str, Any]:
    """Build a unit payload compatible with R3XA schema."""

    payload = {
        "kind": "unit",
    }
    if unit is None:
        raise TypeError("unit requires the `unit` field")
    payload["unit"] = unit
    if title is not None:
        payload["title"] = title
    if value is not None:
        payload["value"] = value
    if scale is not None:
        payload["scale"] = scale
    payload.update(extra)
    return payload


def data_set_file(filename: str, delimiter: Optional[str] = None, data_range: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
    """Build a `data_set_file` payload for `timestamps` or `data` fields."""

    payload = {
        "kind": "data_set_file",
        "filename": filename,
    }
    if delimiter is not None:
        payload["delimiter"] = delimiter
    if data_range is not None:
        if not isinstance(data_range, str):
            raise TypeError("data_range must be a string or None")
        payload["data_range"] = data_range
    payload.update(extra)
    return payload


def _ensure_data_set_file(value: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize string path or dict into a `data_set_file` payload."""

    if isinstance(value, dict):
        return value
    return data_set_file(filename=value)


_GUIDED_SECTION_SUFFIX = {
    "settings": "setting",
    "data_sources": "source",
    "data_sets": "data_set",
}
_GUIDED_ALIAS_TARGETS = {
    "add_image_set_list": "add_list_data_set",
    "add_image_set_file": "add_file_data_set",
}


@lru_cache(maxsize=1)
def _guided_kind_specs() -> Dict[str, Dict[str, Any]]:
    """Return schema-derived helper metadata for every supported kind."""

    schema = load_schema()
    specs: Dict[str, Dict[str, Any]] = {}
    for section, suffix in _GUIDED_SECTION_SUFFIX.items():
        section_defs = schema.get("$defs", {}).get(section, {})
        for kind_name, item_schema in section_defs.items():
            kind = f"{section}/{kind_name}"
            properties = item_schema.get("properties", {})
            required = tuple(
                field
                for field in item_schema.get("required", [])
                if field not in {"id", "kind"}
            )
            array_fields = tuple(
                field_name
                for field_name, field_schema in properties.items()
                if field_schema.get("type") == "array"
            )
            specs[kind] = {
                "required": required,
                "array_fields": array_fields,
                "helper_name": f"add_{kind_name}_{suffix}",
            }
    return specs


def _guided_item_spec(kind: str) -> Dict[str, Any]:
    """Return schema-derived metadata for a specific kind."""

    try:
        return _guided_kind_specs()[kind]
    except KeyError as exc:
        raise ValueError(f"Unsupported guided helper kind: {kind}") from exc


def _make_guided_helper(method_name: str, kind: str, required_fields: Sequence[str]) -> Callable[..., Dict[str, Any]]:
    """Create a guided helper with explicit required parameters for one kind."""

    params = ["self"] + [f"{field}: Any" for field in required_fields] + ["**extra: Any"]
    header = ", ".join(params)
    field_lines = "\n".join(
        f"    fields[{field!r}] = {field}" for field in required_fields
    ) or "    fields = {}"
    if required_fields:
        field_lines = "    fields: Dict[str, Any] = {}\n" + field_lines

    source = (
        f"def {method_name}({header}) -> Dict[str, Any]:\n"
        f"    \"\"\"Add a `{kind}` item.\"\"\"\n"
        f"{field_lines}\n"
        "    fields.update(extra)\n"
        f"    return self._add_guided_item({kind!r}, fields)\n"
    )
    namespace: Dict[str, Any] = {"Any": Any, "Dict": Dict}
    exec(source, namespace)
    helper = namespace[method_name]
    helper.__qualname__ = f"R3XAFile.{method_name}"
    helper.__doc__ = (
        f"Add a `{kind}` item.\n\n"
        f"Required fields: {', '.join(required_fields) if required_fields else '(none)'}.\n"
        "Optional schema fields can be passed through `**extra`."
    )
    return helper


def _make_guided_alias(alias_name: str, target_name: str) -> Callable[..., Dict[str, Any]]:
    """Create a backward-compatible guided helper alias."""

    def alias(self: "R3XAFile", *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return getattr(self, target_name)(*args, **kwargs)

    alias.__name__ = alias_name
    alias.__qualname__ = f"R3XAFile.{alias_name}"
    alias.__doc__ = f"Alias for `{target_name}`."
    alias.__signature__ = inspect.signature(getattr(R3XAFile, target_name))
    return alias


class _ModelAwareList(list):
    """List that accepts dicts and typed models exposing `model_dump`."""

    def __init__(self, values: Iterable[Any] = ()) -> None:
        super().__init__()
        self.extend(values)

    @staticmethod
    def _normalize(value: Any) -> Dict[str, Any]:
        return from_model(value)

    def append(self, value: Any) -> None:
        super().append(self._normalize(value))

    def extend(self, values: Iterable[Any]) -> None:
        super().extend(self._normalize(value) for value in values)

    def insert(self, index: int, value: Any) -> None:
        super().insert(index, self._normalize(value))

    def __setitem__(self, index: Any, value: Any) -> None:
        if isinstance(index, slice):
            super().__setitem__(index, [self._normalize(item) for item in value])
            return
        super().__setitem__(index, self._normalize(value))


class R3XAFile:
    """Mutable builder for an R3XA JSON document."""

    def __init__(self, version: Optional[str] = None, **header: Any):
        """Initialize an R3XA document with optional header overrides."""

        self.header: Dict[str, Any] = dict(header)
        self.header.setdefault("version", version or schema_version())
        self.settings: List[Dict[str, Any]] = _ModelAwareList()
        self.data_sources: List[Dict[str, Any]] = _ModelAwareList()
        self.data_sets: List[Dict[str, Any]] = _ModelAwareList()

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "R3XAFile":
        """Create a builder from an existing document payload."""

        version = payload.get("version")
        header = {k: v for k, v in payload.items() if k not in {"version", "settings", "data_sources", "data_sets"}}
        obj = cls(version=version, **header)
        obj.settings = _ModelAwareList(payload.get("settings", []))
        obj.data_sources = _ModelAwareList(payload.get("data_sources", []))
        obj.data_sets = _ModelAwareList(payload.get("data_sets", []))
        return obj

    @classmethod
    def load(cls, path: str | Path) -> "R3XAFile":
        """Load an R3XA JSON file from disk."""

        return cls.loads(Path(path).read_text(encoding="utf-8"))

    @classmethod
    def loads(cls, text: str) -> "R3XAFile":
        """Load an R3XA document from a JSON string."""

        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise TypeError("R3XA document root must be a JSON object")
        return cls.from_dict(payload)

    def set_header(self, **fields: Any) -> "R3XAFile":
        """Update top-level header fields in place."""

        self.header.update(fields)
        return self

    def _target_collection(self, kind: str) -> List[Dict[str, Any]]:
        """Return the target top-level collection matching item kind."""

        section = kind.split("/", 1)[0]
        if section == "settings":
            return self.settings
        if section == "data_sources":
            return self.data_sources
        if section == "data_sets":
            return self.data_sets
        raise ValueError("kind must start with settings/, data_sources/, or data_sets/")

    def add_item(self, kind: str, **fields: Any) -> Dict[str, Any]:
        """Append an item to the correct collection from its kind prefix."""

        item = new_item(kind, **fields)
        self._target_collection(kind).append(item)
        return item

    def add_setting(self, kind: str, **fields: Any) -> Dict[str, Any]:
        """Append a setting item and return it."""

        if not kind.startswith("settings/"):
            raise ValueError("add_setting expects a kind starting with settings/")
        return self.add_item(kind, **fields)

    def add_data_source(self, kind: str, **fields: Any) -> Dict[str, Any]:
        """Append a data source item and return it."""

        if not kind.startswith("data_sources/"):
            raise ValueError("add_data_source expects a kind starting with data_sources/")
        return self.add_item(kind, **fields)

    def add_data_set(self, kind: str, **fields: Any) -> Dict[str, Any]:
        """Append a dataset item and return it."""

        if not kind.startswith("data_sets/"):
            raise ValueError("add_data_set expects a kind starting with data_sets/")
        return self.add_item(kind, **fields)

    def _normalize_guided_fields(self, kind: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize guided helper fields before delegating to low-level add methods."""

        normalized = dict(fields)
        spec = _guided_item_spec(kind)
        for field_name in spec["array_fields"]:
            if field_name not in normalized or isinstance(normalized[field_name], list):
                continue
            value = normalized[field_name]
            if isinstance(value, (str, bytes, dict)):
                continue
            normalized[field_name] = list(value)

        if kind == "data_sets/file":
            normalized["timestamps"] = _ensure_data_set_file(normalized["timestamps"])
            normalized["data"] = _ensure_data_set_file(normalized["data"])

        if kind == "data_sets/list":
            time_reference = normalized["time_reference"]
            if not isinstance(time_reference, dict) or time_reference.get("kind") != "unit":
                raise ValueError("time_reference for data_sets/list must be a unit payload")

        return normalized

    def _add_guided_item(self, kind: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate required schema fields and append one guided item."""

        spec = _guided_item_spec(kind)
        missing_fields = [field for field in spec["required"] if field not in fields]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise TypeError(f"{spec['helper_name']} missing required arguments: {missing}")
        return self.add_item(kind, **self._normalize_guided_fields(kind, fields))

    def to_dict(self) -> Dict[str, Any]:
        """Return the complete JSON payload for this builder."""

        payload = dict(self.header)
        payload["settings"] = self.settings
        payload["data_sources"] = self.data_sources
        payload["data_sets"] = self.data_sets
        return payload

    def validate(self) -> None:
        """Validate current payload against the active schema."""

        validate(self.to_dict())

    def dump(self, indent: int = 4) -> str:
        """Serialize payload as a JSON string."""

        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str | Path, indent: int = 4, validate: bool = True) -> Path:
        """Validate optionally, then serialize payload as JSON to disk."""

        if validate:
            self.validate()

        path = Path(path)
        path.write_text(self.dump(indent=indent) + "\n", encoding="utf-8")
        return path


def _install_guided_helpers() -> None:
    """Attach schema-driven guided helper methods to `R3XAFile`."""

    for kind, spec in _guided_kind_specs().items():
        setattr(
            R3XAFile,
            spec["helper_name"],
            _make_guided_helper(spec["helper_name"], kind, spec["required"]),
        )

    for alias_name, target_name in _GUIDED_ALIAS_TARGETS.items():
        setattr(R3XAFile, alias_name, _make_guided_alias(alias_name, target_name))


_install_guided_helpers()
