from r3xa_api.webcore._graph_core import EdgeRecord, build_graph_model


def test_graph_model_includes_settings_as_root_nodes() -> None:
    payload = {
        "settings": [
            {"id": "specimen", "title": "Specimen"},
            {
                "id": "machine",
                "title": "Testing machine",
                "attached_data_sources": ["machine_acquisition"],
            },
        ],
        "data_sources": [
            {"id": "machine_acquisition", "title": "Machine acquisition"},
            {"id": "camera", "title": "Camera"},
            {"id": "dic", "title": "DIC", "input_data_sets": ["images"]},
        ],
        "data_sets": [
            {"id": "machine_data", "title": "Machine data", "parent_data_sources": ["machine_acquisition"]},
            {"id": "images", "title": "Images", "parent_data_sources": ["camera"]},
            {"id": "displacements", "title": "Displacements", "parent_data_sources": ["dic"]},
        ],
    }

    model = build_graph_model(payload)

    assert model.setting_ids == ["specimen", "machine"]
    assert model.levels["specimen"] == 0
    assert model.levels["machine"] == 0
    assert EdgeRecord("machine", "machine_acquisition", "setting") in model.edge_records
    assert EdgeRecord("machine_acquisition", "machine_data", "data_initial") in model.edge_records
    assert EdgeRecord("camera", "images", "data_initial") in model.edge_records
    assert EdgeRecord("images", "dic", "input") in model.edge_records
    assert EdgeRecord("dic", "displacements", "data") in model.edge_records
