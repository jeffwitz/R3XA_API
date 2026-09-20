import json
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


@pytest.fixture(scope="module")
def web_server() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "web.app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{base_url}/health", timeout=1) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(0.1)
    else:
        process.terminate()
        process.wait(timeout=5)
        raise RuntimeError("WebUI test server did not start.")
    yield base_url
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture
def page(web_server: str) -> Page:
    with sync_playwright() as runtime:
        browser: Browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        context = browser.new_context(locale="en-US")
        page = context.new_page()
        page.set_default_timeout(10_000)
        page.goto(web_server)
        yield page
        context.close()
        browser.close()


def _payload(page: Page) -> dict:
    return json.loads(page.locator("#json-input").input_value())


def _payload_from_registry(page: Page) -> dict:
    return json.loads(page.locator("#registry-json-input").input_value())


def test_home_starts_from_experiment_profiles(page: Page) -> None:
    page.wait_for_selector(".profile-card")
    assert page.locator(".profile-card").count() >= 3
    assert page.locator(".advanced-tools a[href='/registry/']").count() == 1
    assert page.locator(".hero a[href='/registry']").count() == 0


def test_generic_profile_is_explicitly_free_form(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=generic")
    page.wait_for_selector("#guided-steps")
    page.wait_for_function("document.querySelector('#guided-prefill')?.hidden === true")
    button_state = page.locator("#guided-prefill").evaluate("element => ({hidden: element.hidden, display: getComputedStyle(element).display, profile: document.querySelector('#profile-select').value})")
    assert button_state["hidden"], button_state
    assert "free-form" in page.locator("#mode-help").inner_text()
    assert page.locator(".guided-step-block").count() == 4


def test_generic_home_entry_starts_a_new_empty_document(page: Page, web_server: str) -> None:
    page.goto(web_server)
    page.evaluate("localStorage.setItem('r3xaDraft', JSON.stringify({title: 'Old draft', description: 'Old', authors: ['Old'], date: '2026-01-01', version: '2026.9.17', settings: [{id: 'old', kind: 'settings/generic'}], data_sources: [], data_sets: []}))")
    page.goto(f"{web_server}/edit?profile=generic&new=1")
    page.wait_for_function(
        """() => {
          const payload = JSON.parse(document.querySelector('#json-input').value || '{}');
          return payload.title === '' && payload.settings?.length === 0;
        }"""
    )
    payload = _payload(page)
    assert payload["title"] == ""
    assert payload["settings"] == []
    assert payload["data_sources"] == []
    assert payload["data_sets"] == []


def test_guided_items_use_kind_prefixed_ids(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=stereo_dic&prefill=1")
    page.wait_for_selector("#schema-summary")
    payload = _payload(page)
    prefixes = {"settings": "stg", "data_sources": "src", "data_sets": "set"}
    for section, prefix in prefixes.items():
        for item in payload[section]:
            kind_name = item["kind"].split("/", 1)[1]
            assert item["id"].startswith(f"{prefix}-{kind_name}-"), item["id"]


def test_existing_document_ids_are_migrated_to_kind_prefixes(page: Page, web_server: str) -> None:
    legacy = {
        "title": "Legacy document",
        "description": "Legacy document",
        "version": "2026.9.18",
        "authors": [],
        "date": "2026-09-02",
        "settings": [{"id": "id_specimen", "kind": "settings/specimen", "title": "Specimen"}],
        "data_sources": [{"id": "id_camera", "kind": "data_sources/camera", "title": "Camera"}],
        "data_sets": [{
            "id": "id_images",
            "kind": "data_sets/list",
            "title": "Images",
            "parent_data_sources": ["id_camera"],
        }],
    }
    page.goto(web_server)
    page.evaluate("payload => localStorage.setItem('r3xaDraft', JSON.stringify(payload))", legacy)
    page.goto(f"{web_server}/edit?profile=generic")
    page.wait_for_selector("#schema-summary")
    payload = _payload(page)
    assert payload["settings"][0]["id"].startswith("stg-specimen-")
    assert payload["data_sources"][0]["id"].startswith("src-camera-")
    assert payload["data_sets"][0]["id"].startswith("set-list-")
    assert payload["data_sets"][0]["parent_data_sources"] == [payload["data_sources"][0]["id"]]


def test_duplicate_ids_are_not_migrated_ambiguously(page: Page, web_server: str) -> None:
    duplicate_id = "legacy-duplicate"
    payload = {
        "title": "Duplicate ID fixture",
        "description": "Fixture for ambiguous identifier migration.",
        "authors": [{"name": "Test author"}],
        "date": "2026-09-18",
        "version": "2026.9.17",
        "settings": [{"id": duplicate_id, "kind": "settings/specimen", "title": "Specimen"}],
        "data_sources": [{"id": duplicate_id, "kind": "data_sources/camera", "title": "Camera"}],
        "data_sets": [],
    }
    page.goto(web_server)
    page.evaluate("payload => localStorage.setItem('r3xaDraft', JSON.stringify(payload))", payload)
    page.goto(f"{web_server}/edit?profile=generic")
    loaded = _payload(page)
    assert loaded["settings"][0]["id"] == duplicate_id
    assert loaded["data_sources"][0]["id"] == duplicate_id
    assert "duplicated" in page.locator("#validation-output").inner_text()


def test_switching_to_generic_discards_existing_items_after_confirmation(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d&prefill=1")
    page.wait_for_selector(".guided-step")
    print("GUIDED DEBUG", page.locator("#guided-steps").inner_text())
    print("JSON DEBUG", page.locator("#json-input").input_value()[:300])
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#profile-select").select_option("generic")
    page.wait_for_function(
        "() => JSON.parse(document.querySelector('#json-input').value || '{}').data_sources?.length === 0"
    )
    payload = _payload(page)
    assert payload["settings"] == []
    assert payload["data_sources"] == []
    assert payload["data_sets"] == []


def test_language_switch_translates_the_home_page(page: Page) -> None:
    page.wait_for_selector(".profile-card")
    page.locator("[data-language-select]").select_option("fr")
    assert page.locator("h1").inner_text() == "Décrivez votre expérience"
    assert page.get_by_text("Outils avancés").count() == 1


def test_prefilled_values_are_editable_without_confirmation(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d&prefill=1")
    page.wait_for_selector(".guided-step")
    page.locator("#guided-prefill").click()
    page.locator(".guided-step-block").filter(has_text="Universal testing machine").first.locator(".guided-step").click()
    page.wait_for_selector(".example-values-help")
    assert page.locator(".template-review-control").count() == 0
    page.evaluate("window.showSaveFilePicker = undefined")
    with page.expect_download():
        page.locator("#save-json-btn").click()
    assert "Review the" not in page.locator("#validation-output").inner_text()


def test_advanced_editor_adds_and_edits_author_objects(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=generic&new=1")
    page.wait_for_selector("#schema-summary")
    page.locator("[data-editor-mode='advanced']").click()
    author_field = page.locator("#field-authors")
    author_field.get_by_role("button", name="Add object").click()
    page.locator("#field-authors-0-name").fill("Jean-Charles Passieux")
    page.locator("#field-authors-0-affiliation").fill("CNRS")
    page.locator("#field-authors-0-orcid").fill("https://orcid.org/0000-0000-0000-0000")
    assert _payload(page)["authors"] == [{
        "name": "Jean-Charles Passieux",
        "affiliation": "CNRS",
        "orcid": "https://orcid.org/0000-0000-0000-0000",
    }]


def test_advanced_item_validation_uses_registry_validation(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=tabular_file&prefill=1")
    page.wait_for_selector("#schema-summary")
    page.locator("[data-editor-mode='advanced']").click()
    data_set = page.locator("#data-sets-form .array-item").filter(has_text="Force time series")
    data_set.get_by_role("button", name="Validate item").click()
    page.wait_for_function("document.querySelector('#validation-output').textContent.length > 0")
    assert "Valid" in page.locator("#validation-output").inner_text()


def test_registry_form_syncs_with_json_and_preserves_unknown_fields(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/registry")
    page.wait_for_selector("#registry-form .registry-field")
    page.locator("#registry-kind").select_option("data_sources/camera")
    page.locator("#registry-field-title").fill("Camera from form")
    payload = _payload_from_registry(page)
    assert payload["kind"] == "data_sources/camera"
    assert payload["title"] == "Camera from form"

    payload["title"] = "Camera from JSON"
    payload["custom_extension"] = {"kept": True}
    page.locator("#registry-json-input").fill(json.dumps(payload, indent=2))
    page.wait_for_function("document.querySelector('#registry-field-title')?.value === 'Camera from JSON'")
    page.locator("#registry-field-description").fill("Edited without losing extensions")
    updated = _payload_from_registry(page)
    assert updated["description"] == "Edited without losing extensions"
    assert updated["custom_extension"] == {"kept": True}


def test_registry_import_preserves_item_until_explicit_example_completion(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/registry")
    page.wait_for_selector("#registry-form .registry-field")
    imported = {
        "id": "legacy-camera",
        "kind": "data_sources/camera",
        "title": "Imported camera",
        "description": "Only the information supplied by the user.",
        "exposure": {"kind": "unit", "title": "Example Title", "unit": "unit", "scale": 1},
    }
    page.locator("#registry-load-input").set_input_files({
        "name": "imported.json",
        "mimeType": "application/json",
        "buffer": json.dumps(imported).encode(),
    })
    page.wait_for_function(
        "expected => JSON.stringify(JSON.parse(document.querySelector('#registry-json-input').value)) === JSON.stringify(expected)",
        arg=imported,
    )
    assert _payload_from_registry(page) == imported
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#registry-complete-btn").click()
    page.wait_for_function("document.querySelector('#registry-field-exposure-value')?.value === '0.01'")
    completed = _payload_from_registry(page)
    assert completed["id"] == imported["id"]
    assert completed["exposure"]["unit"] == "s"


def test_registry_id_generator_uses_kind_prefixes(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/registry")
    page.wait_for_selector("#registry-form .registry-field")
    page.on("dialog", lambda dialog: dialog.accept())
    for kind, prefix in [
        ("settings/specimen", "stg-specimen-"),
        ("data_sources/camera", "src-camera-"),
        ("data_sets/list", "set-list-"),
    ]:
        page.locator("#registry-kind").select_option(kind)
        assert page.locator("#registry-field-id").input_value().startswith(prefix)
        page.locator("[data-json-path='id']").get_by_role("button", name="Generate new ID").click()
        assert page.locator("#registry-field-id").input_value().startswith(prefix)


def test_adding_a_guided_item_does_not_overwrite_a_manual_relationship(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d")
    page.wait_for_selector(".guided-step")

    machine_step = page.locator(".guided-step-block").filter(has_text="Universal testing machine").first
    machine_step.locator(".guided-step").click()
    machine_step.get_by_role("button").click()

    machine_data_step = page.locator(".guided-step-block").filter(has_text="Machine test files").first
    machine_data_step.locator(".guided-step").click()
    machine_data_step.get_by_role("button").click()
    page.get_by_role("button", name="Clear selection").click()

    camera_step = page.locator(".guided-step-block").filter(has_text="Camera").first
    camera_step.locator(".guided-step").click()
    camera_step.get_by_role("button").click()

    payload = _payload(page)
    machine_data = next(item for item in payload["data_sets"] if item.get("path") == "machine/")
    assert machine_data.get("parent_data_sources") == []


def test_schema_page_keeps_existing_draft(page: Page, web_server: str) -> None:
    page.evaluate("localStorage.setItem('r3xaDraft', JSON.stringify({title: 'Draft', description: 'Kept', authors: ['Tester'], date: '2026-09-05', version: '2026.9.17', settings: [], data_sources: [], data_sets: []}))")
    page.goto(f"{web_server}/schema")
    page.wait_for_timeout(150)
    assert page.evaluate("localStorage.getItem('r3xaDraft')") is not None


def test_graph_palette_selector_is_sent_to_api(page: Page, web_server: str) -> None:
    payload = {
        "title": "Palette test",
        "description": "Graph palette test",
        "authors": ["Tester"],
        "date": "2026-09-05",
        "version": "2026.9.17",
        "settings": [],
        "data_sources": [],
        "data_sets": [],
    }
    page.evaluate("payload => localStorage.setItem('r3xaDraft', JSON.stringify(payload))", payload)
    page.goto(f"{web_server}/schema")
    page.wait_for_selector("#graph-palette")
    graph_urls = []

    def fulfill_graph(route) -> None:
        graph_urls.append(route.request.url)
        route.fulfill(
            status=200,
            content_type="image/svg+xml",
            body='<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>',
        )

    page.route("**/api/graph**", fulfill_graph)
    page.locator("#graph-palette").select_option("classic")
    page.wait_for_selector("#graph-container svg")

    assert len(graph_urls) == 1
    assert "palette=classic" in graph_urls[0]
    assert "show_description=true" in graph_urls[0]


def test_graph_backend_selector_renders_interactive_and_static_views(page: Page, web_server: str) -> None:
    payload = {
        "title": "Backend test",
        "description": "Graph backend test",
        "authors": [{"name": "Tester"}],
        "date": "2026-09-05",
        "version": "2026.9.18",
        "settings": [],
        "data_sources": [],
        "data_sets": [],
    }
    page.evaluate("payload => localStorage.setItem('r3xaDraft', JSON.stringify(payload))", payload)

    graph_urls: list[str] = []

    def fulfill_graph(route) -> None:
        url = route.request.url
        graph_urls.append(url)
        if "backend=pyvis" in url:
            route.fulfill(status=200, content_type="text/html", body="<html><body>interactive</body></html>")
        elif "backend=matplotlib" in url:
            route.fulfill(status=200, content_type="image/png", body=b"\x89PNG\r\n\x1a\n")
        else:
            route.fulfill(
                status=200,
                content_type="image/svg+xml",
                body='<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>',
            )

    page.route("**/api/graph**", fulfill_graph)
    page.goto(f"{web_server}/schema")
    assert page.locator("#graph-backend").input_value() == "graphviz-wasm"
    page.locator("#generate-graph-btn").click()
    page.wait_for_selector("#graph-container svg")

    page.locator("#graph-backend").select_option("pyvis")
    page.wait_for_selector("#graph-container iframe.graph-frame")
    assert page.locator("#save-graph-btn").is_visible()
    assert page.locator("#export-standalone-btn").is_hidden()

    page.locator("#graph-backend").select_option("matplotlib")
    page.wait_for_selector("#graph-container img.graph-image")
    assert page.locator("#save-graph-btn").is_visible()

    page.locator("#graph-backend").select_option("graphviz-wasm")
    page.wait_for_selector("#graph-container svg")
    assert "backend=graphviz-wasm" in graph_urls[-1]


def test_reloaded_renamed_items_are_recovered_from_dependencies(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d&prefill=1")
    page.wait_for_selector("#json-input", state="attached")
    payload = _payload(page)
    for item in payload["data_sets"]:
        if item.get("path") == "machine/":
            item["title"] = "Measured force and displacement"
        if item.get("path") == "dic/":
            item["title"] = "Computed displacement fields"
    page.locator("#json-input").evaluate(
        "(element, value) => { element.value = value; element.dispatchEvent(new Event('input', {bubbles: true})); }",
        json.dumps(payload),
    )
    page.evaluate("localStorage.removeItem('r3xaGuidedStepItems:dic_2d')")
    page.reload()
    page.wait_for_selector("#guided-steps")
    assert page.get_by_text("Several items match this kind.").count() == 0


def test_folder_import_populates_and_naturally_sorts_data_files(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d&prefill=1")
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
    payload = _payload(page)
    images = next(item for item in payload["data_sets"] if item.get("path") == "images/")
    assert images["values"] == ["image_2.tif", "image_10.tif"]
