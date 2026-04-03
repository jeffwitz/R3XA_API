import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import r3xa_api
from r3xa_api import R3XAFile, from_model, schema_version, validate

pydantic = pytest.importorskip("pydantic")
ValidationError = pydantic.ValidationError
models = pytest.importorskip("r3xa_api.models")


def _valid_camera():
    return models.CameraSource(
        id="cam_01",
        kind="data_sources/camera",
        title="CCD Camera",
        output_components=1,
        output_dimension="surface",
        output_units=[models.Unit(kind="unit", unit="gl", title="graylevel", value=1.0)],
        image_size=[
            models.Unit(kind="unit", unit="px", title="width", value=1392),
            models.Unit(kind="unit", unit="px", title="height", value=1040),
        ],
        manufacturer="AVT",
        model="Dolphin F-145B",
    )


def test_typed_available():
    assert hasattr(r3xa_api, "_TYPED_AVAILABLE")
    assert r3xa_api._TYPED_AVAILABLE is True


def test_unit_valid():
    unit = models.Unit(kind="unit", unit="px")
    assert unit.unit == "px"


def test_unit_invalid_missing_unit():
    with pytest.raises(ValidationError):
        models.Unit(kind="unit")


def test_camera_source_valid():
    camera = _valid_camera()
    assert camera.title == "CCD Camera"


def test_camera_source_invalid_dimension():
    with pytest.raises(ValidationError):
        models.CameraSource(
            id="cam_01",
            kind="data_sources/camera",
            title="CCD Camera",
            output_components=1,
            output_dimension="invalid-dimension",
            output_units=[models.Unit(kind="unit", unit="gl")],
            image_size=[models.Unit(kind="unit", unit="px")],
        )


def test_camera_source_invalid_components():
    with pytest.raises(ValidationError):
        models.CameraSource(
            id="cam_01",
            kind="data_sources/camera",
            title="CCD Camera",
            output_components="not-an-int",
            output_dimension="surface",
            output_units=[models.Unit(kind="unit", unit="gl")],
            image_size=[models.Unit(kind="unit", unit="px")],
        )


def test_from_model_roundtrip():
    camera = _valid_camera()
    payload = {
        "title": "Typed model roundtrip",
        "description": "Roundtrip from typed model to dict",
        "version": schema_version(),
        "authors": "R3XA Team",
        "date": "2026-02-19",
        "settings": [],
        "data_sources": [from_model(camera)],
        "data_sets": [],
    }
    validate(payload)


def test_r3xafile_accepts_typed_model_direct_append():
    camera = _valid_camera()
    r3xa = R3XAFile(
        title="Typed append",
        description="R3XAFile accepts typed models in lists",
        authors="R3XA Team",
        date="2026-03-01",
    )
    r3xa.data_sources.append(camera)
    validate(r3xa.to_dict())


def test_r3xa_document_valid():
    doc = models.R3XADocument(
        title="Typed document",
        description="Pydantic model",
        version=schema_version(),
        authors="R3XA Team",
        date="2026-02-19",
        settings=[],
        data_sources=[],
        data_sets=[],
    )
    assert doc.version == schema_version()


def test_generic_setting_uses_lowercase_documentation_field():
    setting = models.GenericSetting(
        id="set_generic_01",
        kind="settings/generic",
        title="Lighting",
        description="LED setup",
        documentation="https://example.org/lighting.pdf",
    )
    assert setting.documentation == "https://example.org/lighting.pdf"


def test_models_not_required(tmp_path: Path):
    fake_pydantic = tmp_path / "pydantic.py"
    fake_pydantic.write_text("raise ModuleNotFoundError(\"No module named 'pydantic'\")\n", encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{tmp_path}:{repo_root}" + (f":{existing}" if existing else "")

    code = (
        "import r3xa_api\n"
        "assert hasattr(r3xa_api, '_TYPED_AVAILABLE')\n"
        "assert r3xa_api._TYPED_AVAILABLE is False\n"
        "print('ok')\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_typed_example_script_generates_valid_json():
    root = Path(__file__).resolve().parents[1]
    script_path = root / "examples" / "python" / "typed_dic_pipeline.py"
    output_path = root / "examples" / "artifacts" / "dic_pipeline_typed.json"

    previous_content = output_path.read_bytes() if output_path.exists() else None

    spec = importlib.util.spec_from_file_location(script_path.stem, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    try:
        spec.loader.exec_module(module)
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        validate(payload)
    finally:
        if previous_content is None:
            if output_path.exists():
                output_path.unlink()
        else:
            output_path.write_bytes(previous_content)
