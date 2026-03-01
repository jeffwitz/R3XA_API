from r3xa_api import R3XAFile, data_set_file, unit, validate


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
