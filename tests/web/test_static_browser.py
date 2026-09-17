from __future__ import annotations

import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Browser, Page, sync_playwright


ROOT = Path(__file__).resolve().parents[2]


def _chromium_path() -> str:
    configured = os.environ.get("R3XA_CHROMIUM_EXECUTABLE")
    candidates = [configured, shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("google-chrome")]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    pytest.skip("A Chromium executable is required for browser tests.")


def _load_dev_module():
    script_path = ROOT / "scripts" / "dev.py"
    spec = importlib.util.spec_from_file_location("r3xa_dev_static_browser_test", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def static_site(tmp_path: Path) -> str:
    output_dir = tmp_path / "r3xa-webui"
    _load_dev_module().build_static_web(output_dir)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", str(output_dir)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{base_url}/", timeout=1) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(0.1)
    else:
        process.terminate()
        process.wait(timeout=5)
        raise RuntimeError("Static WebUI test server did not start.")
    yield base_url
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture
def static_page(static_site: str) -> Page:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        context = browser.new_context(locale="en-US")
        page = context.new_page()
        page.set_default_timeout(10_000)
        page.goto(static_site)
        yield page
        context.close()
        browser.close()


def test_static_editor_loads_catalogue_and_validates_locally(static_page: Page, static_site: str) -> None:
    requests: list[str] = []
    static_page.on("request", lambda request: requests.append(request.url))
    static_page.goto(f"{static_site}/edit/")
    static_page.wait_for_selector("#schema-summary")
    assert static_page.evaluate("window.R3XARuntime.mode") == "static"
    static_page.click("#validate-btn")
    static_page.wait_for_function("document.querySelector('#validation-output').textContent.length > 0")
    assert "Invalid" in static_page.locator("#validation-output").inner_text()
    assert not any("/api/" in url for url in requests)
    report = static_page.evaluate(
        """
        async () => (await window.R3XARuntime.validateDocument({
          title: "Integrity test",
          description: "Integrity test",
          version: "2026.9.18",
          authors: [{name: "Tester"}],
          date: "2026-09-17",
          settings: [{id: "duplicate", kind: "settings/generic", title: "Setup"}],
          data_sources: [{
            id: "duplicate",
            kind: "data_sources/generic",
            title: "Source",
            output_components: 1,
            output_dimension: "point",
            output_units: [],
          }],
          data_sets: [],
        })).json()
        """
    )
    assert report["valid"] is False
    assert any(error["validator"] == "integrity" for error in report["errors"])


def test_static_registry_validation_uses_local_validator(static_site: str) -> None:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f"{static_site}/registry/")
        page.wait_for_selector("#registry-validation-output", state="attached")
        page.click("#registry-validate-btn")
        page.wait_for_function("document.querySelector('#registry-validation-output').textContent.length > 0")
        assert "Valid registry item" in page.locator("#registry-validation-output").inner_text()
        browser.close()


def test_static_graph_renders_with_local_graphviz_wasm(static_site: str) -> None:
    requests: list[str] = []
    payload = {
        "title": "Browser graph",
        "description": "Static graph test",
        "version": "2026.9.18",
        "authors": [{"name": "Tester"}],
        "date": "2026-09-17",
        "settings": [{"id": "machine", "kind": "settings/generic", "title": "Machine"}],
        "data_sources": [{"id": "camera", "kind": "data_sources/generic", "title": "Camera"}],
        "data_sets": [{
            "id": "images",
            "kind": "data_sets/generic",
            "title": "Images",
            "parent_data_sources": ["camera"],
        }],
    }
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.on("request", lambda request: requests.append(request.url))
        page.goto(f"{static_site}/schema/")
        assert page.locator("#graph-backend option:checked").inner_text() == "Graphviz WebAssembly · SVG · browser"
        page.evaluate("payload => localStorage.setItem('r3xaDraft', JSON.stringify(payload))", payload)
        page.reload()
        page.wait_for_selector("#graph-backend")
        page.locator("#generate-graph-btn").click()
        page.wait_for_selector("#graph-container svg", state="attached", timeout=30_000)
        assert page.locator("#graph-container svg").count() == 1
        assert "Machine" in page.locator("#graph-container").inner_text()
        assert not any("/api/" in url for url in requests)
        browser.close()


def test_static_schema_viewer_handles_an_invalid_saved_draft(static_site: str) -> None:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f"{static_site}/schema/")
        page.evaluate("localStorage.setItem('r3xaDraft', 'not-json')")
        page.reload()
        page.wait_for_selector("#schema-tree")
        assert "Failed to load draft" not in page.locator("#schema-tree").inner_text()
        assert "schema_version" in page.locator("#schema-tree").inner_text()
        browser.close()
