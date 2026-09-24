# Validation

The [R3XA_SPEC](https://gitlab.com/photomechanics/R3XA_SPEC) JSON Schema
defines the allowed document structure, field types, and required fields for
each kind. R3XA_API also checks document integrity, including duplicate IDs,
references to missing items, and calendar dates. A structurally valid file
does not certify that illustrative values from a profile describe your actual
experiment.

## Complete documents

```python
from r3xa_api import R3XAFile

document = R3XAFile.load("experiment.json")
document.validate()  # returns None on success; raises on failure
```

The same validation is available from the static [WebUI](web.md), entirely in
the browser. Validate before saving or sharing the file, and inspect the
reported field paths when validation fails.

## Standalone items

An individual Registry item is checked against the definition for its
`kind` (for example `data_sources/camera`), without wrapping it in a fake
document. This permits reusable items to be validated before insertion into
an experiment. Use an item's `validate()` method in Python or the
[Registry editor](registry_web.md) in the browser.

## Common errors

- A field is missing even though the selected kind requires it.
- A number is written as a string, or a `kind` has the wrong constant value.
- Two items have the same `id`.
- A reference such as `parent_data_sources` names an absent item.
- The date matches `YYYY-MM-DD` textually but is not a real calendar date.

Check the [generated specification](specification.md) for exact current
requirements. Do not infer them from an old tutorial or an archived example.
