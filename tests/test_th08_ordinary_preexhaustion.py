from __future__ import annotations

import unittest
from types import SimpleNamespace

from th08_live.controller import (
    _ordinary_nonspell_preexhaustion_filter,
    _ordinary_target_query_frame,
)
from th08_time_scale import TH08_UNIT_TIME_SCALE_BITS
from touhou_control.local_pipeline_oracle import LocalPipelineRoot


class OrdinaryNonspellPreexhaustionTests(unittest.TestCase):
    def _build(self, **overrides):
        arguments = {
            "enabled": True,
            "spell_active": False,
            "player_phase": 0,
            "root_scale_bits": TH08_UNIT_TIME_SCALE_BITS,
            "root": LocalPipelineRoot("stay", "stay"),
            "action_hold_frames": 3,
            "player_x": 192.0,
            "player_y": 400.0,
            "current_frame": 100,
            "future_solution": None,
            "future_hazard_coverage": None,
        }
        arguments.update(overrides)
        return _ordinary_nonspell_preexhaustion_filter(**arguments)

    def test_phase_zero_is_not_blocked_by_retained_deathbomb_limit(self) -> None:
        result = self._build()

        self.assertTrue(result.state_eligible)
        self.assertEqual(result.reason, "future_policy_unavailable")

    def test_phase_three_remains_a_native_movement_phase(self) -> None:
        result = self._build(player_phase=3)

        self.assertTrue(result.state_eligible)
        self.assertEqual(result.reason, "future_policy_unavailable")

    def test_spell_phase_has_no_authority(self) -> None:
        result = self._build(spell_active=True)

        self.assertFalse(result.authority_eligible)
        self.assertEqual(result.reason, "spell_active")

    def test_nonunit_root_scale_fails_closed(self) -> None:
        result = self._build(root_scale_bits=0x3F000000)

        self.assertFalse(result.authority_eligible)
        self.assertEqual(result.reason, "nonunit_root_time_scale")

    def test_player_transition_fails_closed(self) -> None:
        result = self._build(player_phase=2)

        self.assertFalse(result.state_eligible)
        self.assertEqual(result.reason, "player_transition")

    def test_active_policy_target_keeps_a_complete_pickup_lease(self) -> None:
        policy = SimpleNamespace(
            config=SimpleNamespace(frames_per_layer=8),
            horizon_frames=80,
        )

        self.assertEqual(
            _ordinary_target_query_frame(policy=policy, policy_age=0),
            8,
        )
        self.assertEqual(
            _ordinary_target_query_frame(policy=policy, policy_age=1),
            8,
        )
        self.assertEqual(
            _ordinary_target_query_frame(policy=policy, policy_age=2),
            16,
        )
        self.assertIsNone(
            _ordinary_target_query_frame(policy=policy, policy_age=73)
        )
