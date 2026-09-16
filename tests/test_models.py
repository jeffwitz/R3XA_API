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
    unit = models.Unit(unit="px")
    assert unit.unit == "px"
    assert unit.kind == "unit"


def test_unit_invalid_missing_unit():
    with pytest.raises(ValidationError):
        models.Unit(kind="unit")


def test_camera_source_valid():
    camera = _valid_camera()
    assert camera.title == "CCD Camera"
    assert camera.id
    assert camera.kind == "data_sources/camera"


def test_generated_models_expose_stable_public_aliases():
    expected = {
        "CameraSource",
        "GenericSource",
        "InfraredSource",
        "TomographSource",
        "LoadCellSource",
        "StrainGaugeSource",
        "PointTemperatureSource",
        "DicMeasurementSource",
        "MechanicalAnalysisSource",
        "IdentificationSource",
        "StrainComputationSource",
        "SpecimenSetting",
        "GenericSetting",
        "TestingMachineSetting",
        "StereorigSetting",
        "ListDataSet",
        "FileDataSet",
        "GenericDataSet",
    }
    assert expected.issubset(set(models.__all__))
    assert all(issubclass(getattr(models, name), models.R3XAModel) for name in expected)


def test_generated_model_common_helpers(tmp_path: Path):
    camera = _valid_camera()

    assert "id" in camera.required_fields()
    assert "description" in camera.optional_fields()
    assert "Description of the camera." in camera.field_descriptions()["description"]
    assert "description" not in camera.to_dict()
    assert "  description: None" in camera.summary()

    output_path = camera.save(tmp_path / "camera.json")
    loaded = models.CameraSource.load(output_path)

    assert output_path == tmp_path / "camera.json"
    assert loaded.to_dict() == camera.to_dict()
    assert loaded.validate() is loaded


def test_summary_renders_values_for_humans():
    summary = _valid_camera().summary()

    # Units collapse to `value unit`, both alone and inside a list.
    assert "  image_size: [1392 px, 1040 px]" in summary
    assert "* output_units: [1 gl]" in summary
    # Constrained scalars and enums read as their payload, not their repr.
    assert "* output_components: 1" in summary
    assert "* output_dimension: surface" in summary
    # Required fields stay marked, optional ones stay listed even when null.
    assert "* title: CCD Camera" in summary
    assert "  lens: None" in summary
    assert "Unit(" not in summary
    assert "root=" not in summary


def test_generated_models_document_their_fields():
    doc = models.CameraSource.__doc__

    assert doc, "generated models must carry a docstring"
    assert "data_sources/camera" in doc
    # Every field is documented, with its schema description.
    assert "title : str" in doc
    assert "Title of the camera." in doc
    assert "Required." in doc
    # Optional fields are marked once, in the suffix - not as Optional[...].
    assert "description : str, optional" in doc
    assert "Optional[" not in doc
    # Enumerations advertise what they accept.
    assert "Allowed values: [point, curve, surface, volume]." in doc
    # `kind` is set by the model rather than passed in.
    assert 'Automatically set to "data_sources/camera".' in doc


def test_explicit_docstrings_are_not_overwritten():
    class Documented(models.R3XAModel):
        """A hand-written docstring."""

    assert Documented.__doc__ == "A hand-written docstring."


def test_generated_models_fill_schema_constants():
    document = models.R3XADocument(
        title="Typed document",
        description="Pydantic model",
        authors=["R3XA Team"],
        date="2026-09-07",
    )
    unit = models.Unit(unit="mm", value=2.0)
    data_file = models.DataSetFile(filename="values.csv")

    assert document.version == schema_version()
    assert unit.kind == "unit"
    assert data_file.kind == "data_set_file"
    document.validate()
    unit.validate()
    data_file.validate()


def test_typed_document_adds_and_links_items():
    camera = _valid_camera()
    images = models.ListDataSet(
        title="Camera images",
        description="Images recorded during the test",
        data_type="image/tiff",
        parent_data_sources=[],
        timestamps=[0.0],
        values=["image_0000.tif"],
    )
    document = models.R3XADocument(
        title="Typed linked document",
        description="Typed document with an acquisition relationship",
        authors=["R3XA Team"],
        date="2026-09-07",
    )

    document.add_data_source(camera)
    document.add_data_set(images)
    document.link_output(camera, images)

    assert document.find(camera.id) is camera
    assert document.find(images.id) is images
    assert [reference.root for reference in images.parent_data_sources] == [camera.id]
    assert document.integrity_errors() == []
    document.validate_integrity().validate()


def test_typed_document_links_inputs_and_reports_dangling_references():
    camera = _valid_camera()
    images = models.ListDataSet(
        title="Camera images",
        description="Images recorded during the test",
        data_type="image/tiff",
        parent_data_sources=[],
        timestamps=[0.0],
        values=["image_0000.tif"],
    )
    document = models.R3XADocument(
        title="Typed input document",
        description="Typed document with an input relationship",
        authors=["R3XA Team"],
        date="2026-09-07",
    )
    document.add_data_source(camera)
    document.add_data_set(images)
    document.link_input(camera, images)

    assert [reference.root for reference in camera.input_data_sets] == [images.id]
    assert document.integrity_errors() == []

    images.parent_data_sources = [*images.parent_data_sources, "missing-source"]
    errors = document.integrity_errors()
    assert any("missing-source" in error for error in errors)
    with pytest.raises(ValueError, match="missing-source"):
        document.validate_integrity()


def test_typed_document_rejects_duplicate_ids():
    camera = _valid_camera()
    document = models.R3XADocument(
        title="Duplicate ID document",
        description="Typed document with duplicate IDs",
        authors=["R3XA Team"],
        date="2026-09-07",
    )
    document.add_data_source(camera)

    duplicate = models.CameraSource(
        id=camera.id,
        title="Duplicate camera",
        output_components=1,
        output_dimension="surface",
        output_units=[models.Unit(unit="graylevel")],
        image_size=[models.Unit(unit="px", value=1), models.Unit(unit="px", value=1)],
    )
    with pytest.raises(ValueError, match="Duplicate R3XA item id"):
        document.add_data_source(duplicate)


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
        "authors": ["R3XA Team"],
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
        authors=["R3XA Team"],
        date="2026-03-01",
    )
    r3xa.data_sources.append(camera)
    validate(r3xa.to_dict())


def test_r3xa_document_valid():
    doc = models.R3XADocument(
        title="Typed document",
        description="Pydantic model",
        version=schema_version(),
        authors=["R3XA Team"],
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
