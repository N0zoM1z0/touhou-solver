#!/usr/bin/env python3
"""Build the SEM-TIMER x87 differential probe for Linux and/or Windows."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
NATIVE_ROOT = ROOT / "native"
SOURCE = NATIVE_ROOT / "tests" / "th08_ecl_timer_probe.cpp"


def _build(*, compiler: str, output: Path, windows: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        compiler,
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(SOURCE),
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
    arguments = parser.parse_args(argv)

    if arguments.target in ("linux", "all"):
        compiler = os.environ.get("CXX") or shutil.which("g++")
        if compiler is None:
            parser.error("g++ is required for the Linux timer probe")
        _build(
            compiler=compiler,
            output=(NATIVE_ROOT / "build" / "linux-x86_64" / "th08_ecl_timer_probe"),
            windows=False,
        )
    if arguments.target in ("windows", "all"):
        compiler = os.environ.get("MINGW_CXX") or shutil.which("x86_64-w64-mingw32-g++")
        if compiler is None:
            parser.error("x86_64-w64-mingw32-g++ is required for the Windows probe")
        _build(
            compiler=compiler,
            output=(
                NATIVE_ROOT / "build" / "windows-x86_64" / "th08_ecl_timer_probe.exe"
            ),
            windows=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
