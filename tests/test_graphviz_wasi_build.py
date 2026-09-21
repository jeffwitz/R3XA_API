from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "graphviz-wasi" / "manifest.json"
ARTIFACT = ROOT / "r3xa_api" / "resources" / "graphviz" / "graphviz-12.2.1.wasm"


def test_graphviz_wasi_build_manifest_matches_committed_artifact():
    manifest = json.loads(MANIFEST.read_text())
    digest = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()

    assert manifest["graphviz_version"] == "12.2.1"
    assert manifest["wasi_sdk_target"] == "wasm32-wasip1"
    assert manifest["current_artifact_size"] == ARTIFACT.stat().st_size
    assert manifest["current_artifact_sha256"] == digest


def test_graphviz_wasi_rebuild_inputs_are_versioned():
    tool_dir = MANIFEST.parent
    assert (tool_dir / "build.py").is_file()
    assert (tool_dir / "CMakeLists.txt").is_file()
    assert (tool_dir / "wrapper.c").is_file()
