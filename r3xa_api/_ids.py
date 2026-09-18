from __future__ import annotations

import secrets
import string


_SECTION_PREFIXES = {
    "settings": "stg",
    "data_sources": "src",
    "data_sets": "set",
}


def id_prefix(kind: str) -> str:
    """Return the canonical identifier prefix for a schema kind."""

    section, _, name = kind.partition("/")
    prefix = _SECTION_PREFIXES.get(section)
    if prefix is None or not name:
        return "r3xa"
    return f"{prefix}-{name}-"


def generate_id(kind: str, length: int = 12) -> str:
    """Generate a readable, section- and kind-specific R3XA identifier."""

    suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length))
    return f"{id_prefix(kind)}{suffix}"
