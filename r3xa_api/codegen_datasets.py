# -*- coding: utf-8 -*-
"""
codegen_datasets.py

Generate new_dataset.py from resources/schema.json.

Usage:

    python codegen_datasets.py

The generated file (new_dataset.py) must not be edited manually:
re-run this script whenever schema.json changes.

This generator mirrors codegen_datasources.py / codegen_settings.py
exactly (same architecture, same reasoning), applied to the schema's
``$defs.data_sets`` section.

Design notes
------------
* ``Dataset`` is the mother class. It carries the attributes common to
  every data set (those found in ``$defs.data_sets.generic``) and
  implements every method that does *not* depend on a specific set of
  attributes: ``validate()``, ``save()``, ``load()``, ``from_dict()``,
  ``print()``, ``__str__()`` and ``__repr__()``. Those methods are
  written once and inherited by every subclass.

* ``GenericDataSet`` is the concrete subclass of ``Dataset`` bound to
  the ``data_sets/generic`` kind. It is also the fallback target of
  ``Dataset.load()``/``Dataset.from_dict()`` when a payload's ``kind``
  is missing or not recognised.

* Every other data set kind declared in the schema (``file``,
  ``list``) gets its own subclass of ``Dataset`` (``FileDataSet``,
  ``ListDataSet``), each with its own ``__init__`` (only the required
  fields of *that* kind are mandatory), its own ``kind`` (fixed, via a
  read-only property) and its own ``to_dict()`` /
  ``_format_attributes()``.

* ``Dataset.load()``/``from_dict()`` dispatch dynamically on the
  payload's ``"kind"`` via a small registry populated automatically
  while this module is generated -- so code such as::

      data_sets = [Dataset.from_dict(item) for item in data_sets_payloads]

  never needs to know which concrete data set kinds exist.

* ``id`` is always optional in every constructor, even though the
  schema marks it as required: if omitted, a random id is generated
  automatically.

* ``validate()`` uses ``registry.validate_item()`` (single item,
  validated against its own ``$defs`` entry via its ``kind``), not
  ``validate.validate()`` (which expects a complete R3XA document).
"""

from __future__ import annotations

import json
import keyword
from pathlib import Path
from typing import Any


# ============================================================================
# Configuration
# ============================================================================

ROOT = Path(__file__).resolve().parent

SCHEMA_PATH = ROOT / "resources" / "schema.json"
OUTPUT_PATH = ROOT / "new_dataset.py"

# Name of the mother class.
MOTHER_CLASS_NAME = "DataSet"

# Name of the concrete class for the generic ("data_sets/generic") kind.
GENERIC_CLASS_NAME = "GenericDataSet"


# ============================================================================
# Schema loading
# ============================================================================


def load_schema(path: Path) -> dict[str, Any]:
    """Load the JSON schema."""

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_data_sets(
    schema: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """
    Return the data set definitions from the schema.

    Expected structure:

        $defs:
            data_sets:
                ...
    """

    try:
        data_sets = schema["$defs"]["data_sets"]
    except KeyError as exc:
        raise ValueError(
            "Unable to find '$defs.data_sets' in schema.json."
        ) from exc

    if not isinstance(data_sets, dict):
        raise ValueError(
            "'$defs.data_sets' must be a dictionary."
        )

    return data_sets


def get_properties(
    definition: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return the properties of a schema definition."""

    properties = definition.get(
        "properties",
        {},
    )

    if not isinstance(properties, dict):
        return {}

    return properties


def get_required(
    definition: dict[str, Any],
) -> list[str]:
    """Return the required properties, in schema order."""

    required = definition.get(
        "required",
        [],
    )

    if not isinstance(required, list):
        return []

    return [
        value
        for value in required
        if isinstance(value, str)
    ]


def get_kind(
    definition: dict[str, Any],
) -> str | None:
    """Return the constant value of the kind property."""

    properties = get_properties(
        definition
    )

    kind_schema = properties.get(
        "kind"
    )

    if not isinstance(kind_schema, dict):
        return None

    kind = kind_schema.get(
        "const"
    )

    if isinstance(kind, str):
        return kind

    return None


# ============================================================================
# Python names
# ============================================================================


def check_identifier(name: str) -> None:
    """Check that a schema property is a valid Python identifier."""

    if not name.isidentifier():
        raise ValueError(
            f"'{name}' is not a valid Python identifier."
        )

    if keyword.iskeyword(name):
        raise ValueError(
            f"'{name}' is a Python keyword."
        )


def to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase."""

    return "".join(
        part.capitalize()
        for part in name.split("_")
    )


def class_name_for(name: str) -> str:
    """Return the Python class name for a data set definition."""

    if name == "generic":
        return GENERIC_CLASS_NAME

    return f"{to_pascal_case(name)}DataSet"


# ============================================================================
# Type handling
# ============================================================================


def schema_type_to_python(
    property_schema: dict[str, Any],
) -> str:
    """
    Convert a JSON Schema property into a Python type annotation.

    Complex schema constructs are intentionally represented as Any.
    """

    if "$ref" in property_schema:
        return "Any"

    if "oneOf" in property_schema:
        return "Any"

    if "anyOf" in property_schema:
        return "Any"

    if "allOf" in property_schema:
        return "Any"

    if "enum" in property_schema:

        values = property_schema["enum"]

        if not values:
            return "Any"

        first_value = values[0]

        if isinstance(first_value, bool):
            return "bool"

        if isinstance(first_value, int):
            return "int"

        if isinstance(first_value, float):
            return "float"

        if isinstance(first_value, str):
            return "str"

        return "Any"

    if "const" in property_schema:

        value = property_schema["const"]

        if isinstance(value, bool):
            return "bool"

        if isinstance(value, int):
            return "int"

        if isinstance(value, float):
            return "float"

        if isinstance(value, str):
            return "str"

        return "Any"

    schema_type = property_schema.get(
        "type"
    )

    if schema_type == "string":
        return "str"

    if schema_type == "integer":
        return "int"

    if schema_type == "number":
        return "float"

    if schema_type == "boolean":
        return "bool"

    if schema_type == "object":
        return "dict[str, Any]"

    if schema_type == "array":

        items = property_schema.get(
            "items",
            {},
        )

        if isinstance(items, dict):
            item_type = schema_type_to_python(
                items
            )
        else:
            item_type = "Any"

        return f"list[{item_type}]"

    return "Any"


def schema_type_to_doc(
    property_schema: dict[str, Any],
) -> str:
    """
    Convert a JSON Schema property into a human-readable type.

    A reference to ``#/$defs/types/<name>`` is rendered as
    ``R3XA.<NAME>`` (e.g. ``#/$defs/types/unit`` -> ``R3XA.UNIT``,
    ``#/$defs/types/data_set_file`` -> ``R3XA.DATA_SET_FILE``).
    """

    if "$ref" in property_schema:

        ref = property_schema["$ref"]
        ref_name = ref.split("/")[-1]

        return f"R3XA.{ref_name.upper()}"

    if "oneOf" in property_schema:
        return "Any"

    if "anyOf" in property_schema:
        return "Any"

    if "allOf" in property_schema:
        return "Any"

    if "enum" in property_schema:

        values = property_schema["enum"]

        if values:

            first_value = values[0]

            if isinstance(first_value, bool):
                return "bool"

            if isinstance(first_value, int):
                return "int"

            if isinstance(first_value, float):
                return "float"

            if isinstance(first_value, str):
                return "str"

        return "Any"

    if property_schema.get("type") == "array":

        items = property_schema.get(
            "items",
            {},
        )

        if isinstance(items, dict):
            item_doc = schema_type_to_doc(
                items
            )
        else:
            item_doc = "Any"

        return f"list[{item_doc}]"

    mapping = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "object": "dict",
        "null": "None",
    }

    return mapping.get(
        property_schema.get("type"),
        "Any",
    )


# ============================================================================
# Documentation helpers
# ============================================================================


def get_description(
    property_schema: dict[str, Any],
) -> str:
    """Return the property description."""

    description = property_schema.get(
        "description",
        "",
    )

    if not isinstance(description, str):
        return ""

    return (
        description
        .replace("\r\n", " ")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace('"""', '\\"\\"\\"')
        .strip()
    )


def format_enum(
    values: list[Any],
) -> str:
    """Format enum values for documentation."""

    formatted = []

    for value in values:

        if isinstance(value, str):
            formatted.append(value)
        else:
            formatted.append(str(value))

    return ", ".join(formatted)


def generate_attribute_doc(
    name: str,
    property_schema: dict[str, Any],
    required: bool,
    *,
    fixed_kind: str | None = None,
) -> list[str]:
    """Generate one NumPy-style Attributes documentation entry."""

    doc_type = schema_type_to_doc(
        property_schema
    )

    if not required:
        doc_type += ", optional"

    lines = [
        f"    {name} : {doc_type}",
    ]

    description = get_description(
        property_schema
    )

    if description:
        lines.append(
            f"        {description}"
        )
    else:
        lines.append(
            "        No description provided."
        )

    if name == "id":
        lines.append(
            "        Required by the schema, but optional in this "
            "constructor: a random id is generated automatically "
            "when omitted."
        )
    elif fixed_kind is not None and name == "kind":
        lines.append(
            f'        Automatically set to "{fixed_kind}". '
            "Not a constructor parameter."
        )
    elif required:
        lines.append(
            "        Required."
        )

    if "enum" in property_schema:

        values = property_schema["enum"]

        if values:
            lines.append(
                "        "
                f"Allowed values: [{format_enum(values)}]."
            )

    return lines


def generate_class_docstring(
    class_name: str,
    definition: dict[str, Any],
    *,
    fix_kind: bool,
) -> list[str]:
    """Generate a conventional NumPy-style class docstring."""

    properties = get_properties(
        definition
    )

    required = set(
        get_required(definition)
    )

    kind = get_kind(
        definition
    )

    lines: list[str] = []

    lines.append('    """')

    if fix_kind and kind:
        lines.append(
            f"    Data set of type ``{kind}``."
        )
    else:
        lines.append(
            "    Mother class for every R3XA data set."
        )

    if properties:

        lines.append("")
        lines.append(
            "    Attributes"
        )
        lines.append(
            "    ----------"
        )

        for name, property_schema in properties.items():

            check_identifier(name)

            lines.append("")

            lines.extend(
                generate_attribute_doc(
                    name,
                    property_schema,
                    name in required,
                    fixed_kind=kind if fix_kind else None,
                )
            )

    lines.append(
        '    """'
    )

    return lines


# ============================================================================
# Constructor
# ============================================================================


def generate_parameter(
    name: str,
    property_schema: dict[str, Any],
    *,
    required: bool,
) -> str:
    """Generate a constructor parameter."""

    check_identifier(name)

    python_type = schema_type_to_python(
        property_schema
    )

    if required:
        return f"{name}: {python_type}"

    return f"{name}: {python_type} | None = None"


def split_required_optional(
    properties: dict[str, dict[str, Any]],
    required: list[str],
    *,
    fix_kind: bool,
) -> tuple[list[str], list[str]]:
    """
    Split property names into (hard_required, optional) constructor
    groups, preserving the schema's declaration order within each
    group.

    ``kind`` is dropped entirely when ``fix_kind`` is True.
    ``id`` is always treated as optional, since it is generated
    automatically when omitted.
    """

    required_set = set(required)

    hard_required: list[str] = []
    optional: list[str] = []

    for name in properties:

        if name == "kind" and fix_kind:
            continue

        if name == "id":
            optional.append(name)
        elif name in required_set:
            hard_required.append(name)
        else:
            optional.append(name)

    return hard_required, optional


def generate_init(
    properties: dict[str, dict[str, Any]],
    required: list[str],
    *,
    fix_kind: bool,
) -> list[str]:
    """Generate the class constructor."""

    hard_required, optional = split_required_optional(
        properties,
        required,
        fix_kind=fix_kind,
    )

    lines: list[str] = []

    lines.append(
        "    def __init__("
    )

    lines.append(
        "        self,"
    )

    for name in hard_required:

        parameter = generate_parameter(
            name,
            properties[name],
            required=True,
        )

        lines.append(
            f"        {parameter},"
        )

    for name in optional:

        parameter = generate_parameter(
            name,
            properties[name],
            required=False,
        )

        lines.append(
            f"        {parameter},"
        )

    lines.append(
        "    ) -> None:"
    )

    lines.append(
        '        """Initialize the data set."""'
    )

    lines.append("")

    for name in (*hard_required, *optional):

        if name == "id":

            lines.append(
                "        self.id = "
                "id if id is not None else _random_id()"
            )

        else:

            lines.append(
                f"        self.{name} = {name}"
            )

    lines.append("")

    return lines


# ============================================================================
# kind
# ============================================================================


def generate_kind_property(
    kind: str,
) -> list[str]:
    """Generate the fixed, read-only kind property."""

    return [
        "    @property",
        "    def kind(self) -> str:",
        '        """Return the data set kind (fixed for this class)."""',
        "",
        f'        return "{kind}"',
        "",
    ]


# ============================================================================
# to_dict
# ============================================================================


def generate_to_dict(
    properties: dict[str, dict[str, Any]],
) -> list[str]:
    """
    Generate to_dict().

    ``kind`` is always handled separately (via ``self.kind``, whether
    that is a fixed property or a regular attribute) so this works
    identically for the mother class and every subclass.
    """

    lines = [
        "    def to_dict(self) -> dict[str, Any]:",
        '        """Convert the data set to a Python dictionary."""',
        "",
        "        data: dict[str, Any] = {}",
        "",
    ]

    for name in properties:

        if name == "kind":
            continue

        lines.append(
            f"        if self.{name} is not None:"
        )

        lines.append(
            f'            data["{name}"] = self.{name}'
        )

    lines.extend(
        [
            "",
            "        if self.kind is not None:",
            '            data["kind"] = self.kind',
            "",
            "        return data",
            "",
        ]
    )

    return lines


# ============================================================================
# validate / save / load / from_dict (mother class only, inherited)
# ============================================================================


def generate_validate() -> list[str]:
    """Generate validate() (defined once, on the mother class)."""

    return [
        "    def validate(self) -> None:",
        '        """',
        "        Validate this data set against its R3XA schema entry.",
        "",
        "        Uses ``registry.validate_item()``, which validates a",
        "        single item against its own ``$defs`` entry via its",
        "        ``kind`` -- unlike ``validate.validate()``, which expects",
        "        a complete R3XA document.",
        '        """',
        "",
        "        from .registry import validate_item",
        "",
        "        validate_item(",
        "            self.to_dict(),",
        "            kind=self.kind,",
        "        )",
        "",
    ]


def generate_save() -> list[str]:
    """Generate save() (defined once, on the mother class)."""

    return [
        "    def save(",
        "        self,",
        "        path: str | Path,",
        "        *,",
        "        validate: bool = True,",
        "    ) -> Path:",
        '        """Save the data set as a JSON file (via registry.save_item)."""',
        "",
        "        from .registry import save_item",
        "",
        "        return save_item(",
        "            path,",
        "            self.to_dict(),",
        "            validate=validate,",
        "            kind=self.kind,",
        "        )",
        "",
    ]


def generate_load(mother_class_name: str) -> list[str]:
    """
    Generate load() (defined once, on the mother class).

    When called on the mother class itself, dispatches to the correct
    subclass via ``from_dict()``. When called on a concrete subclass,
    ``from_dict()`` instantiates that subclass directly.
    """

    return [
        "    @classmethod",
        "    def load(",
        "        cls,",
        "        path: str | Path,",
        "        *,",
        "        validate: bool = True,",
        f"    ) -> {mother_class_name}:",
        '        """Load a data set from a JSON file (via registry.load_item)."""',
        "",
        "        from .registry import load_item, validate_item",
        "",
        "        payload = load_item(path)",
        "",
        "        if validate:",
        "            validate_item(",
        "                payload,",
        '                kind=payload.get("kind"),',
        "            )",
        "",
        "        return cls.from_dict(payload)",
        "",
    ]


def generate_from_dict(
    mother_class_name: str,
    generic_class_name: str,
    registry_name: str,
) -> list[str]:
    """
    Generate from_dict() (defined once, on the mother class).

    This is where the dynamic dispatch on ``kind`` happens: calling
    ``Dataset.from_dict(payload)`` instantiates the right registered
    subclass (``GenericDataSet`` if the kind is missing or unknown),
    while calling ``SomeConcreteDataSet.from_dict(payload)`` simply
    builds that subclass.
    """

    return [
        "    @classmethod",
        "    def from_dict(",
        "        cls,",
        "        payload: dict[str, Any],",
        f"    ) -> {mother_class_name}:",
        '        """Create a data set from a dictionary, dispatching on `kind`."""',
        "",
        "        data = dict(payload)",
        '        kind = data.pop("kind", None)',
        "",
        f"        if cls is {mother_class_name}:",
        f"            target_cls = {registry_name}.get(",
        "                kind,",
        f"                {generic_class_name},",
        "            )",
        "            return target_cls(**data)",
        "",
        "        return cls(**data)",
        "",
    ]


# ============================================================================
# Pretty printing
# ============================================================================


def generate_format_value(mother_class_name: str) -> list[str]:
    """Generate the helper used by print() (mother class only, inherited)."""

    return [
        "    @staticmethod",
        "    def _format_value_for_print(value: Any) -> str:",
        '        """Format a value for human-readable display."""',
        "",
        "        if isinstance(value, dict):",
        "",
        '            if value.get("kind") == "unit":',
        '                if "value" in value and "unit" in value:',
        '                    return f\'{value["value"]} {value["unit"]}\'',
        "",
        "            return (",
        '                "{"',
        "                + \", \".join(",
        "                    f'{key}: '",
        f"                    f'{{{mother_class_name}._format_value_for_print(item)}}'",
        "                    for key, item in value.items()",
        "                )",
        '                + "}"',
        "            )",
        "",
        "        if isinstance(value, (list, tuple)):",
        "            return (",
        '                "["',
        "                + \", \".join(",
        f"                    {mother_class_name}._format_value_for_print(item)",
        "                    for item in value",
        "                )",
        '                + "]"',
        "            )",
        "",
        "        return str(value)",
        "",
    ]


def generate_format_attributes(
    properties: dict[str, dict[str, Any]],
    required: list[str],
) -> list[str]:
    """
    Generate the attribute formatter.

    This must be regenerated for every class since it enumerates that
    class's specific set of attributes.
    """

    lines = [
        "    def _format_attributes(self) -> str:",
        '        """Format all data set attributes for display."""',
        "",
        "        attributes: dict[str, Any] = {}",
        "",
    ]

    for name in properties:

        if name == "kind":

            lines.append(
                '        attributes["kind"] = self.kind'
            )

        else:

            lines.append(
                f'        attributes["{name}"] = '
                f"getattr(self, {name!r}, None)"
            )

    lines.extend(
        [
            "",
            "        required_fields = {",
        ]
    )

    for field in required:

        lines.append(
            f"            {field!r},"
        )

    lines.extend(
        [
            "        }",
            "",
            "        display_names = {}",
            "",
            "        for key in attributes:",
            "            display_names[key] = (",
            "                key + ",
            '                ("*" if key in required_fields else "")',
            "            )",
            "",
            "        key_width = max(",
            "            len(name)",
            "            for name in display_names.values()",
            "        )",
            "",
            "        lines = [",
            "            self.__class__.__name__,",
            "            '─' * max(key_width + 20, 30),",
            "        ]",
            "",
            "        for key, value in attributes.items():",
            "            display_name = display_names[key]",
            "",
            "            formatted = self._format_value_for_print(value)",
            "",
            "            lines.append(",
            "                f'{display_name:<{key_width}} : {formatted}'",
            "            )",
            "",
            "        return '\\n'.join(lines)",
            "",
        ]
    )

    return lines


def generate_print() -> list[str]:
    """Generate print() (mother class only, inherited)."""

    return [
        "    def print(self) -> None:",
        '        """Print all data set attributes in a readable format."""',
        "",
        "        print(self._format_attributes())",
        "",
    ]


def generate_str_repr() -> list[str]:
    """Generate __str__ and __repr__ (mother class only, inherited)."""

    return [
        "    def __str__(self) -> str:",
        '        """Return a human-readable representation."""',
        "",
        "        return self._format_attributes()",
        "",
        "    def __repr__(self) -> str:",
        '        """Return a human-readable representation."""',
        "",
        "        return self._format_attributes()",
        "",
    ]


# ============================================================================
# Class generation
# ============================================================================


def generate_class(
    class_name: str,
    definition: dict[str, Any],
    *,
    base_class: str | None,
    fix_kind: bool,
    is_mother_class: bool,
) -> list[str]:
    """
    Generate one complete data set class.

    Parameters
    ----------
    base_class : str, optional
        Name of the Python base class (``"Dataset"`` for every
        subclass, ``None`` for the mother class itself).
    fix_kind : bool
        If True, ``kind`` becomes a read-only property fixed to the
        definition's ``const`` value and is removed from the
        constructor. If False (mother class only), ``kind`` is a
        regular constructor parameter/attribute.
    is_mother_class : bool
        If True, also generate the methods that are shared by every
        subclass (``validate``, ``save``, ``load``, ``from_dict``,
        ``print``, ``__str__``, ``__repr__`` and the static print
        helper). Subclasses inherit these instead of regenerating them.
    """

    properties = get_properties(
        definition
    )

    required = get_required(
        definition
    )

    kind = get_kind(
        definition
    )

    if fix_kind and kind is None:
        raise ValueError(
            f"Definition for {class_name!r} has no constant 'kind'; "
            "cannot fix it."
        )

    lines: list[str] = []

    # ------------------------------------------------------------------
    # Class declaration
    # ------------------------------------------------------------------

    if base_class:

        lines.append(
            f"class {class_name}({base_class}):"
        )

    else:

        lines.append(
            f"class {class_name}:"
        )

    # ------------------------------------------------------------------
    # Class docstring
    # ------------------------------------------------------------------

    lines.extend(
        generate_class_docstring(
            class_name,
            definition,
            fix_kind=fix_kind,
        )
    )

    lines.append("")

    # ------------------------------------------------------------------
    # Required fields (used by _format_attributes for the '*' marker)
    # ------------------------------------------------------------------

    lines.append(
        "    _required_fields = {"
    )

    for field in required:

        lines.append(
            f"        {field!r},"
        )

    lines.append(
        "    }"
    )

    lines.append("")

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    lines.extend(
        generate_init(
            properties,
            required,
            fix_kind=fix_kind,
        )
    )

    # ------------------------------------------------------------------
    # kind (fixed subclasses only)
    # ------------------------------------------------------------------

    if fix_kind:

        lines.extend(
            generate_kind_property(
                kind,
            )
        )

    # ------------------------------------------------------------------
    # to_dict (always regenerated: attribute set is class-specific)
    # ------------------------------------------------------------------

    lines.extend(
        generate_to_dict(
            properties,
        )
    )

    # ------------------------------------------------------------------
    # Methods shared by every subclass: generated once, on the mother
    # class only.
    # ------------------------------------------------------------------

    if is_mother_class:

        lines.extend(
            generate_validate()
        )

        lines.extend(
            generate_save()
        )

        lines.extend(
            generate_load(MOTHER_CLASS_NAME)
        )

        lines.extend(
            generate_from_dict(
                MOTHER_CLASS_NAME,
                GENERIC_CLASS_NAME,
                "_DATA_SET_KIND_REGISTRY",
            )
        )

    # ------------------------------------------------------------------
    # print (always regenerated: attribute set is class-specific)
    # ------------------------------------------------------------------

    lines.extend(
        generate_format_attributes(
            properties,
            required,
        )
    )

    if is_mother_class:

        lines.extend(
            generate_format_value(MOTHER_CLASS_NAME)
        )

        lines.extend(
            generate_print()
        )

        lines.extend(
            generate_str_repr()
        )

    return lines


# ============================================================================
# Complete file generation
# ============================================================================


def generate_file(
    schema: dict[str, Any],
) -> str:
    """Generate the complete new_dataset.py file."""

    data_sets = get_data_sets(
        schema
    )

    if "generic" not in data_sets:
        raise ValueError(
            "No generic data set definition found in the schema "
            "('generic' expected under $defs.data_sets)."
        )

    generic_definition = data_sets["generic"]
    generic_kind = get_kind(generic_definition)

    lines: list[str] = []

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    lines.extend(
        [
            "# ============================================================",
            "# THIS FILE IS AUTO-GENERATED.",
            "# DO NOT EDIT MANUALLY.",
            "#",
            "# Generated by codegen_datasets.py from resources/schema.json",
            "# ============================================================",
            "",
            "from __future__ import annotations",
            "",
            "import random",
            "import string",
            "",
            "from pathlib import Path",
            "from typing import Any",
            "",
            "",
        ]
    )

    # ------------------------------------------------------------------
    # Random ID helper
    #
    # NOTE: ideally this would live in core.py and be imported from
    # there (`from .core import _random_id`), matching new_datasource.py
    # and new_setting.py.
    # ------------------------------------------------------------------

    lines.extend(
        [
            "def _random_id(n: int = 24) -> str:",
            '    """Generate a lowercase identifier suitable for JSON object ids."""',
            "",
            "    chars = string.ascii_lowercase",
            '    return "".join(random.choice(chars) for _ in range(n))',
            "",
            "",
        ]
    )

    # ------------------------------------------------------------------
    # kind -> class registry, used by Dataset.from_dict() to
    # dynamically instantiate the right subclass. Populated below,
    # right after each subclass is defined.
    # ------------------------------------------------------------------

    lines.extend(
        [
            "# Populated below, once each subclass has been defined.",
            "_DATA_SET_KIND_REGISTRY: dict[str, type] = {}",
            "",
            "",
        ]
    )

    # ------------------------------------------------------------------
    # Mother class: Dataset
    # ------------------------------------------------------------------

    lines.extend(
        generate_class(
            MOTHER_CLASS_NAME,
            generic_definition,
            base_class=None,
            fix_kind=False,
            is_mother_class=True,
        )
    )

    lines.extend(["", ""])

    # ------------------------------------------------------------------
    # GenericDataSet: concrete class for kind == "data_sets/generic",
    # also the fallback target of Dataset.load()/from_dict().
    # ------------------------------------------------------------------

    lines.extend(
        generate_class(
            GENERIC_CLASS_NAME,
            generic_definition,
            base_class=MOTHER_CLASS_NAME,
            fix_kind=True,
            is_mother_class=False,
        )
    )

    lines.extend(["", ""])

    if generic_kind is not None:
        lines.append(
            f'_DATA_SET_KIND_REGISTRY["{generic_kind}"] = {GENERIC_CLASS_NAME}'
        )
        lines.extend(["", ""])

    # ------------------------------------------------------------------
    # One concrete class per remaining data set kind
    # ------------------------------------------------------------------

    generated_names = [MOTHER_CLASS_NAME, GENERIC_CLASS_NAME]

    for name, definition in data_sets.items():

        if name == "generic":
            continue

        class_name = class_name_for(name)
        kind = get_kind(definition)

        lines.extend(
            generate_class(
                class_name,
                definition,
                base_class=MOTHER_CLASS_NAME,
                fix_kind=True,
                is_mother_class=False,
            )
        )

        lines.extend(["", ""])

        if kind is not None:
            lines.append(
                f'_DATA_SET_KIND_REGISTRY["{kind}"] = {class_name}'
            )
            lines.extend(["", ""])

        generated_names.append(class_name)

    # ------------------------------------------------------------------
    # __all__
    # ------------------------------------------------------------------

    lines.append("__all__ = [")

    for name in generated_names:
        lines.append(f'    "{name}",')

    lines.extend(["]", ""])

    return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================


def main() -> None:
    """Run the generator."""

    print("==============================================")
    print(" R3XA Dataset code generator")
    print("==============================================")
    print()
    print(f"Schema : {SCHEMA_PATH}")
    print(f"Output : {OUTPUT_PATH}")
    print()

    schema = load_schema(SCHEMA_PATH)
    data_sets = get_data_sets(schema)

    print(f"{len(data_sets)} data sets found:")

    for name, definition in data_sets.items():
        class_name = class_name_for(name)
        kind = get_kind(definition)
        print(f"  {class_name:<40} {kind or ''}")

    print()

    content = generate_file(schema)

    OUTPUT_PATH.write_text(content, encoding="utf-8")

    print(f"Generated file: {OUTPUT_PATH}")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
