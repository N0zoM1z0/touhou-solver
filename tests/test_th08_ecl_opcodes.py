#!/usr/bin/env python3
"""Regression tests for solver-relevant ECL opcode classifications."""

from __future__ import annotations

import unittest

from th08_ecl_opcodes import opcode_spec
from th08_pattern_adapter import lower_opcode_9b, lower_opcode_9d, lower_opcode_af


class Th08EclOpcodeTests(unittest.TestCase):
    def test_opcode_5f_is_forced_hp_zero_not_immediate_retirement(
        self,
    ) -> None:
        spec = opcode_spec(0x5F)
        self.assertEqual(
            spec.name,
            "zero_eligible_enemy_hp_with_score_items",
        )
        self.assertIn("active-bit retirement is deferred", spec.description)
        self.assertEqual(spec.confidence, "observed")

    def test_boss_flag_is_not_an_opaque_secondary_flag(self) -> None:
        spec = opcode_spec(0x53)
        self.assertEqual(spec.name, "set_boss_flag")
        self.assertEqual(spec.category, "boss")
        self.assertEqual(spec.confidence, "observed")

    def test_boss_phase_configuration_opcodes_retain_mode_gate(self) -> None:
        timer = opcode_spec(0x84)
        health = opcode_spec(0x85)
        timeout = opcode_spec(0x86)
        self.assertEqual(timer.confidence, "observed")
        self.assertIn("phase timer's elapsed value", timer.description)
        self.assertIn("engine-mode gate suppresses", health.description)
        self.assertIn("conditionally set", timeout.description)
        self.assertIn("reset the phase timer", timeout.description)

    def test_defeat_mode_is_not_a_render_mode(self) -> None:
        spec = opcode_spec(0x81)
        self.assertEqual(spec.name, "set_enemy_defeat_mode")
        self.assertEqual(spec.confidence, "observed")

    def test_animation_refresh_is_presentation_only(self) -> None:
        spec = opcode_spec(0x91)
        self.assertEqual(spec.name, "enable_enemy_animation_script_refresh")
        self.assertEqual(spec.category, "animation")
        self.assertEqual(spec.confidence, "observed")

    def test_timeline_spawn_suppression_lowers_to_neutral_gate(self) -> None:
        spec = opcode_spec(0xAF)
        self.assertEqual(spec.name, "set_timeline_enemy_spawn_suppressed")
        self.assertEqual(spec.confidence, "observed")
        self.assertTrue(lower_opcode_af(0).enabled)
        self.assertFalse(lower_opcode_af(1).enabled)

    def test_unreferenced_write_stays_out_of_solver_state(self) -> None:
        spec = opcode_spec(0x93)
        self.assertEqual(spec.name, "write_unreferenced_global_4ea290")
        self.assertEqual(spec.category, "validation")

    def test_player_bomb_interaction_flags_are_solver_state(self) -> None:
        pause = opcode_spec(0xAD)
        immunity = opcode_spec(0xB7)
        self.assertEqual(pause.name, "set_enemy_pause_during_bomb_or_transition")
        self.assertEqual(immunity.name, "set_enemy_bomb_damage_immunity")
        self.assertEqual(pause.confidence, "observed")
        self.assertEqual(immunity.confidence, "observed")

    def test_spell_reward_mode_lowers_without_visual_state(self) -> None:
        spec = opcode_spec(0x9B)
        self.assertEqual(spec.name, "set_fixed_spell_reward_mode")
        self.assertEqual(spec.confidence, "observed")
        self.assertIsNone(lower_opcode_9b(0))
        self.assertEqual(lower_opcode_9b(1).initial_bonus, 99_999_990)

    def test_shipped_trail_shape_has_no_historical_collision(self) -> None:
        spec = opcode_spec(0x9D)
        self.assertEqual(spec.name, "configure_enemy_trail")
        shipped = lower_opcode_9d(5, 15, 0, 1)
        self.assertTrue(shipped.presentation.enabled)
        self.assertIsNone(shipped.collision)

        hypothetical = lower_opcode_9d(7, 15, 13, 1)
        self.assertIsNotNone(hypothetical.collision)
        self.assertTrue(hypothetical.collision.interpolate_collision)

    def test_render_only_enemy_modes_are_classified(self) -> None:
        self.assertEqual(opcode_spec(0x9F).name, "set_enemy_render_layer")
        self.assertEqual(
            opcode_spec(0xB6).name,
            "set_secondary_animation_shared_anchor",
        )
        self.assertEqual(opcode_spec(0x9F).category, "animation")
        self.assertEqual(opcode_spec(0xB6).category, "animation")

    def test_stage_background_sequence_handlers_are_observed(self) -> None:
        self.assertEqual(opcode_spec(0xB3).confidence, "observed")
        self.assertEqual(opcode_spec(0xB4).confidence, "observed")
        self.assertEqual(opcode_spec(0xB5).confidence, "observed")


if __name__ == "__main__":
    unittest.main()
