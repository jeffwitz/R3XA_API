from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict


def from_model(model: Any) -> Dict[str, Any]:
    """Convert supported item wrappers or Pydantic models to a plain dict."""

    if isinstance(model, Mapping):
        return dict(model)

    to_dict = getattr(model, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())

    model_dump = getattr(model, "model_dump", None)
    if callable(model_dump):
        return model_dump(exclude_none=True, mode="json")

    raise TypeError("from_model expects a Pydantic model instance, mapping, or object exposing to_dict().")
