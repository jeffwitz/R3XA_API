from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from r3xa_api import R3XAFile, unit

sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright


def _chromium_path() -> str:
    for candidate in (shutil.which("chromium"), shutil.which("chromium-browser")):
        if candidate:
            return candidate
    pytest.skip("A Chromium executable is required for browser tests.")


def test_python_cytoscape_export_runs_offline_and_inspects_items(tmp_path: Path) -> None:
    document = R3XAFile(
        title="Standalone graph",
        description="Offline test",
        authors=[{"name": "Tester"}],
        date="2026-10-25",
    )
    camera = document.add_generic_source(
        title="Camera",
        description="Visible camera",
        output_components=1,
        output_dimension="surface",
        output_units=[unit(unit="px")],
    )
    document.add_generic_data_set(
        title="Images", path="images/", parent_data_sources=[camera],
    )
    output = document.plot(tmp_path / "graph", backend="cytoscape")

    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        errors = []
        requests = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url))
        page.set_content(output.read_text(encoding="utf-8"), wait_until="load")
        camera_node = page.locator(f'.standalone-node-hit-area[data-node-id="{camera.id}"]')
        camera_node.wait_for(state="attached")
        assert page.locator("#graph canvas").count() > 0
        camera_node.click()
        assert page.locator("#selected-title").inner_text() == "Camera"
        assert "Visible camera" in page.locator("#selected-fields").inner_text()
        page.locator("#graph-zoom-in").click()
        camera_node.dblclick()
        page.locator("#graph-fit").click()
        assert errors == []
        assert requests == []
        browser.close()


def test_python_cytoscape_export_escapes_document_text(tmp_path: Path) -> None:
    document = R3XAFile(
        title="</script><script>window.injected=true</script>",
        description="HTML escaping",
        authors=[{"name": "Tester"}],
        date="2026-10-25",
    )
    output = document.plot(tmp_path / "graph", backend="cytoscape")

    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True, executable_path=_chromium_path())
        page = browser.new_page()
        page.set_content(output.read_text(encoding="utf-8"), wait_until="load")
        assert page.evaluate("window.injected === true") is False
        assert page.locator("h1").inner_text() == document.title
        browser.close()
