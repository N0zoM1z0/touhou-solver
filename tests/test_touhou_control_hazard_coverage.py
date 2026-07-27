from __future__ import annotations

import unittest

from touhou_control.hazard_coverage import (
    HazardCoverageClass,
    HazardCoverageSlab,
    assess_hazard_coverage,
)
from touhou_control.pipeline_identity import VersionIdentity


def _slab(
    start: int,
    end: int,
    coverage_class: HazardCoverageClass,
    *,
    source: str = "observed_entities",
) -> HazardCoverageSlab:
    return HazardCoverageSlab(
        start_frame=start,
        end_frame=end,
        coverage_class=coverage_class,
        source=source,
        version=VersionIdentity.from_mapping(
            "hazard-source",
            {"revision": 1},
        ),
        rationale="test coverage contract",
    )


class HazardCoverageTests(unittest.TestCase):
    def test_known_classes_cover_complete_horizon(self) -> None:
        result = assess_hazard_coverage(
            root_frame=10,
            horizon_frame=18,
            slabs=(
                _slab(11, 12, HazardCoverageClass.DETERMINISTIC),
                _slab(13, 15, HazardCoverageClass.FINITE_SUPPORT),
                _slab(16, 20, HazardCoverageClass.BOUNDED_ENVELOPE),
            ),
        )

        self.assertTrue(result.complete)
        self.assertEqual(result.covered_through_frame, 18)
        self.assertIsNone(result.unknown_from_frame)

    def test_unknown_truncates_at_first_reachable_frame(self) -> None:
        result = assess_hazard_coverage(
            root_frame=10,
            horizon_frame=18,
            slabs=(
                _slab(11, 14, HazardCoverageClass.BOUNDED_ENVELOPE),
                _slab(
                    15,
                    20,
                    HazardCoverageClass.UNKNOWN,
                    source="future_births",
                ),
            ),
        )

        self.assertTrue(result.model_unknown)
        self.assertEqual(result.covered_through_frame, 14)
        self.assertEqual(result.unknown_from_frame, 15)
        self.assertEqual(
            result.reason,
            "unknown_hazard_coverage:future_births",
        )

    def test_missing_slab_is_unknown_not_free_space(self) -> None:
        result = assess_hazard_coverage(
            root_frame=10,
            horizon_frame=18,
            slabs=(
                _slab(11, 12, HazardCoverageClass.DETERMINISTIC),
                _slab(14, 18, HazardCoverageClass.DETERMINISTIC),
            ),
        )

        self.assertTrue(result.model_unknown)
        self.assertEqual(result.covered_through_frame, 12)
        self.assertEqual(result.unknown_from_frame, 13)
        self.assertEqual(result.reason, "missing_hazard_coverage_slab")

    def test_unknown_on_first_transition_has_no_modeled_cover(self) -> None:
        result = assess_hazard_coverage(
            root_frame=10,
            horizon_frame=18,
            slabs=(
                _slab(
                    11,
                    18,
                    HazardCoverageClass.UNKNOWN,
                    source="unseen_future_events",
                ),
            ),
        )

        self.assertEqual(result.covered_through_frame, 10)
        self.assertEqual(result.unknown_from_frame, 11)

    def test_overlapping_slabs_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not overlap"):
            assess_hazard_coverage(
                root_frame=10,
                horizon_frame=18,
                slabs=(
                    _slab(11, 15, HazardCoverageClass.DETERMINISTIC),
                    _slab(15, 18, HazardCoverageClass.DETERMINISTIC),
                ),
            )


if __name__ == "__main__":
    unittest.main()
