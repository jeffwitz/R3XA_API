#!/usr/bin/env python3
"""Rebuild the bundled Graphviz WASI module from pinned sources."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
MANIFEST = json.loads((TOOLS / "manifest.json").read_text())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path, expected_sha256: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and _sha256(destination) == expected_sha256:
        return destination
    print(f"Downloading {url}")
    with urlopen(url) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    actual = _sha256(destination)
    if actual != expected_sha256:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"SHA-256 mismatch for {destination}: {actual}")
    return destination


def _run(*command: str, cwd: Path | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def _source_tree(workdir: Path, source: Path | None) -> Path:
    if source is not None:
        source = source.resolve()
        git_dir = source / ".git"
        if git_dir.exists():
            revision = subprocess.check_output(
                ("git", "-C", str(source), "rev-parse", "HEAD"),
                text=True,
            ).strip()
            if revision != MANIFEST["graphviz_commit"]:
                raise RuntimeError(
                    f"Graphviz source revision {revision} does not match "
                    f"{MANIFEST['graphviz_commit']}"
                )
        return source
    archive = workdir / "graphviz-source.tar.gz"
    _download(
        MANIFEST["graphviz_source_url"],
        archive,
        MANIFEST["graphviz_source_sha256"],
    )
    source_root = workdir / "graphviz-source"
    if not source_root.exists():
        source_root.mkdir()
        with tarfile.open(archive, "r:gz") as handle:
            handle.extractall(source_root)
    entries = [path for path in source_root.iterdir() if path.is_dir()]
    if len(entries) != 1:
        raise RuntimeError(f"Expected one Graphviz source directory in {source_root}")
    return entries[0]


def _wasi_sdk(workdir: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        raise RuntimeError(
            "Automatic WASI SDK download is pinned for Linux x86_64. "
            "Pass --wasi-sdk for another host."
        )
    archive = workdir / "wasi-sdk.tar.gz"
    _download(
        MANIFEST["wasi_sdk_linux_x86_64_url"],
        archive,
        MANIFEST["wasi_sdk_linux_x86_64_sha256"],
    )
    sdk_root = workdir / "wasi-sdk"
    if not sdk_root.exists():
        sdk_root.mkdir()
        with tarfile.open(archive, "r:gz") as handle:
            handle.extractall(sdk_root)
    entries = [path for path in sdk_root.iterdir() if path.is_dir()]
    if len(entries) != 1:
        raise RuntimeError(f"Expected one WASI SDK directory in {sdk_root}")
    return entries[0]


def _toolchain(sdk: Path, path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "set(CMAKE_SYSTEM_NAME WASI CACHE STRING \"\")",
                "set(CMAKE_SYSTEM_VERSION 1 CACHE STRING \"\")",
                f"set(CMAKE_SYSROOT \"{sdk / 'share/wasi-sysroot'}\" CACHE PATH \"\")",
                f"set(CMAKE_C_COMPILER \"{sdk / 'bin/clang'}\" CACHE FILEPATH \"\")",
                f"set(CMAKE_CXX_COMPILER \"{sdk / 'bin/clang++'}\" CACHE FILEPATH \"\")",
                f"set(CMAKE_AR \"{sdk / 'bin/llvm-ar'}\" CACHE FILEPATH \"\")",
                f"set(CMAKE_RANLIB \"{sdk / 'bin/llvm-ranlib'}\" CACHE FILEPATH \"\")",
                "set(CMAKE_C_COMPILER_TARGET wasm32-wasip1 CACHE STRING \"\")",
                "set(CMAKE_CXX_COMPILER_TARGET wasm32-wasip1 CACHE STRING \"\")",
                "set(CMAKE_EXE_LINKER_FLAGS \"--target=wasm32-wasip1\" CACHE STRING \"\")",
            ]
        )
        + "\n"
    )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graphviz-source", type=Path, help="use an existing pinned Graphviz source tree")
    parser.add_argument("--wasi-sdk", type=Path, help="use an existing WASI SDK installation")
    parser.add_argument("--workdir", type=Path, default=Path("build/graphviz-wasi"))
    parser.add_argument("--output", type=Path, default=ROOT / MANIFEST["output"])
    args = parser.parse_args(argv)

    workdir = (ROOT / args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    source = _source_tree(workdir, args.graphviz_source)
    sdk = _wasi_sdk(workdir, args.wasi_sdk)
    build_dir = workdir / "build"
    toolchain = _toolchain(sdk, workdir / "wasi-toolchain.cmake")
    install_dir = workdir / "install"

    _run(
        "cmake",
        "-S",
        str(TOOLS),
        "-B",
        str(build_dir),
        f"-DGRAPHVIZ_SOURCE_DIR={source}",
        f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
    )
    _run(
        "cmake",
        "--build",
        str(build_dir),
        "--target",
        "r3xa_graphviz",
        "--parallel",
    )
    built = build_dir / "graphviz-12.2.1.wasm"
    if not built.is_file():
        raise RuntimeError(f"Build completed without producing {built}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, args.output)
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")
    digest = _sha256(args.output)
    print(f"SHA-256: {digest}")
    if digest == MANIFEST["current_artifact_sha256"]:
        print("The rebuilt artifact matches the committed artifact hash.")
    else:
        print(
            "The rebuilt artifact differs from the committed hash; review the "
            "toolchain and resulting exports before replacing the package file."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
