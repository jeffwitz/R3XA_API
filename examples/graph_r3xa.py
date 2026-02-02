import argparse
import json
from pathlib import Path
from typing import Dict, Any, Iterable


STYLES = {
    "data_sources": {
        "initial": {"shape": "ellipse", "fillcolor": "white", "color": "lightgreen", "style": "filled", "penwidth": "4"},
        "intermediate": {"shape": "ellipse", "fillcolor": "lightblue", "color": "black", "style": "filled", "penwidth": "2"},
    },
    "data_sets": {
        "intermediate": {"shape": "box", "fillcolor": "lightgrey", "color": "black", "style": "filled", "penwidth": "2"},
        "final": {"shape": "box", "fillcolor": "#FFA07A", "color": "red", "style": "filled", "penwidth": "6"},
    },
    "edges": {
        "data_initial": {"color": "black"},
        "data": {"color": "black"},
        "input": {"color": "black"},
    },
}


def _get_input_data_sets(source: Dict[str, Any]) -> Iterable[str]:
    value = source.get("input_data_sets")
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    if isinstance(value, dict):
        return [v for v in value.values() if v]
    return []


def _get_data_sources(dataset: Dict[str, Any]) -> Iterable[str]:
    value = dataset.get("data_sources")
    if value is None and "data_source" in dataset:
        value = dataset.get("data_source")
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    return [value]


def _compute_used_datasets(data: Dict[str, Any]) -> set[str]:
    used = set()
    for source in data.get("data_sources", []):
        for ds_id in _get_input_data_sets(source):
            used.add(ds_id)
    return used


def _convert_styles_to_pyvis(graphviz_styles: Dict[str, Any]) -> Dict[str, Any]:
    pyvis_styles: Dict[str, Any] = {"data_sources": {}, "data_sets": {}, "edges": {}}

    for node_type in ["data_sources", "data_sets"]:
        for status, style_attrs in graphviz_styles[node_type].items():
            pyvis_style = {
                "borderWidth": int(style_attrs.get("penwidth", 2)),
                "color": {
                    "border": style_attrs.get("color", "black"),
                    "background": style_attrs.get("fillcolor", "lightgrey"),
                },
                "shape": style_attrs.get("shape", "ellipse"),
            }
            pyvis_styles[node_type][status] = pyvis_style

    for edge_type, style_attrs in graphviz_styles["edges"].items():
        pyvis_styles["edges"][edge_type] = {"color": style_attrs.get("color", "black")}

    return pyvis_styles


def _graphviz_backend(data: Dict[str, Any], output_path: Path) -> Path:
    from graphviz import Digraph

    dot = Digraph(comment="R3XA graph", format="svg")
    dot.attr("node", margin="0.2,0.1")
    styles = STYLES

    used_datasets = _compute_used_datasets(data)
    intermediate_sources = {s.get("id") for s in data.get("data_sources", []) if _get_input_data_sets(s)}

    for source in data.get("data_sources", []):
        is_intermediate = source.get("id") in intermediate_sources
        style = styles["data_sources"]["intermediate" if is_intermediate else "initial"]
        label = f"{source.get('title','')}\n({source.get('description','')})"
        dot.node(source["id"], label, **style)

    for dataset in data.get("data_sets", []):
        is_intermediate = dataset["id"] in used_datasets
        style = styles["data_sets"]["intermediate" if is_intermediate else "final"]
        label = f"{dataset.get('title','')}\n({dataset.get('description','')})"
        dot.node(dataset["id"], label, **style)

    for source in data.get("data_sources", []):
        for input_set in _get_input_data_sets(source):
            dot.edge(input_set, source["id"], **styles["edges"]["input"])

    for dataset in data.get("data_sets", []):
        for src in _get_data_sources(dataset):
            edge_style = styles["edges"]["data_initial"] if src not in intermediate_sources else styles["edges"]["data"]
            dot.edge(src, dataset["id"], **edge_style)

    return Path(dot.render(str(output_path), view=False))


def _pyvis_backend(data: Dict[str, Any], output_path: Path) -> Path:
    from pyvis.network import Network

    net = Network(height="900px", width="1000px", directed=True)
    net.set_options(
        """
        {
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -3000,
              "centralGravity": 0.2,
              "springLength": 2,
              "springConstant": 0.003,
              "damping": 0.09,
              "avoidOverlap": 0
            },
            "solver": "barnesHut"
          }
        }
        """
    )

    styles = _convert_styles_to_pyvis(STYLES)
    used_datasets = _compute_used_datasets(data)
    intermediate_sources = {s.get("id") for s in data.get("data_sources", []) if _get_input_data_sets(s)}

    for source in data.get("data_sources", []):
        is_intermediate = source.get("id") in intermediate_sources
        style = styles["data_sources"]["intermediate" if is_intermediate else "initial"]
        label = f"{source.get('title','')}\n({source.get('description','')})"
        net.add_node(source["id"], label=label, **style)

    for dataset in data.get("data_sets", []):
        is_intermediate = dataset["id"] in used_datasets
        style = styles["data_sets"]["intermediate" if is_intermediate else "final"]
        label = f"{dataset.get('title','')}\n({dataset.get('description','')})"
        net.add_node(dataset["id"], label=label, **style)

    for source in data.get("data_sources", []):
        for input_set in _get_input_data_sets(source):
            net.add_edge(input_set, source["id"], **styles["edges"]["input"])

    for dataset in data.get("data_sets", []):
        for src in _get_data_sources(dataset):
            edge_style = styles["edges"]["data_initial"] if src not in intermediate_sources else styles["edges"]["data"]
            net.add_edge(src, dataset["id"], **edge_style)

    out = output_path.with_suffix(".html")
    net.write_html(str(out))
    return out


def main() -> None:
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
    args = parser.parse_args()

    json_path = Path(args.input)
    out_base = Path(args.output)
    out_base.parent.mkdir(parents=True, exist_ok=True)

    data = json.loads(json_path.read_text(encoding="utf-8"))

    svg_path = _graphviz_backend(data, out_base)
    html_path = _pyvis_backend(data, out_base)

    print(f"Graphviz SVG: {svg_path}")
    print(f"PyVis HTML: {html_path}")


if __name__ == "__main__":
    main()
