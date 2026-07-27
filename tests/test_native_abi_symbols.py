from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "native" / "abi_symbols_v1.txt"


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
