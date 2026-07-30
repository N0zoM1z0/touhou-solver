from __future__ import annotations

import unittest

from tools.th08_native_snapshot_trial import (
    DEFAULT_ACTION_B,
    DEFAULT_STAGE5_SHA256,
    DEFAULT_TARGET_MANAGER_FRAME,
    build_parser,
)


class NativeSnapshotTrialCliTests(unittest.TestCase):
    def test_parser_pins_canonical_stage5_root_and_distinct_action(self) -> None:
        arguments = build_parser().parse_args(["--output", "native_snapshot.json"])

        self.assertEqual(
            arguments.target_manager_frame,
            DEFAULT_TARGET_MANAGER_FRAME,
        )
        self.assertEqual(arguments.action_b, DEFAULT_ACTION_B)
        self.assertEqual(
            arguments.expected_replay_sha256,
            DEFAULT_STAGE5_SHA256,
        )

    def test_action_mask_accepts_hexadecimal(self) -> None:
        arguments = build_parser().parse_args(
            [
                "--output",
                "native_snapshot.json",
                "--action-b",
                "0x15",
            ]
        )

        self.assertEqual(arguments.action_b, 0x15)


if __name__ == "__main__":
    unittest.main()
