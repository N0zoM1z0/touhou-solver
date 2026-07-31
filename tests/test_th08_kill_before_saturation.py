from __future__ import annotations

import unittest

from th08_live.enemy_combat_progress import (
    EnemyCombatProgressInventory,
    EnemyCombatProgressObservation,
)
from th08_live.kill_before_saturation import (
    KillBeforeSaturationTarget,
    choose_kill_before_saturation_preference,
    observe_kill_before_saturation_target,
    unfocused_peer_action,
)
from th08_live.models import EnemyBody
from th08_live.movement import PLANNER_ACTIONS


def _inventory(
    *,
    health: int = 20,
    maximum_health: int = 200,
    enemy_pointer: int = 0x5D63C0,
) -> EnemyCombatProgressInventory:
    return EnemyCombatProgressInventory(
        scanned_slots=64,
        active_slots=1,
        observations=(
            EnemyCombatProgressObservation(
                slot=16,
                enemy_pointer=enemy_pointer,
                flags=0,
                flags2=0,
                current_health=health,
                maximum_health=maximum_health,
                phase_start_health=maximum_health,
                frame_damage=0,
                local_damage_flags_open=False,
                defeat_mode=0,
            ),
        ),
        decode_ms=0.1,
    )


def _target(
    *,
    x: float = 145.0,
    vx: float = 0.0,
    current_health: int = 20,
    maximum_health: int = 30,
) -> KillBeforeSaturationTarget:
    return KillBeforeSaturationTarget(
        slot=16,
        enemy_pointer=0x5D63C0,
        current_health=current_health,
        maximum_health=maximum_health,
        x=x,
        y=90.0,
        vx=vx,
        vy=0.0,
        half_width=12.0,
        position_uncertainty=0.0,
        horizontal_separation=x - 192.0,
        vertical_separation=330.0,
        local_damage_flags_open=True,
    )


class KillBeforeSaturationTests(unittest.TestCase):
    def test_native_root_shape_selects_low_hp_target_before_gate_opens(
        self,
    ) -> None:
        result = observe_kill_before_saturation_target(
            enabled=True,
            inventory=_inventory(),
            enemy_bodies=(
                EnemyBody(
                    pointer=0x5D63C0,
                    x=262.94,
                    y=91.34,
                    vx=0.0,
                    vy=0.0,
                    half_width=12.0,
                    half_height=12.0,
                    flags=1,
                ),
            ),
            player_x=187.51,
            player_y=427.19,
            power=114.0,
            spell_active=False,
        )

        self.assertEqual(result.reason, "low_hp_ordinary_enemy_observed")
        self.assertIsNotNone(result.target)
        assert result.target is not None
        self.assertEqual(result.target.enemy_pointer, 0x5D63C0)
        self.assertFalse(result.target.local_damage_flags_open)

    def test_small_enemy_is_observed_at_full_health_and_boss_is_excluded(
        self,
    ) -> None:
        common = {
            "enabled": True,
            "inventory": _inventory(
                health=30,
                maximum_health=30,
            ),
            "enemy_bodies": (
                EnemyBody(
                    pointer=0x5D63C0,
                    x=20.0,
                    y=90.0,
                    vx=1.0,
                    vy=0.0,
                    half_width=12.0,
                    half_height=12.0,
                    flags=1,
                ),
            ),
            "player_x": 190.0,
            "player_y": 420.0,
            "power": 114.0,
            "spell_active": False,
        }
        observed = observe_kill_before_saturation_target(**common)

        self.assertEqual(
            observed.reason,
            "small_ordinary_enemy_observed",
        )
        self.assertIsNotNone(observed.target)
        assert observed.target is not None
        self.assertEqual(observed.target.vx, 1.0)
        self.assertEqual(observed.target.half_width, 12.0)
        self.assertIsNone(
            observe_kill_before_saturation_target(
                **common,
                excluded_enemy_pointer=0x5D63C0,
            ).target
        )

    def test_policy_fails_closed_outside_root_supported_scope(self) -> None:
        common = {
            "enabled": True,
            "inventory": _inventory(),
            "enemy_bodies": (
                EnemyBody(
                    pointer=0x5D63C0,
                    x=260.0,
                    y=90.0,
                    vx=0.0,
                    vy=0.0,
                    half_width=12.0,
                    half_height=12.0,
                    flags=1,
                ),
            ),
            "player_x": 190.0,
            "player_y": 420.0,
            "power": 114.0,
            "spell_active": False,
        }
        self.assertIsNone(
            observe_kill_before_saturation_target(
                **{**common, "spell_active": True}
            ).target
        )
        self.assertIsNone(
            observe_kill_before_saturation_target(
                **{**common, "power": 99.0}
            ).target
        )
        self.assertIsNone(
            observe_kill_before_saturation_target(
                **{**common, "inventory": _inventory(health=23)}
            ).target
        )

    def test_unfocused_peer_preserves_direction_and_rejects_stay(self) -> None:
        self.assertEqual(
            unfocused_peer_action(
                "down_left",
                actions=PLANNER_ACTIONS,
            ),
            "down_left_fast",
        )
        self.assertIsNone(
            unfocused_peer_action(
                "down_left_fast",
                actions=PLANNER_ACTIONS,
            )
        )
        self.assertIsNone(
            unfocused_peer_action("stay", actions=PLANNER_ACTIONS)
        )

    def test_winning_global_set_moves_toward_observed_enemy_location(
        self,
    ) -> None:
        result = choose_kill_before_saturation_preference(
            "stay",
            target=_target(),
            player_x=192.0,
            action_hold_frames=3,
            target_forecast_frames=6,
            allowed_first_actions=tuple(
                action.name for action in PLANNER_ACTIONS
            ),
            actions=PLANNER_ACTIONS,
        )

        self.assertEqual(result.action, "left_fast")
        self.assertEqual(
            result.reason,
            "global_viable_target_alignment",
        )
        self.assertGreater(result.alignment_improvement, 0.0)

    def test_target_velocity_is_forecast_without_changing_observations(
        self,
    ) -> None:
        result = choose_kill_before_saturation_preference(
            "stay",
            target=_target(x=190.0, vx=2.0),
            player_x=192.0,
            action_hold_frames=3,
            target_forecast_frames=6,
            allowed_first_actions=("stay", "right", "right_fast"),
            actions=PLANNER_ACTIONS,
        )

        self.assertEqual(result.target_x, 202.0)
        self.assertEqual(result.action, "right_fast")

    def test_preference_fails_closed_after_global_exhaustion(
        self,
    ) -> None:
        result = choose_kill_before_saturation_preference(
            "stay",
            target=_target(),
            player_x=192.0,
            action_hold_frames=3,
            target_forecast_frames=6,
            allowed_first_actions=None,
            actions=PLANNER_ACTIONS,
        )

        self.assertIsNone(result.action)
        self.assertEqual(
            result.reason,
            "global_viability_unavailable_or_exhausted",
        )

    def test_preference_preserves_vertical_tendency_and_unfocus_fallback(
        self,
    ) -> None:
        rejected = choose_kill_before_saturation_preference(
            "up",
            target=_target(),
            player_x=192.0,
            action_hold_frames=3,
            target_forecast_frames=6,
            allowed_first_actions=("left_fast",),
            actions=PLANNER_ACTIONS,
        )
        fallback = choose_kill_before_saturation_preference(
            "up",
            target=_target(x=192.0),
            player_x=192.0,
            action_hold_frames=3,
            target_forecast_frames=6,
            allowed_first_actions=("up", "up_fast"),
            actions=PLANNER_ACTIONS,
        )

        self.assertIsNone(rejected.action)
        self.assertEqual(
            rejected.reason,
            "no_global_safe_action_preserves_vertical_tendency",
        )
        self.assertEqual(fallback.action, "up_fast")
        self.assertEqual(
            fallback.reason,
            "global_viable_same_direction_unfocused",
        )


if __name__ == "__main__":
    unittest.main()
