from __future__ import annotations

import argparse
import unittest

from benchmarks.benchmark_supplemental_continuation_lane import (
    _componentwise_regression,
    _parse_widths,
    _variant_name,
)
from benchmarks.benchmark_th08_local_intensive_cases import (
    build_intensive_cases,
)


class SupplementalContinuationBenchmarkTests(unittest.TestCase):
    def test_width_parser_and_names_are_deterministic(self) -> None:
        self.assertEqual(_parse_widths("4,8,12"), (4, 8, 12))
        self.assertEqual(_variant_name(None), "historical")
        self.assertEqual(_variant_name(0), "final_only")
        self.assertEqual(_variant_name(8), "supplemental_8")
        for invalid in ("", "0", "4,4", "-1,4"):
            with self.assertRaises(argparse.ArgumentTypeError):
                _parse_widths(invalid)

    def test_hard_filter_is_componentwise_not_lexicographic(self) -> None:
        incumbent = (0, 0.0, 0, 0.0, 0)
        self.assertFalse(
            _componentwise_regression(incumbent, incumbent)
        )
        self.assertTrue(
            _componentwise_regression(
                (0, 0.0, 0, 0.25, 0),
                incumbent,
            )
        )
        self.assertTrue(
            _componentwise_regression(
                (0, 0.0, 1, 0.0, 0),
                incumbent,
            )
        )

    def test_intensive_corpus_exceeds_native_pools_and_has_events(
        self,
    ) -> None:
        cases = {
            case.name: case
            for case in build_intensive_cases(0xCE0130)
        }
        self.assertEqual(
            set(cases),
            {
                "native_pool_live_like",
                "native_pool_reachable_tube",
                "beyond_pool_piecewise_transform",
                "off_tube_broadphase",
                "boundary_near_tangent",
                "laser_degenerate_crossing",
            },
        )
        beyond = cases["beyond_pool_piecewise_transform"]
        self.assertGreater(len(beyond.bullets), 1536)
        self.assertGreater(len(beyond.lasers), 256)
        self.assertTrue(
            any(bullet.velocity_changes for bullet in beyond.bullets)
        )
        self.assertTrue(
            any(bullet.transform_flags for bullet in beyond.bullets)
        )
        self.assertTrue(
            any(laser.state is not None for laser in beyond.lasers)
        )
        tangent = cases["boundary_near_tangent"]
        self.assertTrue(
            any(
                bullet.transform_flags
                for bullet in tangent.bullets
            )
        )
        degenerate = cases["laser_degenerate_crossing"]
        self.assertTrue(
            any(
                abs(laser.head - laser.tail) <= 1e-6
                for laser in degenerate.lasers
            )
        )


if __name__ == "__main__":
    unittest.main()
