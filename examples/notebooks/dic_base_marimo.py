import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    # Cell 1 — Shared imports and symbols used by downstream cells.
    import base64
    import html as html_std
    import json
    import re
    from pathlib import Path

    import marimo as mo

    from r3xa_api import R3XAFile, unit, validate
    from r3xa_api.webcore.graph import render_pyvis_html

    return Path, R3XAFile, base64, html_std, json, mo, re, render_pyvis_html, unit, validate


@app.cell
def _(mo):
    # Cell 2 — Notebook title and high-level objective.
    intro = mo.md("""
    # Base DIC example (R3XA_API)

    This notebook reproduces the base DIC pipeline used in JC's presentation:
    camera acquisition -> image list -> DIC processing (`pyxel`) -> displacement fields.
    """)
    intro
    return


@app.cell
def _():
    # Cell 3 — Editable experiment parameters (single place to customize the demo).
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
def _(mo):
    # Cell 4 — Human-readable guide: what each notebook cell does.
    cell_map = mo.md("""
    ## Notebook cell map

    1. **Imports**: load Python modules and R3XA API helpers.
    2. **Intro**: describe the base DIC workflow.
    3. **Parameters**: editable metadata, paths, and frame settings.
    4. **Cell map**: this guide.
    5. **Build payload**: create a full R3XA document from scratch.
    6. **UI state**: initialize uploaded payload and status message.
    7. **Import UI**: upload/reset controls and JSON validation callback.
    8. **Reset action**: apply reset when requested.
    9. **Status view**: display current import/validation state.
    10. **Active payload**: choose uploaded vs generated payload.
    11. **Preview**: validate and show JSON excerpt.
    12. **Export JSON**: download JSON + repository save helper.
    13. **Graph rendering**: generate and embed the PyVis graph.
    14. **Graph trigger**: button used to trigger graph generation.
    """)
    cell_map
    return


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
    # Cell 5 — Build a complete R3XA payload from scratch using the API.
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
    # Cell 6 — Initialize reactive states (uploaded payload + status callout state).
    get_uploaded_payload, set_uploaded_payload = mo.state(None)
    get_upload_status, set_upload_status = mo.state(
        (
            "No JSON uploaded. The notebook currently uses the from-scratch payload.",
            "info",
        )
    )
    return get_upload_status, get_uploaded_payload, set_upload_status, set_uploaded_payload


@app.cell
def _(json, mo, set_upload_status, set_uploaded_payload, validate):
    # Cell 7 — Import/reset UI and file-upload callback with schema validation.
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
    return clear_loaded_json, upload_json


@app.cell
def _(clear_loaded_json, set_upload_status, set_uploaded_payload):
    # Cell 8 — Handle "reset to from-scratch" action.
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
    # Cell 9 — Render status feedback for upload/validation operations.
    status_message, status_kind = get_upload_status()
    status_view = mo.callout(status_message, kind=status_kind)
    status_view
    return


@app.cell
def _(from_scratch_payload, get_uploaded_payload):
    # Cell 10 — Select the payload currently used by preview/export/graph cells.
    uploaded_payload = get_uploaded_payload()
    active_payload = uploaded_payload if uploaded_payload is not None else from_scratch_payload
    payload_source = "uploaded JSON" if uploaded_payload is not None else "from-scratch builder"
    return active_payload, payload_source


@app.cell
def _(active_payload, json, mo, payload_source, validate):
    # Cell 11 — Validate active payload and show a JSON preview snippet.
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
    # Cell 12 — Provide JSON download and optional repository save helper.
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
    return (save_document,)


@app.cell
def _(Path, active_payload, base64, generate_graph_button, html_std, mo, re, render_pyvis_html):
    # Cell 13 — Build, display, and export the interactive PyVis HTML graph.
    view = None

    if not generate_graph_button.value:
        view = mo.callout("Click **Generate PyVis HTML graph** to build the graph.", kind="info")
    else:
        try:
            html_path = render_pyvis_html(
                active_payload,
                Path("examples/artifacts/dic_pipeline_notebook_pyvis"),
            )
            html_text = html_path.read_text(encoding="utf-8")
            height_match = re.search(
                r"#mynetwork\s*\{[^}]*?height:\s*([0-9]+)px",
                html_text,
                flags=re.IGNORECASE | re.DOTALL,
            )
            iframe_height_value = max(1400, int(height_match.group(1)) + 220) if height_match else 1800
            iframe_height = f"{iframe_height_value}px"
            html_srcdoc = html_std.escape(html_text, quote=True)
            html_data_url = "data:text/html;base64," + base64.b64encode(
                html_text.encode("utf-8")
            ).decode("ascii")
        except Exception as exc:
            view = mo.callout(
                f"Graph generation error: {exc}\n\n"
                "Install Python package `pyvis`.",
                kind="danger",
            )
        else:
            view = mo.vstack(
                [
                    mo.callout(f"Graph generated: `{html_path}`", kind="success"),
                    mo.Html(
                        f'<a href="{html_data_url}" target="_blank" rel="noopener noreferrer">'
                        "Open graph in new tab"
                        "</a>"
                    ),
                    mo.Html(
                        f'<div style="width:100%; min-height:{iframe_height}; height:{iframe_height};">'
                        f'<iframe srcdoc="{html_srcdoc}" width="100%" height="{iframe_height}" '
                        'frameborder="0" '
                        f'style="display:block; width:100%; height:{iframe_height}; border:0;"></iframe>'
                        "</div>"
                    ),
                    mo.download(
                        data=html_text,
                        filename="dic_pipeline_notebook_pyvis.html",
                        mimetype="text/html",
                        label="Export graph HTML to PC",
                    ),
                ]
            )

    view
    return


@app.cell
def _(mo):
    # Cell 14 — Trigger button for graph generation (read by Cell 13).
    generate_graph_button = mo.ui.run_button(
        label="Generate PyVis HTML graph",
        kind="success",
    )
    generate_graph_button
    return (generate_graph_button,)


if __name__ == "__main__":
    app.run()
