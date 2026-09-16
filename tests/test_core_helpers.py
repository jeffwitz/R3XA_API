import jsonschema
import pytest

from r3xa_api import R3XAFile, data_set_file, load_schema, unit, validate


class _FakeTypedModel:
    def __init__(self, payload: dict):
        self._payload = payload

    def model_dump(self, **kwargs):
        return dict(self._payload)


def test_data_set_file_accepts_column_and_row_selection() -> None:
    r3xa = R3XAFile(
        title="Tabular file with range",
        description="Use column and row selectors for tabular data",
        authors=["R3XA API"],
        date="2026-03-01",
    )

    source = r3xa.add_data_source(
        "data_sources/generic",
        title="Load cell",
        description="Force measurement",
        output_components=1,
        output_dimension="point",
        output_units=[unit(title="force", value=1.0, unit="N")],
        manufacturer="Instron",
        model="5800",
    )

    timestamps = data_set_file(filename="timestamps.csv", file_type="text/csv", col="time", rows=[0, 98])
    values = data_set_file(filename="force.csv", file_type="text/csv", col=1, rows=[0, 98])

    assert timestamps["col"] == "time"
    assert timestamps["rows"] == [0, 98]
    assert values["col"] == 1
    assert values["rows"] == [0, 98]

    r3xa.add_data_set(
        "data_sets/file",
        title="Force time series",
        description="Force vs time",
        parent_data_sources=[source["id"]],
        timestamps=timestamps,
        values=values,
    )

    validate(r3xa.to_dict())


def test_data_set_file_rejects_string_rows() -> None:
    with pytest.raises(TypeError):
        data_set_file(filename="timestamps.csv", rows="0:100")  # type: ignore[arg-type]


def test_unit_accepts_minimal_schema_payload() -> None:
    payload = unit(unit="px")
    assert payload == {"kind": "unit", "unit": "px", "scale": 1.0}


def test_unit_requires_unit_field() -> None:
    with pytest.raises(TypeError):
        unit(title="width")


def test_generic_data_source_accepts_uncertainty() -> None:
    r3xa = R3XAFile(
        title="Generic source uncertainty",
        description="Generic data source with explicit uncertainty",
        authors=["R3XA API"],
        date="2026-04-03",
    )

    source = r3xa.add_data_source(
        "data_sources/generic",
        title="Torque sensor",
        description="Generic torque measurement",
        output_components=1,
        output_dimension="point",
        output_units=[unit(title="torque", value=1.0, unit="N*m")],
        manufacturer="Andilog",
        model="TT 6",
        uncertainty=unit(title="resolution", value=0.6, unit="mN*m"),
    )

    assert source["uncertainty"]["unit"] == "mN*m"
    validate(r3xa.to_dict())


def test_generic_setting_accepts_lowercase_documentation() -> None:
    r3xa = R3XAFile(
        title="Generic setting documentation",
        description="Lowercase documentation field",
        authors=["R3XA API"],
        date="2026-04-03",
    )

    r3xa.add_generic_setting(
        title="Lighting setup",
        description="LED lighting for torsion setup",
        documentation="https://example.org/light.pdf",
    )

    validate(r3xa.to_dict())


def test_r3xafile_lists_accept_model_dump_objects() -> None:
    r3xa = R3XAFile(
        title="Typed-like model compatibility",
        description="Accept model_dump objects in R3XAFile lists",
        authors=["R3XA API"],
        date="2026-03-01",
    )

    source_id = "src_force_01"

    r3xa.settings.append(
        _FakeTypedModel(
            {
                "id": "set_generic_01",
                "kind": "settings/generic",
                "title": "Experiment setting",
                "description": "Generic setting block",
            }
        )
    )
    r3xa.data_sources.append(
        _FakeTypedModel(
            {
                "id": source_id,
                "kind": "data_sources/generic",
                "title": "Load cell",
                "description": "Force measurement",
                "output_components": 1,
                "output_dimension": "point",
                "output_units": [unit(title="force", value=1.0, unit="N")],
                "manufacturer": "Instron",
                "model": "5800",
            }
        )
    )
    r3xa.data_sets.append(
        _FakeTypedModel(
            {
                "id": "ds_force_01",
                "kind": "data_sets/file",
                "title": "Force over time",
                "description": "Single-column force file",
                "parent_data_sources": [source_id],
                "timestamps": data_set_file(filename="timestamps.csv", col=0, rows=[0, 99]),
                "values": data_set_file(filename="force.csv", col=1, rows=[0, 99]),
            }
        )
    )

    payload = r3xa.to_dict()
    assert isinstance(payload["settings"][0], dict)
    assert isinstance(payload["data_sources"][0], dict)
    assert isinstance(payload["data_sets"][0], dict)
    validate(payload)


def test_add_item_routes_to_expected_collection() -> None:
    r3xa = R3XAFile(title="Routing", description="Kind routing", authors=["R3XA API"], date="2026-03-01")

    setting = r3xa.add_item("settings/generic", title="S", description="Setting")
    source = r3xa.add_item(
        "data_sources/generic",
        title="Source",
        description="Generic source",
        output_components=1,
        output_dimension="point",
        output_units=[unit(title="u", value=1.0, unit="N")],
        manufacturer="ACME",
        model="m1",
    )
    dataset = r3xa.add_item(
        "data_sets/file",
        title="D",
        description="Dataset",
        parent_data_sources=[source["id"]],
        timestamps=data_set_file(filename="t.csv"),
        values=data_set_file(filename="d.csv"),
    )

    assert setting in r3xa.settings
    assert source in r3xa.data_sources
    assert dataset in r3xa.data_sets
    validate(r3xa.to_dict())


def test_add_setting_rejects_wrong_kind_prefix() -> None:
    r3xa = R3XAFile(title="Kinds", description="Kinds", authors=["R3XA API"], date="2026-03-01")
    with pytest.raises(ValueError):
        r3xa.add_setting("data_sources/generic", title="bad", description="bad")


def test_add_item_rejects_unknown_kind_prefix() -> None:
    r3xa = R3XAFile(title="Kinds", description="Kinds", authors=["R3XA API"], date="2026-03-01")
    with pytest.raises(ValueError):
        r3xa.add_item("unknown/item", title="bad", description="bad")


def test_r3xafile_dump_save_and_load_roundtrip(tmp_path) -> None:
    r3xa = R3XAFile(
        title="Roundtrip",
        description="Roundtrip test",
        authors=["R3XA API"],
        date="2026-03-01",
    )
    source = r3xa.add_data_source(
        "data_sources/generic",
        title="Load cell",
        description="Force measurement",
        output_components=1,
        output_dimension="point",
        output_units=[unit(title="force", value=1.0, unit="N")],
        manufacturer="Instron",
        model="5800",
    )
    r3xa.add_data_set(
        "data_sets/file",
        title="Force",
        description="Force signal",
        parent_data_sources=[source["id"]],
        timestamps=data_set_file(filename="t.csv"),
        values=data_set_file(filename="d.csv"),
    )

    dumped = r3xa.dump(indent=2)
    assert '"title": "Roundtrip"' in dumped

    output_path = tmp_path / "roundtrip.json"
    saved_path = r3xa.save(output_path, indent=2)
    loaded = R3XAFile.load(output_path)
    loaded_from_text = R3XAFile.loads(dumped)

    assert saved_path == output_path
    assert loaded.to_dict() == r3xa.to_dict()
    assert loaded_from_text.to_dict() == r3xa.to_dict()


def test_r3xafile_save_validates_by_default(tmp_path) -> None:
    r3xa = R3XAFile(description="Missing required fields")

    with pytest.raises(jsonschema.ValidationError):
        r3xa.save(tmp_path / "invalid.json")


def test_guided_helpers_cover_all_schema_kinds() -> None:
    schema = load_schema()
    suffixes = {
        "settings": "setting",
        "data_sources": "source",
        "data_sets": "data_set",
    }

    expected = {
        f"add_{kind_name}_{suffixes[section]}"
        for section in suffixes
        for kind_name in schema["$defs"][section]
    }
    expected.update({"add_image_set_list", "add_image_set_file"})

    missing = sorted(name for name in expected if not hasattr(R3XAFile, name))
    assert missing == []


def test_new_guided_helpers_validate_against_schema() -> None:
    r3xa = R3XAFile(
        title="Guided helper coverage",
        description="Exercise helpers generated from schema kinds",
        authors=["R3XA API"],
        date="2026-04-03",
    )

    r3xa.add_testing_machine_setting(
        title="Testing machine",
        description="Torsion testing machine",
        type="torsion",
    )

    source = r3xa.add_load_cell_source(
        output_components=1,
        output_dimension="point",
        output_units=[unit(unit="N")],
        capacity=unit(title="capacity", value=1000.0, unit="N"),
        title="Load cell",
        description="Primary force measurement",
    )

    r3xa.add_generic_data_set(
        title="Force archive",
        description="Generic archived force dataset",
        parent_data_sources=[source["id"]],
        data_type="application/octet-stream",
        path="force/",
    )

    validate(r3xa.to_dict())


def _document_with_items() -> R3XAFile:
    document = R3XAFile(
        title="Torsion test",
        description="A short document",
        authors=["J.-C. Passieux"],
        date="2026-09-07",
    )
    document.add_specimen_setting(
        title="Open-hole sample",
        description="sample",
        sizes=[unit(title="width", value=20, unit="mm")],
    )
    document.add_camera_source(
        title="CCD Camera",
        description="camera",
        output_components=1,
        output_dimension="surface",
        output_units=[unit(title="graylevel", value=1.0, unit="gl")],
    )
    return document


def test_document_summary_lists_header_and_item_titles() -> None:
    summary = _document_with_items().summary()

    # Schema-required header fields are marked, optional ones still listed.
    assert "* title" in summary
    assert "Torsion test" in summary
    assert "  repository" in summary
    # Collections are identified by the titles a reader recognises.
    assert "settings" in summary and "[Open-hole sample]" in summary
    assert "data_sources" in summary and "[CCD Camera]" in summary
    assert "data_sets" in summary and "[]" in summary


def test_document_summary_shares_value_formatting_with_models() -> None:
    document = R3XAFile(title="t", description="d", authors=["a"], date="2026-01-01")
    document.header["license"] = unit(title="w", value=1392, unit="px")

    # The unit collapses exactly as it does in a model's summary().
    assert "1392 px" in document.summary()


def test_plot_lets_the_backend_choose_the_extension(tmp_path) -> None:
    pytest.importorskip("graphviz")
    document = _document_with_items()

    without_suffix = document.plot(tmp_path / "graph")
    with_suffix = document.plot(tmp_path / "other.svg")

    # Graphviz appends the format itself: neither form may double it.
    assert without_suffix.name == "graph.svg"
    assert with_suffix.name == "other.svg"
    assert without_suffix.exists() and with_suffix.exists()


def test_plot_creates_missing_parent_directories(tmp_path) -> None:
    pytest.importorskip("graphviz")

    output = _document_with_items().plot(tmp_path / "nested" / "dir" / "graph")

    assert output.exists()


def test_plot_rejects_an_unknown_backend(tmp_path) -> None:
    with pytest.raises(ValueError, match="Unknown graph backend"):
        _document_with_items().plot(tmp_path / "graph", backend="nope")


def test_printing_a_document_directly_shows_its_summary() -> None:
    document = _document_with_items()

    # `print(document)` must work, not only `document.print()`.
    assert str(document) == document.summary()
    assert repr(document) == document.summary()
    assert "R3XA File" in str(document)
    assert "object at 0x" not in repr(document)


def _document_with_every_section() -> R3XAFile:
    """A document covering all three sections, so every palette slot is drawn."""

    document = _document_with_items()
    source_id = document.data_sources[0]["id"]
    document.add_file_data_set(
        title="graylevel images",
        description="images",
        parent_data_sources=[source_id],
        time_reference=unit(title="t0", value=0.0, unit="s"),
        timestamps=data_set_file(filename="timestamps.csv", file_type="text/csv"),
        values=data_set_file(filename="images.csv", file_type="text/csv"),
    )
    return document


def test_palette_option_applies_to_every_backend(tmp_path) -> None:
    pytest.importorskip("graphviz")
    document = _document_with_every_section()
    ochre, crimson, teal = "c4894f", "bf0040", "038181"

    default_svg = document.plot(tmp_path / "default").read_text(encoding="utf-8").lower()
    document_svg = document.plot(
        tmp_path / "document", palette="document"
    ).read_text(encoding="utf-8").lower()

    # The palette swaps the colours wholesale rather than mixing the two.
    assert "2b587a" in default_svg and ochre not in default_svg
    assert all(colour in document_svg for colour in (ochre, crimson, teal))
    assert "2b587a" not in document_svg


def test_palette_option_reaches_pyvis(tmp_path) -> None:
    pytest.importorskip("pyvis")
    document = _document_with_items()

    html = document.plot(
        tmp_path / "graph", backend="pyvis", palette="document"
    ).read_text(encoding="utf-8").lower()

    assert "c4894f" in html


def test_palette_rejects_an_unknown_name(tmp_path) -> None:
    with pytest.raises(ValueError, match="Unknown palette"):
        _document_with_items().plot(tmp_path / "graph", palette="nope")
