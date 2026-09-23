from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import py_compile

from r3xa_api import validate, validate_item


def _run_script(root: Path, path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def _snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.exists() else None for path in paths}


def _restore(snapshot: dict[Path, bytes | None]) -> None:
    for path, content in snapshot.items():
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(content)


def test_tutorial_scripts_write_valid_artifacts() -> None:
    root = Path(__file__).parents[1]
    tutorial_scripts = sorted((root / "examples" / "tutorials" / "python").glob("*.py"))
    tutorial_artifacts = root / "examples" / "artifacts" / "tutorials"
    case_scripts = [
        root / "examples" / "cases" / "torsion" / "example.py",
        root / "examples" / "cases" / "qi_hu" / "example.py",
    ]
    case_artifacts = [
        root / "examples" / "artifacts" / "torsion_experiment.json",
        root / "examples" / "artifacts" / "graph_torsion_experiment.svg",
        root / "examples" / "artifacts" / "qi_hu_tutorial.json",
        root / "examples" / "artifacts" / "graph_qi_hu_tutorial.svg",
    ]
    generated = [*tutorial_artifacts.glob("*")]
    snapshot = _snapshot([*generated, *case_artifacts])

    try:
        for script in tutorial_scripts:
            _run_script(root, script)
        for script in case_scripts:
            _run_script(root, script)

        for path in [
            *sorted(tutorial_artifacts.glob("*.json")),
            root / "examples" / "artifacts" / "torsion_experiment.json",
            root / "examples" / "artifacts" / "qi_hu_tutorial.json",
        ]:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload.get("kind"), str):
                validate_item(payload)
            else:
                validate(payload)
        for graph in [
            root / "examples" / "artifacts" / "graph_torsion_experiment.svg",
            root / "examples" / "artifacts" / "graph_qi_hu_tutorial.svg",
        ]:
            assert graph.read_text(encoding="utf-8").lstrip().startswith("<?xml")
    finally:
        _restore(snapshot)
        for path in [*tutorial_artifacts.glob("*"), *case_artifacts]:
            if path not in snapshot:
                path.unlink(missing_ok=True)


def test_jupyter_and_marimo_tutorial_sources_are_complete() -> None:
    root = Path(__file__).parents[1]
    notebooks = sorted((root / "examples" / "tutorials" / "jupyter").glob("*.ipynb"))
    marimo_sources = sorted((root / "examples" / "tutorials" / "marimo").glob("*.py"))
    marimo_sources.extend(
        sorted((root / "examples" / "cases").glob("*/marimo/example.py"))
    )
    matlab_sources = [
        root / "examples" / "tutorials" / "matlab" / "tutorial0_basic.m",
        root / "examples" / "cases" / "torsion" / "example.m",
        root / "examples" / "cases" / "qi_hu" / "example.m",
    ]

    assert len(notebooks) == 6
    assert len(marimo_sources) == 8
    assert all(path.is_file() for path in matlab_sources)
    for notebook in notebooks:
        payload = json.loads(notebook.read_text(encoding="utf-8"))
        assert payload["nbformat"] >= 4
        assert all(not cell.get("outputs") for cell in payload["cells"])
        assert all(cell.get("execution_count") is None for cell in payload["cells"])

    for source in marimo_sources:
        py_compile.compile(str(source), doraise=True)
        text = source.read_text(encoding="utf-8")
        assert "import marimo" in text
        assert "marimo.App()" in text
        assert "examples/artifacts" not in text
        assert "Path(__file__)" in text

    for notebook in [
        root / "examples" / "tutorials" / "jupyter" / "tutorial1_printing_and_plotting.ipynb",
        root / "examples" / "tutorials" / "jupyter" / "tutorial3_build_use_predefined_items.ipynb",
        root / "examples" / "cases" / "torsion" / "example.ipynb",
        root / "examples" / "cases" / "qi_hu" / "example.ipynb",
    ]:
        text = notebook.read_text(encoding="utf-8")
        assert "IPython.display" in text
        assert "display(SVG" in text

    for source in [
        root / "examples" / "tutorials" / "marimo" / "tutorial1_printing_and_plotting.py",
        root / "examples" / "tutorials" / "marimo" / "tutorial3_build_use_predefined_items.py",
        root / "examples" / "cases" / "torsion" / "marimo" / "example.py",
        root / "examples" / "cases" / "qi_hu" / "marimo" / "example.py",
    ]:
        assert "mo.Html" in source.read_text(encoding="utf-8")

    for source in matlab_sources:
        text = source.read_text(encoding="utf-8")
        assert "r3xa.R3XAFile" in text
        assert ".save(" in text
