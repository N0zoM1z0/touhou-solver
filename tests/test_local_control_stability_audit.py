from __future__ import annotations

import unittest

from analysis.local_control_stability_audit import (
    analyze_rows,
    horizontal_sign,
)


def _row(
    frame: int,
    *,
    desired_mask: int,
    active_mask: int,
    x: float,
    objective: bool = True,
    action: str = "synthetic",
) -> dict[str, object]:
    row: dict[str, object] = {
        "kind": "decision",
        "frame": frame,
        "gameplay_epoch": 0,
        "mask": desired_mask,
        "action": action,
        "hit_count": 0,
        "active_bullets": 0,
        "active_lasers": 0,
        "active_enemy_bodies": 0,
        "input_snapshot": {"current": active_mask},
        "player": {
            "x": x,
            "y": 400.0,
            "phase": 0,
            "phase_at_action": 0,
        },
        "deadline_guard": {"missed": False},
        "robust_control": {
            "worst_collisions": 0,
            "min_clearance": 9999.0,
        },
        "terminal_threat": {
            "collisions": 0,
            "min_clearance": 9999.0,
        },
    }
    if objective:
        row["planner_objective"] = {
            "corridor_target": None,
            "damage_target_x": None,
            "damageable": False,
            "active_items": 0,
            "preserve_previous_direction_inertia": True,
            "corridor_context_changed": False,
        }
        row["planner_guidance"] = {
            "support_covers_current": True,
            "allowed_first_actions": (
                "left",
                "right",
                "stay",
            ),
        }
    return row


class LocalControlStabilityAuditTests(unittest.TestCase):
    def test_horizontal_sign_rejects_aliases(self) -> None:
        self.assertEqual(horizontal_sign(0), 0)
        self.assertEqual(horizontal_sign(0x40), -1)
        self.assertEqual(horizontal_sign(0x80), 1)
        self.assertEqual(horizontal_sign(0xC0), 0)

    def test_desired_and_native_ping_pong_are_separate(self) -> None:
        rows = [
            _row(100, desired_mask=0x44, active_mask=0x04, x=192.0),
            _row(104, desired_mask=0x84, active_mask=0x44, x=190.0),
            _row(108, desired_mask=0x44, active_mask=0x84, x=192.0),
            _row(112, desired_mask=0x44, active_mask=0x44, x=190.0),
        ]

        report = analyze_rows(rows)

        self.assertEqual(report["desired"]["reversals"]["count"], 2)
        self.assertEqual(report["native_active"]["reversals"]["count"], 2)
        self.assertEqual(report["desired"]["ping_pong"]["count"], 1)
        self.assertEqual(
            report["native_active"]["ping_pong"]["count"],
            1,
        )
        self.assertEqual(
            report["desired"]["ping_pong"][
                "settled_default_target_count"
            ],
            1,
        )
        self.assertEqual(
            report["desired"]["ping_pong"][
                "guidance_horizontally_unconstrained_count"
            ],
            1,
        )
        self.assertEqual(
            report["desired"]["ping_pong"]["inertia_enabled_count"],
            1,
        )
        self.assertGreater(
            report["desired_active_horizontal_disagreement_samples"],
            0,
        )

    def test_old_trace_cannot_be_called_objective_free(self) -> None:
        rows = [
            _row(
                100,
                desired_mask=0x44,
                active_mask=0x44,
                x=192.0,
                objective=False,
            ),
            _row(
                104,
                desired_mask=0x84,
                active_mask=0x84,
                x=192.0,
                objective=False,
            ),
            _row(
                108,
                desired_mask=0x44,
                active_mask=0x44,
                x=192.0,
                objective=False,
            ),
        ]

        report = analyze_rows(rows)

        self.assertEqual(report["objective_schema_samples"], 0)
        self.assertEqual(report["guidance_schema_samples"], 0)
        self.assertEqual(report["default_only_controllable_samples"], 0)
        self.assertEqual(
            report["desired"]["ping_pong"]["objective_unknown_count"],
            1,
        )

    def test_explicit_root_marks_hard_equivalent_opposed_write(self) -> None:
        first = _row(
            100,
            desired_mask=0x44,
            active_mask=0x44,
            x=192.0,
            action="left",
        )
        opposed = _row(
            104,
            desired_mask=0x84,
            active_mask=0x44,
            x=192.0,
            action="right",
        )
        opposed["local_pipeline_root"] = {
            "held_desired_action": "left",
            "held_desired_mask": 0x44,
        }
        opposed["local_pipeline_certificate_shadow"] = {
            "status": "complete",
            "certificates": [
                {
                    "action": "left",
                    "worst_collisions": 0,
                    "min_clearance": 8.0,
                },
                {
                    "action": "right",
                    "worst_collisions": 0,
                    "min_clearance": 12.0,
                },
            ],
        }

        report = analyze_rows([first, opposed])
        switches = report["sampled_explicit_root_opposed_switches"]

        self.assertEqual(switches["opposed_horizontal_writes"], 1)
        self.assertEqual(switches["both_actions_hard_safe"], 1)
        self.assertEqual(switches["hard_equivalent_soft_switch"], 1)
        self.assertEqual(switches["both_actions_globally_allowed"], 1)
        self.assertEqual(
            switches["hard_equivalent_selected_clearance_better"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
