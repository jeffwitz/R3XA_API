from __future__ import annotations

import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.request import urlopen

import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Browser, Page, sync_playwright

from r3xa_api.webcore import build_validation_report


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


@contextmanager
def _serve_static_directory(directory: Path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", str(directory)],
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
    try:
        yield base_url
    finally:
        process.terminate()
        process.wait(timeout=5)


@pytest.fixture
def static_site(tmp_path: Path) -> str:
    output_dir = tmp_path / "r3xa-webui"
    _load_dev_module().build_static_web(output_dir)
    with _serve_static_directory(output_dir) as base_url:
        yield base_url


@pytest.fixture
def static_subpath_site(tmp_path: Path) -> str:
    host_dir = tmp_path / "host"
    output_dir = host_dir / "r3xa-webui"
    _load_dev_module().build_static_web(output_dir)
    with _serve_static_directory(host_dir) as base_url:
        yield f"{base_url}/r3xa-webui"


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


def test_static_web_works_under_a_non_root_subpath(static_subpath_site: str) -> None:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f"{static_subpath_site}/edit/")
        page.wait_for_selector("#schema-summary")
        assert page.evaluate("window.R3XARuntime.mode") == "static"
        page.goto(f"{static_subpath_site}/")
        page.wait_for_selector(".profile-card")
        page.locator(".profile-card").first.click()
        page.wait_for_selector("#schema-summary")
        assert page.url.startswith(f"{static_subpath_site}/edit/")
        page.goto(f"{static_subpath_site}/schema/")
        page.wait_for_selector("#schema-tree")
        page.goto(f"{static_subpath_site}/registry/")
        page.wait_for_selector("#registry-json-input")
        browser.close()


def test_static_navigation_uses_only_same_origin_get_requests(static_site: str) -> None:
    requests: list[tuple[str, str]] = []
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.on("request", lambda request: requests.append((request.method, request.url)))
        page.goto(f"{static_site}/")
        page.wait_for_selector(".profile-card")
        page.goto(f"{static_site}/edit/")
        page.wait_for_selector("#schema-summary")
        page.goto(f"{static_site}/schema/")
        page.wait_for_selector("#schema-tree")
        page.goto(f"{static_site}/registry/")
        page.wait_for_selector("#registry-json-input")
        browser.close()

    assert requests
    assert all(method == "GET" for method, _ in requests)
    assert all(url.startswith(static_site) for _, url in requests)
    assert not any("/api/" in url for _, url in requests)


def test_static_user_session_uses_no_remote_or_post_requests(static_site: str) -> None:
    requests: list[tuple[str, str]] = []
    payload = {
        "title": "Static session",
        "description": "No network session",
        "version": "2026.9.18",
        "authors": [{"name": "Tester"}],
        "date": "2026-09-17",
        "settings": [],
        "data_sources": [],
        "data_sets": [],
    }
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.on("request", lambda request: requests.append((request.method, request.url)))
        page.goto(f"{static_site}/edit/?profile=generic&new=1")
        page.wait_for_selector("#schema-summary")
        page.evaluate("payload => localStorage.setItem('r3xaDraft', JSON.stringify(payload))", payload)
        page.reload()
        page.locator("#validate-btn").click()
        page.wait_for_function("document.querySelector('#validation-output').textContent.length > 0")
        page.goto(f"{static_site}/schema/")
        page.wait_for_selector("#schema-tree")
        page.locator("#generate-graph-btn").click()
        page.wait_for_selector("#graph-container svg", state="attached", timeout=30_000)
        page.goto(f"{static_site}/registry/")
        page.wait_for_selector("#registry-json-input")
        browser.close()

    assert requests
    assert all(method == "GET" for method, _ in requests)
    assert all(url.startswith(static_site) for _, url in requests)
    assert not any("/api/" in url for _, url in requests)


def test_static_editor_preserves_one_document_across_modes(static_site: str) -> None:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f"{static_site}/edit/?profile=dic_2d&prefill=1")
        page.wait_for_selector("#schema-summary")
        page.wait_for_function("Boolean(localStorage.getItem('r3xaDraft'))")
        original = page.evaluate("localStorage.getItem('r3xaDraft')")
        for mode in ("advanced", "expert", "guided"):
            page.locator(f"[data-editor-mode='{mode}']").click()
            page.wait_for_function("mode => document.body.dataset.editorMode === mode", arg=mode)
            assert page.evaluate("localStorage.getItem('r3xaDraft')") == original
        browser.close()


def test_static_editor_imports_json_and_persists_it_locally(static_site: str) -> None:
    payload = {
        "title": "Imported static document",
        "description": "Loaded from a local file",
        "version": "2026.9.18",
        "authors": [{"name": "Tester"}],
        "date": "2026-09-17",
        "settings": [],
        "data_sources": [],
        "data_sets": [],
    }
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f"{static_site}/edit/?profile=generic&new=1")
        page.wait_for_selector("#schema-summary")
        page.locator("#load-json-input").evaluate(
            """(input, text) => {
              const files = new DataTransfer();
              files.items.add(new File([text], 'imported.json', {type: 'application/json'}));
              Object.defineProperty(input, 'files', {value: files.files});
              input.dispatchEvent(new Event('change', {bubbles: true}));
            }""",
            json.dumps(payload),
        )
        page.wait_for_function("JSON.parse(document.querySelector('#json-input').value).title === 'Imported static document'")
        page.reload()
        page.wait_for_function("JSON.parse(document.querySelector('#json-input').value).title === 'Imported static document'")
        assert page.evaluate("JSON.parse(document.querySelector('#json-input').value).title") == payload["title"]
        browser.close()


def test_static_directory_selection_naturally_sorts_list_values(static_site: str) -> None:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f"{static_site}/edit/?profile=dic_2d&prefill=1")
        page.wait_for_selector(".guided-step")
        page.locator(".guided-step").filter(has_text="Images").click()
        page.locator("[id^='guided-images-template-'] input[type=file]").evaluate(
            """input => {
              const files = new DataTransfer();
              files.items.add(new File(['10'], 'image_10.tif', {type: 'image/tiff'}));
              files.items.add(new File(['2'], 'image_2.tif', {type: 'image/tiff'}));
              Object.defineProperty(input, 'files', {value: files.files});
              input.dispatchEvent(new Event('change', {bubbles: true}));
            }"""
        )
        payload = page.evaluate("JSON.parse(document.querySelector('#json-input').value)")
        images = next(item for item in payload["data_sets"] if item.get("path") == "images/")
        assert images["values"] == ["image_2.tif", "image_10.tif"]
        browser.close()


def test_static_graph_exports_svg_and_standalone_html(static_site: str) -> None:
    payload = {
        "title": "Export graph",
        "description": "Static export test",
        "version": "2026.9.18",
        "authors": [{"name": "Tester"}],
        "date": "2026-09-17",
        "settings": [],
        "data_sources": [],
        "data_sets": [],
    }
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(f"{static_site}/schema/")
        page.evaluate("payload => localStorage.setItem('r3xaDraft', JSON.stringify(payload))", payload)
        page.reload()
        page.locator("#generate-graph-btn").click()
        page.wait_for_selector("#graph-container svg", state="attached", timeout=30_000)
        page.locator("#graph-palette").select_option("classic")
        page.wait_for_selector("#graph-container svg", state="attached", timeout=30_000)
        page.locator("#fullscreen-graph-btn").click()
        page.wait_for_selector(".graph-overlay")
        page.keyboard.press("Escape")
        assert page.locator(".graph-overlay").count() == 0
        with page.expect_download() as svg_download:
            page.locator("#save-graph-btn").click()
        assert svg_download.value.suggested_filename == "r3xa-graph.svg"
        with page.expect_download() as html_download:
            page.locator("#export-standalone-btn").click()
        assert html_download.value.suggested_filename == "r3xa-standalone.html"
        browser.close()


def test_static_language_switch_updates_home_page(static_site: str) -> None:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page(locale="en-US")
        page.goto(f"{static_site}/")
        page.wait_for_selector(".profile-card")
        page.locator("[data-language-select]").select_option("fr")
        assert page.locator("h1").inner_text() == "Décrivez votre expérience"
        browser.close()


def test_static_registry_validation_uses_local_validator(static_site: str) -> None:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        requests: list[tuple[str, str]] = []
        page.on("request", lambda request: requests.append((request.method, request.url)))
        page.goto(f"{static_site}/registry/")
        page.wait_for_selector("#registry-validation-output", state="attached")
        page.click("#registry-validate-btn")
        page.wait_for_function("document.querySelector('#registry-validation-output').textContent.length > 0")
        assert "Valid registry item" in page.locator("#registry-validation-output").inner_text()
        assert all(method == "GET" for method, _ in requests)
        assert all(url.startswith(static_site) for _, url in requests)
        assert not any("/api/" in url for _, url in requests)
        browser.close()


def test_static_graph_renders_with_local_graphviz_wasm(static_site: str) -> None:
    requests: list[tuple[str, str]] = []
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
        page.on("request", lambda request: requests.append((request.method, request.url)))
        page.goto(f"{static_site}/schema/")
        assert page.locator("#graph-backend option:checked").inner_text() == "Graphviz WebAssembly · SVG · browser"
        page.evaluate("payload => localStorage.setItem('r3xaDraft', JSON.stringify(payload))", payload)
        page.reload()
        page.wait_for_selector("#graph-backend")
        page.locator("#generate-graph-btn").click()
        page.wait_for_selector("#graph-container svg", state="attached", timeout=30_000)
        assert page.locator("#graph-container svg").count() == 1
        assert "Machine" in page.locator("#graph-container").inner_text()
        assert all(method == "GET" for method, _ in requests)
        assert all(url.startswith(static_site) for _, url in requests)
        assert not any("/api/" in url for _, url in requests)
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


def test_static_schema_viewer_falls_back_for_complex_drafts(static_site: str) -> None:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f"{static_site}/edit/?profile=stereo_dic&prefill=1")
        page.wait_for_function("localStorage.getItem('r3xaDraft')?.includes('Stereo DIC')")
        page.goto(f"{static_site}/schema/")
        page.wait_for_selector("#schema-tree")
        tree_text = page.locator("#schema-tree").inner_text()
        assert "Failed to load draft" not in tree_text
        assert "Stereo DIC" in tree_text
        browser.close()


def test_static_graph_failure_does_not_break_the_editor(static_site: str) -> None:
    payload = {
        "title": "WASM fallback",
        "description": "Graph failure must not disable editing",
        "version": "2026.9.18",
        "authors": [{"name": "Tester"}],
        "date": "2026-09-17",
        "settings": [],
        "data_sources": [],
        "data_sets": [],
    }
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f"{static_site}/schema/")
        page.evaluate("payload => localStorage.setItem('r3xaDraft', JSON.stringify(payload))", payload)
        page.reload()
        page.route("**/assets/graph.generated.js", lambda route: route.abort())
        page.locator("#generate-graph-btn").click()
        page.wait_for_function(
            "document.querySelector('#graph-container').textContent.includes('Graphviz WASM rendering failed')"
        )
        page.goto(f"{static_site}/edit/")
        page.wait_for_selector("#json-input", state="attached")
        assert page.evaluate("window.R3XARuntime.mode") == "static"
        browser.close()


def test_static_validation_matches_python_for_schema_and_integrity_errors(static_site: str) -> None:
    valid_payload = {
        "title": "Parity document",
        "description": "Validation parity",
        "version": "2026.9.18",
        "authors": [{"name": "Tester"}],
        "date": "2026-09-17",
        "settings": [{"id": "duplicate", "kind": "settings/generic", "title": "Setup"}],
        "data_sources": [{
            "id": "duplicate",
            "kind": "data_sources/generic",
            "title": "Source",
            "output_components": 1,
            "output_dimension": "point",
            "output_units": [],
        }],
        "data_sets": [],
    }
    cases = {
        "schema": {key: value for key, value in valid_payload.items() if key != "title"},
        "wrong_version": {**valid_payload, "version": "not-the-current-schema"},
        "wrong_author_type": {**valid_payload, "authors": ["Tester"]},
        "integrity": valid_payload,
    }
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f"{static_site}/edit/")
        page.wait_for_selector("#schema-summary")
        for name, payload in cases.items():
            expected = build_validation_report(payload)
            actual = page.evaluate(
                """async payload => {
                  const response = await window.R3XARuntime.validateDocument(payload);
                  return response.json();
                }""",
                payload,
            )
            assert actual["valid"] == expected["valid"], name
            assert [(error["path"], error["validator"]) for error in actual["errors"]] == [
                (error["path"], error["validator"]) for error in expected["errors"]
            ], name
            if name != "integrity":
                assert [error["user_message"] for error in actual["errors"]] == [
                    error["user_message"] for error in expected["errors"]
                ], name
        browser.close()
