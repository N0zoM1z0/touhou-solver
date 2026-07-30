from __future__ import annotations

import unittest

from analysis.th08_native_h1_ecl_source_differential import (
    _birth_and_removal_rows,
    _float32_bits,
    _rng_alignment,
)


def _bullet(slot: int, speed: float = 1.0) -> list[object]:
    return [
        slot,
        0.0,
        0.0,
        0.0,
        0.0,
        2.0,
        2.0,
        0,
        [
            speed,
            0.0,
            0x203,
            0,
            [0, 0, 0, 0.0, 0.0, 0, 0],
            0.0,
            0,
            0,
            0.0,
            0.0,
            0,
            0,
            1,
            0,
            [],
            0.0,
            0.0,
        ],
    ]


class NativeH1EclSourceDifferentialTests(unittest.TestCase):
    def test_birth_and_removal_identity_fails_closed(self) -> None:
        root = {
            "bullets": [
                *(_bullet(slot) for slot in (87, 120, 545, 710)),
            ]
        }
        endpoint = {
            "bullets": [
                *(_bullet(slot) for slot in range(1220, 1227)),
            ]
        }

        births, removals = _birth_and_removal_rows(root, endpoint)

        self.assertEqual([row[0] for row in births], list(range(1220, 1227)))
        self.assertEqual(removals, [87, 120, 545, 710])
        endpoint["bullets"].append(_bullet(1300))
        with self.assertRaisesRegex(ValueError, "birth slots"):
            _birth_and_removal_rows(root, endpoint)

    def test_rng_alignment_is_retrospective_and_closes_exact_calls(self) -> None:
        root = {"rng_state": 45644, "rng_calls": 22684}
        endpoint = {"rng_calls": 22716}
        expected_speeds = [
            0.9987534284591675,
            1.8943283557891846,
            1.1563938856124878,
            1.2838727235794067,
            1.1203123331069946,
            1.7414411306381226,
            1.7299515008926392,
        ]
        births = [
            _bullet(slot, speed)
            for slot, speed in zip(
                range(1220, 1227),
                expected_speeds,
                strict=True,
            )
        ]

        result = _rng_alignment(root, endpoint, births)

        self.assertEqual(result["u16_calls_consumed"], 32)
        self.assertEqual(
            [row["matching_birth_slot"] for row in result["pairs"]],
            [None, *range(1220, 1227)],
        )
        self.assertEqual(
            result["pairs"][2]["rank_adjusted_speed_bits"],
            _float32_bits(expected_speeds[1]),
        )
        self.assertIn("retrospective", result["authority"])


if __name__ == "__main__":
    unittest.main()
