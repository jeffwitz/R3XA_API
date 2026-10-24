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
    tutorial_artifacts = root / "artifacts" / "examples" / "tutorials"
    case_scripts = [
        root / "examples" / "cases" / "torsion" / "example.py",
        root / "examples" / "cases" / "qi_hu" / "example.py",
    ]
    case_artifacts = [
        root / "artifacts" / "examples" / "torsion_experiment.json",
        root / "artifacts" / "examples" / "graph_torsion_experiment.svg",
        root / "artifacts" / "examples" / "qi_hu_tutorial.json",
        root / "artifacts" / "examples" / "graph_qi_hu_tutorial.svg",
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
            root / "artifacts" / "examples" / "torsion_experiment.json",
            root / "artifacts" / "examples" / "qi_hu_tutorial.json",
        ]:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload.get("kind"), str):
                validate_item(payload)
            else:
                validate(payload)
        torsion_payload = json.loads(
            (root / "artifacts" / "examples" / "torsion_experiment.json").read_text(
                encoding="utf-8"
            )
        )
        assert {
            item["id"]
            for section in ("settings", "data_sources", "data_sets")
            for item in torsion_payload[section]
        } == {
            "stg-generic-torsion-lights",
            "stg-testing-machine-torsion-apparatus",
            "stg-specimen-torsion-sample",
            "stg-generic-torsion-calibration-board",
            "src-generic-torsion-torque-sensor",
            "src-generic-torsion-angle-sensor",
            "src-camera-torsion-camera",
            "src-generic-torsion-camera-calibration",
            "set-list-torsion-calibration-images",
            "set-file-torsion-scan-angles",
            "set-list-torsion-scanning-images",
            "set-file-torsion-torque-series",
            "set-file-torsion-angle-series",
            "set-list-torsion-images",
            "set-generic-torsion-camera-intrinsics",
        }
        for graph in [
            root / "artifacts" / "examples" / "graph_torsion_experiment.svg",
            root / "artifacts" / "examples" / "graph_qi_hu_tutorial.svg",
        ]:
            assert graph.read_text(encoding="utf-8").lstrip().startswith("<?xml")
        interactive_html = tutorial_artifacts / "torsion_cytoscape.html"
        assert interactive_html.read_text(encoding="utf-8").lstrip().startswith("<!doctype html>")
        assert "R3XAStandaloneGraph" in interactive_html.read_text(encoding="utf-8")
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
        sorted((root / "examples" / "cases").rglob("marimo/example.py"))
    )
    matlab_sources = [
        root / "examples" / "tutorials" / "matlab" / "tutorial0_basic.m",
        root / "examples" / "cases" / "torsion" / "example.m",
        root / "examples" / "cases" / "qi_hu" / "example.m",
    ]

    assert len(notebooks) == 7
    assert len(marimo_sources) == 10
    assert all(path.is_file() for path in matlab_sources)
    for notebook in notebooks:
        payload = json.loads(notebook.read_text(encoding="utf-8"))
        assert payload["nbformat"] >= 4
        assert all(not cell.get("outputs") for cell in payload["cells"])
        assert all(cell.get("execution_count") is None for cell in payload["cells"])
        if "tutorial" in notebook.parts:
            notebook_source = "\n".join(
                "".join(cell.get("source", [])) for cell in payload["cells"]
            )
            assert "repo_root = Path.cwd().resolve()" in notebook_source
            assert "ARTIFACTS = repo_root / 'artifacts'" in notebook_source
            assert "artifacts/examples/" not in notebook_source

    torsion_ids = (
        "stg-generic-torsion-lights",
        "stg-testing-machine-torsion-apparatus",
        "stg-specimen-torsion-sample",
        "stg-generic-torsion-calibration-board",
        "src-generic-torsion-torque-sensor",
        "src-generic-torsion-angle-sensor",
        "src-camera-torsion-camera",
        "src-generic-torsion-camera-calibration",
        "set-list-torsion-calibration-images",
        "set-file-torsion-scan-angles",
        "set-list-torsion-scanning-images",
        "set-file-torsion-torque-series",
        "set-file-torsion-angle-series",
        "set-list-torsion-images",
        "set-generic-torsion-camera-intrinsics",
    )
    torsion_sources = [
        root / "examples" / "cases" / "torsion" / "example.py",
        root / "examples" / "cases" / "torsion" / "marimo" / "example.py",
    ]
    torsion_notebook = root / "examples" / "cases" / "torsion" / "example.ipynb"
    torsion_notebook_payload = json.loads(torsion_notebook.read_text(encoding="utf-8"))
    torsion_sources_text = [path.read_text(encoding="utf-8") for path in torsion_sources]
    torsion_sources_text.append(
        "\n".join(
            "".join(cell.get("source", []))
            for cell in torsion_notebook_payload["cells"]
        )
    )
    assert all(all(identifier in source for identifier in torsion_ids) for source in torsion_sources_text)

    tutorial4_csv = root / "artifacts" / "examples" / "tutorials" / "tutorial4_file.csv"
    assert tutorial4_csv.read_text(encoding="utf-8").splitlines() == [
        "0.0;img_0000.tif",
        "0.1;img_0001.tif",
        "0.2;img_0002.tif",
        "0.3;img_0003.tif",
    ]

    for source in marimo_sources:
        py_compile.compile(str(source), doraise=True)
        text = source.read_text(encoding="utf-8")
        assert "import marimo" in text
        assert "marimo.App(" in text
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


def test_interactive_cytoscape_tutorial_sources() -> None:
    root = Path(__file__).parents[1]
    script = root / "examples" / "tutorials" / "python" / "tutorial6_interactive_cytoscape.py"
    notebook = root / "examples" / "tutorials" / "jupyter" / "tutorial6_interactive_cytoscape.ipynb"
    marimo = root / "examples" / "tutorials" / "marimo" / "tutorial6_interactive_cytoscape.py"
    payload = json.loads(notebook.read_text(encoding="utf-8"))
    notebook_source = "\n".join("".join(cell.get("source", [])) for cell in payload["cells"])
    marimo_source = marimo.read_text(encoding="utf-8")
    script_source = script.read_text(encoding="utf-8")

    assert all(not cell.get("outputs") for cell in payload["cells"])
    assert "R3XAFile.load(source)" in notebook_source
    assert "backend='cytoscape'" in notebook_source
    assert "IFrame(" in notebook_source
    assert 'sandbox="allow-scripts"' in notebook_source
    assert "R3XAFile.load(source)" in marimo_source
    assert 'backend="cytoscape"' in marimo_source
    assert 'sandbox="allow-scripts"' in marimo_source
    assert "R3XAFile.load(source)" in script_source
    assert 'backend="cytoscape"' in script_source
