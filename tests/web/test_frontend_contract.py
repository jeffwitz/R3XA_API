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
    assert "applyProfileLinks" in source
    assert "overwrite: true" in source
    assert "pre-filled when possible" in source
    assert "createPrefilledWorkflow" in source
    assert "applyStepDefaults" in source
    assert "guidedStepItemsStorageKey" in source
    assert "selectGuidedStepItem" in source
    assert "if (candidates.length !== 1) return null;" in source
    assert "guided-item-picker" in source
    assert "reference-checklist" in source
    assert "check every upstream object" in source
    assert "selectedIds.add" in source
    assert 'localStorage.removeItem("r3xaDraftLast")' in source
    assert 'key.startsWith("r3xaGuidedStepItems:")' in source
    assert "return (payload[step.section] || []).find" not in source
    assert "isReferenceMeta" in source
    assert "meta.items?.ref" in source
    assert 'meta.type === "array"' in source
    assert "Optional relationships" in source
    assert "Related data sources" in source
    assert "to_field" in source
    assert "Object.entries(schemaCatalog.sections[step.section]?.kinds || {})" in source
    assert "focusValidationTarget" in source
    assert "renderValidationReport" in source
    template = (root / "web" / "templates" / "edit.html").read_text(encoding="utf-8")
    stylesheet = (root / "web" / "static" / "style.css").read_text(encoding="utf-8")
    schema_script = (root / "web" / "static" / "schema.js").read_text(encoding="utf-8")
    assert 'data-editor-mode="guided"' in template
    assert 'id="guided-prefill"' in template
    assert "Create prefilled workflow" in template
    assert '/static/app.js?v={{ app_start }}' in template
    assert '/static/style.css?v={{ app_start }}' in template
    assert 'data-editor-surface="header"' in template
    assert 'data-editor-surface="data_sets"' in template
    assert 'body[data-editor-mode="guided"] .editor-surface' in stylesheet
    assert 'body[data-editor-mode="advanced"] .expert-panel' in stylesheet
    assert ".guided-item-picker" in stylesheet
    assert ".reference-checklist" in stylesheet
    assert 'localStorage.removeItem("r3xaDraftLast")' in schema_script
    assert 'key.startsWith("r3xaGuidedStepItems:")' in schema_script
    assert "const templates =" not in source
