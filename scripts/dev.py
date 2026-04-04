#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FULL_DEV_EXTRAS = ".[dev,docs,typed,web,notebook,graph_nx]"
BUILD_BOOTSTRAP_PACKAGES = ("pip", "setuptools>=68", "wheel")


def _project_python() -> str:
    candidates = [
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise RuntimeError(
        "Project virtual environment not found at .venv. "
        "Create it first with `python -m venv .venv` and activate it."
    )


PYTHON = _project_python()


def _run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def _run_or_print(args: tuple[str, ...], *, dry_run: bool) -> None:
    if dry_run:
        print("+", " ".join(shlex.quote(arg) for arg in args))
        return
    _run(*args)


def cmd_generate_spec(_: argparse.Namespace) -> None:
    _run(
        PYTHON,
        "tools/generate_spec.py",
        "r3xa_api/resources/schema.json",
        "docs/specification.md",
    )


def cmd_build_docs(args: argparse.Namespace) -> None:
    cmd_generate_spec(args)
    _run(PYTHON, "-m", "sphinx", "-b", "html", "docs", "docs/_build/html")


def cmd_generate_models(_: argparse.Namespace) -> None:
    _run(
        PYTHON,
        "-m",
        "datamodel_code_generator",
        "--input",
        "r3xa_api/resources/schema.json",
        "--input-file-type",
        "jsonschema",
        "--output",
        "r3xa_api/models.py",
        "--use-standard-collections",
        "--target-python-version",
        "3.10",
        "--field-constraints",
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--class-name",
        "R3XADocument",
        "--disable-timestamp",
        "--no-use-union-operator",
    )
    _run(PYTHON, "scripts/postprocess_models.py")


def cmd_generate_stubs(_: argparse.Namespace) -> None:
    _run(PYTHON, "scripts/generate_core_stub.py")


def cmd_notebook_dic(args: argparse.Namespace) -> None:
    command = [
        PYTHON,
        "-m",
        "marimo",
        "edit",
        "examples/notebooks/dic_base_marimo.py",
    ]
    if args.port is not None:
        command.extend(["--port", str(args.port)])
    _run(*command)


def cmd_notebook_dic_export(_: argparse.Namespace) -> None:
    _run(
        PYTHON,
        "-m",
        "marimo",
        "export",
        "html",
        "examples/notebooks/dic_base_marimo.py",
        "-o",
        "docs/figures/dic_base_marimo/index.html",
        "--force",
    )


def cmd_run_web(args: argparse.Namespace) -> None:
    if args.install:
        _run(PYTHON, "-m", "pip", "install", "-e", ".[web]")
    command = [
        PYTHON,
        "-m",
        "uvicorn",
        args.app,
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.reload:
        command.append("--reload")
    _run(*command)


def cmd_clean_artifacts(_: argparse.Namespace) -> None:
    directories = [
        ROOT / "docs" / "_build",
        ROOT / "web" / "node_modules",
        ROOT / "build",
        ROOT / "dist",
        ROOT / ".pytest_cache",
        ROOT / ".mypy_cache",
        ROOT / ".ruff_cache",
        ROOT / "htmlcov",
    ]
    files = [ROOT / ".coverage"]

    for directory in directories:
        if directory.exists():
            shutil.rmtree(directory)

    for file_path in files:
        if file_path.exists():
            file_path.unlink()

    for cache_dir in ROOT.rglob("__pycache__"):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir)

    for compiled in ROOT.rglob("*.pyc"):
        compiled.unlink()
    for compiled in ROOT.rglob("*.pyo"):
        compiled.unlink()

    for egg_info in ROOT.rglob("*.egg-info"):
        if egg_info.is_dir():
            shutil.rmtree(egg_info)


def cmd_source_archive(_: argparse.Namespace) -> None:
    archive_dir = ROOT / "archives"
    archive_dir.mkdir(exist_ok=True)
    _run(
        "git",
        "archive",
        "--format=zip",
        "--output",
        str(archive_dir / "R3XA_API-source.zip"),
        "HEAD",
    )


def cmd_setup_dev(args: argparse.Namespace) -> None:
    steps: list[tuple[str, ...]] = []

    if not args.skip_install:
        steps.append(
            (
                PYTHON,
                "-m",
                "pip",
                "install",
                "--upgrade",
                *BUILD_BOOTSTRAP_PACKAGES,
            )
        )
        steps.append(
            (
                PYTHON,
                "-m",
                "pip",
                "install",
                "--no-build-isolation",
                "-e",
                args.extras,
            )
        )

    steps.extend(
        [
            (
                PYTHON,
                "-m",
                "datamodel_code_generator",
                "--input",
                "r3xa_api/resources/schema.json",
                "--input-file-type",
                "jsonschema",
                "--output",
                "r3xa_api/models.py",
                "--use-standard-collections",
                "--target-python-version",
                "3.10",
                "--field-constraints",
                "--output-model-type",
                "pydantic_v2.BaseModel",
                "--class-name",
                "R3XADocument",
                "--disable-timestamp",
                "--no-use-union-operator",
            ),
            (PYTHON, "scripts/postprocess_models.py"),
            (PYTHON, "scripts/generate_core_stub.py"),
        ]
    )

    if args.build_docs:
        steps.extend(
            [
                (
                    PYTHON,
                    "tools/generate_spec.py",
                    "r3xa_api/resources/schema.json",
                    "docs/specification.md",
                ),
                (PYTHON, "-m", "sphinx", "-b", "html", "docs", "docs/_build/html"),
            ]
        )
    else:
        steps.append(
            (
                PYTHON,
                "tools/generate_spec.py",
                "r3xa_api/resources/schema.json",
                "docs/specification.md",
            )
        )

    for step in steps:
        _run_or_print(step, dry_run=args.dry_run)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-platform developer commands for R3XA_API.",
    )
    parser.add_argument(
        "--python",
        action="version",
        version=PYTHON,
        help="show the Python interpreter used by the task runner",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_spec = subparsers.add_parser("generate-spec", help="regenerate docs/specification.md from the packaged schema")
    generate_spec.set_defaults(func=cmd_generate_spec)

    build_docs = subparsers.add_parser("build-docs", help="regenerate the spec page and build Sphinx HTML docs")
    build_docs.set_defaults(func=cmd_build_docs)

    generate_models = subparsers.add_parser("generate-models", help="regenerate typed Pydantic models from the packaged schema")
    generate_models.set_defaults(func=cmd_generate_models)

    generate_stubs = subparsers.add_parser("generate-stubs", help="regenerate the IDE/type-checker stub for guided helpers")
    generate_stubs.set_defaults(func=cmd_generate_stubs)

    setup_dev = subparsers.add_parser(
        "setup-dev",
        help="install the full contributor stack and regenerate schema-derived artifacts",
    )
    setup_dev.add_argument(
        "--extras",
        default=FULL_DEV_EXTRAS,
        help=f'editable extras set to install first (default: "{FULL_DEV_EXTRAS}")',
    )
    setup_dev.add_argument(
        "--skip-install",
        action="store_true",
        help="skip the editable pip install step and only regenerate derived artifacts",
    )
    setup_dev.add_argument(
        "--no-build-docs",
        dest="build_docs",
        action="store_false",
        help="regenerate docs/specification.md but skip the full Sphinx HTML build",
    )
    setup_dev.add_argument(
        "--dry-run",
        action="store_true",
        help="print the planned bootstrap commands without executing them",
    )
    setup_dev.set_defaults(func=cmd_setup_dev, build_docs=True)

    notebook_dic = subparsers.add_parser("notebook-dic", help="launch the interactive Marimo DIC notebook")
    notebook_dic.add_argument("--port", type=int, default=None, help="optional Marimo port override")
    notebook_dic.set_defaults(func=cmd_notebook_dic)

    notebook_export = subparsers.add_parser("notebook-dic-export", help="export the Marimo notebook to static HTML")
    notebook_export.set_defaults(func=cmd_notebook_dic_export)

    run_web = subparsers.add_parser("run-web", help="launch the local FastAPI web UI")
    run_web.add_argument("--host", default="127.0.0.1", help="host interface for Uvicorn")
    run_web.add_argument("--port", type=int, default=8002, help="port for Uvicorn")
    run_web.add_argument("--app", default="web.app.main:app", help="ASGI application import path")
    run_web.add_argument("--no-reload", dest="reload", action="store_false", help="disable Uvicorn autoreload")
    run_web.add_argument("--install", action="store_true", help="install the web extra before launching the server")
    run_web.set_defaults(func=cmd_run_web, reload=True)

    clean = subparsers.add_parser("clean-artifacts", help="remove build products, caches, and generated artifacts")
    clean.set_defaults(func=cmd_clean_artifacts)

    archive = subparsers.add_parser("source-archive", help="create archives/R3XA_API-source.zip from tracked files")
    archive.set_defaults(func=cmd_source_archive)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
