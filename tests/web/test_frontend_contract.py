from pathlib import Path


def test_frontend_assets_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "web" / "static" / "app.js").read_text(encoding="utf-8")

    assert 'fetch("/api/schema/catalog")' in source
    assert 'fetch("/api/ui")' in source
    template = (root / "web" / "templates" / "edit.html").read_text(encoding="utf-8")
    index_template = (root / "web" / "templates" / "index.html").read_text(encoding="utf-8")
    stylesheet = (root / "web" / "static" / "style.css").read_text(encoding="utf-8")
    assert 'data-editor-mode="guided"' in template
    assert 'id="guided-prefill"' in template
    assert "Create prefilled workflow" in template
    assert 'src="/static/i18n.js?v={{ app_start }}"' in template
    assert '/static/app.js?v={{ app_start }}' in template
    assert '/static/style.css?v={{ app_start }}' in template
    assert 'data-editor-surface="header"' in template
    assert 'data-editor-surface="data_sets"' in template
    assert 'id="profile-cards"' in index_template
    assert "advanced-tools" in index_template
    assert 'src="/static/home.js?v={{ app_start }}"' in index_template
    assert 'body[data-editor-mode="guided"] .editor-surface' in stylesheet
    assert 'body[data-editor-mode="advanced"] .expert-panel' in stylesheet
    assert ".profile-cards" in stylesheet
    assert ".template-review-control" in stylesheet
    assert ".data-set-list-field" in stylesheet
    assert "renderDataSetListField" in source
