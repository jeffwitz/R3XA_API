from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

from r3xa_api.registry import validate_item
from r3xa_api.webcore import build_validation_report


ROOT = Path(__file__).resolve().parents[2]


def _load_dev_module():
    script_path = ROOT / "scripts" / "dev.py"
    spec = importlib.util.spec_from_file_location("r3xa_dev_static_parity_test", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_static_validator_agrees_with_python_on_schema_cases(tmp_path: Path) -> None:
    output_dir = tmp_path / "r3xa-webui"
    _load_dev_module().build_static_web(output_dir)
    valid_payload = json.loads((ROOT / "examples/artifacts/dic_pipeline.json").read_text(encoding="utf-8"))
    cases = {
        "valid": valid_payload,
        "missing_title": {key: value for key, value in valid_payload.items() if key != "title"},
        "wrong_version": {**valid_payload, "version": "not-the-current-schema"},
        "wrong_author_type": {**valid_payload, "authors": ["Tester"]},
    }
    expected = {
        name: build_validation_report(payload)["valid"]
        for name, payload in cases.items()
    }
    script = """
import {readFileSync} from "node:fs";
const {validate} = await import(process.argv[1]);
const cases = JSON.parse(readFileSync(0, "utf8"));
const result = {};
for (const [name, payload] of Object.entries(cases)) {
  result[name] = Boolean(validate(payload));
}
process.stdout.write(JSON.stringify(result));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script, str(output_dir / "assets/validator.generated.js")],
        input=json.dumps(cases),
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(result.stdout) == expected


def test_static_registry_validator_validates_items_directly(tmp_path: Path) -> None:
    output_dir = tmp_path / "r3xa-webui"
    _load_dev_module().build_static_web(output_dir)
    items = {
        str(path.relative_to(ROOT)): json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "registry").rglob("*.json"))
    }
    invalid_item = {
        **items["registry/data_sources/camera/avt_dolphin_f145b.json"],
        "output_components": "not-a-number",
    }
    script = """
import {readFileSync} from "node:fs";
const {validateRegistryItem} = await import(process.argv[1]);
const cases = JSON.parse(readFileSync(0, "utf8"));
const result = {};
for (const [name, payload] of Object.entries(cases)) {
  result[name] = Boolean(validateRegistryItem(payload, payload.kind));
}
process.stdout.write(JSON.stringify(result));
"""
    cases = {**{name: item for name, item in items.items()}, "invalid_camera": invalid_item}
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script, str(output_dir / "assets/validator.generated.js")],
        input=json.dumps(cases),
        check=True,
        capture_output=True,
        text=True,
    )

    static_result = json.loads(result.stdout)
    assert static_result["invalid_camera"] is False
    for name, item in items.items():
        validate_item(item)
        assert static_result[name] is True
