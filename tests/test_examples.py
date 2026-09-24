from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from r3xa_api import validate, validate_item


def test_examples_directory_contains_only_tutorials_and_cases() -> None:
    root = Path(__file__).parents[1]
    entries = {path.name for path in (root / "examples").iterdir()}

    assert entries == {"cases", "tutorials"}


def test_committed_documents_and_artifacts_validate_against_current_schema() -> None:
    root = Path(__file__).parents[1]
    json_paths = sorted((root / "tests" / "fixtures" / "documents").rglob("*.json"))
    json_paths.extend(sorted((root / "artifacts" / "examples").rglob("*.json")))

    assert json_paths
    for path in json_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("kind"), str):
            validate_item(payload)
        else:
            validate(payload)


def test_registry_examples_use_kind_prefixed_ids() -> None:
    root = Path(__file__).parents[1]
    artifacts = root / "artifacts" / "examples"
    prefixes = {"settings": "stg", "data_sources": "src", "data_sets": "set"}

    registry_document = json.loads(
        (artifacts / "dic_pipeline_registry.json").read_text(encoding="utf-8")
    )
    merged_item = json.loads(
        (artifacts / "registry_camera_merged.json").read_text(encoding="utf-8")
    )
    items = [merged_item]
    items.extend(
        item
        for section in ("settings", "data_sources", "data_sets")
        for item in registry_document[section]
    )

    for item in items:
        section, kind_name = item["kind"].split("/", 1)
        assert item["id"].startswith(f"{prefixes[section]}-{kind_name}-"), item["id"]


def test_validation_scripts_run() -> None:
    root = Path(__file__).parents[1]
    for name in ("validate_static_examples.py", "validate_all_examples.py"):
        completed = subprocess.run(
            [sys.executable, str(root / "scripts" / name)],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr or completed.stdout


def test_graph_example_uses_wasm_and_accepts_classic_palette(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    output = tmp_path / "graph"
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "graph_r3xa.py"),
            "--input",
            str(root / "tests" / "fixtures" / "documents" / "valid_tabular_file.json"),
            "--output",
            str(output),
            "--palette",
            "classic",
            "--dot",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.with_suffix(".svg").read_text(encoding="utf-8").lstrip().startswith("<?xml")
    assert output.with_suffix(".dot").is_file()
