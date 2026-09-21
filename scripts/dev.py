#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import shutil
import subprocess
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FULL_DEV_EXTRAS = ".[dev,docs,web,notebook,graph_nx]"
BUILD_BOOTSTRAP_PACKAGES = ("pip", "setuptools>=68", "wheel")
SCHEMA_RESOURCE = "r3xa_api/resources/schema.json"
MODELS_OUTPUT = "r3xa_api/models.py"
WEB_TEMPLATES = ROOT / "web" / "templates"
WEB_STATIC = ROOT / "web" / "static"


def model_codegen_command(python: str, output: str = MODELS_OUTPUT) -> tuple[str, ...]:
    """Return the datamodel-code-generator invocation that builds the typed models.

    `tests/test_models_sync.py` reuses this so the sync check cannot drift from
    the command developers actually run.
    """

    return (
        python,
        "-m",
        "datamodel_code_generator",
        "--input",
        SCHEMA_RESOURCE,
        "--input-file-type",
        "jsonschema",
        "--output",
        output,
        "--use-standard-collections",
        "--target-python-version",
        "3.10",
        "--field-constraints",
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--base-class",
        "r3xa_api.model_base.R3XAItem",
        "--class-name",
        "R3XADocument",
        "--disable-timestamp",
        "--no-use-union-operator",
        "--use-one-literal-as-default",
        "--force-optional",
    )


def _ensure_graphviz() -> Path:
    from r3xa_api.graphviz_setup import ensure_graphviz

    return ensure_graphviz()


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


def project_python() -> str:
    return _project_python()


class ShowPythonAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[override]
        print(project_python())
        parser.exit()


def _run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def _run_or_print(args: tuple[str, ...], *, dry_run: bool) -> None:
    if dry_run:
        print("+", " ".join(shlex.quote(arg) for arg in args))
        return
    _run(*args)


def cmd_generate_spec(_: argparse.Namespace) -> None:
    python = project_python()
    _run(
        python,
        "tools/generate_spec.py",
        "r3xa_api/resources/schema.json",
        "docs/specification.md",
    )


def cmd_build_docs(args: argparse.Namespace) -> None:
    python = project_python()
    cmd_generate_spec(args)
    _run(python, "-m", "sphinx", "-b", "html", "docs", "docs/_build/html")


def cmd_generate_models(_: argparse.Namespace) -> None:
    python = project_python()
    _run(*model_codegen_command(python))
    _run(python, "scripts/postprocess_models.py")


def cmd_generate_stubs(_: argparse.Namespace) -> None:
    _run(project_python(), "scripts/generate_core_stub.py")


def cmd_notebook_dic(args: argparse.Namespace) -> None:
    python = project_python()
    if args.ensure_graphviz:
        print(f"Graphviz is ready: {_ensure_graphviz()}")
    command = [
        python,
        "-m",
        "marimo",
        "edit",
        "examples/notebooks/dic_base_marimo.py",
    ]
    if args.port is not None:
        command.extend(["--port", str(args.port)])
    _run(*command)


def cmd_notebook_dic_export(_: argparse.Namespace) -> None:
    python = project_python()
    _run(
        python,
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
    python = project_python()
    if args.ensure_graphviz:
        print(f"Graphviz is ready: {_ensure_graphviz()}")
    if args.install:
        _run(python, "-m", "pip", "install", "-e", ".[web]")
    command = [
        python,
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


def _git_revision() -> str:
    try:
        return subprocess.check_output(
            ("git", "rev-parse", "HEAD"),
            cwd=ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _project_version() -> str:
    """Read the checkout version instead of trusting an installed distribution."""

    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"^version\s*=\s*[\"']([^\"']+)[\"']\s*$", text, re.MULTILINE)
    if match:
        return match.group(1)
    try:
        return package_version("r3xa-api")
    except PackageNotFoundError:
        return "development"


def _static_build_id() -> str:
    """Return a cache key that changes with the checked-out WebUI inputs."""

    digest = hashlib.sha256()
    inputs = [
        SCHEMA_RESOURCE,
        "scripts/dev.py",
        *sorted(str(path.relative_to(ROOT)) for path in WEB_STATIC.rglob("*" ) if path.is_file()),
        *sorted(
            str(path.relative_to(ROOT))
            for path in (ROOT / "r3xa_api" / "resources" / "ui").rglob("*")
            if path.is_file()
        ),
    ]
    for relative_path in inputs:
        path = ROOT / relative_path
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"{_git_revision()[:12]}-{digest.hexdigest()[:16]}"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_static_web(output_dir: Path) -> Path:
    """Build the schema/catalogue-backed static WebUI scaffold."""

    from jinja2 import Environment, FileSystemLoader
    from r3xa_api.schema import load_schema
    from r3xa_api.webcore import build_schema_catalog, build_schema_summary, build_ui_catalog
    from r3xa_api.webcore._graph_core import PALETTES

    if output_dir.exists():
        shutil.rmtree(output_dir)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True)
    shutil.copytree(
        WEB_STATIC,
        assets_dir,
        ignore=shutil.ignore_patterns("runtime.js", "graph-core.mjs", "graph-runtime.mjs"),
        dirs_exist_ok=True,
    )
    shutil.copy2(
        ROOT / "r3xa_api" / "resources" / "graphviz" / "graphviz-12.2.1.wasm",
        assets_dir / "graphviz-12.2.1.wasm",
    )

    schema = load_schema()
    schema_catalog = build_schema_catalog(schema)
    _write_json(assets_dir / "schema.json", schema)
    _write_json(assets_dir / "schema-catalog.json", schema_catalog)
    _write_json(assets_dir / "schema-summary.json", build_schema_summary(schema))
    _write_json(assets_dir / "ui-catalog.json", build_ui_catalog(schema_catalog))
    _write_json(assets_dir / "graph-palettes.json", PALETTES)
    build_id = _static_build_id()
    _write_json(
        assets_dir / "build-info.json",
        {
            "api_version": _project_version(),
            "schema_version": schema_catalog.get("schema_version"),
            "git_commit": _git_revision(),
            "build_id": build_id,
        },
    )
    node = shutil.which("node")
    if node is None:
        raise RuntimeError(
            "Node.js is required to build the static validator. "
            "Install Node.js and run `npm ci` in web/ first."
        )
    _run(
        node,
        "web/scripts/build-validator.mjs",
        SCHEMA_RESOURCE,
        str(assets_dir / "validator.generated.js"),
    )
    _run(
        node,
        "web/scripts/build-graph.mjs",
        "web/static/graph-runtime.mjs",
        str(assets_dir / "graph.generated.js"),
    )

    environment = Environment(loader=FileSystemLoader(str(WEB_TEMPLATES)))
    pages = {
        "index.html": ("index.html", ".", "."),
        "edit/index.html": ("edit.html", "..", ".."),
        "schema/index.html": ("schema.html", "..", ".."),
        "registry/index.html": ("registry.html", "..", ".."),
    }
    for relative_path, (template_name, static_base, app_base) in pages.items():
        destination = output_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            environment.get_template(template_name).render(
                app_start=build_id,
                app_base=app_base,
                runtime_name="runtime-static.js",
                static_base=f"{static_base}/assets" if static_base != "." else "assets",
            ),
            encoding="utf-8",
        )
    return output_dir


def cmd_build_static_web(args: argparse.Namespace) -> None:
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    build_static_web(output_dir)
    print(f"Static WebUI written to {output_dir}")


def cmd_test_static_web(args: argparse.Namespace) -> None:
    python = project_python()
    tests = (
        "tests/web/test_static_build.py",
        "tests/web/test_static_graph.py",
        "tests/web/test_static_parity.py",
        "tests/web/test_static_browser.py",
    )
    _run(python, "-m", "pytest", *tests, *args.pytest_args)


def cmd_serve_static_web(args: argparse.Namespace) -> None:
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    if not args.no_build:
        build_static_web(output_dir)
    python = project_python()
    _run(
        python,
        "-m",
        "http.server",
        str(args.port),
        "--bind",
        args.host,
        "--directory",
        str(output_dir),
    )


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
    python = project_python()
    steps: list[tuple[str, ...]] = []

    if args.graphviz_wasm == "source":
        steps.append((python, "tools/graphviz-wasi/build.py"))

    if not args.skip_install:
        steps.append(
            (
                python,
                "-m",
                "pip",
                "install",
                "--upgrade",
                *BUILD_BOOTSTRAP_PACKAGES,
            )
        )
        steps.append(
            (
                python,
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
            model_codegen_command(python),
            (python, "scripts/postprocess_models.py"),
            (python, "scripts/generate_core_stub.py"),
        ]
    )

    if args.build_docs:
        steps.extend(
            [
                (
                    python,
                    "tools/generate_spec.py",
                    "r3xa_api/resources/schema.json",
                    "docs/specification.md",
                ),
                (python, "-m", "sphinx", "-b", "html", "docs", "docs/_build/html"),
            ]
        )
    else:
        steps.append(
            (
                python,
                "tools/generate_spec.py",
                "r3xa_api/resources/schema.json",
                "docs/specification.md",
            )
        )

    for step in steps:
        _run_or_print(step, dry_run=args.dry_run)


def cmd_ensure_graphviz(_: argparse.Namespace) -> None:
    print(f"Graphviz is ready: {_ensure_graphviz()}")


def cmd_build_graphviz_wasm(args: argparse.Namespace) -> None:
    command = [project_python(), "tools/graphviz-wasi/build.py"]
    if args.graphviz_source:
        command.extend(["--graphviz-source", args.graphviz_source])
    if args.wasi_sdk:
        command.extend(["--wasi-sdk", args.wasi_sdk])
    if args.workdir:
        command.extend(["--workdir", args.workdir])
    if args.output:
        command.extend(["--output", args.output])
    _run(*command)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-platform developer commands for R3XA_API.",
    )
    parser.add_argument(
        "--python",
        nargs=0,
        action=ShowPythonAction,
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
        "--graphviz-wasm",
        choices=("bundled", "source"),
        default="bundled",
        help="use the committed WASM artifact (default) or rebuild it from pinned sources first",
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
    notebook_dic.add_argument(
        "--ensure-graphviz",
        action="store_true",
        help="install Graphviz with the platform package manager when dot is missing",
    )
    notebook_dic.set_defaults(func=cmd_notebook_dic)

    notebook_export = subparsers.add_parser("notebook-dic-export", help="export the Marimo notebook to static HTML")
    notebook_export.set_defaults(func=cmd_notebook_dic_export)

    run_web = subparsers.add_parser("run-web", help="launch the local FastAPI web UI")
    run_web.add_argument("--host", default="127.0.0.1", help="host interface for Uvicorn")
    run_web.add_argument("--port", type=int, default=8002, help="port for Uvicorn")
    run_web.add_argument("--app", default="web.app.main:app", help="ASGI application import path")
    run_web.add_argument("--no-reload", dest="reload", action="store_false", help="disable Uvicorn autoreload")
    run_web.add_argument("--install", action="store_true", help="install the web extra before launching the server")
    run_web.add_argument(
        "--ensure-graphviz",
        action="store_true",
        help="install Graphviz with the platform package manager when dot is missing",
    )
    run_web.set_defaults(func=cmd_run_web, reload=True)

    static_web = subparsers.add_parser(
        "build-static-web",
        help="build the schema-driven static WebUI distribution",
    )
    static_web.add_argument(
        "--output",
        default="dist/r3xa-webui",
        help="output directory, relative to the project root by default",
    )
    static_web.set_defaults(func=cmd_build_static_web)

    test_static_web = subparsers.add_parser(
        "test-static-web",
        help="run static build, graph, and browser tests",
    )
    test_static_web.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="additional arguments passed to pytest",
    )
    test_static_web.set_defaults(func=cmd_test_static_web)

    serve_static_web = subparsers.add_parser(
        "serve-static-web",
        help="build and serve the static WebUI without FastAPI",
    )
    serve_static_web.add_argument(
        "--output",
        default="dist/r3xa-webui",
        help="static site directory, relative to the project root by default",
    )
    serve_static_web.add_argument("--host", default="127.0.0.1", help="HTTP server bind address")
    serve_static_web.add_argument("--port", type=int, default=8080, help="HTTP server port")
    serve_static_web.add_argument(
        "--no-build",
        action="store_true",
        help="serve an existing static site without rebuilding it",
    )
    serve_static_web.set_defaults(func=cmd_serve_static_web)

    ensure_graphviz_command = subparsers.add_parser(
        "ensure-graphviz",
        help="install Graphviz with the platform package manager when dot is missing",
    )
    ensure_graphviz_command.set_defaults(func=cmd_ensure_graphviz)

    build_graphviz_wasm = subparsers.add_parser(
        "build-graphviz-wasm",
        help="rebuild the pinned Graphviz WASI module from source",
    )
    build_graphviz_wasm.add_argument(
        "--graphviz-source",
        help="existing checkout of the pinned Graphviz source",
    )
    build_graphviz_wasm.add_argument(
        "--wasi-sdk",
        help="existing WASI SDK installation",
    )
    build_graphviz_wasm.add_argument(
        "--workdir",
        default="build/graphviz-wasi",
        help="temporary build and download directory",
    )
    build_graphviz_wasm.add_argument(
        "--output",
        default="r3xa_api/resources/graphviz/graphviz-12.2.1.wasm",
        help="output WASM path",
    )
    build_graphviz_wasm.set_defaults(func=cmd_build_graphviz_wasm)

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
