import ast
from pathlib import Path

from r3xa_api._stubgen import render_core_stub


def test_generated_core_stub_matches_checked_in_file() -> None:
    stub_path = Path("r3xa_api/core.pyi")
    assert stub_path.read_text(encoding="utf-8") == render_core_stub()


def test_generated_core_stub_is_valid_python_syntax() -> None:
    source = Path("r3xa_api/core.pyi").read_text(encoding="utf-8")
    ast.parse(source)
