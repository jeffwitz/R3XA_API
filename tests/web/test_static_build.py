from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path


def _load_dev_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "dev.py"
    spec = importlib.util.spec_from_file_location("r3xa_dev_static_test", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_static_web_build_contains_local_pages_and_catalogues(tmp_path: Path) -> None:
    module = _load_dev_module()
    output_dir = tmp_path / "r3xa-webui"

    module.build_static_web(output_dir)

    assert (output_dir / "index.html").is_file()
    assert (output_dir / "edit" / "index.html").is_file()
    assert (output_dir / "schema" / "index.html").is_file()
    assert (output_dir / "registry" / "index.html").is_file()
    assets = output_dir / "assets"
    for name in (
        "schema.json",
        "schema-catalog.json",
        "schema-summary.json",
        "ui-catalog.json",
        "build-info.json",
        "graph-palettes.json",
        "graph-relations.json",
        "graphviz-12.2.1.wasm",
        "runtime-static.js",
        "id-utils.js",
        "registry-storage.js",
        "graph.generated.js",
        "cytoscape.generated.js",
        "validator.generated.js",
    ):
        assert (assets / name).is_file(), name
    assert not (assets / "runtime.js").exists()
    validator_source = (assets / "validator.generated.js").read_text(encoding="utf-8")
    assert "export" in validator_source
    assert "validateRegistryItem" in validator_source
    assert "registryKinds" in validator_source
    static_runtime = (assets / "runtime-static.js").read_text(encoding="utf-8")
    assert "integrityErrors" in static_runtime
    assert "validateItem" in static_runtime
    assert "graphBackends" in static_runtime
    assert "graph-relations.json" in static_runtime
    assert "cytoscape.generated.js" in static_runtime
    assert (assets / "graphviz-12.2.1.wasm").stat().st_size > 1_000_000
    source_wasm = (
        Path(__file__).resolve().parents[2]
        / "r3xa_api"
        / "resources"
        / "graphviz"
        / "graphviz-12.2.1.wasm"
    )
    assert (assets / "graphviz-12.2.1.wasm").read_bytes() == source_wasm.read_bytes()

    catalog = json.loads((assets / "schema-catalog.json").read_text(encoding="utf-8"))
    assert catalog["schema_version"]
    assert "data_sources" in catalog["sections"]
    graph_relations = json.loads((assets / "graph-relations.json").read_text(encoding="utf-8"))
    assert graph_relations["fields"]["data_sources/dic_measurement"]["mesh"] == "settings"
    assert graph_relations["semantics"]["mesh"]["role"] == "context"
    build_info = json.loads((assets / "build-info.json").read_text(encoding="utf-8"))
    assert build_info["build_id"] == module._static_build_id()
    assert build_info["git_commit"]
    assert "assetUrl" in static_runtime
    assert "assetVersion" in static_runtime
    index = (output_dir / "index.html").read_text(encoding="utf-8")
    editor = (output_dir / "edit" / "index.html").read_text(encoding="utf-8")
    assert 'src="assets/runtime-static.js' in index
    assert 'data-asset-version="' in index
    assert 'src="../assets/runtime-static.js' in editor
    assert 'href="./edit/"' in index
    assert 'href="../schema/"' in editor
    assert 'src="../assets/photomeca-logo.png"' in editor
    assert 'src="../assets/photomeca-logo.png"' in (output_dir / "schema" / "index.html").read_text(encoding="utf-8")

    for page in output_dir.rglob("*.html"):
        source = page.read_text(encoding="utf-8")
        assert "onerror=" not in source
        assert "onclick=" not in source
        assert "style=" not in source


def test_static_web_assets_do_not_use_fastapi_api_urls(tmp_path: Path) -> None:
    module = _load_dev_module()
    output_dir = tmp_path / "r3xa-webui"
    module.build_static_web(output_dir)

    for asset in (output_dir / "assets").rglob("*.js"):
        source = asset.read_text(encoding="utf-8")
        assert 'fetch("/api/' not in source
        assert "fetch(`/api/" not in source


def test_static_web_pages_reference_only_local_runtime_assets(tmp_path: Path) -> None:
    module = _load_dev_module()
    output_dir = tmp_path / "r3xa-webui"
    module.build_static_web(output_dir)

    url_attributes = re.compile(r"(?:src|href)=[\"']([^\"']+)[\"']")
    for page in output_dir.rglob("*.html"):
        for url in url_attributes.findall(page.read_text(encoding="utf-8")):
            assert not url.startswith(("http://", "https://", "//")), (page, url)

    for asset in (output_dir / "assets").rglob("*.css"):
        for url in re.findall(r"url\(\s*[\"']?([^\"')]+)", asset.read_text(encoding="utf-8")):
            assert not url.startswith(("http://", "https://", "//")), (asset, url)

    runtime = (output_dir / "assets" / "runtime-static.js").read_text(encoding="utf-8")
    assert "https://" not in runtime
    assert "http://" not in runtime
    assert "/api/" not in runtime
