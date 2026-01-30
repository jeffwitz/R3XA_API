# Validation & Best Practices

## Why validation matters
R3XA is defined by a JSON Schema. Validation ensures:
- **Completeness**: required fields are present.
- **Consistency**: values and types match the schema.
- **Reproducibility**: others can reuse your data without guessing missing metadata.

## Two levels of validation
### 1) Full file validation
Use when you have a complete R3XA document:
```python
r3xa.validate()
```

### 2) Item (registry) validation
Use for reusable components stored in the registry:
```python
from r3xa_api import validate_item
validate_item(camera_item)
```
This checks against the **specific kind** schema (e.g. `data_sources/camera`) rather than the full R3XA schema.

## Best practices
- **Validate early**: validate items as soon as you define them (especially registry items).
- **Validate before publish**: run full validation before sharing or archiving.
- **Use registry items**: avoid duplicating camera, machine, and software descriptions.
- **Keep IDs stable**: change `id` only when the object is actually different.
- **Document units**: use `unit(...)` consistently for anything with scale/units.

## Common pitfalls
- Missing required fields (e.g., `image_size` for `data_sources/camera`).
- Wrong types (strings instead of numeric timestamps).
- Stale registry items (schema evolves; re‑validate periodically).
