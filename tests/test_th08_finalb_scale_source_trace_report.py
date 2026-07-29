from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analysis.th08_finalb_scale_source_trace_report import (  # noqa: E402
    build_report,
)
from th08_live.scale_source_trace import (  # noqa: E402
    FINAL_B_ECL_STATIC_SHA256,
    FINAL_B_QUARTER_SCALE_BITS,
    FINAL_B_SCALE_HORIZON_FRAMES,
    FINAL_B_SCALE_SOURCE_TRACE_SCHEMA,
)
from th08_runtime.game_state import EXPECTED_EXE_SHA256  # noqa: E402


def _envelope() -> dict[str, object]:
    return {
        "executable_identity": {"sha256": EXPECTED_EXE_SHA256},
        "record": {
            "schema": FINAL_B_SCALE_SOURCE_TRACE_SCHEMA,
            "authority": "trace_only_no_action_authority",
            "status": "accepted_complete_source_trace",
            "hard_action_authority": False,
            "changes_input": False,
            "route_id": 2,
            "difficulty_index": 3,
            "stage_route_index": 7,
            "spell_id": 190,
            "expected_manager_frame": 75000,
            "gameplay_epoch": 4,
            "configuration": {
                "static_sha256": FINAL_B_ECL_STATIC_SHA256,
                "target_subroutine": 44,
                "horizon_frames": FINAL_B_SCALE_HORIZON_FRAMES,
            },
            "runtime_ecl_identity": {
                "exact_match": True,
                "static_sha256": FINAL_B_ECL_STATIC_SHA256,
                "normalized_runtime_sha256": FINAL_B_ECL_STATIC_SHA256,
            },
            "runtime_ecl_capture": {"runtime_base": 0x02100000},
            "source_capture": {
                "coherent": True,
                "ordinary_pool_complete": True,
                "ordinary_pool_slots_scanned": 480,
                "source_count": 1,
                "process_read_count": 24,
                "process_read_bytes": 10_300_000,
                "capture_ms": 4.0,
                "phase_before": {
                    "scale_bits": FINAL_B_QUARTER_SCALE_BITS,
                    "player_bomb_active": 0,
                    "player_predeath_counter": 0,
                },
                "sources": [
                    {
                        "installed_callback": 0,
                        "auxiliary_context_pointers": [0, 0, 0, 0],
                        "invalid_reason": None,
                    }
                ],
            },
            "schedule": {
                "coverage": "complete",
                "complete_horizon": FINAL_B_SCALE_HORIZON_FRAMES,
                "stop_reason": "horizon",
                "stop_frame": FINAL_B_SCALE_HORIZON_FRAMES,
                "root_scale_bits": FINAL_B_QUARTER_SCALE_BITS,
                "player_scale_bits": (
                    [FINAL_B_QUARTER_SCALE_BITS]
                    * FINAL_B_SCALE_HORIZON_FRAMES
                ),
                "laser_scale_bits": (
                    [FINAL_B_QUARTER_SCALE_BITS]
                    * FINAL_B_SCALE_HORIZON_FRAMES
                ),
                "bullet_velocity_rescale_frames": [],
                "writes": [
                    {
                        "frame": 237,
                        "callback_index": 18,
                        "scale_bits_after": 0x3F800000,
                        "scales_active_bullet_velocity": False,
                    }
                ],
            },
            "incomplete_reasons": [],
            "error": None,
        },
    }


class FinalBScaleSourceTraceReportTests(unittest.TestCase):
    def _report(self, envelope: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "observer.json"
            source.write_text(
                json.dumps(envelope),
                encoding="utf-8",
            )
            return build_report(source)

    def test_complete_trace_passes_every_gate(self) -> None:
        report = self._report(_envelope())

        self.assertTrue(report["gate"]["passed"])
        self.assertTrue(all(report["gate"]["checks"].values()))

    def test_auxiliary_context_rejects_report(self) -> None:
        envelope = _envelope()
        record = envelope["record"]
        assert isinstance(record, dict)
        source_capture = record["source_capture"]
        assert isinstance(source_capture, dict)
        sources = source_capture["sources"]
        assert isinstance(sources, list)
        sources[0]["auxiliary_context_pointers"] = [0x02200000, 0, 0, 0]

        report = self._report(envelope)

        self.assertFalse(report["gate"]["passed"])
        self.assertFalse(
            report["gate"]["checks"][
                "source_callback_auxiliary_absence"
            ]
        )

    def test_callback_29_side_effect_rejects_report(self) -> None:
        envelope = _envelope()
        record = envelope["record"]
        assert isinstance(record, dict)
        schedule = record["schedule"]
        assert isinstance(schedule, dict)
        schedule["bullet_velocity_rescale_frames"] = [1]

        report = self._report(envelope)

        self.assertFalse(report["gate"]["passed"])
        self.assertFalse(report["gate"]["checks"]["complete_schedule"])


if __name__ == "__main__":
    unittest.main()
