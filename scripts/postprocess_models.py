#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
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
    aliases = {
        "CameraSource": _pick(available, "Camera"),
        "GenericSource": _pick(available, "GenericModel", "GenericSource"),
        "InfraredSource": _pick(available, "Infrared"),
        "TomographSource": _pick(available, "Tomograph"),
        "LoadCellSource": _pick(available, "LoadCell"),
        "StrainGaugeSource": _pick(available, "StrainGauge"),
        "PointTemperatureSource": _pick(available, "PointTemperature"),
        "DicMeasurementSource": _pick(available, "DicMeasurement"),
        "MechanicalAnalysisSource": _pick(available, "MechanicalAnalysis"),
        "IdentificationSource": _pick(available, "Identification"),
        "StrainComputationSource": _pick(available, "StrainComputation"),
        "SpecimenSetting": _pick(available, "Specimen"),
        "GenericSetting": _pick(available, "GenericModel1", "GenericSetting"),
        "TestingMachineSetting": _pick(available, "TestingMachine"),
        "StereorigSetting": _pick(available, "Stereorig"),
        "ListDataSet": _pick(available, "List", "ListDataSet"),
        "FileDataSet": _pick(available, "File", "FileDataSet"),
        "GenericDataSet": _pick(available, "Generic", "GenericDataSet"),
        "ImageSetList": _pick(available, "List", "ImageSetList"),
        "ImageSetFile": _pick(available, "File", "ImageSetFile"),
    }

    lines = ["", ALIAS_START]
    lines.extend(f"{alias} = {target}" for alias, target in aliases.items())
    lines += [
        "",
        "__all__ = [",
        "    'R3XAModel',",
        "    'Unit',",
        "    'DataSetFile',",
        "    'OutputDimension',",
    "    'R3XADocument',",
        *[f"    '{alias}'," for alias in aliases if alias != "R3XADocument"],
        "]",
        ALIAS_END,
        "",
    ]
    return "\n".join(lines)


def main(models_path: Path | str | None = None) -> None:
    path = Path(models_path) if models_path is not None else MODELS_PATH
    if not path.exists():
        raise FileNotFoundError(f"Missing generated file: {path}")

    body = _strip_codegen_header(path.read_text(encoding="utf-8"))
    body = _remove_existing_alias_block(body)
    available = _class_names(body)
    alias_block = _alias_block(available)

    path.write_text(HEADER + "\n" + body + alias_block, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
