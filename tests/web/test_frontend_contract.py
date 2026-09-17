from pathlib import Path


def test_frontend_assets_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "web" / "static" / "app.js").read_text(encoding="utf-8")
    runtime = (root / "web" / "static" / "runtime.js").read_text(encoding="utf-8")

    assert "window.R3XARuntime.loadSchemaCatalog()" in source
    assert "window.R3XARuntime.loadUiCatalog()" in source
    assert "window.R3XARuntime" in runtime
    assert "validateDocument" in runtime
    assert "validateItem" in runtime
    assert "renderGraph" in runtime
    assert "URLSearchParams" in runtime
    template = (root / "web" / "templates" / "edit.html").read_text(encoding="utf-8")
    index_template = (root / "web" / "templates" / "index.html").read_text(encoding="utf-8")
    stylesheet = (root / "web" / "static" / "style.css").read_text(encoding="utf-8")
    assert 'data-editor-mode="guided"' in template
    assert 'id="guided-prefill"' in template
    assert "Create prefilled workflow" in template
    assert 'src="{{ static_base|default(\'/static\') }}/{{ runtime_name|default(\'runtime.js\') }}?v={{ app_start }}"' in template
    assert '{{ static_base|default(\'/static\') }}/app.js?v={{ app_start }}' in template
    assert '{{ static_base|default(\'/static\') }}/style.css?v={{ app_start }}' in template
    assert 'data-editor-surface="header"' in template
    assert 'data-editor-surface="data_sets"' in template
    assert 'id="profile-cards"' in index_template
    assert "advanced-tools" in index_template
    assert '{{ static_base|default(\'/static\') }}/home.js?v={{ app_start }}' in index_template
    assert 'body[data-editor-mode="guided"] .editor-surface' in stylesheet
    assert 'body[data-editor-mode="advanced"] .expert-panel' in stylesheet
    assert ".profile-cards" in stylesheet
    assert ".template-review-control" in stylesheet
    assert ".data-set-list-field" in stylesheet
    assert "renderDataSetListField" in source
    schema_template = (root / "web" / "templates" / "schema.html").read_text(encoding="utf-8")
    schema_source = (root / "web" / "static" / "schema.js").read_text(encoding="utf-8")
    assert 'id="graph-palette"' in schema_template
    assert 'id="graph-backend"' in schema_template
    assert "palette," in schema_source
    assert "backend," in schema_source
    assert "graph-frame" in schema_source
    for script_name in ("app.js", "home.js", "i18n.js", "registry.js", "schema.js"):
        script_source = (root / "web" / "static" / script_name).read_text(encoding="utf-8")
        assert 'fetch("/api/' not in script_source
        assert "fetch(`/api/" not in script_source
