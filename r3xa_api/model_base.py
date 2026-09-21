from __future__ import annotations

import json
from collections.abc import Iterable
import re
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, Mapping, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, PrivateAttr, RootModel

from ._format import format_json_value
from ._references import reference_fields, reference_id
from ._ids import generate_id
from .schema import load_schema


ModelT = TypeVar("ModelT", bound="R3XAItem")


class R3XAItem(BaseModel):
    """Object-first base class for every generated R3XA object."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")
    _json_indent: ClassVar[int] = 2
    _document: Any = PrivateAttr(default=None)
    _reference_objects: dict[str, Any] = PrivateAttr(default_factory=dict)

    @classmethod
    def _reference_field_map(cls) -> dict[str, str]:
        kind_field = cls.model_fields.get("kind")
        kind = getattr(kind_field, "default", None) if kind_field is not None else None
        return reference_fields(kind if isinstance(kind, str) else None)

    def __init__(self, **data: Any) -> None:
        if "id" in self.__class__.model_fields and "id" not in data:
            kind = data.get("kind")
            if not isinstance(kind, str):
                kind_field = self.__class__.model_fields.get("kind")
                kind = getattr(kind_field, "default", "")
            data["id"] = generate_id(kind if isinstance(kind, str) else "")
        reference_objects: dict[str, Any] = {}
        for field in type(self)._reference_field_map():
            if field not in data or data[field] is None:
                continue
            normalized, objects = self._normalize_reference(data[field])
            data[field] = normalized
            if objects is not None:
                reference_objects[field] = objects
        super().__init__(**data)
        if reference_objects:
            object.__setattr__(self, "_reference_objects", reference_objects)

        for section in ("settings", "data_sources", "data_sets"):
            if section not in self.__class__.model_fields:
                continue
            values = getattr(self, section)
            object.__setattr__(
                self,
                section,
                R3XACollection(values or (), document=self),
            )

    @staticmethod
    def _normalize_reference(value: Any) -> tuple[Any, Any | None]:
        """Convert object references to wire IDs while retaining objects in memory."""

        def normalize_one(item: Any) -> tuple[str | None, Any | None]:
            identifier = reference_id(item)
            if identifier is None:
                return None, None
            if isinstance(item, str) or isinstance(item, Mapping):
                return identifier, None
            return identifier, item

        if (
            isinstance(value, (str, bytes, Mapping))
            or reference_id(value) is not None
            or not isinstance(value, Iterable)
        ):
            identifier, original = normalize_one(value)
            return identifier, original

        normalized: list[str | None] = []
        originals: list[Any] = []
        has_original = False
        for item in value:
            identifier, original = normalize_one(item)
            normalized.append(identifier)
            originals.append(original)
            has_original = has_original or original is not None
        return normalized, originals if has_original else None

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        # Runs once the model class is fully built, so `model_fields` is populated.
        # The generated models carry no docstring of their own, which left
        # `help(CameraSource)` empty even though the schema documents every field.
        super().__pydantic_init_subclass__(**kwargs)
        if not cls.__dict__.get("__doc__"):
            cls.__doc__ = cls._build_docstring()

    @staticmethod
    def _annotation_name(annotation: Any) -> str:
        """Return a readable type name for a field annotation.

        `Optional[X]` unwraps to `X`: the docstring already marks the field as
        optional, so repeating it in the type reads as noise.
        """

        if annotation is None:
            return "Any"

        if get_origin(annotation) is Union:
            variants = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(variants) == 1:
                return R3XAItem._annotation_name(variants[0])
            inner = ", ".join(R3XAItem._annotation_name(arg) for arg in variants)
            return f"Union[{inner}]"

        if isinstance(annotation, type):
            return annotation.__name__

        # Collapse dotted paths (r3xa_api.models.Unit -> Unit) in generic forms.
        text = str(annotation).replace("typing.", "")
        return re.sub(r"\b(?:[A-Za-z_]\w*\.)+([A-Za-z_]\w*)", r"\1", text)

    @staticmethod
    def _allowed_values(annotation: Any) -> list[str]:
        """Return the permitted values when a field is backed by an enumeration."""

        candidates = [annotation, *get_args(annotation)]
        for candidate in candidates:
            if isinstance(candidate, type) and issubclass(candidate, Enum):
                return [str(member.value) for member in candidate]
        return []

    @classmethod
    def _build_docstring(cls) -> str:
        """Build a class docstring documenting every field from the schema."""

        kind = cls.model_fields.get("kind")
        heading = f"R3XA model ``{cls.__name__}``."
        if kind is not None and isinstance(kind.default, str):
            heading = f"R3XA item of kind ``{kind.default}``."

        lines = [heading, "", "Attributes", "----------"]
        required_names = set(cls.required_fields())
        for name, field in cls.model_fields.items():
            is_kind = name == "kind" and isinstance(field.default, str)
            type_name = "str" if is_kind else cls._annotation_name(field.annotation)
            required = name in required_names or is_kind
            suffix = "" if required else ", optional"
            lines.append(f"{name} : {type_name}{suffix}")

            if field.description:
                lines.append(f"    {field.description}")

            if is_kind:
                lines.append(
                    f'    Automatically set to "{field.default}". '
                    "Not a constructor parameter."
                )
            elif required:
                if name == "id":
                    lines.append(
                        "    Required by the schema; a random id is generated "
                        "when omitted."
                    )
                else:
                    lines.append("    Required.")

            allowed = cls._allowed_values(field.annotation)
            if allowed and not is_kind:
                lines.append(f"    Allowed values: [{', '.join(allowed)}].")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    @classmethod
    def required_fields(cls) -> list[str]:
        """Return the names of fields required by the generated model."""

        kind_field = cls.model_fields.get("kind")
        kind = getattr(kind_field, "default", None) if kind_field is not None else None
        if isinstance(kind, str) and "/" in kind:
            section, name = kind.split("/", 1)
            definition = load_schema().get("$defs", {}).get(section, {}).get(name, {})
            required = definition.get("required")
            if isinstance(required, list):
                return [field for field in definition.get("properties", {}) if field in required]
        if {"settings", "data_sources", "data_sets"}.issubset(cls.model_fields):
            return list(load_schema().get("required", ()))
        return [
            name for name, field in cls.model_fields.items() if field.is_required()
        ]

    @classmethod
    def optional_fields(cls) -> list[str]:
        """Return the names of fields that may be omitted."""

        required = set(cls.required_fields())
        kind_field = cls.model_fields.get("kind")
        kind = getattr(kind_field, "default", None) if kind_field is not None else None
        if isinstance(kind, str) and "/" in kind:
            section, name = kind.split("/", 1)
            properties = load_schema().get("$defs", {}).get(section, {}).get(name, {}).get("properties", {})
            return [field for field in properties if field not in required]
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

    def __getitem__(self, field: str) -> Any:
        """Provide a temporary mapping-style bridge during API migration."""

        return getattr(self, field)

    def __setitem__(self, field: str, value: Any) -> None:
        """Set a model attribute; attribute access remains the canonical API."""

        setattr(self, field, value)

    def merge(self: ModelT, **overrides: Any) -> ModelT:
        """Return a typed copy with the supplied attribute overrides."""

        payload = self.to_dict()
        payload.update(overrides)
        return R3XAItem.from_dict(payload, validate=False)  # type: ignore[return-value]

    def __setattr__(self, name: str, value: Any) -> None:
        if name in type(self)._reference_field_map() and value is not None:
            value, objects = self._normalize_reference(value)
            references = getattr(self, "_reference_objects", None)
            if references is not None:
                if objects is None:
                    references.pop(name, None)
                else:
                    references[name] = objects
        elif name in type(self)._reference_field_map():
            try:
                object.__getattribute__(self, "_reference_objects").pop(name, None)
            except AttributeError:
                pass
        super().__setattr__(name, value)
        if name in {"settings", "data_sources", "data_sets"}:
            object.__setattr__(
                self,
                name,
                R3XACollection(getattr(self, name, None) or (), document=self),
            )

    def bind_document(self, document: Any) -> "R3XAItem":
        """Bind this object to a document so references resolve to objects."""

        object.__setattr__(self, "_document", document)
        return self

    def _resolved_reference(self, field: str, value: Any) -> Any:
        document = getattr(self, "_document", None)
        section = type(self)._reference_field_map().get(field)
        if section is None or value is None:
            return value

        objects = getattr(self, "_reference_objects", {}).get(field)
        if document is None and objects is not None:
            return objects
        if document is None:
            return value

        def resolve(item: Any, fallback: Any = None) -> Any:
            identifier = reference_id(item)
            if identifier is None:
                return item
            return document.find(identifier) or fallback or identifier

        if isinstance(value, list):
            fallbacks = objects if isinstance(objects, list) else []
            return [
                resolve(item, fallbacks[index] if index < len(fallbacks) else None)
                for index, item in enumerate(value)
            ]
        return resolve(value, objects)

    def __getattribute__(self, name: str) -> Any:
        try:
            value = object.__getattribute__(self, name)
        except AttributeError:
            value = super().__getattribute__(name)
        if name in type(self)._reference_field_map():
            return self._resolved_reference(name, value)
        return value

    def to_dict(self, *, exclude_none: bool = True) -> Dict[str, Any]:
        """Return a JSON-compatible dictionary representation."""

        payload = self.model_dump(
            mode="json",
            exclude_none=exclude_none,
            fallback=self._to_json_like,
            warnings=False,
        )
        return self._wire_value(payload)

    @classmethod
    def _wire_value(cls, value: Any, field: str | None = None) -> Any:
        """Serialize nested object references as IDs throughout a payload."""

        if field in cls._reference_field_map():
            return cls._reference_wire_value(value)
        if isinstance(value, Mapping):
            return {
                key: cls._wire_value(item, key)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._wire_value(item) for item in value]
        return value

    @staticmethod
    def _reference_wire_value(value: Any) -> Any:
        """Serialize object references as IDs at the JSON boundary."""

        if isinstance(value, list):
            return [R3XAItem._reference_wire_value(item) for item in value]
        identifier = reference_id(value)
        return identifier if identifier is not None else value

    def to_json(self, *, exclude_none: bool = True, indent: int | None = 2) -> str:
        """Return a JSON representation of the model."""

        return json.dumps(
            self.to_dict(exclude_none=exclude_none),
            ensure_ascii=False,
            indent=indent,
        )

    def dump(self, *, exclude_none: bool = True, indent: int | None = 2) -> str:
        """Return the JSON text for this object without writing a file."""

        return self.to_json(exclude_none=exclude_none, indent=indent)

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

    def add(
        self,
        item: Any = None,
        *,
        section: str | None = None,
        **fields: Any,
    ) -> Any:
        """Add a typed or mapping item to the document collection matching its kind."""

        if isinstance(item, str):
            from .core import new_item

            item = new_item(item, **fields)

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
        stored = next(
            (candidate for candidate in getattr(self, target_section) if candidate is item),
            item,
        )
        bind = getattr(stored, "bind_document", None)
        if callable(bind):
            bind(self)
        return stored

    def add_item(self, item: Any = None, **fields: Any) -> Any:
        """Add an item to the collection selected by its kind."""

        return self.add(item, **fields)

    def _add_guided_item(self, kind: str, fields: Dict[str, Any]) -> Any:
        """Create and add a schema-guided item to this document."""

        from .core import build_guided_item

        return self.add(build_guided_item(kind, fields))

    def add_setting(self, item: Any = None, **fields: Any) -> Any:
        """Add a setting to the document."""

        return self.add(item, section="settings", **fields)

    def add_data_source(self, item: Any = None, **fields: Any) -> Any:
        """Add a data source to the document."""

        return self.add(item, section="data_sources", **fields)

    def add_data_set(self, item: Any = None, **fields: Any) -> Any:
        """Add a data set to the document."""

        return self.add(item, section="data_sets", **fields)

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
        references = R3XAItem._value(item, field)
        if references is None:
            references = []
            if isinstance(item, Mapping):
                item[field] = references
            else:
                setattr(item, field, references)
        known_references = [
            R3XAItem._reference_value(value) for value in references
        ]
        if reference not in known_references:
            updated_references = list(references)
            updated_references.append(reference)
            if isinstance(item, Mapping):
                item[field] = updated_references
            else:
                setattr(item, field, updated_references)

    def link_output(self, source: Any, data_set: Any) -> "R3XAItem":
        """Record that a data set is produced by a data source."""

        source = self._resolve_item(source, "data_sources")
        data_set = self._resolve_item(data_set, "data_sets")
        source_id = self._value(source, "id")
        if not source_id:
            raise ValueError("The data source must have an id")
        self._append_reference(data_set, "parent_data_sources", source_id)
        return self

    def link_input(self, source: Any, data_set: Any) -> "R3XAItem":
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

        values = dict(payload)
        if cls is R3XAItem:
            from .core import new_item

            kind = values.get("kind")
            if not isinstance(kind, str):
                raise ValueError("An item kind is required to load a generic R3XAItem")
            model = new_item(kind, **{key: value for key, value in values.items() if key != "kind"})
        else:
            model = cls.model_validate(values)
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

    @classmethod
    def loads(
        cls: type[ModelT],
        text: str,
        *,
        validate: bool = True,
    ) -> ModelT:
        """Load a typed model from JSON text."""

        payload = json.loads(text)
        if not isinstance(payload, Mapping):
            raise TypeError("R3XA JSON root must be an object")
        return cls.from_dict(payload, validate=validate)

    def validate(self, *, schema: Dict[str, Any] | None = None) -> None:
        """Validate this model and return ``None`` when it is valid."""

        from .registry import validate_item
        from .validate import validate as validate_document

        payload = self.to_dict()
        kind = getattr(self, "kind", None)
        if isinstance(kind, str):
            validate_item(payload, kind=kind, schema=schema)
        else:
            validate_document(payload, schema=schema)

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

    @staticmethod
    def _to_json_like(value: Any) -> Any:
        """Reduce pydantic values to plain JSON types, preserving structure."""

        if isinstance(value, Enum):
            return value.value
        if isinstance(value, RootModel):
            # Constrained scalars (Uint, DataSetId, ...) read as their payload.
            return R3XAItem._to_json_like(value.root)
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, Mapping):
            return {key: R3XAItem._to_json_like(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [R3XAItem._to_json_like(item) for item in value]
        return value

    @staticmethod
    def _format_value(value: Any) -> str:
        """Render a field value the way it reads to a user, not as a repr.

        Delegates to `core.format_json_value` so item-level and document-level
        `print()` render units and lists identically.
        """

        return format_json_value(R3XAItem._to_json_like(value))

    @staticmethod
    def _summary_label(value: Any, preferred: str) -> Any:
        """Return the human label for an embedded object or reference."""

        if isinstance(value, Mapping):
            candidates = (preferred, "title", "name", "id", "root")
            for key in candidates:
                candidate = value.get(key)
                if candidate is not None:
                    return candidate
            return value
        candidates = (preferred, "title", "name", "id", "root")
        for attribute in candidates:
            candidate = getattr(value, attribute, None)
            if candidate is not None:
                return candidate
        return value

    @classmethod
    def _summary_field_value(cls, name: str, value: Any) -> Any:
        """Replace verbose embedded objects with labels in human summaries."""

        if name == "authors":
            if isinstance(value, list):
                return [cls._summary_label(item, "name") for item in value]
            return cls._summary_label(value, "name")
        if name in cls._reference_field_map():
            if isinstance(value, list):
                return [cls._summary_label(item, "title") for item in value]
            return cls._summary_label(value, "title")
        return value

    def summary(self) -> str:
        """Return a readable listing of all model fields, including null values."""

        lines = [self.__class__.__name__]
        required = set(self.required_fields())
        for name in type(self).model_fields:
            marker = "*" if name in required else " "
            value = self._summary_field_value(name, getattr(self, name, None))
            if name in {"settings", "data_sources", "data_sets"} and isinstance(value, list):
                value = [getattr(item, "title", None) for item in value]
            lines.append(f"{marker} {name}: {self._format_value(value)}")
        return "\n".join(lines)

    def print(self) -> None:
        """Print a readable listing of all model fields."""

        print(self.summary())

    def __str__(self) -> str:
        # `print(item)` shows the same listing as `item.print()`.
        # `__repr__` stays pydantic's single-line form: it is what a list of
        # items falls back to, and a multi-line summary per element would make
        # `document.data_sources` unreadable.
        return self.summary()

    def __repr__(self) -> str:
        return self.summary()

    def plot(
        self,
        path: str | Path,
        *,
        backend: str = "graphviz-wasm",
        palette: str | None = None,
        include_description: bool = True,
        **kwargs: Any,
    ) -> Path:
        """Render a document model with one of the available graph backends."""

        if not {"settings", "data_sources", "data_sets"}.issubset(type(self).model_fields):
            raise TypeError("plot() is available only on an R3XA document")
        from .webcore import graph as _graph

        renderers: Dict[str, Any] = {
            "graphviz": _graph.render_graphviz_file,
            "graphviz-wasm": _graph.render_graphviz_wasm_file,
            "pyvis": _graph.render_pyvis_html,
            "matplotlib": _graph.render_networkx_matplotlib_file,
        }
        if backend not in renderers:
            raise ValueError(
                f"Unknown graph backend {backend!r}. Available: {', '.join(sorted(renderers))}"
            )
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        if backend in {"graphviz", "graphviz-wasm"} and output.suffix == ".svg":
            output = output.with_suffix("")
        return renderers[backend](
            self.to_dict(),
            output,
            include_description=include_description,
            palette=palette,
            **kwargs,
        )


class R3XACollection(list[Any]):
    """Mutable document collection that preserves typed item identity.

    Pydantic validates the collection contents when it is assigned, then this
    list keeps the original objects and binds them to their containing
    document. Direct ``append`` and slice operations therefore behave like
    the document's object graph rather than creating dictionary copies.
    """

    def __init__(self, values: Iterable[Any] = (), document: Any = None) -> None:
        self.document = document
        super().__init__()
        self.extend(values)

    def _normalize(self, value: Any) -> Any:
        if isinstance(value, R3XAItem):
            item = value
        else:
            if hasattr(value, "to_dict"):
                payload = value.to_dict()
            elif isinstance(value, Mapping):
                payload = dict(value)
            else:
                raise TypeError("Document collections require typed R3XA objects or mappings")
            kind = payload.get("kind")
            if not isinstance(kind, str):
                raise TypeError("Document collection items require a kind")
            from .core import new_item

            item = new_item(kind, **{key: value for key, value in payload.items() if key != "kind"})
        if self.document is not None:
            item.bind_document(self.document)
        return item

    def append(self, value: Any) -> None:
        super().append(self._normalize(value))

    def extend(self, values: Iterable[Any]) -> None:
        for value in values:
            self.append(value)

    def insert(self, index: int, value: Any) -> None:
        super().insert(index, self._normalize(value))

    def __iadd__(self, values: Iterable[Any]) -> "R3XACollection":
        self.extend(values)
        return self

    def __setitem__(self, index: Any, value: Any) -> None:
        if isinstance(index, slice):
            super().__setitem__(index, [self._normalize(item) for item in value])
        else:
            super().__setitem__(index, self._normalize(value))


# Generated models historically inherit the name `R3XAModel`; keep that base
# name while exposing the object-oriented public name `R3XAItem`.
R3XAModel = R3XAItem
