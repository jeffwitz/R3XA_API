# R3XA scientific cases

These cases are larger examples intended to be adapted to real experiments,
not minimal tutorials.

## Torsion experiment

`torsion/example.py` builds and validates a large-rotation torsion experiment
with a specimen, testing machine, sensors, camera, calibration images and
measurement datasets.

```bash
python examples/cases/torsion/example.py
```

The JSON document and Graphviz SVG are written to `examples/artifacts/`.
The equivalent MATLAB entry point writes
`examples/artifacts/torsion_experiment_matlab.json`.

## Qi Hu thermography

`qi_hu/example.py` builds and validates the IR/visible thermography pipeline
from scratch. The referenced image and field files are metadata paths; the
experimental data themselves are not distributed in this repository.

```bash
python examples/cases/qi_hu/example.py
```

The generated document and Graphviz SVG are written to
`examples/artifacts/qi_hu_tutorial.json` and
`examples/artifacts/graph_qi_hu_tutorial.svg`.
The MATLAB entry point writes `examples/artifacts/qi_hu_from_scratch_matlab.json`.

Each case also has a Jupyter notebook with the same construction split into
interactive sections, a Marimo conversion, and a MATLAB entry point. The
Python, Jupyter and Marimo versions validate the document and display the
Graphviz SVG inline. The Qi Hu MATLAB entry point is also available at the historical path
`examples/matlab/qi_hu_from_scratch.m`.
