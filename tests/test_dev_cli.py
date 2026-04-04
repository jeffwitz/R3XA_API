from __future__ import annotations

import io
import importlib.util
import shlex
from contextlib import redirect_stdout
from pathlib import Path

import pytest


def _load_dev_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "dev.py"
    spec = importlib.util.spec_from_file_location("r3xa_dev_cli", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_project_root(tmp_path: Path, *, windows: bool = False) -> tuple[Path, Path]:
    root = tmp_path / "project"
    script_dir = root / "scripts"
    script_dir.mkdir(parents=True)
    script_path = script_dir / "dev.py"
    script_path.write_text("# placeholder", encoding="utf-8")

    if windows:
        python_path = root / ".venv" / "Scripts" / "python.exe"
    else:
        python_path = root / ".venv" / "bin" / "python"

    python_path.parent.mkdir(parents=True)
    python_path.write_text("", encoding="utf-8")
    python_path.chmod(0o755)
    return root, python_path


def test_dev_cli_exposes_cross_platform_commands():
    module = _load_dev_module()
    parser = module.build_parser()
    subparsers = next(
        action for action in parser._actions if getattr(action, "choices", None)
    )
    commands = set(subparsers.choices)

    assert {
        "build-docs",
        "generate-models",
        "generate-spec",
        "generate-stubs",
        "setup-dev",
        "notebook-dic",
        "notebook-dic-export",
        "run-web",
        "clean-artifacts",
        "source-archive",
    }.issubset(commands)


def test_dev_cli_uses_a_real_python_interpreter(tmp_path: Path):
    module = _load_dev_module()
    original_root = module.ROOT
    fake_root, fake_python = _fake_project_root(tmp_path)
    module.ROOT = fake_root

    try:
        python_path = Path(module.project_python())
        assert python_path == fake_python
        assert python_path.exists()
        assert python_path.is_file()
        assert ".venv" in python_path.parts
    finally:
        module.ROOT = original_root


def test_dev_cli_parser_does_not_require_a_venv(tmp_path: Path):
    module = _load_dev_module()
    original_root = module.ROOT
    module.ROOT = tmp_path

    try:
        parser = module.build_parser()
        assert parser is not None
        with pytest.raises(RuntimeError, match="Project virtual environment not found"):
            module.project_python()
    finally:
        module.ROOT = original_root


def test_dev_cli_can_resolve_a_fake_project_python(tmp_path: Path):
    module = _load_dev_module()
    original_root = module.ROOT
    fake_root, fake_python = _fake_project_root(tmp_path)
    module.ROOT = fake_root

    try:
        assert Path(module.project_python()) == fake_python
    finally:
        module.ROOT = original_root


def test_setup_dev_dry_run_prints_bootstrap_plan(tmp_path: Path):
    module = _load_dev_module()
    original_root = module.ROOT
    fake_root, fake_python = _fake_project_root(tmp_path)
    module.ROOT = fake_root
    stdout = io.StringIO()

    try:
        with redirect_stdout(stdout):
            exit_code = module.main(["setup-dev", "--dry-run"])

        output = stdout.getvalue()
        bootstrap_line = " ".join(
            shlex.quote(part)
            for part in (
                str(fake_python),
                "-m",
                "pip",
                "install",
                "--upgrade",
                *module.BUILD_BOOTSTRAP_PACKAGES,
            )
        )
        install_line = " ".join(
            shlex.quote(part)
            for part in (
                str(fake_python),
                "-m",
                "pip",
                "install",
                "--no-build-isolation",
                "-e",
                module.FULL_DEV_EXTRAS,
            )
        )

        assert exit_code == 0
        assert bootstrap_line in output
        assert install_line in output
        assert "datamodel_code_generator" in output
        assert "scripts/postprocess_models.py" in output
        assert "scripts/generate_core_stub.py" in output
        assert "tools/generate_spec.py" in output
        assert "-m sphinx -b html docs docs/_build/html" in output
    finally:
        module.ROOT = original_root
