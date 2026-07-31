from __future__ import annotations

import unittest

from th08_runtime.game_state import (
    ADDR_CURRENT_INPUT,
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_GAMEPLAY_TIME_SCALE,
    ADDR_PLAYER,
    ADDR_PREVIOUS_INPUT,
    ADDR_RAW_INPUT,
    PLAYER_POSITION_OFFSET,
)
from th08_runtime.sensing import capture_player_control_root


class _Reader:
    def __init__(self, values: dict[tuple[str, int], list[object]]) -> None:
        self.values = {
            key: list(sequence) for key, sequence in values.items()
        }

    def _next(self, kind: str, address: int):
        return self.values[(kind, address)].pop(0)

    def u32(self, address: int) -> int:
        return int(self._next("u32", address))

    def u16(self, address: int) -> int:
        return int(self._next("u16", address))

    def f32(self, address: int) -> float:
        return float(self._next("f32", address))


def _values(
    *,
    frames: list[int],
    xs: list[float],
    ys: list[float],
    attempts: int,
) -> dict[tuple[str, int], list[object]]:
    return {
        ("u32", ADDR_ENEMY_MANAGER_FRAME): frames,
        ("u32", ADDR_GAMEPLAY_TIME_SCALE): [0x3F800000] * attempts,
        ("u16", ADDR_RAW_INPUT): [0x100, 0x100] * attempts,
        ("u16", ADDR_CURRENT_INPUT): [0x05, 0x05] * attempts,
        ("u16", ADDR_PREVIOUS_INPUT): [0x01, 0x01] * attempts,
        ("f32", ADDR_PLAYER + PLAYER_POSITION_OFFSET): xs,
        ("f32", ADDR_PLAYER + PLAYER_POSITION_OFFSET + 4): ys,
    }


class PlayerControlRootTests(unittest.TestCase):
    def test_stable_root_binds_position_input_scale_and_frame(self) -> None:
        capture = capture_player_control_root(
            _Reader(
                _values(
                    frames=[100, 100],
                    xs=[192.0, 192.0],
                    ys=[400.0, 400.0],
                    attempts=1,
                )
            )
        )

        self.assertTrue(capture.stable)
        self.assertEqual(capture.attempts, 1)
        self.assertEqual(capture.frame_after, 100)
        self.assertEqual(capture.x, 192.0)
        self.assertEqual(capture.y, 400.0)
        self.assertEqual(capture.input_current, 0x05)
        self.assertEqual(capture.scale_bits, 0x3F800000)

    def test_frozen_manager_frame_does_not_hide_player_motion(self) -> None:
        capture = capture_player_control_root(
            _Reader(
                _values(
                    frames=[100, 100],
                    xs=[192.0, 194.0],
                    ys=[400.0, 400.0],
                    attempts=1,
                )
            ),
            maximum_attempts=1,
        )

        self.assertFalse(capture.stable)

    def test_retry_accepts_only_the_later_coherent_root(self) -> None:
        capture = capture_player_control_root(
            _Reader(
                _values(
                    frames=[100, 100, 101, 101],
                    xs=[192.0, 193.0, 194.0, 194.0],
                    ys=[400.0, 400.0, 398.0, 398.0],
                    attempts=2,
                )
            ),
            maximum_attempts=2,
        )

        self.assertTrue(capture.stable)
        self.assertEqual(capture.attempts, 2)
        self.assertEqual(capture.frame_after, 101)
        self.assertEqual((capture.x, capture.y), (194.0, 398.0))

    def test_attempt_count_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "attempts"):
            capture_player_control_root(
                _Reader({}),
                maximum_attempts=0,
            )


if __name__ == "__main__":
    unittest.main()
