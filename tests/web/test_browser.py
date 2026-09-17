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


def _ui_catalog(web_server: str) -> dict:
    with urlopen(f"{web_server}/api/ui", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


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


def test_switching_to_generic_discards_existing_items_after_confirmation(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d&prefill=1")
    page.wait_for_selector(".template-review-control")
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


def test_prefilled_values_require_individual_confirmation(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d&prefill=1")
    page.wait_for_selector(".template-review-control")
    assert page.locator("#guided-review").count() == 0
    page.locator("#save-json-btn").click()
    assert "Review the" in page.locator("#validation-output").inner_text()
    assert page.locator(".template-review-control input[type=checkbox]").count() > 0


def test_every_prefilled_profile_marks_all_template_defaults_for_review(page: Page, web_server: str) -> None:
    for profile_id, profile in _ui_catalog(web_server)["profiles"].items():
        expected = sum(
            len(set(step.get("defaults", {})) - {"id", "kind", "version"})
            for step in profile.get("steps", [])
        )
        if not expected:
            continue
        page.once("dialog", lambda dialog: dialog.accept())
        page.goto(f"{web_server}/edit?profile={profile_id}&prefill=1")
        page.wait_for_function(
            """([profile, count]) =>
              JSON.parse(localStorage.getItem(`r3xaPendingTemplateReview:${profile}`) || '[]').length === count""",
            arg=[profile_id, expected],
        )
        pending = page.evaluate(
            "profile => JSON.parse(localStorage.getItem(`r3xaPendingTemplateReview:${profile}`) || '[]')",
            profile_id,
        )
        assert len(pending) == expected, profile_id


def test_template_reviews_are_scoped_to_the_selected_profile(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d&prefill=1")
    page.wait_for_selector(".template-review-control")
    pending = page.evaluate("JSON.parse(localStorage.getItem('r3xaPendingTemplateReview:dic_2d'))")
    assert pending
    page.locator("#profile-select").select_option("torsion_test")
    assert page.evaluate("localStorage.getItem('r3xaPendingTemplateReview:torsion_test')") is None
    assert page.evaluate("JSON.parse(localStorage.getItem('r3xaPendingTemplateReview:dic_2d'))") == pending


def test_reset_clears_template_reviews_from_previous_workflows(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d&prefill=1")
    page.wait_for_selector(".template-review-control")
    page.evaluate("localStorage.setItem('r3xaPendingTemplateReview:torsion_test', JSON.stringify(['stale']))")
    page.locator("#reset-btn").click()
    assert page.evaluate("localStorage.getItem('r3xaPendingTemplateReview:dic_2d')") is None
    assert page.evaluate("localStorage.getItem('r3xaPendingTemplateReview:torsion_test')") is None


def test_individually_added_guided_item_requires_template_review(page: Page, web_server: str) -> None:
    page.goto(f"{web_server}/edit?profile=dic_2d")
    page.wait_for_selector(".guided-step")
    camera_step = page.locator(".guided-step-block").filter(has_text="Camera").first
    camera_step.locator(".guided-step").click()
    camera_step.get_by_role("button").click()
    page.wait_for_selector(".template-review-control")
    pending = page.evaluate("JSON.parse(localStorage.getItem('r3xaPendingTemplateReview:dic_2d'))")
    assert pending


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

    def fulfill_graph(route) -> None:
        url = route.request.url
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
    page.locator("#generate-graph-btn").click()
    page.wait_for_selector("#graph-container svg")

    page.locator("#graph-backend").select_option("pyvis")
    page.wait_for_selector("#graph-container iframe.graph-frame")
    assert page.locator("#save-graph-btn").is_visible()
    assert page.locator("#export-standalone-btn").is_hidden()

    page.locator("#graph-backend").select_option("matplotlib")
    page.wait_for_selector("#graph-container img.graph-image")
    assert page.locator("#save-graph-btn").is_visible()


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
