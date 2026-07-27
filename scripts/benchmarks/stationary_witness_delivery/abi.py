"""Exact production ABI verification kept separate from the research DLL."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path


def _manifest_symbols(root: Path) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in (
            root / "native" / "abi_symbols_v1.txt"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _header_symbols(root: Path) -> tuple[str, ...]:
    header = (
        root / "native" / "include" / "touhou_native" / "abi.h"
    ).read_text(encoding="utf-8")
    return tuple(
        sorted(
            re.findall(
                r"\b(touhou_[a-zA-Z0-9_]+)\s*\(",
                header,
            )
        )
    )


def _symbols(command: list[str]) -> tuple[str, ...]:
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return tuple(
        sorted(
            fields[-1]
            for line in completed.stdout.splitlines()
            if (
                (fields := line.split())
                and fields[-1].startswith("touhou_")
            )
        )
    )


def _unc_wsl_root(root: Path) -> tuple[str, str] | None:
    normalized = str(root).replace("/", "\\")
    prefixes = ("\\\\wsl.localhost\\", "\\\\wsl$\\")
    for prefix in prefixes:
        if normalized.lower().startswith(prefix.lower()):
            tail = normalized[len(prefix):]
            fields = [field for field in tail.split("\\") if field]
            if len(fields) < 2:
                return None
            return fields[0], "/" + "/".join(fields[1:])
    return None


def verify_production_abi(root: Path) -> dict[str, object]:
    expected = _manifest_symbols(root)
    header = _header_symbols(root)
    linux_library = (
        root
        / "native"
        / "build"
        / "linux-x86_64"
        / "libtouhou_viability.so"
    )
    windows_library = (
        root
        / "native"
        / "build"
        / "windows-x86_64"
        / "touhou_viability.dll"
    )
    errors: list[str] = []
    linux_symbols: tuple[str, ...] = ()
    windows_symbols: tuple[str, ...] = ()
    try:
        if os.name == "nt":
            mapping = _unc_wsl_root(root)
            wsl = shutil.which("wsl.exe")
            if mapping is None or wsl is None:
                raise RuntimeError(
                    "Windows ABI verification requires the verified WSL UNC "
                    "root and wsl.exe"
                )
            distribution, wsl_root = mapping
            linux_symbols = _symbols(
                [
                    wsl,
                    "-d",
                    distribution,
                    "--",
                    "nm",
                    "-D",
                    "-g",
                    "--defined-only",
                    (
                        f"{wsl_root}/native/build/linux-x86_64/"
                        "libtouhou_viability.so"
                    ),
                ]
            )
            windows_symbols = _symbols(
                [
                    wsl,
                    "-d",
                    distribution,
                    "--",
                    "x86_64-w64-mingw32-nm",
                    "-g",
                    "--defined-only",
                    (
                        f"{wsl_root}/native/build/windows-x86_64/"
                        "touhou_viability.dll"
                    ),
                ]
            )
        else:
            nm = shutil.which("nm")
            mingw_nm = shutil.which("x86_64-w64-mingw32-nm")
            if nm is None or mingw_nm is None:
                raise RuntimeError("Linux and MinGW nm tools are required")
            linux_symbols = _symbols(
                [
                    nm,
                    "-D",
                    "-g",
                    "--defined-only",
                    str(linux_library),
                ]
            )
            windows_symbols = _symbols(
                [
                    mingw_nm,
                    "-g",
                    "--defined-only",
                    str(windows_library),
                ]
            )
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "manifest_symbol_count": len(expected),
        "manifest_sorted_unique": expected == tuple(sorted(set(expected))),
        "header_matches_manifest": header == expected,
        "linux_matches_manifest": linux_symbols == expected,
        "windows_matches_manifest": windows_symbols == expected,
        "research_library_is_separate": True,
        "errors": errors,
        "passed": (
            len(expected) == 46
            and expected == tuple(sorted(set(expected)))
            and header == expected
            and linux_symbols == expected
            and windows_symbols == expected
            and not errors
        ),
    }


__all__ = ["verify_production_abi"]
