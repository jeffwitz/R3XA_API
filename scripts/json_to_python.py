#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import keyword
import re
from pathlib import Path
from pprint import pformat
from typing import Any


def _read_json_payload(path: Path) -> tuple[dict[str, Any], str]:
    """Load a JSON payload as dict and preserve original source text."""

    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected top-level JSON object in {path}")
    return payload, text


def _sha256_text(text: str) -> str:
    """Return SHA-256 digest for UTF-8 text."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_payload(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Split full document into header and collection sections."""

    header = {k: v for k, v in payload.items() if k not in {"settings", "data_sources", "data_sets"}}
    settings = list(payload.get("settings", []))
    data_sources = list(payload.get("data_sources", []))
    data_sets = list(payload.get("data_sets", []))
    return header, settings, data_sources, data_sets


def _py_literal(value: Any) -> str:
    """Format Python literals while preserving insertion order."""

    return pformat(value, width=100, sort_dicts=False)


def _safe_name(raw: str) -> str:
    """Convert arbitrary text into a stable Python identifier fragment."""

    name = re.sub(r"[^0-9a-zA-Z]+", "_", raw).strip("_").lower()
    if not name:
        return "item"
    if name[0].isdigit():
        return f"item_{name}"
    return name


def _item_var_name(
    prefix: str,
    item: dict[str, Any],
    index: int,
    used_names: set[str],
) -> str:
    """Build a unique variable name for a generated payload block."""

    item_id = item.get("id")
    base = _safe_name(item_id) if isinstance(item_id, str) and item_id.strip() else f"item_{index + 1}"
    candidate = f"{prefix}_{base}"
    suffix = 2
    while candidate in used_names:
        candidate = f"{prefix}_{base}_{suffix}"
        suffix += 1
    used_names.add(candidate)
    return candidate


def _is_valid_kwarg_name(name: str) -> bool:
    """Return True when a key can be emitted as a Python keyword argument."""

    return name.isidentifier() and not keyword.iskeyword(name)


def _indent_literal(text: str, spaces: int = 4) -> str:
    """Indent multi-line literals for nicer generated source."""

    prefix = " " * spaces
    return text.replace("\n", f"\n{prefix}")


def _emit_kwarg_line(lines: list[str], key: str, value: Any) -> None:
    """Emit one function argument line."""

    literal = _indent_literal(_py_literal(value), spaces=4)
    if _is_valid_kwarg_name(key):
        lines.append(f"    {key}={literal},\n")
        return
    lines.append(f"    **{{{key!r}: {literal}}},\n")


def _emit_r3xa_constructor(lines: list[str], header: dict[str, Any]) -> None:
    """Emit explicit `R3XAFile(...)` constructor arguments."""

    lines.append("r3xa = R3XAFile(\n")
    if "version" in header:
        _emit_kwarg_line(lines, "version", header["version"])
    for key, value in header.items():
        if key == "version":
            continue
        _emit_kwarg_line(lines, key, value)
    lines.append(")\n\n")


def _emit_items(
    lines: list[str],
    title: str,
    items: list[dict[str, Any]],
    prefix: str,
    add_method: str,
) -> None:
    """Append one-by-one generation blocks for a section."""

    lines.append(f"# {title}\n")
    if not items:
        lines.append("# None\n\n")
        return

    used_names: set[str] = set()
    for index, item in enumerate(items):
        var_name = _item_var_name(prefix=prefix, item=item, index=index, used_names=used_names)
        kind = item.get("kind")
        if not isinstance(kind, str) or not kind:
            raise ValueError(f"Missing/invalid kind for item #{index + 1} in section '{title}'")

        lines.append(f"{var_name} = r3xa.{add_method}(\n")
        lines.append(f"    {kind!r},\n")
        for key, value in item.items():
            if key == "kind":
                continue
            _emit_kwarg_line(lines, key, value)
        lines.append(")\n\n")


def _generated_script(
    payload: dict[str, Any],
    source_path: Path,
    source_sha256: str,
    default_output: str,
) -> str:
    """Build Python source that recreates the document through explicit R3XA API calls."""

    header, settings, data_sources, data_sets = _split_payload(payload)

    lines = [
        "#!/usr/bin/env python3\n",
        "from __future__ import annotations\n\n",
        "import argparse\n",
        "import hashlib\n",
        "from pathlib import Path\n\n",
        "from r3xa_api import R3XAFile\n\n",
        f"SOURCE_PATH = {source_path.as_posix()!r}\n",
        f"SOURCE_SHA256 = {source_sha256!r}\n",
        f"DEFAULT_OUTPUT = {default_output!r}\n\n",
        "parser = argparse.ArgumentParser(\n",
        "    description='Generate R3XA JSON with explicit R3XAFile add_* calls.'\n",
        ")\n",
        "parser.add_argument('--output', default=DEFAULT_OUTPUT, help='Output JSON path')\n",
        "parser.add_argument('--skip-verify', action='store_true', help='Skip SHA-256 check')\n",
        "args = parser.parse_args()\n\n",
        "output_path = Path(args.output)\n",
        "output_path.parent.mkdir(parents=True, exist_ok=True)\n\n",
    ]

    _emit_r3xa_constructor(lines=lines, header=header)
    _emit_items(
        lines=lines,
        title="Settings",
        items=settings,
        prefix="setting",
        add_method="add_setting",
    )
    _emit_items(
        lines=lines,
        title="Data sources",
        items=data_sources,
        prefix="data_source",
        add_method="add_data_source",
    )
    _emit_items(
        lines=lines,
        title="Data sets",
        items=data_sets,
        prefix="data_set",
        add_method="add_data_set",
    )

    lines.extend(
        [
            "r3xa.validate()\n",
            "r3xa.save(output_path.as_posix(), indent=4)\n",
            "print(f'Written: {output_path}')\n\n",
            "if not args.skip_verify:\n",
            "    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()\n",
            "    if digest != SOURCE_SHA256:\n",
            "        raise RuntimeError(f'SHA mismatch for {output_path}: {digest} != {SOURCE_SHA256}')\n",
            "    print(f'Verified SHA-256: {SOURCE_SHA256}')\n",
        ]
    )
    return "".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the JSON-to-Python generator."""

    parser = argparse.ArgumentParser(
        description="Generate a Python script that reproduces a JSON file with explicit R3XA API calls."
    )
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--output-script", required=True, help="Output Python script path")
    parser.add_argument(
        "--default-output",
        default="generated_from_literal.json",
        help="Default output path embedded in generated script",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for JSON -> Python generator."""

    args = parse_args()
    input_path = Path(args.input)
    output_script = Path(args.output_script)

    payload, json_text = _read_json_payload(input_path)
    digest = _sha256_text(json_text)
    script = _generated_script(
        payload=payload,
        source_path=input_path,
        source_sha256=digest,
        default_output=args.default_output,
    )

    output_script.parent.mkdir(parents=True, exist_ok=True)
    output_script.write_text(script, encoding="utf-8")
    output_script.chmod(0o775)
    print(f"Generated script: {output_script}")
    print(f"Source SHA-256: {digest}")


if __name__ == "__main__":
    main()
