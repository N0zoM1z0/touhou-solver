from __future__ import annotations

import unittest

from th08_live.enemy_combat_progress import (
    EnemyCombatProgressInventory,
    EnemyCombatProgressObservation,
)
from th08_live.kill_before_saturation import (
    observe_kill_before_saturation_target,
    unfocused_peer_action,
)
from th08_live.models import EnemyBody
from th08_live.movement import PLANNER_ACTIONS


def _inventory(*, health: int = 20) -> EnemyCombatProgressInventory:
    return EnemyCombatProgressInventory(
        scanned_slots=64,
        active_slots=1,
        observations=(
            EnemyCombatProgressObservation(
                slot=16,
                enemy_pointer=0x5D63C0,
                flags=0,
                flags2=0,
                current_health=health,
                maximum_health=200,
                phase_start_health=200,
                frame_damage=0,
                local_damage_flags_open=False,
                defeat_mode=0,
            ),
        ),
        decode_ms=0.1,
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


if __name__ == "__main__":
    unittest.main()
