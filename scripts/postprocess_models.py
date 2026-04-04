#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

MODELS_PATH = Path("r3xa_api/models.py")
HEADER = (
    "# THIS FILE IS AUTO-GENERATED\n"
    "# Source: r3xa_api/resources/schema.json\n"
    "# Command: python scripts/dev.py generate-models\n"
    "# DO NOT EDIT MANUALLY\n"
)

ALIAS_START = "# --- stable typed aliases (auto-generated) ---"
ALIAS_END = "# --- end stable typed aliases ---"


def _strip_codegen_header(text: str) -> str:
    lines = text.splitlines()
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines).rstrip() + "\n"


def _remove_existing_alias_block(text: str) -> str:
    pattern = re.compile(
        rf"\n?{re.escape(ALIAS_START)}.*?{re.escape(ALIAS_END)}\n?",
        flags=re.S,
    )
    return re.sub(pattern, "\n", text).rstrip() + "\n"


def _class_names(text: str) -> set[str]:
    return set(re.findall(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)\(", text, flags=re.M))


def _pick(available: set[str], *candidates: str) -> str:
    for candidate in candidates:
        if candidate in available:
            return candidate
    raise RuntimeError(f"None of candidates found in generated models: {candidates}")


def _alias_block(available: set[str]) -> str:
    camera = _pick(available, "Camera")
    generic_source = _pick(available, "GenericModel", "GenericSource")
    specimen = _pick(available, "Specimen")
    generic_setting = _pick(available, "GenericModel1", "GenericSetting")
    image_list = _pick(available, "List", "ImageSetList")
    image_file = _pick(available, "File", "ImageSetFile")
    generic_dataset = _pick(available, "Generic", "GenericDataSet")
    document = _pick(available, "R3XADocument")

    lines = [
        "",
        ALIAS_START,
        f"CameraSource = {camera}",
        f"GenericSource = {generic_source}",
        f"SpecimenSetting = {specimen}",
        f"GenericSetting = {generic_setting}",
        f"ImageSetList = {image_list}",
        f"ImageSetFile = {image_file}",
        f"GenericDataSet = {generic_dataset}",
    ]
    if document != "R3XADocument":
        lines.append(f"R3XADocument = {document}")
    lines += [
        "",
        "__all__ = [",
        "    'Unit',",
        "    'DataSetFile',",
        "    'CameraSource',",
        "    'GenericSource',",
        "    'SpecimenSetting',",
        "    'GenericSetting',",
        "    'ImageSetList',",
        "    'ImageSetFile',",
        "    'GenericDataSet',",
        "    'R3XADocument',",
        "]",
        ALIAS_END,
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    if not MODELS_PATH.exists():
        raise FileNotFoundError(f"Missing generated file: {MODELS_PATH}")

    body = _strip_codegen_header(MODELS_PATH.read_text(encoding="utf-8"))
    body = _remove_existing_alias_block(body)
    available = _class_names(body)
    alias_block = _alias_block(available)

    MODELS_PATH.write_text(HEADER + "\n" + body + alias_block, encoding="utf-8")


if __name__ == "__main__":
    main()
