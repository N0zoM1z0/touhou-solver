#!/usr/bin/env python3
"""Tests for action/history-conditioned TH08 enemy mode gates."""

from __future__ import annotations

import itertools
import unittest

from th08_enemy_mode import (
    ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG,
    project_enemy_mode,
    project_route2_enemy_mode,
    route2_enemy_mode_state_key,
)
from th08_option_model import Route2FocusState, step_route2_focus


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
