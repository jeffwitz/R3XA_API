from __future__ import annotations

from typing import Any, Dict


def from_model(model: Any) -> Dict[str, Any]:
    """Convert a Pydantic model to a plain dict for the dict-based API."""

    if isinstance(model, dict):
        return dict(model)

    model_dump = getattr(model, "model_dump", None)
    if callable(model_dump):
        return model_dump(exclude_none=True, mode="json")

    raise TypeError("from_model expects a Pydantic model instance or dict.")
