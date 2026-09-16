from __future__ import annotations

import json
import secrets
import string
from collections.abc import Iterable
from pathlib import Path
from typing import Any, ClassVar, Dict, Mapping, TypeVar

from pydantic import BaseModel, ConfigDict


ModelT = TypeVar("ModelT", bound="R3XAModel")


def _random_id(length: int = 24) -> str:
    return "".join(secrets.choice(string.ascii_lowercase) for _ in range(length))


class R3XAModel(BaseModel):
    """Common ergonomic behavior for schema-generated R3XA models."""

    model_config = ConfigDict(validate_assignment=True)
    _json_indent: ClassVar[int] = 2

    def __init__(self, **data: Any) -> None:
        if "id" in self.__class__.model_fields and "id" not in data:
            data["id"] = _random_id()
        super().__init__(**data)

    @classmethod
    def required_fields(cls) -> list[str]:
        """Return the names of fields required by the generated model."""

        return [
            name for name, field in cls.model_fields.items() if field.is_required()
        ]

    @classmethod
    def optional_fields(cls) -> list[str]:
        """Return the names of fields that may be omitted."""

        return [
            name for name, field in cls.model_fields.items() if not field.is_required()
        ]

    @classmethod
    def field_descriptions(cls) -> Dict[str, str]:
        """Return schema descriptions for fields that provide one."""

        return {
            name: field.description
            for name, field in cls.model_fields.items()
            if field.description
        }

    def missing_fields(self) -> list[str]:
        """Return required fields whose current value is missing or null."""

        return [
            name
            for name in self.required_fields()
            if getattr(self, name, None) is None
        ]

    def to_dict(self, *, exclude_none: bool = True) -> Dict[str, Any]:
        """Return a JSON-compatible dictionary representation."""

        return self.model_dump(mode="json", exclude_none=exclude_none)

    def to_json(self, *, exclude_none: bool = True, indent: int | None = 2) -> str:
        """Return a JSON representation of the model."""

        return json.dumps(
            self.to_dict(exclude_none=exclude_none),
            ensure_ascii=False,
            indent=indent,
        )

    @staticmethod
    def _value(item: Any, field: str) -> Any:
        if isinstance(item, Mapping):
            return item.get(field)
        return getattr(item, field, None)

    @staticmethod
    def _reference_value(reference: Any) -> Any:
        if isinstance(reference, str):
            return reference
        if isinstance(reference, Mapping):
            return reference.get("root", reference.get("id"))
        return getattr(reference, "root", getattr(reference, "id", None))

    def iter_items(self) -> Iterable[tuple[str, Any]]:
        """Iterate over settings, data sources, and data sets in a document model."""

        for section in ("settings", "data_sources", "data_sets"):
            values = getattr(self, section, None)
            if values:
                yield from ((section, item) for item in values)

    def find(self, item_id: str) -> Any | None:
        """Find a document item by its identifier."""

        for _, item in self.iter_items():
            if self._value(item, "id") == item_id:
                return item
        return None

    def add(self, item: Any, *, section: str | None = None) -> Any:
        """Add a typed or mapping item to the document collection matching its kind."""

        kind = self._value(item, "kind")
        target_section = section or (
            kind.split("/", 1)[0] if isinstance(kind, str) else None
        )
        if target_section not in {"settings", "data_sources", "data_sets"}:
            raise ValueError(
                "An item kind or an explicit document section is required"
            )

        item_id = self._value(item, "id")
        if item_id and self.find(item_id) is not None:
            raise ValueError(f"Duplicate R3XA item id: {item_id}")

        values = list(getattr(self, target_section, None) or [])
        values.append(item)
        setattr(self, target_section, values)
        return item

    def add_setting(self, item: Any) -> Any:
        """Add a setting to the document."""

        return self.add(item, section="settings")

    def add_data_source(self, item: Any) -> Any:
        """Add a data source to the document."""

        return self.add(item, section="data_sources")

    def add_data_set(self, item: Any) -> Any:
        """Add a data set to the document."""

        return self.add(item, section="data_sets")

    def _resolve_item(self, item: Any, expected_section: str) -> Any:
        if isinstance(item, str):
            resolved = self.find(item)
            if resolved is None:
                raise ValueError(f"Unknown R3XA item id: {item}")
            item = resolved
        kind = self._value(item, "kind")
        if not isinstance(kind, str) or not kind.startswith(f"{expected_section}/"):
            raise ValueError(f"Expected an item from section {expected_section!r}")
        return item

    @staticmethod
    def _append_reference(item: Any, field: str, reference: str) -> None:
        references = R3XAModel._value(item, field)
        if references is None:
            references = []
            if isinstance(item, Mapping):
                item[field] = references
            else:
                setattr(item, field, references)
        known_references = [
            R3XAModel._reference_value(value) for value in references
        ]
        if reference not in known_references:
            updated_references = list(references)
            updated_references.append(reference)
            if isinstance(item, Mapping):
                item[field] = updated_references
            else:
                setattr(item, field, updated_references)

    def link_output(self, source: Any, data_set: Any) -> "R3XAModel":
        """Record that a data set is produced by a data source."""

        source = self._resolve_item(source, "data_sources")
        data_set = self._resolve_item(data_set, "data_sets")
        source_id = self._value(source, "id")
        if not source_id:
            raise ValueError("The data source must have an id")
        self._append_reference(data_set, "parent_data_sources", source_id)
        return self

    def link_input(self, source: Any, data_set: Any) -> "R3XAModel":
        """Record that a data source consumes a data set."""

        source = self._resolve_item(source, "data_sources")
        data_set = self._resolve_item(data_set, "data_sets")
        data_set_id = self._value(data_set, "id")
        if not data_set_id:
            raise ValueError("The data set must have an id")
        self._append_reference(source, "input_data_sets", data_set_id)
        return self

    def integrity_errors(self) -> list[str]:
        """Return dangling-reference and duplicate-id errors for a document model."""

        errors: list[str] = []
        identifiers: dict[str, str] = {}
        source_ids: set[str] = set()
        data_set_ids: set[str] = set()

        for section, item in self.iter_items():
            item_id = self._value(item, "id")
            if isinstance(item_id, str):
                previous = identifiers.get(item_id)
                if previous is not None:
                    errors.append(f"duplicate id {item_id!r} in {previous} and {section}")
                else:
                    identifiers[item_id] = section
                if section == "data_sources":
                    source_ids.add(item_id)
                elif section == "data_sets":
                    data_set_ids.add(item_id)

        for section, item in self.iter_items():
            item_id = self._value(item, "id") or "<unknown>"
            if section == "data_sets":
                for reference in self._value(item, "parent_data_sources") or []:
                    reference_id = self._reference_value(reference)
                    if reference_id not in source_ids:
                        errors.append(
                            f"{section}/{item_id} references unknown data source "
                            f"{reference_id!r}"
                        )
            if section == "data_sources":
                for reference in self._value(item, "input_data_sets") or []:
                    reference_id = self._reference_value(reference)
                    if reference_id not in data_set_ids:
                        errors.append(
                            f"{section}/{item_id} references unknown data set "
                            f"{reference_id!r}"
                        )
            if section == "settings":
                for reference in self._value(item, "attached_data_sources") or []:
                    reference_id = self._reference_value(reference)
                    if reference_id not in source_ids:
                        errors.append(
                            f"{section}/{item_id} references unknown data source "
                            f"{reference_id!r}"
                        )
        return errors

    def validate_integrity(self: ModelT) -> ModelT:
        """Validate document references and return this model."""

        errors = self.integrity_errors()
        if errors:
            raise ValueError("\n".join(f"- {error}" for error in errors))
        return self

    @classmethod
    def from_dict(
        cls: type[ModelT],
        payload: Mapping[str, Any],
        *,
        validate: bool = True,
    ) -> ModelT:
        """Create a typed model from a mapping and optionally validate its R3XA schema."""

        model = cls.model_validate(dict(payload))
        if validate:
            model.validate()
        return model

    @classmethod
    def load(
        cls: type[ModelT],
        path: str | Path,
        *,
        validate: bool = True,
    ) -> ModelT:
        """Load a typed model from a JSON file."""

        with Path(path).open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
        return cls.from_dict(payload, validate=validate)

    def validate(self: ModelT, *, schema: Dict[str, Any] | None = None) -> ModelT:
        """Validate this model against the packaged R3XA JSON Schema."""

        from .registry import validate_item
        from .validate import validate as validate_document

        payload = self.to_dict()
        kind = getattr(self, "kind", None)
        if isinstance(kind, str):
            validate_item(payload, kind=kind, schema=schema)
        else:
            validate_document(payload, schema=schema)
        return self

    def save(
        self,
        path: str | Path,
        *,
        validate: bool = True,
        exclude_none: bool = True,
        indent: int | None = 2,
    ) -> Path:
        """Validate and save this model to a JSON file."""

        if validate:
            self.validate()
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            self.to_json(exclude_none=exclude_none, indent=indent) + "\n",
            encoding="utf-8",
        )
        return destination

    def summary(self) -> str:
        """Return a readable listing of all model fields, including null values."""

        lines = [self.__class__.__name__]
        required = set(self.required_fields())
        for name in type(self).model_fields:
            marker = "*" if name in required else " "
            lines.append(f"{marker} {name}: {getattr(self, name, None)!r}")
        return "\n".join(lines)

    def print(self) -> None:
        """Print a readable listing of all model fields."""

        print(self.summary())
