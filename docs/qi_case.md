# Qi case study (IR Lagrangian thermography)

This page documents the **Qi experimental case** and how it maps to R3XA concepts.

## Context
The Qi dataset is a complex experimental pipeline (IR + visible imaging, post‑processing, DIC‑like steps).

## Data flow (conceptual)
**IR camera → raw images → Lagrangian thermography processing → derived fields**  
This is represented as a **directed graph** using:
- `data_sources` (sensors / processing steps)
- `data_sets` (raw and derived data products)
- `input_data_sets` (what a source consumes)
- `data_sources` (what a dataset depends on)

## Graph (Qi example)
Below is the generated SVG graph for the Qi case:

![Qi data flow graph](../examples/artifacts/graph_qi.svg)

## How to generate the graph
The graph is generated with the `graph_r3xa.py` tool (Graphviz + PyVis backends).
To reproduce the Qi SVG:

```bash
. .venv/bin/activate
python examples/graph_r3xa.py \
  --input /home/jeff/Documents/R3XA_Data/Qi/IR_Lagrangian_Qi_hu_valid.json \
  --output examples/artifacts/graph_qi
```

This command creates:
- `examples/artifacts/graph_qi.svg` (Graphviz SVG)
- `examples/artifacts/graph_qi.html` (PyVis HTML, ignored by git)

## Graph semantics (colors & shapes)
The graph encodes **object types** and **data‑flow roles**:

### Data sources (ellipses)
- **Initial data sources** (no `input_data_sets`):  
  - **Shape**: ellipse  
  - **Fill**: white  
  - **Border**: light green  
  - **Pen width**: 4
- **Intermediate data sources** (consume datasets via `input_data_sets`):  
  - **Shape**: ellipse  
  - **Fill**: light blue  
  - **Border**: black  
  - **Pen width**: 2

### Data sets (rectangles)
- **Intermediate datasets** (used as input to a later source):  
  - **Shape**: box  
  - **Fill**: light grey  
  - **Border**: black  
  - **Pen width**: 2
- **Final datasets** (not used as input later):  
  - **Shape**: box  
  - **Fill**: salmon `#FFA07A`  
  - **Border**: red  
  - **Pen width**: 6

### Edges
- **Input flow** (`input_data_sets` → data_source): black
- **Output flow** (data_source → data_set): black  

These styles are defined in `examples/graph_r3xa.py` and shared across Graphviz and PyVis.

## Files used
- Input JSON: `IR_Lagrangian_Qi_hu_valid.json` (outside repo)
- Graph tool: `examples/graph_r3xa.py`
- Output SVG: `examples/artifacts/graph_qi.svg`
