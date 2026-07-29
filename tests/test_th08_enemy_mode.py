#!/usr/bin/env python3
"""Tests for action/history-conditioned TH08 enemy mode gates."""

from __future__ import annotations

import itertools
import unittest

from th08_enemy_mode import (
    ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG,
    Route2EnemyModeBody,
    merge_route2_mode_decision_observation_classes,
    merge_route2_mode_observation_classes,
    project_enemy_mode,
    project_route2_enemy_mode,
    project_route2_mode_decision_branches,
    project_route2_mode_pipeline_branches,
    route2_enemy_mode_state_key,
    step_route2_enemy_mode_state,
)
from th08_option_model import Route2FocusState, step_route2_focus
from touhou_control.local_pipeline_oracle import LocalPipelineRoot


def _oracle_step(
    state: tuple[int, bool, int],
    focused: bool,
) -> tuple[int, bool, int]:
    focus_value, secondary_active, counter = state
    if focused:
        counter = counter + 1 if focus_value == 1 else 0
        if counter >= 7:
            secondary_active = True
        focus_value = 1
    else:
        counter = 0 if focus_value != 0 else counter + 1
        if counter >= 7:
            secondary_active = False
        focus_value = 0
    return focus_value, secondary_active, counter


class EnemyModeTests(unittest.TestCase):
    MODE_SENSITIVE_CONTACT_AND_DAMAGE = 0x0100114D

    def test_secondary_character_blocks_contact_and_damage_together(self) -> None:
        human = project_enemy_mode(
            self.MODE_SENSITIVE_CONTACT_AND_DAMAGE,
            secondary_character_active=False,
        )
        self.assertTrue(human.secondary_character_synchronized)
        self.assertTrue(human.manager_gate_open)
        self.assertTrue(human.contact_eligible)
        self.assertTrue(human.player_shot_damage_eligible)

        secondary = project_enemy_mode(
            self.MODE_SENSITIVE_CONTACT_AND_DAMAGE,
            secondary_character_active=True,
        )
        self.assertEqual(
            secondary.projected_flags,
            human.projected_flags | ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG,
        )
        self.assertFalse(secondary.manager_gate_open)
        self.assertFalse(secondary.contact_eligible)
        self.assertFalse(secondary.player_shot_damage_eligible)

    def test_contact_and_player_shot_damage_bits_are_independent(self) -> None:
        contact_only = project_enemy_mode(
            0x00000005,
            secondary_character_active=False,
        )
        self.assertTrue(contact_only.contact_eligible)
        self.assertFalse(contact_only.player_shot_damage_eligible)

        damage_only = project_enemy_mode(
            0x00000041,
            secondary_character_active=False,
        )
        self.assertFalse(damage_only.contact_eligible)
        self.assertTrue(damage_only.player_shot_damage_eligible)

    def test_non_synchronized_enemy_preserves_observed_bit_0x800(self) -> None:
        raw = 0x00000845
        for secondary_active in (False, True):
            projection = project_enemy_mode(
                raw,
                secondary_character_active=secondary_active,
            )
            self.assertFalse(projection.secondary_character_synchronized)
            self.assertEqual(projection.projected_flags, raw)
            self.assertFalse(projection.manager_gate_open)

    def test_blocking_bits_0x10_and_0x20_remain_distinct_from_mode_sync(self) -> None:
        for flag in (0x10, 0x20):
            projection = project_enemy_mode(
                0x00000145 | flag,
                secondary_character_active=False,
            )
            self.assertTrue(projection.secondary_character_synchronized)
            self.assertFalse(projection.manager_gate_open)
            self.assertFalse(projection.contact_eligible)
            self.assertFalse(projection.player_shot_damage_eligible)

    def test_ce_0176_frame_10065_to_10075_release_opens_gate(self) -> None:
        state = Route2FocusState(
            focus_logic_value=1,
            remilia_character_active=True,
            transition_counter=7,
        )
        eligibility: list[bool] = []
        for _ in range(8):
            state = step_route2_focus(
                state,
                focused=False,
                post_movement_player_x=0.0,
                post_movement_player_y=0.0,
            )
            eligibility.append(
                project_route2_enemy_mode(
                    self.MODE_SENSITIVE_CONTACT_AND_DAMAGE,
                    focus_state=state,
                ).contact_eligible
            )
        self.assertEqual(eligibility, [False] * 7 + [True])

        blocked_again: list[bool] = []
        for _ in range(8):
            state = step_route2_focus(
                state,
                focused=True,
                post_movement_player_x=0.0,
                post_movement_player_y=0.0,
            )
            blocked_again.append(
                not project_route2_enemy_mode(
                    self.MODE_SENSITIVE_CONTACT_AND_DAMAGE,
                    focus_state=state,
                ).contact_eligible
            )
        self.assertEqual(blocked_again, [False] * 7 + [True])

    def test_adversarial_focus_histories_match_independent_scalar_oracle(
        self,
    ) -> None:
        initial_states = (
            Route2FocusState(),
            Route2FocusState(focus_logic_value=2),
            Route2FocusState(
                focus_logic_value=1,
                remilia_character_active=True,
                transition_counter=11,
            ),
        )
        for initial in initial_states:
            for history in itertools.product((False, True), repeat=9):
                model = initial
                oracle = route2_enemy_mode_state_key(initial)
                for focused in history:
                    self.assertEqual(
                        step_route2_enemy_mode_state(
                            oracle,
                            focused=focused,
                        ),
                        _oracle_step(oracle, focused),
                    )
                    model = step_route2_focus(
                        model,
                        focused=focused,
                        post_movement_player_x=0.0,
                        post_movement_player_y=0.0,
                    )
                    oracle = _oracle_step(oracle, focused)
                    self.assertEqual(
                        route2_enemy_mode_state_key(model),
                        oracle,
                    )
                    expected_contact = not oracle[1]
                    projection = project_route2_enemy_mode(
                        self.MODE_SENSITIVE_CONTACT_AND_DAMAGE,
                        focus_state=model,
                    )
                    self.assertEqual(
                        projection.contact_eligible,
                        expected_contact,
                    )
                    self.assertEqual(
                        projection.player_shot_damage_eligible,
                        expected_contact,
                    )

    def test_pipeline_pickup_delay_changes_mode_conditioned_body_gate(
        self,
    ) -> None:
        body_frames = tuple(
            (
                Route2EnemyModeBody(
                    identity=0x1000,
                    raw_flags=self.MODE_SENSITIVE_CONTACT_AND_DAMAGE,
                ),
            )
            for _ in range(10)
        )
        branches = project_route2_mode_pipeline_branches(
            pipeline_root=LocalPipelineRoot(
                active_action="fast",
                held_desired_action="fast",
            ),
            selected_action="focus",
            action_masks={"fast": 0x01, "focus": 0x05},
            delay_frames=(0, 2),
            initial_mode_state=(0, False, 7),
            enemy_flag_frames=body_frames,
        )
        self.assertEqual(
            tuple(branch.pipeline_branch.new_delay for branch in branches),
            (0, 2),
        )

        for branch in branches:
            oracle = (0, False, 7)
            for active_action, frame in zip(
                branch.pipeline_branch.active_actions,
                branch.frames,
                strict=True,
            ):
                oracle = _oracle_step(
                    oracle,
                    bool({"fast": 0x01, "focus": 0x05}[active_action] & 0x04),
                )
                self.assertEqual(frame.mode_state_after, oracle)
                self.assertEqual(
                    frame.contact_body_ids,
                    () if oracle[1] else (0x1000,),
                )
                self.assertEqual(
                    frame.player_shot_damage_body_ids,
                    () if oracle[1] else (0x1000,),
                )

        delay_zero, delay_two = branches
        self.assertEqual(
            tuple(frame.active_action for frame in delay_zero.frames[:3]),
            ("focus", "focus", "focus"),
        )
        self.assertEqual(
            tuple(frame.active_action for frame in delay_two.frames[:3]),
            ("fast", "fast", "focus"),
        )
        self.assertEqual(delay_zero.frames[7].contact_body_ids, ())
        self.assertEqual(delay_two.frames[7].contact_body_ids, (0x1000,))
        self.assertEqual(delay_two.frames[9].contact_body_ids, ())

    def test_no_write_preserves_pending_and_merges_hidden_remaining_delay(
        self,
    ) -> None:
        branches = project_route2_mode_pipeline_branches(
            pipeline_root=LocalPipelineRoot(
                active_action="left_fast",
                held_desired_action="right_fast",
                pending_action="right_fast",
                remaining_delay_support=(1, 2),
            ),
            selected_action="right_fast",
            action_masks={"left_fast": 0x01, "right_fast": 0x01},
            delay_frames=(0, 2),
            initial_mode_state=(0, False, 0),
            enemy_flag_frames=((), (), ()),
        )
        self.assertEqual(len(branches), 2)
        self.assertTrue(
            all(not branch.pipeline_branch.write_required for branch in branches)
        )
        self.assertEqual(
            tuple(branch.pipeline_branch.new_delay for branch in branches),
            (None, None),
        )
        self.assertEqual(
            tuple(branch.pipeline_branch.older_remaining for branch in branches),
            (1, 2),
        )

        classes = merge_route2_mode_observation_classes(
            branches,
            physical_step=3,
            base_observation=lambda _branch, _frame: (
                "same_position",
                "same_hazard_version",
            ),
        )
        self.assertEqual(len(classes), 1)
        self.assertEqual(len(classes[0].hidden_branches), 2)
        self.assertEqual(classes[0].key.active_action, "right_fast")
        self.assertEqual(classes[0].key.held_desired_action, "right_fast")

    def test_observation_merge_keeps_different_hidden_mode_states_apart(
        self,
    ) -> None:
        branches = project_route2_mode_pipeline_branches(
            pipeline_root=LocalPipelineRoot(
                active_action="fast",
                held_desired_action="fast",
            ),
            selected_action="focus",
            action_masks={"fast": 0x01, "focus": 0x05},
            delay_frames=(0, 2),
            initial_mode_state=(0, False, 0),
            enemy_flag_frames=((), (), ()),
        )
        classes = merge_route2_mode_observation_classes(
            branches,
            physical_step=3,
            base_observation=lambda _branch, _frame: "same_base",
        )
        self.assertEqual(len(classes), 2)
        self.assertEqual(
            {mode_class.key.active_action for mode_class in classes},
            {"focus"},
        )
        self.assertEqual(
            {mode_class.key.mode_state for mode_class in classes},
            {(1, False, 2), (1, False, 0)},
        )
        self.assertTrue(
            all(len(mode_class.hidden_branches) == 1 for mode_class in classes)
        )

    def test_pipeline_reproduces_ce_0176_release_gate_timing(self) -> None:
        branches = project_route2_mode_pipeline_branches(
            pipeline_root=LocalPipelineRoot(
                active_action="fast",
                held_desired_action="fast",
            ),
            selected_action="fast",
            action_masks={"fast": 0x01},
            delay_frames=(0, 2),
            initial_mode_state=(1, True, 7),
            enemy_flag_frames=tuple(
                (
                    Route2EnemyModeBody(
                        identity=0x1000,
                        raw_flags=self.MODE_SENSITIVE_CONTACT_AND_DAMAGE,
                    ),
                )
                for _ in range(8)
            ),
        )
        self.assertEqual(len(branches), 1)
        self.assertEqual(
            tuple(bool(frame.contact_body_ids) for frame in branches[0].frames),
            (False,) * 7 + (True,),
        )

    def test_decision_transition_branches_recursive_cadence_and_delay(
        self,
    ) -> None:
        branches = project_route2_mode_decision_branches(
            pipeline_root=LocalPipelineRoot(
                active_action="fast",
                held_desired_action="fast",
            ),
            selected_action="focus",
            action_masks={"fast": 0x01, "focus": 0x05},
            delay_frames=(2,),
            decision_frame_support=(1, 3),
            initial_mode_state=(0, False, 0),
            enemy_flag_frames=((), (), ()),
        )
        self.assertEqual(len(branches), 2)
        early, late = branches
        self.assertEqual(early.cadence_frames, 1)
        self.assertEqual(
            early.successor_pipeline_root,
            LocalPipelineRoot(
                active_action="fast",
                held_desired_action="focus",
                pending_action="focus",
                remaining_delay_support=(1,),
            ),
        )
        self.assertEqual(early.successor_mode_state, (0, False, 1))
        self.assertEqual(late.cadence_frames, 3)
        self.assertEqual(
            late.successor_pipeline_root,
            LocalPipelineRoot(
                active_action="focus",
                held_desired_action="focus",
            ),
        )
        self.assertEqual(late.successor_mode_state, (1, False, 0))

    def test_decision_observation_merges_remaining_delay_support(self) -> None:
        branches = project_route2_mode_decision_branches(
            pipeline_root=LocalPipelineRoot(
                active_action="fast",
                held_desired_action="fast",
            ),
            selected_action="focus",
            action_masks={"fast": 0x01, "focus": 0x05},
            delay_frames=(3, 4),
            decision_frame_support=(1,),
            initial_mode_state=(0, False, 0),
            enemy_flag_frames=((),),
        )
        classes = merge_route2_mode_decision_observation_classes(
            branches,
            base_observation=lambda _branch, _frame: (
                "same_position",
                "same_hazard_version",
            ),
        )
        self.assertEqual(len(classes), 1)
        self.assertEqual(len(classes[0].hidden_branches), 2)
        self.assertEqual(
            classes[0].successor_pipeline_root,
            LocalPipelineRoot(
                active_action="fast",
                held_desired_action="focus",
                pending_action="focus",
                remaining_delay_support=(2, 3),
            ),
        )
        self.assertEqual(classes[0].key.physical_step, 1)
        self.assertEqual(classes[0].key.mode_state, (0, False, 1))

    def test_decision_successor_can_be_recurred_without_resetting_pending(
        self,
    ) -> None:
        first = project_route2_mode_decision_branches(
            pipeline_root=LocalPipelineRoot(
                active_action="fast",
                held_desired_action="fast",
            ),
            selected_action="focus",
            action_masks={"fast": 0x01, "focus": 0x05},
            delay_frames=(3, 4),
            decision_frame_support=(1,),
            initial_mode_state=(0, False, 0),
            enemy_flag_frames=((),),
        )
        merged = merge_route2_mode_decision_observation_classes(
            first,
            base_observation=lambda _branch, _frame: "same_base",
        )
        second = project_route2_mode_decision_branches(
            pipeline_root=merged[0].successor_pipeline_root,
            selected_action="focus",
            action_masks={"fast": 0x01, "focus": 0x05},
            delay_frames=(0,),
            decision_frame_support=(1,),
            initial_mode_state=merged[0].key.mode_state,
            enemy_flag_frames=((),),
        )
        self.assertTrue(
            all(
                not branch.hazard_branch.pipeline_branch.write_required
                for branch in second
            )
        )
        self.assertEqual(
            tuple(
                branch.hazard_branch.pipeline_branch.older_remaining
                for branch in second
            ),
            (2, 3),
        )
        self.assertEqual(
            tuple(
                branch.successor_pipeline_root.remaining_delay_support
                for branch in second
            ),
            ((1,), (2,)),
        )

    def test_pipeline_rejects_bomb_masks_and_incomplete_action_map(self) -> None:
        common = {
            "pipeline_root": LocalPipelineRoot(
                active_action="fast",
                held_desired_action="fast",
            ),
            "selected_action": "focus",
            "delay_frames": (0,),
            "initial_mode_state": (0, False, 0),
            "enemy_flag_frames": ((),),
        }
        with self.assertRaisesRegex(ValueError, "hard no-Bomb"):
            project_route2_mode_pipeline_branches(
                **common,
                action_masks={"fast": 0x01, "focus": 0x07},
            )
        with self.assertRaisesRegex(ValueError, "missing complete action"):
            project_route2_mode_pipeline_branches(
                **common,
                action_masks={"fast": 0x01},
            )

    def test_mode_state_key_forbids_hidden_counter_merge(self) -> None:
        early = Route2FocusState(
            focus_logic_value=0,
            remilia_character_active=True,
            transition_counter=2,
        )
        late = Route2FocusState(
            focus_logic_value=0,
            remilia_character_active=True,
            transition_counter=6,
        )
        self.assertNotEqual(
            route2_enemy_mode_state_key(early),
            route2_enemy_mode_state_key(late),
        )


if __name__ == "__main__":
    unittest.main()
