#!/usr/bin/env python3
"""Build-tool entry point for the optional native viability backend."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NATIVE_ROOT = ROOT / "native"
SOURCES = (
    NATIVE_ROOT / "src" / "geometry" / "clearance.cpp",
    NATIVE_ROOT / "src" / "local" / "kernels.cpp",
    NATIVE_ROOT / "src" / "local" / "supplemental_workspace.cpp",
    NATIVE_ROOT / "src" / "pipeline" / "direct_workspace.cpp",
    NATIVE_ROOT / "src" / "pipeline" / "belief_workspace.cpp",
    NATIVE_ROOT / "src" / "pipeline" / "query_local.cpp",
    NATIVE_ROOT / "src" / "viability" / "kernels.cpp",
    NATIVE_ROOT / "src" / "viability" / "losing_labels.cpp",
)


def _build(
    *,
    compiler: str,
    output: Path,
    windows: bool,
    profile: str,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        compiler,
        "-std=c++17",
        "-shared",
        "-I",
        str(NATIVE_ROOT),
        *(str(source) for source in SOURCES),
        "-o",
        str(output),
    ]
    if profile == "release":
        command[2:2] = ("-O3", "-DNDEBUG")
    else:
        command[2:2] = (
            "-O1",
            "-g",
            "-fsanitize=address,undefined",
            "-fno-omit-frame-pointer",
        )
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
    parser.add_argument(
        "--profile",
        choices=("release", "sanitize"),
        default="release",
    )
    args = parser.parse_args(argv)
    if args.profile == "sanitize" and args.target != "linux":
        parser.error("the sanitizer research profile is Linux-only")

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
                / (
                    "libtouhou_viability.so"
                    if args.profile == "release"
                    else "libtouhou_viability_sanitize.so"
                )
            ),
            windows=False,
            profile=args.profile,
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
            profile=args.profile,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
