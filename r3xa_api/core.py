from __future__ import annotations

import json
import inspect
import random
import string
from collections.abc import Mapping
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


def format_number(value: Any) -> str:
    """Render an integral float without its trailing zero: 1392.0 -> 1392."""

    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def format_json_value(value: Any) -> str:
    """Render a JSON-compatible value the way it reads to a user.

    Units collapse to `1392 px` and lists of them to `[1392 px, 1040 px]`.
    The typed models reuse this so document-level and item-level `print()`
    agree on the same conventions; it stays free of any pydantic dependency
    because `R3XAFile` works on plain dictionaries.
    """

    if value is None:
        return "None"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, Mapping):
        if value.get("kind") == "unit" and "value" in value and "unit" in value:
            return f"{format_number(value['value'])} {value['unit']}"
        inner = ", ".join(f"{key}: {format_json_value(item)}" for key, item in value.items())
        return "{" + inner + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(format_json_value(item) for item in value) + "]"
    return format_number(value)


@lru_cache(maxsize=None)
def _reference_fields() -> Dict[str, str]:
    """Return the fields holding item references, mapped to the section they point to.

    Read from the schema rather than hardcoded, so a reference added later is
    resolved too.
    """

    id_types = {
        "#/$defs/types/setting_id": "settings",
        "#/$defs/types/data_source_id": "data_sources",
        "#/$defs/types/data_set_id": "data_sets",
    }
    fields: Dict[str, str] = {}

    def visit(node: Any, field: Optional[str]) -> None:
        if isinstance(node, Mapping):
            reference = node.get("$ref")
            if field and reference in id_types:
                fields[field] = id_types[reference]
            items = node.get("items")
            if field and isinstance(items, Mapping) and items.get("$ref") in id_types:
                fields[field] = id_types[items["$ref"]]
            for key, value in node.items():
                visit(value, key if key not in ("items", "properties", "$defs") else field)
        elif isinstance(node, list):
            for value in node:
                visit(value, field)

    visit(load_schema(), None)
    return fields


@lru_cache(maxsize=None)
def _item_field_spec(kind: str) -> tuple:
    """Return the schema's field order and required names for an item kind.

    Cached, and deliberately returning immutable values: the result is shared.
    """

    schema = load_schema()
    section, _, name = kind.partition("/")
    definition = schema.get("$defs", {}).get(section, {}).get(name, {})
    return tuple(definition.get("properties", {})), frozenset(definition.get("required", ()))


class R3XAItem(dict):
    """An R3XA item that stays a dictionary but prints, validates and saves.

    `R3XAFile` must work without pydantic, so items cannot be typed models.
    The ergonomics are added to the dictionary itself instead: this is a real
    `dict` subclass, so `item["title"]`, `isinstance(item, dict)`, `json.dumps`
    and equality with a plain dict all keep working unchanged.
    """

    # Set when the item joins a document, so `summary()` can show what a
    # reference points at instead of its identifier.
    _document: Any = None

    @property
    def kind(self) -> Optional[str]:
        """Return the item's schema kind, when it carries one."""

        value = self.get("kind")
        return value if isinstance(value, str) else None

    def _resolve_reference(self, section: str, identifier: Any) -> str:
        """Render a reference as the title of the item it points at."""

        document = self._document
        if document is not None and isinstance(identifier, str):
            for candidate in getattr(document, section, ()) or ():
                if isinstance(candidate, Mapping) and candidate.get("id") == identifier:
                    title = candidate.get("title")
                    if title:
                        return str(title)
        return format_json_value(identifier)

    def _format_field(self, name: str, value: Any) -> str:
        """Render one field, resolving references to the titles they point at."""

        section = _reference_fields().get(name)
        if section is None or value is None:
            return format_json_value(value)
        if isinstance(value, list):
            return "[" + ", ".join(self._resolve_reference(section, v) for v in value) + "]"
        return self._resolve_reference(section, value)

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dictionary copy."""

        return dict(self)

    def required_fields(self) -> List[str]:
        """Return the field names the schema requires for this kind."""

        order, required = _item_field_spec(self.kind or "")
        return [name for name in order if name in required]

    def optional_fields(self) -> List[str]:
        """Return the field names the schema allows but does not require."""

        order, required = _item_field_spec(self.kind or "")
        return [name for name in order if name not in required]

    def missing_fields(self) -> List[str]:
        """Return required fields that are absent or null."""

        return [name for name in self.required_fields() if self.get(name) is None]

    def field_descriptions(self) -> Dict[str, str]:
        """Return the schema description of each documented field."""

        schema = load_schema()
        section, _, name = (self.kind or "").partition("/")
        definition = schema.get("$defs", {}).get(section, {}).get(name, {})
        return {
            field: spec["description"]
            for field, spec in definition.get("properties", {}).items()
            if isinstance(spec, dict) and spec.get("description")
        }

    def summary(self) -> str:
        """Return a readable listing of every schema field, including absent ones.

        Same conventions as the typed models: `*` marks required fields, and
        values render through `format_json_value`.
        """

        order, required = _item_field_spec(self.kind or "")
        names = list(order) + [name for name in self if name not in order]

        lines = [self.kind or "R3XA item"]
        for name in names:
            marker = "*" if name in required else " "
            lines.append(f"{marker} {name}: {self._format_field(name, self.get(name))}")
        return "\n".join(lines)

    def print(self) -> None:
        """Print a readable listing of the item."""

        print(self.summary())

    def __str__(self) -> str:
        # `__repr__` stays dict's compact form, so a list of items remains
        # readable; `print(item)` gets the listing.
        return self.summary()

    def validate(self, schema: Optional[Dict[str, Any]] = None) -> "R3XAItem":
        """Validate this item against its schema kind and return it."""

        from .registry import validate_item

        validate_item(self, kind=self.kind, schema=schema)
        return self

    @classmethod
    def load(cls, path: str | Path) -> "R3XAItem":
        """Load a single item from a JSON file."""

        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(
        self,
        path: str | Path,
        *,
        validate: bool = True,
        indent: int = 2,
    ) -> Path:
        """Validate and save this item alone to a JSON file."""

        if validate:
            self.validate()
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=indent) + "\n",
            encoding="utf-8",
        )
        return destination


def new_item(kind: str, **fields: Any) -> R3XAItem:
    """Create a standalone schema item with default `id` and `kind` if missing.

    Returns an `R3XAItem`, so the result prints, validates and saves on its own
    without belonging to any document.
    """

    item = R3XAItem(fields)
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


def author(
    name: str,
    affiliation: Optional[str] = None,
    orcid: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
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
    return payload


def data_set_file(
    filename: str,
    file_type: Optional[str] = None,
    delimiter: Optional[str] = None,
    col: Optional[Union[int, str]] = None,
    rows: Optional[Sequence[Optional[int]]] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Build a `data_set_file` payload for `timestamps` or `values` fields."""

    payload = {
        "kind": "data_set_file",
        "filename": filename,
    }
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
    """List of `R3XAItem`, accepting dicts and typed models exposing `model_dump`."""

    def __init__(self, values: Iterable[Any] = (), document: Any = None) -> None:
        super().__init__()
        self.document = document
        self.extend(values)

    def _normalize(self, value: Any) -> R3XAItem:
        # Already-wrapped items pass through unchanged, so the object returned
        # by `add_item` is the very one stored in the collection.
        if isinstance(value, R3XAItem):
            item = value if value._document in (None, self.document) else R3XAItem(value.to_dict())
        else:
            item = R3XAItem(from_model(value))
        if self.document is not None:
            item._document = self.document
        return item

    def append(self, value: Any) -> None:
        super().append(self._normalize(value))

    def extend(self, values: Iterable[Any]) -> None:
        super().extend(self._normalize(value) for value in values)

    def __iadd__(self, values: Iterable[Any]) -> "_ModelAwareList":
        # `list.__iadd__` is implemented in C and bypasses the `extend` override,
        # so `document.settings += [item]` would otherwise store a bare dict.
        self.extend(values)
        return self

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
        self.settings: List[R3XAItem] = _ModelAwareList(document=self)
        self.data_sources: List[R3XAItem] = _ModelAwareList(document=self)
        self.data_sets: List[R3XAItem] = _ModelAwareList(document=self)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"settings", "data_sources", "data_sets"}:
            if not (isinstance(value, _ModelAwareList) and value.document is self):
                value = _ModelAwareList(value, document=self)
        object.__setattr__(self, name, value)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "R3XAFile":
        """Create a builder from an existing document payload."""

        version = payload.get("version")
        header = {k: v for k, v in payload.items() if k not in {"version", "settings", "data_sources", "data_sets"}}
        obj = cls(version=version, **header)
        obj.settings = _ModelAwareList(payload.get("settings", []), document=obj)
        obj.data_sources = _ModelAwareList(payload.get("data_sources", []), document=obj)
        obj.data_sets = _ModelAwareList(payload.get("data_sets", []), document=obj)
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

    def _target_collection(self, kind: str) -> List[R3XAItem]:
        """Return the target top-level collection matching item kind."""

        section = kind.split("/", 1)[0]
        if section == "settings":
            return self.settings
        if section == "data_sources":
            return self.data_sources
        if section == "data_sets":
            return self.data_sets
        raise ValueError("kind must start with settings/, data_sources/, or data_sets/")

    def add_item(self, kind: str, **fields: Any) -> R3XAItem:
        """Append an item to the correct collection and return it.

        The returned object is the one stored in the collection, so mutating it
        updates the document.
        """

        collection = self._target_collection(kind)
        collection.append(new_item(kind, **fields))
        return collection[-1]

    def add_setting(self, kind: str, **fields: Any) -> R3XAItem:
        """Append a setting item and return it."""

        if not kind.startswith("settings/"):
            raise ValueError("add_setting expects a kind starting with settings/")
        return self.add_item(kind, **fields)

    def add_data_source(self, kind: str, **fields: Any) -> R3XAItem:
        """Append a data source item and return it."""

        if not kind.startswith("data_sources/"):
            raise ValueError("add_data_source expects a kind starting with data_sources/")
        return self.add_item(kind, **fields)

    def add_data_set(self, kind: str, **fields: Any) -> R3XAItem:
        """Append a dataset item and return it."""

        if not kind.startswith("data_sets/"):
            raise ValueError("add_data_set expects a kind starting with data_sets/")
        return self.add_item(kind, **fields)

    def _normalize_guided_fields(self, kind: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Deprecated shim: use the module-level `_normalize_guided_fields`."""

        return _normalize_guided_fields(kind, fields)

    def _add_guided_item(self, kind: str, fields: Dict[str, Any]) -> R3XAItem:
        """Validate required schema fields and append one guided item."""

        item = build_guided_item(kind, fields)
        collection = self._target_collection(kind)
        collection.append(item)
        return collection[-1]

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

    @staticmethod
    def _item_titles(items: Iterable[R3XAItem]) -> str:
        """Return the titles of a collection, which is what identifies items on sight."""

        return "[" + ", ".join(str(item.get("title", "None")) for item in items) + "]"

    def summary(self) -> str:
        """Return a readable listing of the header and the document collections.

        Header fields follow the schema's own order and are marked with `*`
        when the schema requires them, matching the typed models' `summary()`.
        """

        schema = load_schema()
        properties = schema.get("properties", {})
        collections = ("settings", "data_sources", "data_sets")
        required = set(schema.get("required", []))

        names = [name for name in properties if name not in collections]
        # Header keys the document carries but the schema does not describe.
        names += [name for name in self.header if name not in properties]

        width = max(len(name) for name in names + list(collections))
        lines = ["R3XA File", "─" * max(width + 20, 40)]

        for name in names:
            marker = "*" if name in required else " "
            value = self.header.get(name)
            if name == "authors" and isinstance(value, list):
                # A listing wants who the authors are, not their affiliations
                # and ORCIDs; those stay one `to_dict()` away.
                value = "[" + ", ".join(
                    str(a.get("name", a)) if isinstance(a, Mapping) else str(a) for a in value
                ) + "]"
            else:
                value = format_json_value(value)
            lines.append(f"{marker} {name:<{width}} : {value}")

        for name in collections:
            marker = "*" if name in required else " "
            titles = self._item_titles(getattr(self, name))
            lines.append(f"{marker} {name:<{width}} : {titles}")

        return "\n".join(lines)

    def print(self) -> None:
        """Print a readable listing of the document."""

        print(self.summary())

    def __str__(self) -> str:
        return self.summary()

    def __repr__(self) -> str:
        # The default object repr carried no information at all, so showing the
        # same listing costs nothing and makes a bare `document` useful in a REPL.
        return self.summary()

    def plot(
        self,
        path: str | Path,
        *,
        backend: str = "graphviz",
        palette: str | None = None,
        include_description: bool = True,
        **kwargs: Any,
    ) -> Path:
        """Render the document's item graph to a file and return its path.

        `backend` selects the renderer: "graphviz" (SVG), "pyvis" (interactive
        HTML) or "matplotlib" (PNG). Each needs its optional dependency, so the
        import happens here rather than at module import time. The extension is
        supplied by the backend; the returned path is the file actually written.

        `palette` selects the colours, identically for every backend: "default",
        or "document" for J-C. Passieux's ochre/crimson/teal scheme.
        """

        from .webcore import graph as _graph

        renderers: Dict[str, Callable[..., Path]] = {
            "graphviz": _graph.render_graphviz_file,
            "pyvis": _graph.render_pyvis_html,
            "matplotlib": _graph.render_networkx_matplotlib_file,
        }
        if backend not in renderers:
            raise ValueError(
                f"Unknown graph backend {backend!r}. "
                f"Available: {', '.join(sorted(renderers))}"
            )

        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        if backend == "graphviz" and output.suffix == ".svg":
            # Graphviz appends the format itself, so `g.svg` would become
            # `g.svg.svg`. The other backends normalise the suffix themselves.
            output = output.with_suffix("")

        return renderers[backend](
            self.to_dict(),
            output,
            include_description=include_description,
            palette=palette,
            **kwargs,
        )

    def save(self, path: str | Path, indent: int = 4, validate: bool = True) -> Path:
        """Validate optionally, then serialize payload as JSON to disk."""

        if validate:
            self.validate()

        path = Path(path)
        path.write_text(self.dump(indent=indent) + "\n", encoding="utf-8")
        return path


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

    for alias_name, target_name in _GUIDED_ALIAS_TARGETS.items():
        setattr(R3XAFile, alias_name, _make_guided_alias(alias_name, target_name))
        builder_alias = "new_" + alias_name[len("add_"):]
        target_builder = "new_" + target_name[len("add_"):]
        globals()[builder_alias] = globals()[target_builder]
        GUIDED_BUILDERS[builder_alias] = GUIDED_BUILDERS[target_builder]


_install_guided_helpers()
