import argparse
import json
from pathlib import Path

from r3xa_api.webcore.graph import render_graphviz_file, render_pyvis_html


def main() -> None:
    """Generate Graphviz and PyVis outputs from an R3XA JSON payload."""

    base = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description="Generate R3XA graph (Graphviz + PyVis).")
    parser.add_argument(
        "--input",
        default=str(base / "examples" / "artifacts" / "dic_pipeline.json"),
        help="Path to R3XA JSON file (default: examples/artifacts/dic_pipeline.json)",
    )
    parser.add_argument(
        "--output",
        default=str(base / "examples" / "artifacts" / "graph_r3xa"),
        help="Output base path without extension",
    )
    parser.add_argument(
        "--dot",
        action="store_true",
        help="Export Graphviz DOT source alongside SVG",
    )
    args = parser.parse_args()

    json_path = Path(args.input)
    out_base = Path(args.output)
    out_base.parent.mkdir(parents=True, exist_ok=True)

    data = json.loads(json_path.read_text(encoding="utf-8"))

    svg_path = render_graphviz_file(data, out_base, export_dot=args.dot)
    html_path = render_pyvis_html(data, out_base)

    print(f"Graphviz SVG: {svg_path}")
    print(f"PyVis HTML: {html_path}")


if __name__ == "__main__":
    main()
