from __future__ import annotations

import unittest
from types import SimpleNamespace

from th08_live.enemy_sensor import ENEMY_STRIDE
from th08_runtime.native_snapshot_projection import (
    ENEMY_ANM_PREFIX_SIZE,
    FRSCREEN_NOTIFICATION_COUNTERS_OFFSET,
    normalized_causal_component_records,
)


def _component(name: str, data: bytes) -> object:
    return SimpleNamespace(
        spec=SimpleNamespace(name=name),
        data=data,
    )


class NativeSnapshotProjectionTests(unittest.TestCase):
    def test_enemy_render_prefix_does_not_change_causal_digest(self) -> None:
        left = bytearray(ENEMY_STRIDE)
        right = bytearray(left)
        right[ENEMY_ANM_PREFIX_SIZE - 1] = 1

        left_record = normalized_causal_component_records(
            [_component("ordinary_enemy_ecl_and_callback_roots", left)]
        )
        right_record = normalized_causal_component_records(
            [_component("ordinary_enemy_ecl_and_callback_roots", right)]
        )

        self.assertEqual(left_record, right_record)

    def test_enemy_ecl_tail_change_changes_causal_digest(self) -> None:
        left = bytearray(ENEMY_STRIDE)
        right = bytearray(left)
        right[ENEMY_ANM_PREFIX_SIZE] = 1

        left_record = normalized_causal_component_records(
            [_component("ordinary_enemy_ecl_and_callback_roots", left)]
        )
        right_record = normalized_causal_component_records(
            [_component("ordinary_enemy_ecl_and_callback_roots", right)]
        )

        self.assertNotEqual(left_record, right_record)

    def test_broad_player_bytes_are_explicitly_replaced(self) -> None:
        left = normalized_causal_component_records(
            [
                _component(
                    "player_state_through_resource_transitions",
                    b"\x00" * 32,
                )
            ]
        )
        right = normalized_causal_component_records(
            [
                _component(
                    "player_state_through_resource_transitions",
                    b"\x01" * 32,
                )
            ]
        )

        self.assertEqual(left, right)
        self.assertEqual(
            left[0]["mode"],
            "replaced_by_explicit_collision_control_fields",
        )

    def test_unclassified_component_remains_byte_exact(self) -> None:
        left = normalized_causal_component_records(
            [_component("gameplay_rng_exact", b"\x00" * 8)]
        )
        right = normalized_causal_component_records(
            [_component("gameplay_rng_exact", b"\x00" * 7 + b"\x01")]
        )

        self.assertNotEqual(left, right)

    def test_frscreen_render_consumed_notification_counter_is_excluded(
        self,
    ) -> None:
        left = bytearray(0x118)
        right = bytearray(left)
        right[FRSCREEN_NOTIFICATION_COUNTERS_OFFSET] = 0x40

        left_record = normalized_causal_component_records(
            [_component("scheduler_gate_globals", left)]
        )
        right_record = normalized_causal_component_records(
            [_component("scheduler_gate_globals", right)]
        )

        self.assertEqual(left_record, right_record)

        right[0] = 1
        other_change = normalized_causal_component_records(
            [_component("scheduler_gate_globals", right)]
        )
        self.assertNotEqual(left_record, other_change)


if __name__ == "__main__":
    unittest.main()
