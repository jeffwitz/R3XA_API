from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def find_dot() -> Path | None:
    executable = shutil.which("dot")
    if executable:
        return Path(executable)

    if sys.platform != "win32":
        return None

    roots = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        Path(os.environ.get("LOCALAPPDATA", r"C:\Users\Public\AppData\Local")) / "Programs",
    ]
    candidates: list[Path] = []
    for root in roots:
        candidates.append(root / "Graphviz" / "bin" / "dot.exe")
        candidates.extend(root.glob("Graphviz*/bin/dot.exe"))

    chocolatey_root = os.environ.get("ChocolateyInstall")
    if chocolatey_root:
        candidates.append(Path(chocolatey_root) / "bin" / "dot.exe")

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _install_command() -> tuple[str, ...]:
    if sys.platform == "win32":
        if shutil.which("winget"):
            return (
                "winget",
                "install",
                "--id",
                "Graphviz.Graphviz",
                "--exact",
                "--source",
                "winget",
                "--accept-source-agreements",
                "--accept-package-agreements",
            )
        if shutil.which("choco"):
            return ("choco", "install", "graphviz", "--yes")
        raise RuntimeError(
            "Graphviz is not installed and neither winget nor Chocolatey was found. "
            "Install Graphviz from https://graphviz.org/download/, then restart the terminal."
        )

    if sys.platform == "darwin":
        if shutil.which("brew"):
            return ("brew", "install", "graphviz")
        raise RuntimeError(
            "Graphviz is not installed and Homebrew was not found. "
            "Install Homebrew or Graphviz from https://graphviz.org/download/."
        )

    raise RuntimeError(
        "Automatic Graphviz installation is supported on Windows and macOS only. "
        "Install the Graphviz system package with your operating system package manager."
    )


def install_graphviz() -> Path:
    command = _install_command()
    print(f"Installing Graphviz with: {' '.join(command)}")
    subprocess.run(command, check=True)

    executable = find_dot()
    if executable is None:
        raise RuntimeError(
            "Graphviz installation completed, but dot was not found in PATH. "
            "Restart the terminal and run `dot -V` to verify the installation."
        )
    return executable


def ensure_graphviz() -> Path:
    executable = find_dot()
    if executable is not None:
        return executable

    executable = install_graphviz()
    os.environ["PATH"] = str(executable.parent) + os.pathsep + os.environ.get("PATH", "")
    return executable


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install Graphviz when dot is unavailable.")
    parser.parse_args(argv)
    try:
        executable = ensure_graphviz()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    print(f"Graphviz is ready: {executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
