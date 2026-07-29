from __future__ import annotations

import unittest
from dataclasses import dataclass

from analysis.pipeline_pickup_audit import audit_rows
from th08_live.pipeline_shadow import build_pipeline_shadow_snapshot
from touhou_control.delay import PendingCommandEstimate


SUPPORTED = 0xF7


@dataclass(frozen=True)
class _Solution:
    source_frame: int = 8
    snapshot_frame: int = 8
    context_key: tuple[int, int, int | None] = (1, 0, None)


def _action(mask: int) -> str:
    return f"movement_{mask & 0xF4:02x}"


def _transitions(previous: int, target: int) -> list[list[object]]:
    changed = previous ^ target
    releases = [
        [1 << index, False]
        for index in range(16)
        if changed & previous & (1 << index)
    ]
    presses = [
        [1 << index, True]
        for index in range(16)
        if changed & target & (1 << index)
    ]
    return releases + presses


def _row(
    *,
    frame: int,
    active: int,
    held: int,
    target: int,
    pending: PendingCommandEstimate | None,
    delay_support: tuple[int, ...] = (2, 3),
) -> dict[str, object]:
    root = build_pipeline_shadow_snapshot(
        supported_mask=SUPPORTED,
        native_active_mask=active,
        held_desired_mask=held,
        pending_estimate=pending,
        action_from_mask=_action,
        gameplay_epoch=1,
        stage_route_index=0,
        spell_id=None,
        manager_frame=frame,
        query_frame=frame,
        target_frame=frame + 2,
        player_x=192.0,
        player_y=384.0,
        hazard_horizon_frames=10,
        corridor_solution=_Solution(),
    ).record
    transitions = _transitions(held, target)
    return {
        "kind": "decision",
        "frame": frame,
        "snapshot_frame": frame,
        "gameplay_epoch": 1,
        "stage_route_index": 0,
        "spell": {"active": False, "spell_id": 0},
        "action": _action(target),
        "mask": target,
        "control_delay_candidates": list(delay_support),
        "local_pipeline_root": root,
        "input_dispatch": {
            "role": "observed_issue_transaction",
            "previous_mask": held,
            "target_mask": target,
            "write_required": bool(transitions),
            "transition_count": len(transitions),
            "transitions": transitions,
            "estimator_issued": bool(transitions),
        },
    }


class PipelinePickupAuditTests(unittest.TestCase):
    def test_multikey_last_write_wins_no_write_and_pickup(self) -> None:
        rows = [
            _row(frame=10, active=0x05, held=0x05, target=0x55, pending=None),
            _row(
                frame=11,
                active=0x05,
                held=0x55,
                target=0x45,
                pending=PendingCommandEstimate(
                    expected_mask=0x55,
                    remaining_frames=(1, 2),
                    snapshot_age=1,
                    issue_age=1,
                    overdue=False,
                ),
            ),
            _row(
                frame=12,
                active=0x05,
                held=0x45,
                target=0x45,
                pending=PendingCommandEstimate(
                    expected_mask=0x45,
                    remaining_frames=(1, 2),
                    snapshot_age=1,
                    issue_age=1,
                    overdue=False,
                ),
            ),
            _row(
                frame=13,
                active=0x45,
                held=0x45,
                target=0x45,
                pending=None,
            ),
        ]

        report = audit_rows(rows, supported_mask=SUPPORTED)

        self.assertTrue(report["passed"], report["failures"])
        counts = report["counts"]
        self.assertEqual(counts["multikey_transactions"], 1)
        self.assertEqual(counts["last_write_wins_replacements"], 1)
        self.assertEqual(counts["pending_no_write_carries"], 1)
        self.assertEqual(counts["observed_pickups"], 1)
        self.assertEqual(counts["model_unknown_roots"], 4)
        self.assertEqual(counts["canonical_identity_valid"], 4)
        self.assertEqual(counts["pending_projected_action_reissues"], 0)
        self.assertFalse(report["live_pipeline_promotion_ready"])
        self.assertIn(
            "future_hazard_coverage_is_model_unknown",
            report["promotion_blockers"],
        )

    def test_pending_same_movement_complete_mask_write_blocks_promotion(
        self,
    ) -> None:
        row = _row(
            frame=10,
            active=0x05,
            held=0x85,
            target=0x84,
            pending=PendingCommandEstimate(
                expected_mask=0x85,
                remaining_frames=(1, 2, 3),
                snapshot_age=2,
                issue_age=1,
                overdue=False,
            ),
        )

        report = audit_rows([row], supported_mask=SUPPORTED)

        self.assertTrue(report["passed"], report["failures"])
        self.assertEqual(
            report["counts"]["pending_projected_action_reissues"],
            1,
        )
        self.assertFalse(report["live_pipeline_promotion_ready"])
        self.assertIn(
            "complete_mask_write_collapses_to_held_movement_action",
            report["promotion_blockers"],
        )

    def test_ordered_partial_mask_pickup_blocks_atomic_model_promotion(
        self,
    ) -> None:
        rows = [
            _row(
                frame=10,
                active=0x65,
                held=0x65,
                target=0x41,
                pending=None,
                delay_support=(1, 2),
            ),
            _row(
                frame=11,
                active=0x61,
                held=0x41,
                target=0x41,
                pending=PendingCommandEstimate(
                    expected_mask=0x41,
                    remaining_frames=(1,),
                    snapshot_age=1,
                    issue_age=1,
                    overdue=False,
                ),
                delay_support=(1, 2),
            ),
        ]

        report = audit_rows(rows, supported_mask=SUPPORTED)

        self.assertTrue(report["passed"], report["failures"])
        self.assertEqual(report["counts"]["ordered_partial_pickups"], 1)
        self.assertFalse(report["live_pipeline_promotion_ready"])
        self.assertIn(
            "ordered_partial_transition_pickup_requires_expanded_root",
            report["promotion_blockers"],
        )

    def test_missing_unknown_coverage_fails_closed(self) -> None:
        row = _row(
            frame=10,
            active=0x05,
            held=0x05,
            target=0x05,
            pending=None,
        )
        row["local_pipeline_root"]["hazard_coverage"]["status"] = "complete"

        report = audit_rows([row], supported_mask=SUPPORTED)

        self.assertFalse(report["passed"])
        self.assertEqual(report["failures"][0]["code"], "root_contract")

    def test_transition_order_mismatch_is_rejected(self) -> None:
        row = _row(
            frame=10,
            active=0x05,
            held=0x05,
            target=0x55,
            pending=None,
        )
        row["input_dispatch"]["transitions"].reverse()

        report = audit_rows([row], supported_mask=SUPPORTED)

        self.assertFalse(report["passed"])
        self.assertTrue(
            any(
                failure["code"] == "dispatch_contract"
                for failure in report["failures"]
            )
        )


if __name__ == "__main__":
    unittest.main()
