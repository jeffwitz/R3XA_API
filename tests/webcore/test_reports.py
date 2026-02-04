import json
from pathlib import Path

from r3xa_api.webcore import build_validation_report


def _load_example() -> dict:
    root = Path(__file__).resolve().parents[2]
    path = root / "examples" / "artifacts" / "dic_pipeline.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_validation_report_valid() -> None:
    payload = _load_example()
    report = build_validation_report(payload)
    assert report["valid"] is True
    assert report["errors"] == []


def test_validation_report_invalid() -> None:
    payload = _load_example()
    payload["version"] = "invalid"
    report = build_validation_report(payload)
    assert report["valid"] is False
    assert report["errors"]
    error = report["errors"][0]
    assert {"path", "message", "validator", "schema_path"} <= set(error.keys())
