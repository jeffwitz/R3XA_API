# How R3XA fits together

R3XA is a metadata layer for experimental and computational photomechanics.
A document describes the experiment, the devices and processing steps, and
where the resulting data can be found. It does not embed the experimental
files themselves.

## Three repositories, one contract

```text
R3XA_SPEC (JSON Schema)
        |
        +--> R3XA_API (Python SDK, generated models, validation, WebUI)
        |
        +--> R3XA_REGISTRY (shareable items validated against the schema)
```

[R3XA_SPEC](https://gitlab.com/photomechanics/R3XA_SPEC) owns the normative
JSON Schema. R3XA_API packages a byte-for-byte synchronised schema and derives
the Python models, documentation, browser catalogues, and browser validators
from it. [R3XA_REGISTRY](https://gitlab.com/photomechanics/R3XA_REGISTRY)
holds reusable items such as cameras, specimens, and dataset templates. The
`registry/` folder in R3XA_API is a small bundled example/test catalogue.

The schema determines whether a JSON document is structurally valid. The API
and browser add integrity checks, such as unique identifiers and references
to existing items. For exact fields and current kinds, consult the
[generated specification](specification.md), rather than examples from an
older schema.

## Document structure

A document has top-level metadata such as `title`, `authors`, `date`, and
`version`, followed by three collections:

- `settings`: specimen, testing machine, stereo rig, and other experimental
  context;
- `data_sources`: sensors and processing steps, such as cameras or DIC;
- `data_sets`: raw or derived outputs, file sequences, or tabular data.

Every collection item has a `kind` and an `id`. Relationships refer to
those IDs in JSON: for example, a dataset's `parent_data_sources` names
the sources that produced it. In Python the generated objects can hold direct
references to each other; `to_dict()` writes their IDs at the JSON boundary.
The WebUI edits the same JSON document in Guided, Advanced, and Expert views.

The graph represents both data flow and semantic context. Ellipses are data
sources, rectangles are data sets, and hexagons are settings. Solid edges
show data flow; dashed edges show configuration relationships such as a
setting attached to a source or a specimen mesh used for DIC. The Document
palette uses ochre, crimson, and teal; Classic remains available.

## Ways to work

- [Public static WebUI](web.md): edit, validate, and graph in the browser.
  User documents stay local to that browser; the site is published on
  GitLab Pages.
- [Python SDK](getting_started.md): create generated Pydantic objects with
  attribute completion, validate, plot, and save JSON.
- [MATLAB binding](matlab.md): generate R3XA JSON from MATLAB.
- [Registry editor](registry_web.md): prepare an individual reusable item.
  Items saved in browser storage are local and separate from the shareable
  `R3XA_REGISTRY` repository.

For a complete experimental example, see the [Qi Hu case study](qi_case.md).
For the exact public Python methods, see the [API reference](api.md).
