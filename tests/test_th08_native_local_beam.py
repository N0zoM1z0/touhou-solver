from __future__ import annotations

import math
import unittest

import numpy as np

import th08_live_dodge_agent as live
from touhou_control import native_backend


def _native_available() -> bool:
    return native_backend._load_local_beam_reduce_function() is not None


def _boundary_deficit(
    x: float,
    y: float,
    reserve: float,
    bounds: tuple[float, float, float, float],
) -> float:
    if reserve <= 0.0:
        return 0.0
    left, right, top, bottom = bounds
    return sum(
        (
            max(reserve - (x - left), 0.0),
            max(reserve - (right - x), 0.0),
            max(reserve - (y - top), 0.0),
            max(reserve - (bottom - y), 0.0),
        )
    )


def _minimum_travel_frames(
    x: float,
    y: float,
    target_x: float,
    target_y: float,
    diagonal_speed: float,
    cardinal_speed: float,
) -> float:
    horizontal = max(abs(x - target_x) - 6.0, 0.0)
    vertical = max(abs(y - target_y) - 6.0, 0.0)
    diagonal = min(horizontal, vertical)
    straight = max(horizontal, vertical) - diagonal
    return diagonal / diagonal_speed + straight / cardinal_speed


def _python_reduce(
    *,
    draft_x: np.ndarray,
    draft_y: np.ndarray,
    first_action: np.ndarray,
    last_direction: np.ndarray,
    last_focused: np.ndarray,
    collected_mask: np.ndarray,
    risk: np.ndarray,
    collisions: np.ndarray,
    minimum_clearance: np.ndarray,
    step: int,
    beam_width: int,
    target_x: float | None,
    target_y: float | None,
    target_deadline: int | None,
    item_safety_clearance: float,
    bounds: tuple[float, float, float, float],
    reserve_distance: float,
    diagonal_speed: float,
    cardinal_speed: float,
    certificate_collisions: np.ndarray,
    certificate_minimum: np.ndarray,
    survival_preferred: np.ndarray,
    safety_preferred: np.ndarray,
    recovery_distance: np.ndarray,
) -> np.ndarray:
    keys: list[tuple[object, ...]] = []
    for index, (x, y) in enumerate(zip(draft_x, draft_y)):
        action = int(first_action[index])
        gate_deficit = 0.0
        if target_x is not None:
            assert target_y is not None
            assert target_deadline is not None
            gate_deficit = max(
                _minimum_travel_frames(
                    float(x),
                    float(y),
                    target_x,
                    target_y,
                    diagonal_speed,
                    cardinal_speed,
                )
                - max(target_deadline - step, 0),
                0.0,
            )
        keys.append(
            (
                int(collisions[index]),
                int(certificate_collisions[action]),
                max(-float(certificate_minimum[action]), 0.0),
                max(-float(minimum_clearance[index]), 0.0),
                0 if survival_preferred[action] else 1,
                gate_deficit,
                max(
                    item_safety_clearance
                    - float(minimum_clearance[index]),
                    0.0,
                ),
                0 if safety_preferred[action] else 1,
                _boundary_deficit(
                    float(x),
                    float(y),
                    reserve_distance,
                    bounds,
                ),
                float(recovery_distance[action]),
                float(risk[index]),
                -float(minimum_clearance[index]),
            )
        )

    winners: dict[tuple[object, ...], int] = {}
    for index, (x, y) in enumerate(zip(draft_x, draft_y)):
        quantized = (
            round(float(x) * 0.5),
            round(float(y) * 0.5),
            int(last_direction[index]),
            bool(last_focused[index]),
            int(collected_mask[index]),
        )
        incumbent = winners.get(quantized)
        if incumbent is None or keys[index] < keys[incumbent]:
            winners[quantized] = index
    retained = sorted(winners.values(), key=keys.__getitem__)[:beam_width]
    return np.asarray(retained, dtype=np.int32)


def _native_reduce(**values: object) -> np.ndarray:
    result = native_backend.reduce_local_beam(
        position_quantization=0.5,
        playfield_left=8.0,
        playfield_right=376.0,
        playfield_top=16.0,
        playfield_bottom=432.0,
        **values,
    )
    if result is None:
        raise AssertionError("native local beam reducer is unavailable")
    return result


@unittest.skipUnless(_native_available(), "native local beam reducer unavailable")
class NativeLocalBeamTests(unittest.TestCase):
    def assert_reducer_parity(self, **values: object) -> None:
        bounds = (8.0, 376.0, 16.0, 432.0)
        reference = _python_reduce(bounds=bounds, **values)
        native = _native_reduce(**values)
        np.testing.assert_array_equal(native, reference)

    def test_half_grid_rounding_and_stable_equal_keys(self) -> None:
        self.assert_reducer_parity(
            draft_x=np.asarray([9.0, 8.9, 11.0, 11.1, 30.0], dtype=np.float64),
            draft_y=np.asarray([17.0, 17.1, 19.0, 18.9, 30.0], dtype=np.float64),
            first_action=np.asarray([0, 0, 1, 1, 0], dtype=np.int32),
            last_direction=np.asarray([1, 1, 2, 2, 0], dtype=np.int32),
            last_focused=np.asarray([0, 0, 1, 1, 1], dtype=np.uint8),
            collected_mask=np.zeros(5, dtype=np.uint32),
            risk=np.asarray([5.0, 4.0, 3.0, 2.0, 1.0], dtype=np.float64),
            collisions=np.zeros(5, dtype=np.int32),
            minimum_clearance=np.full(5, 9.0, dtype=np.float64),
            step=3,
            beam_width=5,
            target_x=None,
            target_y=None,
            target_deadline=None,
            item_safety_clearance=8.0,
            reserve_distance=0.0,
            diagonal_speed=3.5 / math.sqrt(2.0),
            cardinal_speed=3.5,
            certificate_collisions=np.zeros(2, dtype=np.int32),
            certificate_minimum=np.full(2, 12.0, dtype=np.float64),
            survival_preferred=np.ones(2, dtype=np.uint8),
            safety_preferred=np.ones(2, dtype=np.uint8),
            recovery_distance=np.full(2, math.inf, dtype=np.float64),
        )

    def test_adversarial_lexicographic_columns(self) -> None:
        count = 12
        self.assert_reducer_parity(
            draft_x=np.linspace(8.0, 376.0, count, dtype=np.float64),
            draft_y=np.linspace(432.0, 16.0, count, dtype=np.float64),
            first_action=np.asarray([0, 1, 2] * 4, dtype=np.int32),
            last_direction=np.asarray(range(count), dtype=np.int32),
            last_focused=np.asarray([0, 1] * 6, dtype=np.uint8),
            collected_mask=np.asarray(range(count), dtype=np.uint32),
            risk=np.asarray(
                [0.0, 1.0, 1.0, 2.0, 3.0, 3.0, 4.0, 5.0, 5.0, 6.0, 7.0, 7.0],
                dtype=np.float64,
            ),
            collisions=np.asarray([0, 0, 1] * 4, dtype=np.int32),
            minimum_clearance=np.asarray(
                [math.inf, 10.0, -1.0, 8.0, 0.0, 4.0] * 2,
                dtype=np.float64,
            ),
            step=7,
            beam_width=8,
            target_x=192.0,
            target_y=400.0,
            target_deadline=10,
            item_safety_clearance=8.0,
            reserve_distance=14.0,
            diagonal_speed=3.5 / math.sqrt(2.0),
            cardinal_speed=3.5,
            certificate_collisions=np.asarray([0, 1, 0], dtype=np.int32),
            certificate_minimum=np.asarray([2.0, -3.0, 0.0], dtype=np.float64),
            survival_preferred=np.asarray([1, 0, 1], dtype=np.uint8),
            safety_preferred=np.asarray([0, 1, 1], dtype=np.uint8),
            recovery_distance=np.asarray([math.inf, 5.0, 0.0], dtype=np.float64),
        )

    def test_randomized_differential(self) -> None:
        rng = np.random.default_rng(0xCE0124)
        for case in range(96):
            action_count = int(rng.integers(1, 18))
            draft_count = int(rng.integers(1, 420))
            target_enabled = bool(case % 2)
            minimum = rng.uniform(-12.0, 80.0, draft_count)
            if case % 7 == 0:
                minimum[0] = math.inf
            recovery = rng.uniform(0.0, 100.0, action_count)
            if case % 3 == 0:
                recovery[0] = math.inf
            self.assert_reducer_parity(
                draft_x=rng.uniform(8.0, 376.0, draft_count),
                draft_y=rng.uniform(16.0, 432.0, draft_count),
                first_action=rng.integers(
                    0,
                    action_count,
                    draft_count,
                    dtype=np.int32,
                ),
                last_direction=rng.integers(
                    0,
                    16,
                    draft_count,
                    dtype=np.int32,
                ),
                last_focused=rng.integers(
                    0,
                    2,
                    draft_count,
                    dtype=np.uint8,
                ),
                collected_mask=rng.integers(
                    0,
                    1 << 12,
                    draft_count,
                    dtype=np.uint32,
                ),
                risk=rng.uniform(0.0, 10000.0, draft_count),
                collisions=rng.integers(
                    0,
                    5,
                    draft_count,
                    dtype=np.int32,
                ),
                minimum_clearance=minimum,
                step=int(rng.integers(1, 33)),
                beam_width=int(rng.integers(1, 65)),
                target_x=192.0 if target_enabled else None,
                target_y=400.0 if target_enabled else None,
                target_deadline=32 if target_enabled else None,
                item_safety_clearance=8.0,
                reserve_distance=float(rng.uniform(0.0, 30.0)),
                diagonal_speed=3.5 / math.sqrt(2.0),
                cardinal_speed=3.5,
                certificate_collisions=rng.integers(
                    0,
                    3,
                    action_count,
                    dtype=np.int32,
                ),
                certificate_minimum=rng.uniform(
                    -20.0,
                    50.0,
                    action_count,
                ),
                survival_preferred=rng.integers(
                    0,
                    2,
                    action_count,
                    dtype=np.uint8,
                ),
                safety_preferred=rng.integers(
                    0,
                    2,
                    action_count,
                    dtype=np.uint8,
                ),
                recovery_distance=recovery,
            )

    def test_choose_action_end_to_end_matches_python_reducer(self) -> None:
        rng = np.random.default_rng(0xBEA0124)
        try:
            for case in range(32):
                bullets = tuple(
                    live.Bullet(
                        x=float(rng.uniform(20.0, 364.0)),
                        y=float(rng.uniform(30.0, 420.0)),
                        vx=float(rng.uniform(-2.5, 2.5)),
                        vy=float(rng.uniform(-2.5, 2.5)),
                        half_width=float(rng.uniform(1.0, 8.0)),
                        half_height=float(rng.uniform(1.0, 8.0)),
                        transform_flags=int(rng.integers(0, 2)),
                        slot=index,
                    )
                    for index in range(int(rng.integers(0, 90)))
                )
                arguments = {
                    "player_x": float(rng.uniform(30.0, 354.0)),
                    "player_y": float(rng.uniform(80.0, 420.0)),
                    "bullets": bullets,
                    "lasers": (),
                    "previous_direction": int(
                        rng.choice((0, live.LEFT, live.RIGHT, live.UP, live.DOWN))
                    ),
                    "previous_focus": bool(case % 2),
                    "can_bomb": False,
                    "control_delay_frames": 2,
                    "control_delay_candidates": (1, 2, 3),
                    "action_hold_frames": 4,
                    "horizon": 10,
                    "threat_horizon": 14,
                    "beam_width": 24,
                    "target_x": 192.0 if case % 3 else None,
                    "target_y": 400.0 if case % 3 else None,
                    "target_deadline": 10 if case % 3 else None,
                    "preserve_previous_direction_inertia": True,
                }
                live._configure_local_beam_reducer("python")
                reference = live.choose_action(**arguments)
                live._configure_local_beam_reducer("native")
                native = live.choose_action(**arguments)
                reference_fields = vars(reference).copy()
                native_fields = vars(native).copy()
                reference_fields.pop("local_certificate_timing")
                native_fields.pop("local_certificate_timing")
                self.assertEqual(native_fields, reference_fields, msg=f"case={case}")
        finally:
            live._configure_local_beam_reducer("python")


if __name__ == "__main__":
    unittest.main()
