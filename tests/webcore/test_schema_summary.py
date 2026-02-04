from r3xa_api.webcore import build_schema_summary


def test_schema_summary_sections() -> None:
    summary = build_schema_summary()
    assert summary["schema_version"] == "2024.7.1"
    assert set(summary["sections"].keys()) == {
        "header",
        "settings",
        "data_sources",
        "data_sets",
    }
