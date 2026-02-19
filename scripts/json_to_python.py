#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _read_json_text(path: Path) -> str:
    """Load and validate a JSON file, then return its raw text."""

    text = path.read_text(encoding="utf-8")
    json.loads(text)
    return text


def _sha256_text(text: str) -> str:
    """Return SHA-256 digest for UTF-8 text."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _generated_script(
    source_json_text: str,
    source_path: Path,
    source_sha256: str,
    default_output: str,
) -> str:
    """Build the Python source code that reproduces the JSON file."""

    return (
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n\n"
        "import argparse\n"
        "import hashlib\n"
        "from pathlib import Path\n\n"
        f"SOURCE_PATH = {source_path.as_posix()!r}\n"
        f"SOURCE_SHA256 = {source_sha256!r}\n"
        f"JSON_TEXT = {source_json_text!r}\n\n"
        "def write_json(output_path: Path) -> None:\n"
        "    \"\"\"Write the literal JSON payload to disk.\"\"\"\n"
        "    output_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    output_path.write_text(JSON_TEXT, encoding='utf-8')\n\n"
        "def verify_json(output_path: Path) -> None:\n"
        "    \"\"\"Ensure output is byte-identical to original JSON text.\"\"\"\n"
        "    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()\n"
        "    if digest != SOURCE_SHA256:\n"
        "        raise RuntimeError(\n"
        "            f'SHA mismatch for {output_path}: {digest} != {SOURCE_SHA256}'\n"
        "        )\n\n"
        "def parse_args() -> argparse.Namespace:\n"
        "    parser = argparse.ArgumentParser(\n"
        "        description='Generate the original JSON payload from a literal Python script.'\n"
        "    )\n"
        f"    parser.add_argument('--output', default={default_output!r}, help='Output JSON path')\n"
        "    parser.add_argument(\n"
        "        '--verify',\n"
        "        action='store_true',\n"
        "        help='Check byte-level identity against source SHA-256',\n"
        "    )\n"
        "    return parser.parse_args()\n\n"
        "def main() -> None:\n"
        "    args = parse_args()\n"
        "    output_path = Path(args.output)\n"
        "    write_json(output_path)\n"
        "    if args.verify:\n"
        "        verify_json(output_path)\n"
        "    print(f'Written: {output_path}')\n"
        "    if args.verify:\n"
        "        print(f'Verified SHA-256: {SOURCE_SHA256}')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the JSON-to-Python literal generator."""

    parser = argparse.ArgumentParser(
        description="Generate a Python script that reproduces a JSON file literally."
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
    """Entry point for literal JSON -> Python script generation."""

    args = parse_args()
    input_path = Path(args.input)
    output_script = Path(args.output_script)

    json_text = _read_json_text(input_path)
    digest = _sha256_text(json_text)
    script = _generated_script(
        source_json_text=json_text,
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
