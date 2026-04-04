from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .core import _GUIDED_ALIAS_TARGETS, _guided_kind_specs


_CORE_STUB_PATH = Path(__file__).with_name("core.pyi")


def _indent(lines: Iterable[str], prefix: str = "    ") -> list[str]:
    return [f"{prefix}{line}" if line else "" for line in lines]


def _render_method_stub(name: str, required_fields: tuple[str, ...], return_type: str = "Dict[str, Any]") -> list[str]:
    lines = [f"def {name}("]
    lines.extend(_indent(["self,"]))
    for field in required_fields:
        lines.extend(_indent([f"{field}: Any,"]))
    lines.extend(_indent(["**extra: Any,"]))
    lines.append(f") -> {return_type}: ...")
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


def render_core_stub() -> str:
    helper_specs = _guided_kind_specs()
    helper_by_name = {
        spec["helper_name"]: tuple(spec["required"]) for spec in helper_specs.values()
    }

    lines: list[str] = [
        "from __future__ import annotations",
        "",
        "# AUTO-GENERATED FROM THE ACTIVE R3XA SCHEMA.",
        "# DO NOT EDIT MANUALLY.",
        "",
        "from pathlib import Path",
        "from typing import Any, Dict, Optional",
        "",
        "def new_item(kind: str, **fields: Any) -> Dict[str, Any]: ...",
        "",
        "def unit(",
        "    title: Optional[str] = ...,",
        "    value: Optional[float] = ...,",
        "    unit: Optional[str] = ...,",
        "    scale: Optional[float] = ...,",
        "    **extra: Any,",
        ") -> Dict[str, Any]: ...",
        "",
        "def data_set_file(",
        "    filename: str,",
        "    delimiter: Optional[str] = ...,",
        "    data_range: Optional[str] = ...,",
        "    **extra: Any,",
        ") -> Dict[str, Any]: ...",
        "",
        "class R3XAFile:",
        "    header: Dict[str, Any]",
        "    settings: list[Dict[str, Any]]",
        "    data_sources: list[Dict[str, Any]]",
        "    data_sets: list[Dict[str, Any]]",
        "",
        "    def __init__(self, version: Optional[str] = ..., **header: Any) -> None: ...",
        "",
        "    @classmethod",
        "    def from_dict(cls, payload: Dict[str, Any]) -> R3XAFile: ...",
        "",
        "    @classmethod",
        "    def load(cls, path: str | Path) -> R3XAFile: ...",
        "",
        "    @classmethod",
        "    def loads(cls, text: str) -> R3XAFile: ...",
        "",
        "    def set_header(self, **fields: Any) -> R3XAFile: ...",
        "",
        "    def add_item(self, kind: str, **fields: Any) -> Dict[str, Any]: ...",
        "    def add_setting(self, kind: str, **fields: Any) -> Dict[str, Any]: ...",
        "    def add_data_source(self, kind: str, **fields: Any) -> Dict[str, Any]: ...",
        "    def add_data_set(self, kind: str, **fields: Any) -> Dict[str, Any]: ...",
        "",
    ]

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

    lines.append("    # Legacy guided helper aliases")
    for alias_name, target_name in _GUIDED_ALIAS_TARGETS.items():
        target_required = helper_by_name[target_name]
        lines.extend(_indent(_render_method_stub(alias_name, target_required)))
        lines.append("")

    lines.extend(
        [
            "    def to_dict(self) -> Dict[str, Any]: ...",
            "    def validate(self) -> None: ...",
            "    def dump(self, indent: int = ...) -> str: ...",
            "    def save(self, path: str | Path, indent: int = ..., validate: bool = ...) -> Path: ...",
            "",
        ]
    )

    return "\n".join(lines)


def write_core_stub(path: Path = _CORE_STUB_PATH) -> Path:
    path.write_text(render_core_stub(), encoding="utf-8")
    return path
