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
    assert any(
        edge.src == "machine"
        and edge.dst == "machine_acquisition"
        and edge.style_key == "setting"
        and edge.relation == "attached_data_sources"
        and edge.role == "context"
        for edge in model.edge_records
    )
    assert {edge.src for edge in model.edge_records if edge.style_key == "data_initial"} == {
        "machine_acquisition",
        "camera",
    }
    assert any((edge.src, edge.dst, edge.style_key) == ("images", "dic", "input") for edge in model.edge_records)
    assert any((edge.src, edge.dst, edge.style_key) == ("dic", "displacements", "data") for edge in model.edge_records)


def test_graph_model_includes_mesh_context_and_supports_dataflow_view() -> None:
    payload = {
        "settings": [{"id": "specimen", "kind": "settings/specimen", "title": "Specimen"}],
        "data_sources": [{
            "id": "dic",
            "kind": "data_sources/dic_measurement",
            "title": "DIC",
            "mesh": "specimen",
        }],
        "data_sets": [],
    }

    complete = build_graph_model(payload)
    mesh = next(edge for edge in complete.edge_records if edge.relation == "mesh")
    assert (mesh.src, mesh.dst) == ("specimen", "dic")
    assert mesh.style_key == "setting"
    assert mesh.role == "context"
    assert mesh.label == "mesh"

    assert build_graph_model(payload, relations="dataflow").edge_records == []
