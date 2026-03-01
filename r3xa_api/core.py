from __future__ import annotations

import json
import random
import string
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from .schema import schema_version
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


def unit(title: str, value: float, unit: str, scale: float = 1.0, **extra: Any) -> Dict[str, Any]:
    """Build a unit payload compatible with R3XA schema."""

    payload = {
        "kind": "unit",
        "title": title,
        "value": value,
        "unit": unit,
        "scale": scale,
    }
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

    def set_header(self, **fields: Any) -> "R3XAFile":
        """Update top-level header fields in place."""

        self.header.update(fields)
        return self

    def add_setting(self, kind: str, **fields: Any) -> Dict[str, Any]:
        """Append a setting item and return it."""

        item = new_item(kind, **fields)
        self.settings.append(item)
        return item

    def add_data_source(self, kind: str, **fields: Any) -> Dict[str, Any]:
        """Append a data source item and return it."""

        item = new_item(kind, **fields)
        self.data_sources.append(item)
        return item

    def add_data_set(self, kind: str, **fields: Any) -> Dict[str, Any]:
        """Append a dataset item and return it."""

        item = new_item(kind, **fields)
        self.data_sets.append(item)
        return item

    # Guided helpers
    def add_generic_setting(self, title: str, description: str, **extra: Any) -> Dict[str, Any]:
        """Add a `settings/generic` item."""

        return self.add_setting(
            "settings/generic",
            title=title,
            description=description,
            **extra,
        )

    def add_specimen_setting(
        self,
        title: str,
        description: str,
        sizes: Optional[List[Dict[str, Any]]] = None,
        patterning_technique: Optional[str] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        """Add a `settings/specimen` item with optional specimen metadata."""

        fields: Dict[str, Any] = {
            "title": title,
            "description": description,
        }
        if sizes is not None:
            fields["sizes"] = sizes
        if patterning_technique is not None:
            fields["patterning_technique"] = patterning_technique
        fields.update(extra)
        return self.add_setting("settings/specimen", **fields)

    def add_camera_source(
        self,
        title: str,
        description: str,
        output_components: int,
        output_dimension: str,
        output_units: Sequence[Dict[str, Any]],
        manufacturer: str,
        model: str,
        image_size: Sequence[Dict[str, Any]],
        **extra: Any,
    ) -> Dict[str, Any]:
        """Add a `data_sources/camera` item."""

        return self.add_data_source(
            "data_sources/camera",
            title=title,
            description=description,
            output_components=output_components,
            output_dimension=output_dimension,
            output_units=list(output_units),
            manufacturer=manufacturer,
            model=model,
            image_size=list(image_size),
            **extra,
        )

    def add_image_set_list(
        self,
        title: str,
        description: str,
        path: str,
        file_type: str,
        data_sources: Sequence[str],
        time_reference: Dict[str, Any],
        timestamps: Sequence[float],
        data: Sequence[str],
        **extra: Any,
    ) -> Dict[str, Any]:
        """Add a `data_sets/list` item with explicit unit-based time reference."""

        if not isinstance(time_reference, dict) or time_reference.get("kind") != "unit":
            raise ValueError("time_reference for data_sets/list must be a unit payload")
        return self.add_data_set(
            "data_sets/list",
            title=title,
            description=description,
            path=path,
            file_type=file_type,
            data_sources=list(data_sources),
            time_reference=time_reference,
            timestamps=list(timestamps),
            data=list(data),
            **extra,
        )

    def add_image_set_file(
        self,
        title: str,
        description: str,
        data_sources: Sequence[str],
        time_reference: float,
        timestamps: Union[str, Dict[str, Any]],
        data: Union[str, Dict[str, Any]],
        **extra: Any,
    ) -> Dict[str, Any]:
        """Add a `data_sets/file` item, normalizing file descriptors."""

        return self.add_data_set(
            "data_sets/file",
            title=title,
            description=description,
            data_sources=list(data_sources),
            time_reference=time_reference,
            timestamps=_ensure_data_set_file(timestamps),
            data=_ensure_data_set_file(data),
            **extra,
        )

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

    def save(self, path: str, indent: int = 4) -> None:
        """Serialize payload as JSON to disk."""

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent)
