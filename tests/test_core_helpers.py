import pytest

from r3xa_api import R3XAFile, data_set_file, unit, validate


class _FakeTypedModel:
    def __init__(self, payload: dict):
        self._payload = payload

    def model_dump(self, **kwargs):
        return dict(self._payload)


def test_data_set_file_accepts_string_range_and_validates() -> None:
    r3xa = R3XAFile(
        title="Tabular file with range",
        description="Use data_range as spreadsheet-like string",
        authors="R3XA API",
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

    timestamps = data_set_file(filename="timestamps.csv", file_type="text/csv", data_range="A2:A100")
    data = data_set_file(filename="force.csv", file_type="text/csv", data_range="B2:B100")

    assert timestamps["data_range"] == "A2:A100"
    assert data["data_range"] == "B2:B100"

    r3xa.add_data_set(
        "data_sets/file",
        title="Force time series",
        description="Force vs time",
        data_sources=[source["id"]],
        time_reference=0.0,
        timestamps=timestamps,
        data=data,
    )

    validate(r3xa.to_dict())


def test_data_set_file_rejects_non_string_range() -> None:
    with pytest.raises(TypeError):
        data_set_file(filename="timestamps.csv", data_range=["A2:A100"])  # type: ignore[arg-type]


def test_r3xafile_lists_accept_model_dump_objects() -> None:
    r3xa = R3XAFile(
        title="Typed-like model compatibility",
        description="Accept model_dump objects in R3XAFile lists",
        authors="R3XA API",
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
                "data_sources": [source_id],
                "time_reference": 0.0,
                "timestamps": data_set_file(filename="timestamps.csv", data_range="A2:A100"),
                "data": data_set_file(filename="force.csv", data_range="B2:B100"),
            }
        )
    )

    payload = r3xa.to_dict()
    assert isinstance(payload["settings"][0], dict)
    assert isinstance(payload["data_sources"][0], dict)
    assert isinstance(payload["data_sets"][0], dict)
    validate(payload)
