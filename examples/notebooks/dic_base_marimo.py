import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    from pathlib import Path

    import marimo as mo

    from r3xa_api import R3XAFile, unit, validate
    from r3xa_api.webcore import generate_svg

    return Path, R3XAFile, generate_svg, json, mo, unit, validate


@app.cell
def _(mo):
    mo.md("""
    # Base DIC example (R3XA_API)

    This notebook reproduces the base DIC pipeline used in JC's presentation:
    camera acquisition -> image list -> DIC processing (`pyxel`) -> displacement fields.
    """)
    return


@app.cell
def _():
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
    upload_json = mo.ui.file(
        filetypes=[".json"],
        multiple=False,
        kind="button",
        label="Load JSON from PC",
    )
    mo.vstack([mo.md("## Import / Export"), upload_json])
    return (upload_json,)


@app.cell
def _(json, mo, upload_json, validate):
    uploaded_payload = None
    if upload_json.value:
        try:
            uploaded_payload = json.loads(upload_json.contents(0).decode("utf-8"))
            validate(uploaded_payload)
            mo.callout(
                f"Loaded and validated `{upload_json.name(0)}`.",
                kind="success",
            )
        except Exception as exc:
            mo.callout(f"Load/validation error: {exc}", kind="danger")
    else:
        mo.callout(
            "No JSON uploaded. The notebook currently uses the from-scratch payload.",
            kind="info",
        )
    return (uploaded_payload,)


@app.cell
def _(from_scratch_payload, uploaded_payload):
    active_payload = uploaded_payload if uploaded_payload is not None else from_scratch_payload
    payload_source = "uploaded JSON" if uploaded_payload is not None else "from-scratch builder"
    return active_payload, payload_source


@app.cell
def _(active_payload, json, mo, payload_source, validate):
    validate(active_payload)
    preview = json.dumps(active_payload, indent=2)
    mo.vstack(
        [
            mo.callout(
                f"Active payload source: **{payload_source}** (validated against schema).",
                kind="success",
            ),
            mo.md(f"```json\n{preview[:8000]}\n```"),
        ]
    )
    return


@app.cell
def _(Path, active_payload, json, mo):
    json_text = json.dumps(active_payload, indent=2)

    def save_document(path: str = "examples/artifacts/dic_pipeline_notebook.json") -> str:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_text, encoding="utf-8")
        return str(output_path)

    mo.vstack(
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
    return (save_document,)


@app.cell
def _(active_payload, generate_graph_button, generate_svg, mo):
    view = None

    if not generate_graph_button.value:
        view = mo.callout("Click **Generate Graphviz SVG** to build the graph.", kind="info")
    else:
        try:
            svg_bytes = generate_svg(active_payload)
        except Exception as exc:
            view = mo.callout(
                f"Graph generation error: {exc}\n\n"
                "Install Python package `graphviz` and system executable `dot`.",
                kind="danger",
            )
        else:
            view = mo.vstack(
                [
                    mo.Html(svg_bytes.decode("utf-8")),
                    mo.download(
                        data=svg_bytes,
                        filename="dic_pipeline_notebook.svg",
                        mimetype="image/svg+xml",
                        label="Export SVG to PC",
                    ),
                ]
            )

    view
    return


@app.cell
def _(mo):
    generate_graph_button = mo.ui.run_button(
        label="Generate Graphviz SVG",
        kind="success",
    )
    generate_graph_button
    return (generate_graph_button,)


if __name__ == "__main__":
    app.run()
