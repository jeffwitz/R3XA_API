# Case study: Qi Hu thermography

The Qi Hu example describes a larger IR/visible imaging and thermography
pipeline. It demonstrates how R3XA connects acquisition devices, raw data,
processing steps, and derived fields without embedding the experimental
files. The source is maintained under
{glsrc}`examples/cases/qi_hu/`; earlier reconstructions are under
{glsrc}`examples/archive/`.

The document separates three questions:

1. **What was used?** Settings describe the specimen and experimental context.
2. **What produced the data?** Cameras and processing operations are
   `data_sources`.
3. **Where are the outputs?** Raw images and derived fields are `data_sets`.

`parent_data_sources` links a dataset to its producer, while
`input_data_sets` links a processing source to its inputs. Other schema
references describe context; the graph displays these alongside data flow.
For exact field definitions, see the
[generated specification](specification.md).

## Build the document and graph

With R3XA_API installed in the active environment, run from the repository
root:

```bash
python examples/cases/qi_hu/example.py
```

The script validates the document and writes
`examples/artifacts/qi_hu_tutorial.json` and
`examples/artifacts/graph_qi_hu_tutorial.svg`. Open the SVG in a browser to
inspect the complete graph. The referenced scientific file paths are
metadata; the experimental image and field data are not bundled here.

To step through the same construction interactively, open
{glsrc}`examples/cases/qi_hu/example.ipynb` in Jupyter or
{glsrc}`examples/cases/qi_hu/marimo/example.py` in Marimo. Both display the
graph inline; [Interactive tutorials](notebooks.md) explains how to start
their servers. MATLAB users can run
{glsrc}`examples/cases/qi_hu/example.m`.

The torsion case in {glsrc}`examples/cases/torsion/example.py` offers a
second complete workflow with a testing machine, sensors, camera, and
measurement datasets.
