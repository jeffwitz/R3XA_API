"""Guard ``r3xa_api/models.py`` against drift from the packaged schema.

The typed models are generated from ``r3xa_api/resources/schema.json`` by
``python scripts/dev.py generate-models``. ``core.pyi`` already has a sync test
(``test_stub_generation.py``); this is the equivalent guard for the models, so a
schema change cannot land while the models still describe the previous one.

Blank lines are ignored when comparing: import grouping shifts between
``datamodel-code-generator`` formatter defaults and carries no meaning. Every
difference that matters - class names, fields, types, constraints, aliases -
lands on a non-blank line.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip(
    "datamodel_code_generator",
    reason="datamodel-code-generator is only present with the [dev] extra",
)

ROOT = Path(__file__).resolve().parents[1]
MODELS_PATH = ROOT / "r3xa_api" / "models.py"


def _load_dev_module():
    """Import ``scripts/dev.py`` so the codegen command has a single definition."""

    script_path = ROOT / "scripts" / "dev.py"
    spec = importlib.util.spec_from_file_location("r3xa_dev_cli", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _significant_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def test_models_match_packaged_schema(tmp_path: Path) -> None:
    dev = _load_dev_module()
    generated = tmp_path / "models.py"

    command = dev.model_codegen_command(sys.executable, str(generated))
    subprocess.run(list(command), cwd=ROOT, check=True, capture_output=True)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "postprocess_models.py"), str(generated)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )

    expected = _significant_lines(generated.read_text(encoding="utf-8"))
    actual = _significant_lines(MODELS_PATH.read_text(encoding="utf-8"))

    assert actual == expected, (
        "r3xa_api/models.py no longer matches the schema it is generated from.\n"
        "Regenerate it with `python scripts/dev.py generate-models`."
    )
