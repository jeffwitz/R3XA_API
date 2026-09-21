from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, Sequence, Union

from .schema import load_schema
from ._format import format_json_value
from .model_base import R3XAItem
from ._ids import generate_id


def new_item(kind: str, **fields: Any) -> R3XAItem:
    """Create a standalone schema item with default `id` and `kind` if missing.

    Returns an `R3XAItem`, so the result prints, validates and saves on its own
    without belonging to any document.
    """
    model_class = _model_class_for_kind(kind)
    if model_class is None:
        raise ValueError(f"Unsupported R3XA item kind: {kind}")
    payload = dict(fields)
    if "id" in model_class.model_fields:
        payload.setdefault("id", generate_id(kind))
    payload.setdefault("kind", kind)
    return model_class(**payload)


@lru_cache(maxsize=1)
def _model_classes_by_kind() -> Dict[str, type[R3XAItem]]:
    """Discover generated object classes by their schema-fixed `kind`."""

    from . import models

    discovered: Dict[str, type[R3XAItem]] = {}
    for name in getattr(models, "__all__", ()):
        candidate = getattr(models, name, None)
        if not isinstance(candidate, type) or not issubclass(candidate, R3XAItem):
            continue
        field = candidate.model_fields.get("kind")
        value = getattr(field, "default", None) if field is not None else None
        if isinstance(value, str):
            discovered.setdefault(value, candidate)
    return discovered


def _model_class_for_kind(kind: str) -> type[R3XAItem] | None:
    return _model_classes_by_kind().get(kind)


def unit(
    title: Optional[str] = None,
    value: Optional[float] = None,
    unit: Optional[str] = None,
    scale: Optional[float] = 1.0,
    **extra: Any,

) -> R3XAItem:
    """Build a typed unit object compatible with the R3XA schema."""

    if unit is None:
        raise TypeError("unit requires the `unit` field")
    payload: Dict[str, Any] = {"kind": "unit", "unit": unit}
    if title is not None:
        payload["title"] = title
    if value is not None:
        payload["value"] = value
    if scale is not None:
        payload["scale"] = scale
    payload.update(extra)
    return new_item("unit", **{key: value for key, value in payload.items() if key != "kind"})


def author(
    name: str,
    affiliation: Optional[str] = None,
    orcid: Optional[str] = None,
    **extra: Any,
) -> R3XAItem:
    """Build an author payload compatible with the R3XA schema.

    Since schema 2026.9.16 an author carries its own ORCID, instead of being a
    bare name paired with a parallel `author_orcids` array.
    """

    if not name:
        raise TypeError("author requires a non-empty `name`")
    payload: Dict[str, Any] = {"name": name}
    if affiliation is not None:
        payload["affiliation"] = affiliation
    if orcid is not None:
        payload["orcid"] = orcid
    payload.update(extra)
    from . import models

    return models.Author.model_validate(payload)


def data_set_file(
    filename: Optional[str] = None,
    file_type: Optional[str] = None,
    delimiter: Optional[str] = None,
    col: Optional[Union[int, str]] = None,
    rows: Optional[Sequence[Optional[int]]] = None,
    **extra: Any,
) -> R3XAItem:
    """Build a typed `data_set_file` object for timestamps or values."""

    if "data_range" in extra:
        raise TypeError(
            "data_range is not part of schema 2026.9.18; use col= and rows= instead"
        )
    payload: Dict[str, Any] = {"kind": "data_set_file", "filename": filename}
    if file_type is not None:
        payload["file_type"] = file_type
    if delimiter is not None:
        payload["delimiter"] = delimiter
    if col is not None:
        payload["col"] = col
    if rows is not None:
        if isinstance(rows, (str, bytes)):
            raise TypeError("rows must be a sequence of integers or None")
        payload["rows"] = list(rows)
    payload.update(extra)
    return new_item(
        "data_set_file",
        **{key: value for key, value in payload.items() if key != "kind"},
    )


def _ensure_data_set_file(value: Union[str, Mapping[str, Any], R3XAItem]) -> R3XAItem:
    """Normalize a path, mapping, or typed selector into a `DataSetFile`."""

    if isinstance(value, R3XAItem):
        return value
    if isinstance(value, Mapping):
        payload = dict(value)
        payload.pop("kind", None)
        return data_set_file(**payload)
    return data_set_file(filename=value)


_GUIDED_SECTION_SUFFIX = {
    "settings": "setting",
    "data_sources": "source",
    "data_sets": "data_set",
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


def _normalize_guided_fields(kind: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize guided helper fields before building an item."""

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
        normalized["values"] = _ensure_data_set_file(normalized["values"])

    return normalized


def build_guided_item(kind: str, fields: Dict[str, Any]) -> R3XAItem:
    """Build one guided item, checking the schema's required fields.

    Shared by `R3XAFile.add_<kind>_<section>()` and the module-level
    `new_<kind>_<section>()`, so a standalone item and a document-bound one are
    built identically.
    """

    spec = _guided_item_spec(kind)
    missing_fields = [field for field in spec["required"] if field not in fields]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise TypeError(f"{spec['helper_name']} missing required arguments: {missing}")
    return new_item(kind, **_normalize_guided_fields(kind, fields))


def _make_guided_helper(method_name: str, kind: str, required_fields: Sequence[str]) -> Callable[..., R3XAItem]:
    """Create a guided helper with explicit required parameters for one kind."""

    params = ["self"] + [f"{field}: Any" for field in required_fields] + ["**extra: Any"]
    header = ", ".join(params)
    field_lines = "\n".join(
        f"    fields[{field!r}] = {field}" for field in required_fields
    ) or "    fields = {}"
    if required_fields:
        field_lines = "    fields: Dict[str, Any] = {}\n" + field_lines

    source = (
        f"def {method_name}({header}) -> R3XAItem:\n"
        f"    \"\"\"Add a `{kind}` item.\"\"\"\n"
        f"{field_lines}\n"
        "    fields.update(extra)\n"
        f"    return self._add_guided_item({kind!r}, fields)\n"
    )
    namespace: Dict[str, Any] = {"Any": Any, "Dict": Dict, "R3XAItem": R3XAItem}
    exec(source, namespace)
    helper = namespace[method_name]
    helper.__qualname__ = f"R3XAFile.{method_name}"
    helper.__doc__ = (
        f"Add a `{kind}` item.\n\n"
        f"Required fields: {', '.join(required_fields) if required_fields else '(none)'}.\n"
        "Optional schema fields can be passed through `**extra`."
    )
    return helper


class _GeneratedHeaderProxy(MutableMapping[str, Any]):
    """Mapping view over the generated document's direct header attributes."""

    _collections = {"settings", "data_sources", "data_sets"}

    def __init__(self, document: Any) -> None:
        self.document = document

    def __getitem__(self, key: str) -> Any:
        if key not in type(self.document).model_fields or key in self._collections:
            raise KeyError(key)
        return getattr(self.document, key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in type(self.document).model_fields or key in self._collections:
            raise KeyError(key)
        setattr(self.document, key, value)

    def __delitem__(self, key: str) -> None:
        if key not in type(self.document).model_fields or key in self._collections:
            raise KeyError(key)
        setattr(self.document, key, None)

    def __iter__(self):
        return (
            key
            for key in type(self.document).model_fields
            if key not in self._collections and getattr(self.document, key, None) is not None
        )

    def __len__(self) -> int:
        return sum(1 for _ in self)


from . import models as _generated_models


class R3XAFile(_generated_models.R3XADocument):
    """The generated Pydantic R3XA document model.

    The public document API is now the same object-first model family as the
    item API. Instances may be edited while incomplete and become valid only
    after the explicit schema validation boundary.
    """

    @property
    def header(self) -> MutableMapping[str, Any]:
        """Return a mapping view over the document's direct attributes."""

        return _GeneratedHeaderProxy(self)

    def set_header(self, **fields: Any) -> "R3XAFile":
        """Set several top-level document fields and return this document."""

        for field, value in fields.items():
            setattr(self, field, value)
        return self

    def to_model(self) -> "R3XAFile":
        """Return this document; it is already the generated Pydantic model."""

        self.validate()
        return self

    @classmethod
    def from_model(cls, model: Any) -> "R3XAFile":
        """Create this document type from another generated model."""

        if isinstance(model, R3XAItem):
            return cls.model_validate(model.to_dict())
        raise TypeError("R3XAFile.from_model expects a generated Pydantic model")


def _make_standalone_builder(function_name: str, kind: str, required_fields: Sequence[str]) -> Callable[..., R3XAItem]:
    """Create a module-level `new_<kind>_<section>()` building one item alone.

    A setting or a data source is meaningful on its own - a lab's testing
    machines, say - so building one should not require inventing a document to
    hang it on.
    """

    params = [f"{field}: Any" for field in required_fields] + ["**extra: Any"]
    header = ", ".join(params)
    field_lines = "\n".join(f"    fields[{field!r}] = {field}" for field in required_fields)
    if required_fields:
        field_lines = "    fields: Dict[str, Any] = {}\n" + field_lines
    else:
        field_lines = "    fields: Dict[str, Any] = {}"

    source = (
        f"def {function_name}({header}) -> R3XAItem:\n"
        f"{field_lines}\n"
        "    fields.update(extra)\n"
        f"    return build_guided_item({kind!r}, fields)\n"
    )
    namespace: Dict[str, Any] = {
        "Any": Any,
        "Dict": Dict,
        "R3XAItem": R3XAItem,
        "build_guided_item": build_guided_item,
    }
    exec(source, namespace)
    builder = namespace[function_name]
    builder.__qualname__ = function_name
    builder.__doc__ = (
        f"Create a standalone `{kind}` item.\n\n"
        f"Required fields: {', '.join(required_fields) if required_fields else '(none)'}.\n"
        "Optional schema fields can be passed through `**extra`.\n"
        "The item is not attached to any document; add it later with "
        "`document.settings.append(item)` or the matching collection."
    )
    return builder


GUIDED_BUILDERS: Dict[str, str] = {}


def _install_guided_helpers() -> None:
    """Attach schema-driven guided helpers to `R3XAFile` and to this module."""

    for kind, spec in _guided_kind_specs().items():
        setattr(
            R3XAFile,
            spec["helper_name"],
            _make_guided_helper(spec["helper_name"], kind, spec["required"]),
        )
        builder_name = "new_" + spec["helper_name"][len("add_"):]
        globals()[builder_name] = _make_standalone_builder(builder_name, kind, spec["required"])
        GUIDED_BUILDERS[builder_name] = kind

_install_guided_helpers()
