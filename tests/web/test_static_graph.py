from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load_dev_module():
    script_path = ROOT / "scripts" / "dev.py"
    spec = importlib.util.spec_from_file_location("r3xa_dev_static_graph_test", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _payload() -> dict:
    return {
        "title": "Static graph test",
        "description": "A browser-rendered graph",
        "version": "2026.9.18",
        "authors": [{"name": "Tester"}],
        "date": "2026-09-17",
        "settings": [{"id": "machine", "kind": "settings/generic", "title": "Machine"}],
        "data_sources": [
            {"id": "camera", "kind": "data_sources/generic", "title": "Camera"},
            {
                "id": "dic",
                "kind": "data_sources/generic",
                "title": "DIC",
                "input_data_sets": ["images"],
            },
        ],
        "data_sets": [
            {
                "id": "images",
                "kind": "data_sets/generic",
                "title": "Images",
                "parent_data_sources": ["camera"],
            },
            {
                "id": "displacement",
                "kind": "data_sets/generic",
                "title": "Displacement",
                "parent_data_sources": ["dic"],
            },
        ],
    }


def test_static_graph_bundle_renders_svg_without_python_backend(tmp_path: Path) -> None:
    output_dir = tmp_path / "r3xa-webui"
    _load_dev_module().build_static_web(output_dir)
    payload = json.dumps(_payload())
    palettes = (output_dir / "assets" / "graph-palettes.json").read_text(encoding="utf-8")
    script = f"""
import {{renderGraph}} from './assets/graph.generated.js';
const payload = {payload};
const palettes = {palettes};
const svg = await renderGraph(payload, {{palette: 'document', includeDescription: false}}, palettes);
if (!svg.includes('<svg') || !svg.includes('Machine') || !svg.includes('Displacement')) process.exit(1);
console.log('static graph ok');
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=output_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "static graph ok" in result.stdout
