from pathlib import Path

import pytest

from r3xa_api import graphviz_setup


def test_find_dot_uses_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    executable = tmp_path / "dot"
    executable.write_text("", encoding="utf-8")
    monkeypatch.setattr(graphviz_setup.shutil, "which", lambda name: str(executable))

    assert graphviz_setup.find_dot() == executable


def test_windows_install_prefers_winget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(graphviz_setup.sys, "platform", "win32")
    monkeypatch.setattr(
        graphviz_setup.shutil,
        "which",
        lambda name: "C:/Windows/winget.exe" if name == "winget" else None,
    )

    assert graphviz_setup._install_command() == (
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


def test_macos_install_uses_homebrew(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(graphviz_setup.sys, "platform", "darwin")
    monkeypatch.setattr(
        graphviz_setup.shutil,
        "which",
        lambda name: "/opt/homebrew/bin/brew" if name == "brew" else None,
    )

    assert graphviz_setup._install_command() == ("brew", "install", "graphviz")
