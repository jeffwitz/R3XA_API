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

## Files used
- Input JSON: `IR_Lagrangian_Qi_hu_valid.json` (outside repo)
- Graph tool: `examples/graph_r3xa.py`
- Output SVG: `examples/artifacts/graph_qi.svg`
