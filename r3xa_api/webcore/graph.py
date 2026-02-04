from typing import Any, Dict, Iterable


STYLES = {
    "data_sources": {
        "initial": {
            "shape": "ellipse",
            "fillcolor": "white",
            "color": "lightgreen",
            "style": "filled",
            "penwidth": "4",
        },
        "intermediate": {
            "shape": "ellipse",
            "fillcolor": "lightblue",
            "color": "black",
            "style": "filled",
            "penwidth": "2",
        },
    },
    "data_sets": {
        "intermediate": {
            "shape": "box",
            "fillcolor": "lightgrey",
            "color": "black",
            "style": "filled",
            "penwidth": "2",
        },
        "final": {
            "shape": "box",
            "fillcolor": "#FFA07A",
            "color": "red",
            "style": "filled",
            "penwidth": "6",
        },
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


def generate_svg(data: Dict[str, Any]) -> bytes:
    try:
        from graphviz import Digraph
        from graphviz.backend import ExecutableNotFound
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("Graphviz is not installed.") from exc

    dot = Digraph(comment="R3XA graph", format="svg")
    dot.attr("node", margin="0.2,0.1")

    used_datasets = _compute_used_datasets(data)
    intermediate_sources = {s.get("id") for s in data.get("data_sources", []) if _get_input_data_sets(s)}

    for source in data.get("data_sources", []):
        is_intermediate = source.get("id") in intermediate_sources
        style = STYLES["data_sources"]["intermediate" if is_intermediate else "initial"]
        label = f"{source.get('title','')}\n({source.get('description','')})"
        dot.node(source["id"], label, **style)

    for dataset in data.get("data_sets", []):
        is_intermediate = dataset["id"] in used_datasets
        style = STYLES["data_sets"]["intermediate" if is_intermediate else "final"]
        label = f"{dataset.get('title','')}\n({dataset.get('description','')})"
        dot.node(dataset["id"], label, **style)

    for source in data.get("data_sources", []):
        for input_set in _get_input_data_sets(source):
            dot.edge(input_set, source["id"], **STYLES["edges"]["input"])

    for dataset in data.get("data_sets", []):
        for src in _get_data_sources(dataset):
            edge_style = (
                STYLES["edges"]["data_initial"] if src not in intermediate_sources else STYLES["edges"]["data"]
            )
            dot.edge(src, dataset["id"], **edge_style)

    try:
        return dot.pipe(format="svg")
    except ExecutableNotFound as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("Graphviz executable not found (dot).") from exc
