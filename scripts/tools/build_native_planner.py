#!/usr/bin/env python3
"""Build-tool entry point for the optional native viability backend."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "native" / "robust_viability_kernel.cpp"


def _build(
    *,
    compiler: str,
    output: Path,
    windows: bool,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        compiler,
        "-std=c++17",
        "-O3",
        "-DNDEBUG",
        "-shared",
        str(SOURCE),
        "-o",
        str(output),
    ]
    if windows:
        command.extend(("-static", "-static-libgcc", "-static-libstdc++"))
    else:
        command.insert(-2, "-fPIC")
    subprocess.run(command, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=("linux", "windows", "all"),
        default="linux",
    )
    args = parser.parse_args(argv)

    if args.target in ("linux", "all"):
        compiler = os.environ.get("CXX") or shutil.which("g++")
        if compiler is None:
            parser.error("g++ is required for the Linux backend")
        _build(
            compiler=compiler,
            output=(
                ROOT
                / "native"
                / "build"
                / "linux-x86_64"
                / "libtouhou_viability.so"
            ),
            windows=False,
        )
    if args.target in ("windows", "all"):
        compiler = (
            os.environ.get("MINGW_CXX")
            or shutil.which("x86_64-w64-mingw32-g++")
        )
        if compiler is None:
            parser.error(
                "x86_64-w64-mingw32-g++ is required for the Windows backend"
            )
        _build(
            compiler=compiler,
            output=(
                ROOT
                / "native"
                / "build"
                / "windows-x86_64"
                / "touhou_viability.dll"
            ),
            windows=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
