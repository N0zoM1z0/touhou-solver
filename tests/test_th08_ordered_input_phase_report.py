from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from analysis.th08_ordered_input_phase_report import build_report


def _decision(
    *,
    frame: int,
    snapshot_frame: int,
    raw: int,
    current: int,
    previous: int,
    dispatch_previous: int,
    target: int,
    transitions: tuple[tuple[int, bool], ...],
    delay_support: tuple[int, ...] = (1, 2, 3, 4),
    coherent_current: int | None = None,
    pending_mask: int | None = None,
    remaining: tuple[int, ...] = (),
) -> dict[str, object]:
    if coherent_current is None:
        coherent_current = current
    return {
        "kind": "decision",
        "frame": frame,
        "snapshot_frame": snapshot_frame,
        "action_lag": frame - snapshot_frame,
        "gameplay_epoch": 0,
        "stage_route_index": 5,
        "mask": target,
        "bomb": False,
        "input_snapshot": {
            "raw": raw,
            "current": current,
            "previous": previous,
        },
        "control_delay_candidates": list(delay_support),
        "input_dispatch": {
            "role": "observed_issue_transaction",
            "previous_mask": dispatch_previous,
            "target_mask": target,
            "write_required": dispatch_previous != target,
            "transition_count": len(transitions),
            "transitions": [list(value) for value in transitions],
            "estimator_issued": dispatch_previous != target,
        },
        "local_pipeline_root": {
            "pending_mask": pending_mask,
            "remaining_delay_support": list(remaining),
        },
        "player_enemy_mode_capture": {
            "role": "diagnostic_shadow",
            "status": "coherent",
            "coherent": True,
            "action_authority": False,
            "player_before": {"input_current": coherent_current},
            "player_after": {"input_current": coherent_current},
        },
    }


def _report(rows: list[dict[str, object]]) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "trace.jsonl"
        path.write_text(
            "\n".join(json.dumps(row) for row in rows)
            + '\n{"kind":"summary","termination_reason":"route_complete"}\n',
            encoding="utf-8",
        )
        return build_report(path)


class OrderedInputPhaseReportTests(unittest.TestCase):
    def test_ce0193_retains_strong_intermediate_publication_edge(self) -> None:
        report = _report(
            [
                _decision(
                    frame=386,
                    snapshot_frame=384,
                    raw=0x65,
                    current=0x65,
                    previous=0x25,
                    dispatch_previous=0x65,
                    target=0x41,
                    transitions=((0x04, False), (0x20, False)),
                ),
                _decision(
                    frame=389,
                    snapshot_frame=387,
                    raw=0x61,
                    current=0x61,
                    previous=0x65,
                    dispatch_previous=0x41,
                    target=0x41,
                    transitions=(),
                    pending_mask=0x41,
                    remaining=(1,),
                ),
                _decision(
                    frame=391,
                    snapshot_frame=390,
                    raw=0x41,
                    current=0x41,
                    previous=0x41,
                    dispatch_previous=0x41,
                    target=0x51,
                    transitions=((0x10, True),),
                    delay_support=(1, 2, 3, 4, 5, 6),
                ),
            ]
        )

        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(
            report["transactions"]["observed_intermediate_masks"],
            1,
        )
        self.assertEqual(
            report["publication_edges"]["corroborated_sequential_edge_witnesses"],
            1,
        )
        self.assertEqual(
            report["publication_edges"]["edge_position_counts"],
            {"1/2": 1},
        )
        first = report["retained_transactions"][0]
        self.assertEqual(first["outcome"], "final_observed_before_replacement")
        self.assertEqual(first["conditioned_manager_remaining_at_issue"], [1, 2])
        self.assertEqual(first["source_to_first_final_observation"], 6)
        self.assertFalse(first["first_final_observation_within_issued_support"])
        self.assertFalse(
            report["scope"]["ordered_oracle_publication_deadline_adapter_ready"]
        )
        self.assertEqual(
            report["publication_edges"]["canonical_ce0193_edge"]["current_mask"],
            0x61,
        )

    def test_later_coherent_disagreement_downgrades_sequential_edge(self) -> None:
        report = _report(
            [
                _decision(
                    frame=10,
                    snapshot_frame=9,
                    raw=0x65,
                    current=0x65,
                    previous=0x65,
                    dispatch_previous=0x65,
                    target=0x41,
                    transitions=((0x04, False), (0x20, False)),
                ),
                _decision(
                    frame=12,
                    snapshot_frame=11,
                    raw=0x61,
                    current=0x61,
                    previous=0x65,
                    coherent_current=0x41,
                    dispatch_previous=0x41,
                    target=0x41,
                    transitions=(),
                ),
            ]
        )

        self.assertEqual(
            report["publication_edges"]["corroborated_sequential_edge_witnesses"],
            0,
        )
        self.assertEqual(
            report["publication_edges"]["uncorroborated_sequential_matches"],
            1,
        )

    def test_replacement_without_final_observation_is_right_censored(self) -> None:
        report = _report(
            [
                _decision(
                    frame=10,
                    snapshot_frame=9,
                    raw=0x65,
                    current=0x65,
                    previous=0x65,
                    dispatch_previous=0x65,
                    target=0x41,
                    transitions=((0x04, False), (0x20, False)),
                ),
                _decision(
                    frame=12,
                    snapshot_frame=11,
                    raw=0x61,
                    current=0x61,
                    previous=0x65,
                    dispatch_previous=0x41,
                    target=0x51,
                    transitions=((0x10, True),),
                ),
            ]
        )

        self.assertEqual(
            report["transactions"]["outcome_counts"]["right_censored_by_real_write"],
            1,
        )

    def test_dispatch_order_tamper_fails_loudly(self) -> None:
        row = _decision(
            frame=10,
            snapshot_frame=9,
            raw=0x65,
            current=0x65,
            previous=0x65,
            dispatch_previous=0x65,
            target=0x41,
            transitions=((0x20, False), (0x04, False)),
        )
        with self.assertRaisesRegex(
            ValueError,
            "not the declared ordered complete-mask transaction",
        ):
            _report([row])

    def test_bomb_input_is_rejected(self) -> None:
        row = _decision(
            frame=10,
            snapshot_frame=9,
            raw=0x43,
            current=0x43,
            previous=0x41,
            dispatch_previous=0x41,
            target=0x41,
            transitions=(),
        )
        with self.assertRaisesRegex(ValueError, "Bomb input"):
            _report([row])


if __name__ == "__main__":
    unittest.main()
