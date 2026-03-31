import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    # Cell 1 — Minimal imports for early branded introduction.
    import base64
    from pathlib import Path

    import marimo as mo

    return Path, base64, mo


@app.cell(hide_code=True)
def _(Path, base64, mo):
    # Cell 2 — Branding and high-level objective.
    def find_project_root() -> Path:
        starts = []
        if "__file__" in globals():
            starts.append(Path(__file__).resolve())
        starts.append(Path.cwd().resolve())

        visited = set()
        for start in starts:
            for current in [start] + list(start.parents):
                if current in visited:
                    continue
                visited.add(current)
                if (current / "pyproject.toml").exists():
                    return current
        return Path.cwd().resolve()

    project_root = find_project_root()

    def logo_data_uri(candidates: list[str]):
        for candidate in candidates:
            logo_path = (project_root / candidate).resolve()
            if not logo_path.exists():
                continue
            encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
            if logo_path.suffix.lower() == ".svg":
                mime = "image/svg+xml"
            elif logo_path.suffix.lower() in {".jpg", ".jpeg"}:
                mime = "image/jpeg"
            else:
                mime = "image/png"
            return f"data:{mime};base64,{encoded}"
        return None

    r3xa_logo = logo_data_uri(["web/static/r3xa-logo.png", "docs/figures/R3XA.png"])
    photomeca_logo = logo_data_uri(["web/static/photomeca-logo.png"])

    logo_tags = []
    if photomeca_logo:
        logo_tags.append(
            f'<img src="{photomeca_logo}" alt="Photomeca logo" '
            'style="height:88px; width:auto; object-fit:contain;" />'
        )
    if r3xa_logo:
        logo_tags.append(
            f'<img src="{r3xa_logo}" alt="R3XA logo" '
            'style="height:88px; width:auto; object-fit:contain;" />'
        )

    if logo_tags:
        logos = mo.Html(
            "<div style='display:flex; gap:28px; align-items:center; margin-bottom:8px;'>"
            f"{''.join(logo_tags)}"
            "</div>"
        )
    else:
        logos = mo.callout(
            "Logos not found. Expected assets under `web/static/`.",
            kind="warn",
        )
    intro = mo.md("""
    # Base DIC example (R3XA_API)

    This notebook reproduces the base DIC pipeline used in JC's presentation:
    camera acquisition -> image list -> DIC processing (`pyxel`) -> displacement fields.

    **What you can do here**
    - edit parameters,
    - generate/validate the JSON payload,
    - import/export JSON files,
    - generate and export the Graphviz SVG graph.
    """)
    header_view = mo.vstack([logos, intro])
    header_view
    return


@app.cell(hide_code=True)
def _(mo):
    # Cell 3 — Human-readable map of notebook sections.
    cell_map = mo.md("""
    ## Notebook cell map

    1. **Minimal imports** and early introduction.
    2. **Branded intro** and notebook objectives.
    3. **This map**.
    4. **R3XA/JSON/graph imports**.
    5. **Parameters** (editable test settings).
    6. **From-scratch payload builder**.
    7. **Upload state initialization**.
    8. **Import UI + validation callback**.
    9. **Reset uploaded payload**.
    10. **Upload status panel**.
    11. **Active payload selector**.
    12. **Validation + JSON preview**.
    13. **JSON export helpers**.
    14. **Graphviz SVG generation and embedding**.
    15. **Graph generation trigger button**.
    """)
    cell_map
    return


@app.cell
def _():
    # Cell 4 — Full imports for payload construction, validation, and graph rendering.
    import json

    from r3xa_api import R3XAFile, unit, validate
    from r3xa_api.webcore.graph import generate_svg

    return R3XAFile, generate_svg, json, unit, validate


@app.cell
def _():
    # Cell 5 — Editable experiment parameters (single place to customize the demo).
    # Edit these values directly, then re-run dependent cells.
    test_title = "Open-hole tensile test with DIC"
    test_description = "Camera acquisition + DIC processing pipeline"
    authors = "R3XA API"
    date = "2024-10-30"
    num_frames = 5
    dt_seconds = 0.5
    image_path = "images/"
    dic_path = "dic/"
    return (
        authors,
        date,
        dic_path,
        dt_seconds,
        image_path,
        num_frames,
        test_description,
        test_title,
    )


@app.cell
def _(
    R3XAFile,
    authors,
    date,
    dic_path,
    dt_seconds,
    image_path,
    num_frames,
    test_description,
    test_title,
    unit,
):
    # Cell 6 — Build a complete R3XA payload from scratch using the API.
    r3xa = R3XAFile(
        title=test_title,
        description=test_description,
        authors=authors,
        date=date,
    )

    r3xa.add_specimen_setting(
        title="Openhole sample",
        description="Glass-epoxy specimen",
        sizes=[
            unit(title="width", value=30.0, unit="mm", scale=1.0),
            unit(title="thickness", value=2.0, unit="mm", scale=1.0),
        ],
        patterning_technique="white background with black spray paint",
    )

    camera = r3xa.add_camera_source(
        title="CCD Camera",
        description="Encoding: 8-bit",
        output_components=1,
        output_dimension="surface",
        output_units=[unit(title="graylevel", value=1.0, unit="gl", scale=1.0)],
        manufacturer="Allied Vision Technologies (AVT)",
        model="Dolphin F-145B",
        image_size=[
            unit(title="width", value=1392, unit="px", scale=1.0),
            unit(title="height", value=1040, unit="px", scale=1.0),
        ],
        focal_length=unit(title="focal_length", value=25.0, unit="mm", scale=1.0),
        standoff_distance=unit(title="standoff", value=0.5, unit="m", scale=1.0),
    )

    image_files = [f"img_{index:04d}.tif" for index in range(num_frames)]
    timestamps = [round(index * dt_seconds, 6) for index in range(num_frames)]

    images = r3xa.add_image_set_list(
        title="graylevel images",
        description="raw images from CCD camera",
        path=image_path,
        file_type="image/tiff",
        data_sources=[camera["id"]],
        time_reference=unit(title="time_reference", value=0.0, unit="s", scale=1.0),
        timestamps=timestamps,
        data=image_files,
    )

    dic_source = r3xa.add_data_source(
        "data_sources/generic",
        title="DIC processing (pyxel)",
        description="2D DIC using pyxel",
        output_components=2,
        output_dimension="surface",
        output_units=[
            unit(title="ux", value=1.0, unit="mm", scale=1.0),
            unit(title="uy", value=1.0, unit="mm", scale=1.0),
        ],
        manufacturer="Pyxel",
        model="pyxel-2d",
        input_data_sets=[images["id"]],
    )

    dic_files = [f"dic_{index:04d}.csv" for index in range(num_frames)]
    r3xa.add_image_set_list(
        title="DIC displacement fields",
        description="ux, uy per frame",
        path=dic_path,
        file_type="text/csv",
        data_sources=[dic_source["id"]],
        time_reference=unit(title="time_reference", value=0.0, unit="s", scale=1.0),
        timestamps=timestamps,
        data=dic_files,
    )

    from_scratch_payload = r3xa.to_dict()
    return (from_scratch_payload,)


@app.cell
def _(mo):
    # Cell 7 — Initialize reactive states (uploaded payload + status callout state).
    get_uploaded_payload, set_uploaded_payload = mo.state(None)
    get_upload_status, set_upload_status = mo.state(
        (
            "No JSON uploaded. The notebook currently uses the from-scratch payload.",
            "info",
        )
    )
    return (
        get_upload_status,
        get_uploaded_payload,
        set_upload_status,
        set_uploaded_payload,
    )


@app.cell
def _(json, mo, set_upload_status, set_uploaded_payload, validate):
    # Cell 8 — Import/reset UI and file-upload callback with schema validation.
    def on_file_change(files):
        if not files:
            set_uploaded_payload(None)
            set_upload_status(
                (
                    "No JSON uploaded. The notebook currently uses the from-scratch payload.",
                    "info",
                )
            )
            return
        try:
            loaded_payload = json.loads(files[0].contents.decode("utf-8"))
            validate(loaded_payload)
            set_uploaded_payload(loaded_payload)
            set_upload_status((f"Loaded and validated `{files[0].name}`.", "success"))
        except Exception as exc:
            set_uploaded_payload(None)
            set_upload_status((f"Load/validation error: {exc}", "danger"))

    upload_json = mo.ui.file(
        filetypes=[".json"],
        multiple=False,
        kind="button",
        label="Load JSON from PC",
        on_change=on_file_change,
    )
    clear_loaded_json = mo.ui.run_button(
        label="Reset to from-scratch",
        kind="warn",
    )
    upload_panel = mo.vstack(
        [
            mo.md("## Import / Export"),
            mo.hstack([upload_json, clear_loaded_json], justify="start"),
        ]
    )
    upload_panel
    return (clear_loaded_json,)


@app.cell
def _(clear_loaded_json, set_upload_status, set_uploaded_payload):
    # Cell 9 — Handle "reset to from-scratch" action.
    if clear_loaded_json.value:
        set_uploaded_payload(None)
        set_upload_status(
            (
                "Reset done. The notebook now uses the from-scratch payload.",
                "info",
            )
        )
    return


@app.cell
def _(get_upload_status, mo):
    # Cell 10 — Render status feedback for upload/validation operations.
    status_message, status_kind = get_upload_status()
    status_view = mo.callout(status_message, kind=status_kind)
    status_view
    return


@app.cell
def _(from_scratch_payload, get_uploaded_payload):
    # Cell 11 — Select the payload currently used by preview/export/graph cells.
    uploaded_payload = get_uploaded_payload()
    active_payload = uploaded_payload if uploaded_payload is not None else from_scratch_payload
    payload_source = "uploaded JSON" if uploaded_payload is not None else "from-scratch builder"
    return active_payload, payload_source


@app.cell
def _(active_payload, json, mo, payload_source, validate):
    # Cell 12 — Validate active payload and show a JSON preview snippet.
    validate(active_payload)
    preview = json.dumps(active_payload, indent=2)
    payload_view = mo.vstack(
        [
            mo.callout(
                f"Active payload source: **{payload_source}** (validated against schema).",
                kind="success",
            ),
            mo.md(f"```json\n{preview[:8000]}\n```"),
        ]
    )
    payload_view
    return


@app.cell
def _(Path, active_payload, json, mo):
    # Cell 13 — Provide JSON download and optional repository save helper.
    json_text = json.dumps(active_payload, indent=2)

    def save_document(path: str = "examples/artifacts/dic_pipeline_notebook.json") -> str:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_text, encoding="utf-8")
        return str(output_path)

    export_view = mo.vstack(
        [
            mo.download(
                data=json_text,
                filename="dic_pipeline_notebook.json",
                mimetype="application/json",
                label="Export JSON to PC",
            ),
            mo.md(
                """
                Optional repository save helper:

                ```python
                save_document()
                # or
                save_document("examples/artifacts/dic_pipeline_notebook.json")
                ```
                """
            ),
        ]
    )
    export_view
    return


@app.cell
def _(
    Path,
    active_payload,
    generate_graph_button,
    generate_svg,
    mo,
):
    # Cell 14 — Build, display, and export the Graphviz SVG graph.
    view = None
    svg_path = Path("examples/artifacts/dic_pipeline_notebook.svg")
    graph_status_view = None

    if generate_graph_button.value:
        try:
            svg_bytes = generate_svg(active_payload)
            svg_text = svg_bytes.decode("utf-8")
            svg_path.parent.mkdir(parents=True, exist_ok=True)
            svg_path.write_bytes(svg_bytes)
            graph_status_view = mo.callout(f"Graph generated: `{svg_path}`", kind="success")
        except Exception as exc:
            graph_status_view = mo.callout(
                f"Graph generation error: {exc}\n\n"
                "Install Python package `graphviz` and ensure `dot` is available.",
                kind="danger",
            )
    if view is None and svg_path.exists():
        svg_bytes = svg_path.read_bytes()
        svg_text = svg_bytes.decode("utf-8")
        if graph_status_view is None:
            graph_status_view = mo.callout(f"Loaded existing graph: `{svg_path}`", kind="info")
        view = mo.vstack(
            [
                graph_status_view,
                mo.Html(
                    '<div style="width:100%; min-height:1200px; overflow:auto; '
                    'border:1px solid #d0d7de; border-radius:8px; padding:8px; background:white;">'
                    f"{svg_text}"
                    "</div>"
                ),
                mo.download(
                    data=svg_bytes,
                    filename="dic_pipeline_notebook.svg",
                    mimetype="image/svg+xml",
                    label="Save SVG to PC",
                ),
            ]
        )
    elif view is None:
        if graph_status_view is not None:
            view = graph_status_view
        else:
            view = mo.callout("Click **Generate Graphviz SVG** to build the graph.", kind="info")

    view
    return


@app.cell
def _(mo):
    # Cell 15 — Trigger button for graph generation (read by Cell 14).
    generate_graph_button = mo.ui.run_button(
        label="Generate Graphviz SVG",
        kind="success",
    )
    generate_graph_button
    return (generate_graph_button,)


if __name__ == "__main__":
    app.run()
