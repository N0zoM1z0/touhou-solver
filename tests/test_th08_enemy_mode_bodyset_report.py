#!/usr/bin/env python3
"""Tests for physical action-conditioned TH08 mode/body-set reports."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.th08_enemy_mode_bodyset_report import build_report


def _decision(
    *,
    frame: int,
    enemy_frame: int,
    mode_state: tuple[int, bool, int],
    active_action: str,
    active_mask: int,
    selected_action: str,
    selected_mask: int,
    delay_support: tuple[int, ...],
    body_flags: int | None = 0x00000145,
    coherent: bool = True,
    action_authority: bool = False,
    phase: int = 3,
    action_lag: int | None = None,
    held_action: str | None = None,
    held_mask: int | None = None,
    pending_action: str | None = None,
    pending_mask: int | None = None,
    remaining_delay_support: tuple[int, ...] = (),
    dispatch_previous_mask: int | None = None,
    dispatch_transitions: tuple[tuple[int, bool], ...] | None = None,
) -> dict[str, object]:
    bodies = [] if body_flags is None else [[0x1000, body_flags]]
    if held_action is None:
        held_action = active_action
    if held_mask is None:
        held_mask = active_mask
    if dispatch_previous_mask is None:
        dispatch_previous_mask = held_mask
    if dispatch_transitions is None:
        generated_transitions: list[tuple[int, bool]] = []
        changed = dispatch_previous_mask ^ selected_mask
        for bit_index in range(32):
            bit = 1 << bit_index
            if changed & bit:
                generated_transitions.append((bit, bool(selected_mask & bit)))
        dispatch_transitions = tuple(generated_transitions)
    return {
        "kind": "decision",
        "frame": frame,
        "action_lag": (frame - enemy_frame if action_lag is None else action_lag),
        "gameplay_epoch": 1,
        "stage_route_index": 5,
        "action": selected_action,
        "mask": selected_mask,
        "control_delay_candidates": list(delay_support),
        "local_pipeline_root": {
            "canonical_status": "available",
            "estimator_consistent": True,
            "active_action": active_action,
            "active_mask": active_mask,
            "held_desired_action": held_action,
            "held_desired_mask": held_mask,
            "pending_action": pending_action,
            "pending_mask": pending_mask,
            "remaining_delay_support": list(remaining_delay_support),
        },
        "input_dispatch": {
            "previous_mask": dispatch_previous_mask,
            "target_mask": selected_mask,
            "write_required": bool(dispatch_transitions),
            "transition_count": len(dispatch_transitions),
            "transitions": [list(transition) for transition in dispatch_transitions],
        },
        "player_enemy_mode_capture": {
            "role": "diagnostic_shadow",
            "coherent": coherent,
            "enemy_frame_after": enemy_frame,
            "action_authority": action_authority,
            "mode_sensitive_bodies": bodies,
            "player_after": {
                "input_current": active_mask,
                "phase": phase,
                "focus_logic": mode_state[0],
                "secondary_character_active": mode_state[1],
                "focus_transition_counter": mode_state[2],
                "bomb_active": 0,
            },
        },
    }


def _report(rows: list[dict[str, object]]) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        trace = Path(directory) / "trace.jsonl"
        trace.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        return build_report(trace)


class EnemyModeBodysetReportTests(unittest.TestCase):
    def test_delayed_focus_pickup_matches_mode_and_cleared_body_gate(
        self,
    ) -> None:
        report = _report(
            [
                _decision(
                    frame=12,
                    enemy_frame=10,
                    mode_state=(0, True, 4),
                    active_action="fast",
                    active_mask=0x01,
                    selected_action="focus",
                    selected_mask=0x05,
                    delay_support=(1,),
                    body_flags=0x00000945,
                ),
                _decision(
                    frame=15,
                    enemy_frame=13,
                    mode_state=(0, False, 7),
                    active_action="focus",
                    active_mask=0x05,
                    selected_action="focus",
                    selected_mask=0x05,
                    delay_support=(1,),
                    body_flags=0x00000145,
                ),
            ]
        )
        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["intervals"]["eligible"], 1)
        self.assertEqual(report["intervals"]["matched"], 1)
        self.assertEqual(report["body_sets"]["endpoint_bodies_checked"], 1)
        self.assertEqual(report["body_sets"]["mode_bit_cleared_pointers"], 1)
        match = report["retained_transition_matches"][0]
        self.assertEqual(match["compatible_branch_count"], 1)
        self.assertEqual(match["capture_to_issue_steps"], 2)
        self.assertEqual(match["post_issue_steps"], 1)
        self.assertEqual(match["scalar_contact_body_ids"], [0x1000])
        self.assertEqual(match["scalar_damage_body_ids"], [0x1000])

    def test_mode_inconsistent_endpoint_flags_fail_integrity(self) -> None:
        report = _report(
            [
                _decision(
                    frame=1,
                    enemy_frame=1,
                    mode_state=(1, False, 0),
                    active_action="focus",
                    active_mask=0x05,
                    selected_action="focus",
                    selected_mask=0x05,
                    delay_support=(1,),
                ),
                _decision(
                    frame=2,
                    enemy_frame=2,
                    mode_state=(1, True, 7),
                    active_action="focus",
                    active_mask=0x05,
                    selected_action="focus",
                    selected_mask=0x05,
                    delay_support=(1,),
                    body_flags=0x00000145,
                ),
            ]
        )
        self.assertFalse(report["integrity"]["passed"])
        self.assertEqual(report["intervals"]["mismatched"], 1)
        self.assertEqual(
            report["integrity"]["errors"]["causal_endpoint_mismatch_count"],
            1,
        )
        self.assertEqual(len(report["retained_mismatches"]), 1)
        self.assertEqual(
            report["retained_mismatches"][0]["mismatch_code"],
            "mode_or_body_endpoint_outside_manager_frame_decomposition",
        )

    def test_exact_delay_branch_can_be_a_member_of_observed_belief(self) -> None:
        report = _report(
            [
                _decision(
                    frame=10,
                    enemy_frame=9,
                    mode_state=(1, True, 10),
                    active_action="down",
                    active_mask=0x25,
                    selected_action="stay",
                    selected_mask=0x05,
                    delay_support=(1, 2, 3, 4),
                    body_flags=0x00000945,
                ),
                _decision(
                    frame=12,
                    enemy_frame=11,
                    mode_state=(1, True, 12),
                    active_action="down",
                    active_mask=0x25,
                    held_action="stay",
                    held_mask=0x05,
                    pending_action="stay",
                    pending_mask=0x05,
                    remaining_delay_support=(1, 2),
                    selected_action="stay",
                    selected_mask=0x05,
                    delay_support=(1, 2, 3, 4),
                    body_flags=0x00000945,
                ),
            ]
        )
        self.assertTrue(report["integrity"]["passed"])
        match = report["retained_transition_matches"][0]
        self.assertEqual(match["compatible_branch_count"], 2)
        self.assertEqual(match["successor_root_compatible_branch_count"], 2)
        self.assertEqual(match["successor_root_exact_compatible_branch_count"], 0)

    def test_ordered_partial_transition_mask_is_a_physical_model_mismatch(
        self,
    ) -> None:
        report = _report(
            [
                _decision(
                    frame=386,
                    enemy_frame=384,
                    mode_state=(1, True, 1),
                    active_action="down_left_focus",
                    active_mask=0x65,
                    selected_action="left_fast",
                    selected_mask=0x41,
                    delay_support=(2,),
                    body_flags=0x00000945,
                    dispatch_transitions=((0x04, False), (0x20, False)),
                ),
                _decision(
                    frame=389,
                    enemy_frame=387,
                    mode_state=(1, True, 4),
                    active_action="down_left_fast",
                    active_mask=0x61,
                    held_action="left_fast",
                    held_mask=0x41,
                    pending_action="left_fast",
                    pending_mask=0x41,
                    remaining_delay_support=(1,),
                    selected_action="left_fast",
                    selected_mask=0x41,
                    delay_support=(2,),
                    body_flags=0x00000945,
                ),
            ]
        )
        self.assertFalse(report["integrity"]["passed"])
        self.assertEqual(report["intervals"]["eligible"], 1)
        self.assertEqual(
            report["intervals"]["mismatch_counts"],
            {"observed_ordered_partial_transition_mask": 1},
        )
        mismatch = report["retained_mismatches"][0]
        self.assertEqual(
            mismatch["mismatch_code"],
            "observed_ordered_partial_transition_mask",
        )
        self.assertEqual(mismatch["dispatch_transition_masks"], [0x61, 0x41])
        self.assertEqual(mismatch["observed_current_active_mask"], 0x61)
        self.assertGreater(mismatch["mode_body_compatible_branch_count"], 0)
        self.assertEqual(
            report["ordered_partial_transactions"],
            {
                "observed_count": 1,
                "unique_signature_count": 1,
                "edge_position_counts": {"1/2": 1},
                "focus_path_counts": {"1->0->0": 1},
                "shot_path_counts": {"1->1->1": 1},
                "direction_path_counts": {"0x60->0x60->0x40": 1},
                "top_signatures": [
                    {
                        "signature": "0x65->0x61->0x41|observed=0x61",
                        "count": 1,
                    }
                ],
            },
        )

    def test_nondecision_boundary_and_empty_endpoint_are_excluded(self) -> None:
        report = _report(
            [
                _decision(
                    frame=1,
                    enemy_frame=1,
                    mode_state=(0, False, 0),
                    active_action="fast",
                    active_mask=0x01,
                    selected_action="fast",
                    selected_mask=0x01,
                    delay_support=(1,),
                ),
                {"kind": "auto_confirm_wall_pulse", "frame": 1},
                _decision(
                    frame=2,
                    enemy_frame=2,
                    mode_state=(0, False, 1),
                    active_action="fast",
                    active_mask=0x01,
                    selected_action="fast",
                    selected_mask=0x01,
                    delay_support=(1,),
                ),
                _decision(
                    frame=3,
                    enemy_frame=3,
                    mode_state=(0, False, 2),
                    active_action="fast",
                    active_mask=0x01,
                    selected_action="fast",
                    selected_mask=0x01,
                    delay_support=(1,),
                    body_flags=None,
                ),
                _decision(
                    frame=4,
                    enemy_frame=4,
                    mode_state=(0, False, 3),
                    active_action="fast",
                    active_mask=0x01,
                    selected_action="fast",
                    selected_mask=0x01,
                    delay_support=(1,),
                ),
            ]
        )
        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["intervals"]["eligible"], 1)
        self.assertEqual(
            report["intervals"]["exclusion_counts"],
            {
                "intervening_nondecision_trace_record": 1,
                "no_mode_sensitive_endpoint_bodies": 1,
            },
        )

    def test_incoherent_capture_breaks_adjacency(self) -> None:
        rows = [
            _decision(
                frame=1,
                enemy_frame=1,
                mode_state=(0, False, 0),
                active_action="fast",
                active_mask=0x01,
                selected_action="fast",
                selected_mask=0x01,
                delay_support=(1,),
            ),
            _decision(
                frame=2,
                enemy_frame=2,
                mode_state=(0, False, 1),
                active_action="fast",
                active_mask=0x01,
                selected_action="fast",
                selected_mask=0x01,
                delay_support=(1,),
                coherent=False,
            ),
            _decision(
                frame=3,
                enemy_frame=3,
                mode_state=(0, False, 2),
                active_action="fast",
                active_mask=0x01,
                selected_action="fast",
                selected_mask=0x01,
                delay_support=(1,),
            ),
            _decision(
                frame=4,
                enemy_frame=4,
                mode_state=(0, False, 3),
                active_action="fast",
                active_mask=0x01,
                selected_action="fast",
                selected_mask=0x01,
                delay_support=(1,),
            ),
        ]
        report = _report(rows)
        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["rows"]["coherent"], 3)
        self.assertEqual(report["intervals"]["adjacent_coherent"], 1)

    def test_capture_authority_tamper_fails_integrity(self) -> None:
        report = _report(
            [
                _decision(
                    frame=1,
                    enemy_frame=1,
                    mode_state=(0, False, 0),
                    active_action="fast",
                    active_mask=0x01,
                    selected_action="fast",
                    selected_mask=0x01,
                    delay_support=(1,),
                    action_authority=True,
                ),
                _decision(
                    frame=2,
                    enemy_frame=2,
                    mode_state=(0, False, 1),
                    active_action="fast",
                    active_mask=0x01,
                    selected_action="fast",
                    selected_mask=0x01,
                    delay_support=(1,),
                ),
            ]
        )
        self.assertFalse(report["integrity"]["passed"])
        self.assertEqual(
            report["integrity"]["errors"][
                "capture_action_authority_true_or_missing_lines"
            ],
            [1],
        )


if __name__ == "__main__":
    unittest.main()
