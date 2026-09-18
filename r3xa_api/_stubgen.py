from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from . import models
from .core import _guided_kind_specs
from .schema import load_schema


_CORE_STUB_PATH = Path(__file__).with_name("core.pyi")
_PACKAGE_STUB_PATH = Path(__file__).with_name("__init__.pyi")


def _indent(lines: Iterable[str], prefix: str = "    ") -> list[str]:
    return [f"{prefix}{line}" if line else "" for line in lines]


def _render_method_stub(name: str, required_fields: tuple[str, ...], return_type: str = "R3XAItem") -> list[str]:
    lines = [f"def {name}("]
    lines.extend(_indent(["self,"]))
    for field in required_fields:
        lines.extend(_indent([f"{field}: Any,"]))
    lines.extend(_indent(["**extra: Any,"]))
    lines.append(f") -> {return_type}: ...")
    return lines


def _render_function_stub(name: str, required_fields: tuple[str, ...]) -> list[str]:
    lines = [f"def {name}("]
    for field in required_fields:
        lines.extend(_indent([f"{field}: Any,"]))
    lines.extend(_indent(["**extra: Any,"]))
    lines.append(") -> R3XAItem: ...")
    return lines


def _helper_sort_key(item: tuple[str, dict[str, Any]]) -> tuple[int, str]:
    kind, spec = item
    section = kind.split("/", 1)[0]
    section_order = {
        "settings": 0,
        "data_sources": 1,
        "data_sets": 2,
    }
    return section_order[section], str(spec["helper_name"])


def _document_header_stubs() -> list[str]:
    """Render direct document attributes from the schema's top-level fields."""

    properties = load_schema().get("properties", {})
    collections = {"settings", "data_sources", "data_sets"}
    lines: list[str] = []
    for name, field in properties.items():
        if name in collections:
            continue
        if name == "authors":
            annotation = "Optional[list[Author]]"
        else:
            field_type = field.get("type") if isinstance(field, dict) else None
            annotation = {
                "string": "Optional[str]",
                "number": "Optional[float]",
                "integer": "Optional[int]",
                "boolean": "Optional[bool]",
                "object": "Optional[Dict[str, Any]]",
                "array": "Optional[list[Any]]",
            }.get(field_type, "Any")
        lines.append(f"    {name}: {annotation}")
    return lines


def render_core_stub() -> str:
    helper_specs = _guided_kind_specs()
    lines: list[str] = [
        "from __future__ import annotations",
        "",
        "# AUTO-GENERATED FROM THE ACTIVE R3XA SCHEMA.",
        "# DO NOT EDIT MANUALLY.",
        "",
        "from pathlib import Path",
        "from typing import Any, Dict, Mapping, Optional, Union",
        "from r3xa_api.models import (",
        "    Author,",
        "    CameraSource,",
        "    DicMeasurementSource,",
        "    FileDataSet,",
        "    GenericDataSet,",
        "    GenericSetting,",
        "    GenericSource,",
        "    IdentificationSource,",
        "    InfraredSource,",
        "    ListDataSet,",
        "    LoadCellSource,",
        "    MechanicalAnalysisSource,",
        "    PointTemperatureSource,",
        "    R3XADocument,",
        "    SpecimenSetting,",
        "    StrainComputationSource,",
        "    StrainGaugeSource,",
        "    StereorigSetting,",
        "    TestingMachineSetting,",
        "    TomographSource,",
        ")",
        "",
        "SettingItem = Union[GenericSetting, SpecimenSetting, TestingMachineSetting, StereorigSetting]",
        "DataSourceItem = Union[GenericSource, CameraSource, InfraredSource, TomographSource, LoadCellSource, StrainGaugeSource, PointTemperatureSource, DicMeasurementSource, MechanicalAnalysisSource, IdentificationSource, StrainComputationSource]",
        "DataSetItem = Union[GenericDataSet, FileDataSet, ListDataSet]",
        "",
        "class R3XAItem:",
        "    @property",
        "    def kind(self) -> Optional[str]: ...",
        "    def __getitem__(self, field: str) -> Any: ...",
        "    def __setitem__(self, field: str, value: Any) -> None: ...",
        "    def merge(self, **overrides: Any) -> R3XAItem: ...",
        "    def to_dict(self, *, exclude_none: bool = ...) -> Dict[str, Any]: ...",
        "    def to_json(self, *, exclude_none: bool = ..., indent: Optional[int] = ...) -> str: ...",
        "    def dump(self, *, exclude_none: bool = ..., indent: Optional[int] = ...) -> str: ...",
        "    @classmethod",
        "    def from_dict(cls, payload: Mapping[str, Any], *, validate: bool = ...) -> R3XAItem: ...",
        "    def required_fields(self) -> list[str]: ...",
        "    def optional_fields(self) -> list[str]: ...",
        "    def missing_fields(self) -> list[str]: ...",
        "    def field_descriptions(self) -> Dict[str, str]: ...",
        "    def summary(self) -> str: ...",
        "    def print(self) -> None: ...",
        "    def validate(self, *, schema: Optional[Dict[str, Any]] = ...) -> None: ...",
        "    @classmethod",
        "    def load(cls, path: str | Path, *, validate: bool = ...) -> R3XAItem: ...",
        "    @classmethod",
        "    def loads(cls, text: str, *, validate: bool = ...) -> R3XAItem: ...",
        "    def save(self, path: str | Path, *, validate: bool = ..., exclude_none: bool = ..., indent: Optional[int] = ...) -> Path: ...",
        "    def plot(self, path: str | Path, *, backend: str = ..., palette: Optional[str] = ..., include_description: bool = ..., **kwargs: Any) -> Path: ...",
        "",
        "def author(",
        "    name: str,",
        "    affiliation: Optional[str] = ...,",
        "    orcid: Optional[str] = ...,",
        "    **extra: Any,",
        ") -> R3XAItem: ...",
        "",
        "def new_item(kind: str, **fields: Any) -> R3XAItem: ...",
        "",
        "def unit(",
        "    title: Optional[str] = ...,",
        "    value: Optional[float] = ...,",
        "    unit: Optional[str] = ...,",
        "    scale: Optional[float] = ...,",
        "    **extra: Any,",
        ") -> R3XAItem: ...",
        "",
        "def data_set_file(",
        "    filename: Optional[str] = ...,",
        "    file_type: Optional[str] = ...,",
        "    delimiter: Optional[str] = ...,",
        "    col: Optional[int | str] = ...,",
        "    rows: Optional[list[int | None]] = ...,",
        "    **extra: Any,",
        ") -> R3XAItem: ...",
        "",
    ]

    for kind, spec in sorted(helper_specs.items(), key=_helper_sort_key):
        builder_name = "new_" + spec["helper_name"][len("add_"):]
        lines.extend(_render_function_stub(builder_name, tuple(spec["required"])))
        lines.append("")

    lines.extend(
        [
        "class R3XAFile(R3XADocument):",
        "    header: Dict[str, Any]",
        *_document_header_stubs(),
        "    settings: list[SettingItem]",
        "    data_sources: list[DataSourceItem]",
        "    data_sets: list[DataSetItem]",
        "",
        "    def __init__(self, **data: Any) -> None: ...",
        "",
        "    @classmethod",
        "    def from_dict(cls, payload: Mapping[str, Any], *, validate: bool = ...) -> R3XAFile: ...",
        "",
        "    @classmethod",
        "    def load(cls, path: str | Path, *, validate: bool = ...) -> R3XAFile: ...",
        "",
        "    @classmethod",
        "    def from_model(cls, model: R3XADocument) -> R3XAFile: ...",
        "",
        "    @classmethod",
        "    def loads(cls, text: str, *, validate: bool = ...) -> R3XAFile: ...",
        "",
        "    def set_header(self, **fields: Any) -> R3XAFile: ...",
        "",
        "    def add_item(self, item: Any = ..., *, section: Optional[str] = ..., **fields: Any) -> R3XAItem: ...",
        "    def add_setting(self, item: Any = ..., **fields: Any) -> R3XAItem: ...",
        "    def add_data_source(self, item: Any = ..., **fields: Any) -> R3XAItem: ...",
        "    def add_data_set(self, item: Any = ..., **fields: Any) -> R3XAItem: ...",
        "    def find(self, item_id: str) -> Optional[R3XAItem]: ...",
        "    @classmethod",
        "    def required_fields(cls) -> list[str]: ...",
        "    @classmethod",
        "    def optional_fields(cls) -> list[str]: ...",
        "    def missing_fields(self) -> list[str]: ...",
        "    @classmethod",
        "    def field_descriptions(cls) -> Dict[str, str]: ...",
        "",
        ]
    )

    current_section: str | None = None
    for kind, spec in sorted(helper_specs.items(), key=_helper_sort_key):
        helper_name = spec["helper_name"]
        required_fields = tuple(spec["required"])
        section = kind.split("/", 1)[0]
        if section != current_section:
            section_titles = {
                "settings": "Guided setting helpers",
                "data_sources": "Guided data source helpers",
                "data_sets": "Guided data set helpers",
            }
            lines.extend(
                [
                    f"    # {section_titles[section]}",
                ]
            )
            current_section = section
        lines.extend(_indent(_render_method_stub(helper_name, required_fields)))
        lines.append("")

    lines.extend(
        [
            "    def to_dict(self) -> Dict[str, Any]: ...",
            "    def validate(self) -> None: ...",
            "    def to_model(self) -> R3XAFile: ...",
            "    def dump(self, *, exclude_none: bool = ..., indent: Optional[int] = ...) -> str: ...",
            "    def save(self, path: str | Path, *, validate: bool = ..., exclude_none: bool = ..., indent: Optional[int] = ...) -> Path: ...",
            "    def summary(self) -> str: ...",
            "    def print(self) -> None: ...",
            "    def plot(",
            "        self,",
            "        path: str | Path,",
            "        *,",
            "        backend: str = ...,",
            "        palette: str | None = ...,",
            "        include_description: bool = ...,",
            "        **kwargs: Any,",
            "    ) -> Path: ...",
            "",
        ]
    )

    return "\n".join(lines)


def write_core_stub(path: Path = _CORE_STUB_PATH) -> Path:
    path.write_text(render_core_stub(), encoding="utf-8")
    return path


def render_package_stub() -> str:
    """Render the package-level stub, including dynamic top-level exports."""

    model_names = [name for name in models.__all__ if name != "R3XAItem"]
    builder_names = sorted(
        "new_" + spec["helper_name"][len("add_"):]
        for spec in _guided_kind_specs().values()
    )
    lines = [
        "from __future__ import annotations",
        "",
        "# AUTO-GENERATED FROM THE ACTIVE R3XA SCHEMA.",
        "# DO NOT EDIT MANUALLY.",
        "",
        "from typing import Any",
        "",
        "from . import models",
        "from .core import R3XAFile, R3XAItem, author, data_set_file, new_item, unit",
        "from .core import (",
    ]
    lines.extend(f"    {name}," for name in builder_names)
    lines.extend(
        [
            ")",
            "from .models import (",
        ]
    )
    lines.extend(f"    {name}," for name in model_names)
    lines.extend(
        [
            ")",
            "from .registry import (",
            "    Registry,",
            "    RegistryItem,",
            "    load_item,",
            "    load_item_path,",
            "    load_registry,",
            "    merge_item,",
            "    save_item,",
            "    save_item_path,",
            "    validate_item,",
            ")",
            "from .schema import load_schema, schema_version",
            "from .typed import from_model",
            "from .validate import integrity_errors, validate, validate_integrity",
            "",
            "typed_available: bool",
            "",
        ]
    )
    return "\n".join(lines)


def write_package_stub(path: Path = _PACKAGE_STUB_PATH) -> Path:
    path.write_text(render_package_stub(), encoding="utf-8")
    return path
