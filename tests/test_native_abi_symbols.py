from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "native" / "abi_symbols_v1.txt"
ABI_HEADER = ROOT / "native" / "include" / "touhou_native" / "abi.h"


def _manifest_symbols() -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _binary_symbols(*, tool: str, library: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        [tool, "-g", "--defined-only", str(library)],
        check=True,
        capture_output=True,
        text=True,
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


class NativeAbiSymbolTests(unittest.TestCase):
    def test_authoritative_header_matches_export_manifest(self) -> None:
        header_symbols = tuple(
            sorted(
                re.findall(
                    r"\b(touhou_[a-zA-Z0-9_]+)\s*\(",
                    ABI_HEADER.read_text(encoding="utf-8"),
                )
            )
        )
        self.assertEqual(header_symbols, _manifest_symbols())

    def test_authoritative_header_is_self_contained_c_and_cpp(self) -> None:
        cases = (
            (shutil.which("cc"), "c11", "c"),
            (shutil.which("c++"), "c++17", "c++"),
        )
        checked = 0
        for compiler, standard, language in cases:
            if compiler is None:
                continue
            with self.subTest(language=language):
                subprocess.run(
                    [
                        compiler,
                        f"-std={standard}",
                        "-fsyntax-only",
                        "-I",
                        str(ROOT / "native"),
                        "-x",
                        language,
                        "-",
                    ],
                    input=(
                        '#include "include/touhou_native/abi.h"\n'
                        "int main(void) { return 0; }\n"
                    ),
                    check=True,
                    text=True,
                    capture_output=True,
                )
            checked += 1
        if checked == 0:
            self.skipTest("no C/C++ compiler is available")

    def test_linux_dynamic_exports_are_exactly_the_manifest(self) -> None:
        tool = shutil.which("nm")
        library = (
            ROOT
            / "native"
            / "build"
            / "linux-x86_64"
            / "libtouhou_viability.so"
        )
        if tool is None or not library.exists():
            self.skipTest("Linux native library or nm is unavailable")
        completed = subprocess.run(
            [tool, "-D", "-g", "--defined-only", str(library)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            tuple(sorted(line.split()[-1] for line in completed.stdout.splitlines())),
            _manifest_symbols(),
        )

    def test_built_libraries_match_checked_in_export_manifest(self) -> None:
        expected = _manifest_symbols()
        self.assertEqual(expected, tuple(sorted(set(expected))))
        self.assertEqual(len(expected), 43)
        targets = (
            (
                shutil.which("nm"),
                ROOT
                / "native"
                / "build"
                / "linux-x86_64"
                / "libtouhou_viability.so",
            ),
            (
                shutil.which("x86_64-w64-mingw32-nm"),
                ROOT
                / "native"
                / "build"
                / "windows-x86_64"
                / "touhou_viability.dll",
            ),
        )
        checked = 0
        for tool, library in targets:
            if tool is None or not library.exists():
                continue
            with self.subTest(library=library.name):
                self.assertEqual(
                    _binary_symbols(tool=tool, library=library),
                    expected,
                )
            checked += 1
        if checked == 0:
            self.skipTest("no native library/export tool pair is available")


if __name__ == "__main__":
    unittest.main()
