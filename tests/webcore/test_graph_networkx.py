import json
from pathlib import Path

import pytest

pytest.importorskip("networkx")
pytest.importorskip("matplotlib")

from r3xa_api.webcore.graph import render_networkx_matplotlib_file


def _load_example_payload() -> dict:
    root = Path(__file__).resolve().parents[2]
    payload_path = root / "examples" / "artifacts" / "dic_pipeline.json"
    return json.loads(payload_path.read_text(encoding="utf-8"))


def test_render_networkx_matplotlib_png(tmp_path: Path) -> None:
    payload = _load_example_payload()
    output_base = tmp_path / "graph_dic_pipeline_nx"

    output_path = render_networkx_matplotlib_file(payload, output_base, format="png", dpi=120)

    assert output_path.suffix == ".png"
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_render_networkx_matplotlib_invalid_format(tmp_path: Path) -> None:
    payload = _load_example_payload()
    output_base = tmp_path / "graph_dic_pipeline_nx"

    with pytest.raises(ValueError):
        render_networkx_matplotlib_file(payload, output_base, format="jpg", dpi=120)
