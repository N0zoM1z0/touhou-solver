#!/usr/bin/env python3
"""Build the internal stationary-witness differential probe."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NATIVE_ROOT = ROOT / "native"
SOURCES = (
    NATIVE_ROOT / "tests" / "belief_stationary_witness_probe.cpp",
    NATIVE_ROOT / "src" / "pipeline" / "belief_stationary_witness.cpp",
    NATIVE_ROOT / "src" / "pipeline" / "belief_workspace.cpp",
)


def _build(*, compiler: str, output: Path, windows: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        compiler,
        "-std=c++17",
        "-O2",
        "-DNDEBUG",
        "-I",
        str(NATIVE_ROOT),
        *(str(source) for source in SOURCES),
        "-o",
        str(output),
    ]
    if windows:
        command.extend(("-static", "-static-libgcc", "-static-libstdc++"))
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
            parser.error("g++ is required for the Linux probe")
        _build(
            compiler=compiler,
            output=(
                NATIVE_ROOT
                / "build"
                / "linux-x86_64"
                / "belief_stationary_witness_probe"
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
                "x86_64-w64-mingw32-g++ is required for the Windows probe"
            )
        _build(
            compiler=compiler,
            output=(
                NATIVE_ROOT
                / "build"
                / "windows-x86_64"
                / "belief_stationary_witness_probe.exe"
            ),
            windows=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
