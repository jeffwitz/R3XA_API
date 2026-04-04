from __future__ import annotations

import io
import importlib.util
import shlex
from contextlib import redirect_stdout
from pathlib import Path


def _load_dev_module():
    script_path = Path("scripts/dev.py")
    spec = importlib.util.spec_from_file_location("r3xa_dev_cli", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_dev_cli_uses_a_real_python_interpreter():
    module = _load_dev_module()
    python_path = Path(module.PYTHON)

    assert python_path.exists()
    assert python_path.is_file()
    assert ".venv" in python_path.parts


def test_setup_dev_dry_run_prints_bootstrap_plan():
    module = _load_dev_module()
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        exit_code = module.main(["setup-dev", "--dry-run"])

    output = stdout.getvalue()
    bootstrap_line = " ".join(
        shlex.quote(part)
        for part in (
            module.PYTHON,
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
            module.PYTHON,
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
