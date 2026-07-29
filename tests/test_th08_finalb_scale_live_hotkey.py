from __future__ import annotations

import unittest

from th08_live.scale_source_trace import FINAL_B_ECL_STATIC_SHA256
from tools.th08_finalb_scale_live_hotkey import (
    DEFAULT_STATIC_ECL,
    build_parser,
)


class FinalBScaleLiveHotkeyTests(unittest.TestCase):
    def test_defaults_bind_the_retained_finalb_ecl(self) -> None:
        args = build_parser().parse_args([])

        self.assertEqual(args.static_ecl, DEFAULT_STATIC_ECL)
        self.assertEqual(args.static_sha256, FINAL_B_ECL_STATIC_SHA256)
        self.assertEqual(args.duration, 600.0)

    def test_duration_and_identity_are_explicitly_overridable(self) -> None:
        args = build_parser().parse_args(
            [
                "--static-ecl",
                "fixture.ecl",
                "--static-sha256",
                "1" * 64,
                "--duration",
                "300",
            ]
        )

        self.assertEqual(args.static_ecl.name, "fixture.ecl")
        self.assertEqual(args.static_sha256, "1" * 64)
        self.assertEqual(args.duration, 300.0)


if __name__ == "__main__":
    unittest.main()
