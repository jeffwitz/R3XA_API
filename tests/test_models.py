import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import jsonschema

import r3xa_api
from r3xa_api import R3XAFile, from_model, schema_version, validate
from r3xa_api._references import reference_fields

from pydantic import ValidationError

models = r3xa_api.models


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


def test_reference_fields_are_scoped_to_the_schema_kind():
    assert reference_fields("data_sources/camera") == {"input_data_sets": "data_sets"}
    assert reference_fields("data_sources/dic_measurement") == {
        "input_data_sets": "data_sets",
        "mesh": "settings",
    }
    assert reference_fields("data_sets/file") == {"parent_data_sources": "data_sources"}


def test_unit_valid():
    unit = models.Unit(unit="px")
    assert unit.unit == "px"
    assert unit.kind == "unit"


def test_unit_invalid_missing_unit():
    unit = models.Unit(kind="unit")
    with pytest.raises(jsonschema.ValidationError):
        unit.validate()


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
    assert models.R3XAModel is models.R3XAItem


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
    assert loaded.validate() is None


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
        authors=[{"name": "R3XA Team"}],
        date="2026-09-07",
    )
    unit = models.Unit(unit="mm", value=2.0)
    data_file = models.DataSetFile()

    assert document.version == schema_version()
    assert unit.kind == "unit"
    assert data_file.kind == "data_set_file"
    document.validate()
    unit.validate()
    with pytest.raises(jsonschema.ValidationError):
        data_file.validate()


def test_generated_models_are_editable_drafts_with_strict_validation_boundary():
    document = models.R3XADocument()
    data_file = models.DataSetFile()

    assert document.title is None
    assert document.authors is None
    assert document.settings == []
    assert data_file.filename is None
    assert data_file.col is None
    assert data_file.rows is None

    with pytest.raises(jsonschema.ValidationError):
        document.validate()
    with pytest.raises(jsonschema.ValidationError):
        data_file.validate()

    data_file.filename = "results.csv"
    data_file.col = 1
    data_file.rows = (0, None)
    assert data_file.validate() is None


def test_data_set_file_enforces_schema_fields_and_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        models.DataSetFile(filename="results.csv", col=0, rows=[0, None], extra_field="nope")

    data_file = models.DataSetFile.model_construct(
        filename="results.csv",
        col=0,
        rows=(None, 2),
        kind="data_set_file",
    )
    with pytest.raises(jsonschema.ValidationError):
        data_file.validate()


def test_document_collections_preserve_object_identity_and_bind_documents():
    document = models.R3XADocument()
    camera = models.CameraSource(id="camera_01", title="Camera")

    document.data_sources.append(camera)

    assert document.data_sources[0] is camera
    assert camera._document is document

    replacement = models.CameraSource(id="camera_02", title="Replacement")
    document.data_sources = [replacement]

    assert document.data_sources[0] is replacement
    assert replacement._document is document


def test_typed_model_generates_kind_prefixed_ids():
    camera = models.CameraSource(title="Camera")

    assert camera.id.startswith("src-camera-")


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
        authors=[{"name": "R3XA Team"}],
        date="2026-09-07",
    )

    document.add_data_source(camera)
    document.add_data_set(images)
    document.link_output(camera, images)

    assert document.find(camera.id) is camera
    assert document.find(images.id) is images
    assert images.parent_data_sources == [camera]
    assert document.integrity_errors() == []
    document.validate_integrity().validate()


def test_generated_models_keep_object_references_until_serialization():
    camera = _valid_camera()
    images = models.ListDataSet(
        title="Camera images",
        data_type="image/tiff",
        parent_data_sources=[camera],
        timestamps=[0.0],
        values=["image_0000.tif"],
    )

    assert images.parent_data_sources == [camera]
    assert images.parent_data_sources[0] is camera
    assert images.to_dict()["parent_data_sources"] == [camera.id]


def test_generated_reference_annotations_accept_ids_and_objects():
    camera = _valid_camera()
    images = models.ListDataSet(
        title="Camera images",
        timestamps=[0.0],
        values=["image_0000.tif"],
        parent_data_sources=[camera],
    )

    assert "R3XAItem" in str(
        models.ListDataSet.model_fields["parent_data_sources"].annotation
    )
    assert images.to_dict()["parent_data_sources"] == [camera.id]


def test_scalar_reference_preserves_the_object_until_serialization():
    specimen = models.SpecimenSetting(title="Specimen")
    camera = models.CameraSource(
        title="Camera",
        output_components=1,
        output_dimension="surface",
        output_units=[models.Unit(unit="graylevel")],
    )
    dic = models.DicMeasurementSource(
        title="DIC",
        output_components=2,
        output_dimension="surface",
        output_units=[models.Unit(unit="mm"), models.Unit(unit="mm")],
        mesh=specimen,
        input_data_sets=[],
    )

    assert dic.mesh is specimen
    assert dic.to_dict()["mesh"] == specimen.id


def test_object_first_item_merge_returns_a_typed_copy():
    camera = _valid_camera()
    merged = camera.merge(title="Updated camera")

    assert isinstance(merged, models.CameraSource)
    assert merged is not camera
    assert merged.title == "Updated camera"
    assert merged.id == camera.id


def test_generated_document_roundtrips_through_r3xafile():
    document = models.R3XADocument(
        title="Typed document",
        description="A complete generated document",
        authors=[{"name": "R3XA Team"}],
        date="2026-09-17",
        settings=[],
        data_sources=[],
        data_sets=[],
    )

    rebuilt = R3XAFile.from_model(document)

    assert rebuilt.to_model().to_dict() == document.to_dict()


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
        authors=[{"name": "R3XA Team"}],
        date="2026-09-07",
    )
    document.add_data_source(camera)
    document.add_data_set(images)
    document.link_input(camera, images)

    assert camera.input_data_sets == [images]
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
        authors=[{"name": "R3XA Team"}],
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
        "authors": [{"name": "R3XA Team"}],
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
        authors=[{"name": "R3XA Team"}],
        date="2026-03-01",
    )
    r3xa.data_sources.append(camera)
    validate(r3xa.to_dict())


def test_r3xa_document_valid():
    doc = models.R3XADocument(
        title="Typed document",
        description="Pydantic model",
        version=schema_version(),
        authors=[{"name": "R3XA Team"}],
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


def test_object_first_api_requires_pydantic():
    assert r3xa_api.typed_available is True


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


def test_printing_an_item_directly_shows_its_summary():
    camera = _valid_camera()

    assert str(camera) == camera.summary()
    assert "1392 px" in str(camera)
    assert repr(camera) == camera.summary()


def test_legacy_class_names_alias_the_current_ones():
    # Names from the 1.x line and the apijc branch keep resolving, to the very
    # same classes - the field sets match, so the alias is not a rename in
    # disguise.
    legacy = {
        "SpecimenSettings": "SpecimenSetting",
        "StereorigSettings": "StereorigSetting",
        "TestingMachineSettings": "TestingMachineSetting",
        "GenericDataSource": "GenericSource",
        "CameraDataSource": "CameraSource",
        "InfraredDataSource": "InfraredSource",
        "TomographDataSource": "TomographSource",
        "LoadCellDataSource": "LoadCellSource",
        "StrainGaugeDataSource": "StrainGaugeSource",
        "PointTemperatureDataSource": "PointTemperatureSource",
        "DicMeasurementDataSource": "DicMeasurementSource",
        "MechanicalAnalysisDataSource": "MechanicalAnalysisSource",
        "IdentificationDataSource": "IdentificationSource",
        "StrainComputationDataSource": "StrainComputationSource",
    }

    for old, current in legacy.items():
        assert getattr(models, old) is getattr(models, current), old
        assert old in models.__all__
        # Reachable from the package too, like the current names.
        assert getattr(r3xa_api, old) is getattr(models, current)

    # GenericSetting was already singular on the apijc branch: no alias needed.
    assert not hasattr(models, "GenericSettings")
