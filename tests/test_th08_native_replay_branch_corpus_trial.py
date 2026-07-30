from __future__ import annotations

import unittest
from pathlib import Path

from tools.th08_native_replay_branch_corpus_trial import _trial_summary


class NativeReplayBranchCorpusTrialTests(unittest.TestCase):
    def test_no_hit_trial_retains_endpoint_and_native_contract(self) -> None:
        summary = _trial_summary(
            {
                "token": "th08_mask_00",
                "complete_mask": 0,
                "movement_label": "neutral",
                "replay_sha256": "12" * 32,
            },
            {
                "changes_gameplay_input": False,
                "recorded_future_world_reused": False,
                "replay_contract": {"sha256": "12" * 32},
                "result": {
                    "status": "stop_frame_reached_without_hit",
                    "stop_manager_frame": 2136,
                    "history": [
                        {
                            "manager_frame": 2136,
                            "input_current": 0,
                            "player_phase": 0,
                            "player_x": 370.0,
                            "player_y": 430.0,
                        }
                    ],
                },
            },
            report_path=Path("trial.json"),
        )

        self.assertEqual(
            summary["status"],
            "stop_frame_reached_without_hit",
        )
        self.assertEqual(summary["endpoint"]["manager_frame"], 2136)
        self.assertFalse(summary["recorded_future_world_reused"])


if __name__ == "__main__":
    unittest.main()
