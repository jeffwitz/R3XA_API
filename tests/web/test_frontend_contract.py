from pathlib import Path


def test_editor_is_catalog_driven() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "web" / "static" / "app.js").read_text(encoding="utf-8")

    assert 'fetch("/api/schema/catalog")' in source
    assert 'fetch("/api/ui")' in source
    assert "schemaCatalog.sections" in source
    assert "guidedStepIndex" in source
    assert "conditionMatches" in source
    assert "requiredFieldIsPresent" in source
    assert "Object.entries(schemaCatalog.sections[step.section]?.kinds || {})" in source
    assert "focusValidationTarget" in source
    assert "renderValidationReport" in source
    template = (root / "web" / "templates" / "edit.html").read_text(encoding="utf-8")
    stylesheet = (root / "web" / "static" / "style.css").read_text(encoding="utf-8")
    assert 'data-editor-mode="guided"' in template
    assert 'data-editor-surface="header"' in template
    assert 'data-editor-surface="data_sets"' in template
    assert 'body[data-editor-mode="guided"] .editor-surface' in stylesheet
    assert 'body[data-editor-mode="advanced"] .expert-panel' in stylesheet
    assert "const templates =" not in source
