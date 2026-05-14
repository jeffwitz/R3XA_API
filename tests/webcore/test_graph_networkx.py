import json
from pathlib import Path

import pytest

pytest.importorskip("networkx")
pytest.importorskip("matplotlib")

from r3xa_api.webcore.graph import render_networkx_matplotlib_file


GRAPH_CASES = [
    ("dic_pipeline", "dic_pipeline.json"),
    ("qi_hu", "qi_hu_from_scratch.json"),
]


def _load_example_payload(filename: str) -> dict:
    root = Path(__file__).resolve().parents[2]
    payload_path = root / "examples" / "artifacts" / filename
    return json.loads(payload_path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(("case_name", "filename"), GRAPH_CASES)
def test_render_networkx_matplotlib_png(case_name: str, filename: str, tmp_path: Path) -> None:
    payload = _load_example_payload(filename)
    output_base = tmp_path / f"graph_{case_name}_nx"

    output_path = render_networkx_matplotlib_file(payload, output_base, format="png", dpi=120)

    assert output_path.suffix == ".png"
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_render_networkx_matplotlib_can_hide_descriptions(tmp_path: Path) -> None:
    payload = _load_example_payload("dic_pipeline.json")
    output_base = tmp_path / "graph_dic_pipeline_nx_hidden"

    output_path = render_networkx_matplotlib_file(
        payload,
        output_base,
        format="svg",
        dpi=120,
        include_description=False,
    )
    svg_text = output_path.read_text(encoding="utf-8")

    assert "raw images from CCD camera" not in svg_text
    assert "graylevel images" in svg_text


def test_render_networkx_matplotlib_invalid_format(tmp_path: Path) -> None:
    payload = _load_example_payload("dic_pipeline.json")
    output_base = tmp_path / "graph_dic_pipeline_nx"

    with pytest.raises(ValueError):
        render_networkx_matplotlib_file(payload, output_base, format="jpg", dpi=120)
