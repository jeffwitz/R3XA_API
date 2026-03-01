import json
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _schema_path() -> Path:
    return _project_root() / "r3xa_api" / "resources" / "schema.json"


def _script_path() -> Path:
    return _project_root() / "tools" / "generate_spec.py"


def _run_generate(output_path: Path) -> str:
    command = [
        sys.executable,
        str(_script_path()),
        str(_schema_path()),
        str(output_path),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout


def test_script_runs(tmp_path):
    output_path = tmp_path / "specification.md"
    stdout = _run_generate(output_path)
    assert output_path.exists()
    assert "Specification written to" in stdout


def test_output_is_markdown(tmp_path):
    output_path = tmp_path / "specification.md"
    _run_generate(output_path)
    text = output_path.read_text(encoding="utf-8")
    assert text.startswith("<!-- THIS FILE IS AUTO-GENERATED -->")
    assert "<!-- Source: " in text
    assert "<!-- Command: make generate-spec -->" in text


def test_sections_present(tmp_path):
    output_path = tmp_path / "specification.md"
    _run_generate(output_path)
    text = output_path.read_text(encoding="utf-8")
    assert "## Settings" in text
    assert "## Data Sources" in text
    assert "## Data Sets" in text
    assert "## Appendix — Common Types" in text


def test_required_fields_marked(tmp_path):
    output_path = tmp_path / "specification.md"
    _run_generate(output_path)
    text = output_path.read_text(encoding="utf-8")
    assert "| `title` | string | ✅ | Title of the data sets. |" in text
    assert '| `version` | "2024.7.1" (fixed) | ✅ | Version of the schema used. |' in text


def test_enum_rendered(tmp_path):
    output_path = tmp_path / "specification.md"
    _run_generate(output_path)
    text = output_path.read_text(encoding="utf-8")
    assert '"point" \\| "curve" \\| "surface" \\| "volume"' in text


def test_ref_resolved(tmp_path):
    output_path = tmp_path / "specification.md"
    _run_generate(output_path)
    text = output_path.read_text(encoding="utf-8")
    assert '<a href="#unit">Unit</a>' in text
    assert "#/$defs/types/unit" not in text
    assert "unsigned integer" in text


def test_no_section_types_in_body(tmp_path):
    output_path = tmp_path / "specification.md"
    _run_generate(output_path)
    text = output_path.read_text(encoding="utf-8")
    annexe_index = text.index("## Appendix — Common Types")
    unit_index = text.index("### Unit")
    assert unit_index > annexe_index


def test_roundtrip_consistency(tmp_path):
    output_path = tmp_path / "specification.md"
    _run_generate(output_path)
    text = output_path.read_text(encoding="utf-8")
    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    for section in ("settings", "data_sources", "data_sets"):
        defs = schema.get("$defs", {}).get(section, {})
        for item_schema in defs.values():
            kind = item_schema.get("properties", {}).get("kind", {}).get("const")
            assert isinstance(kind, str) and kind in text
