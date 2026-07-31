from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

import numpy as np

from touhou_control.hazard_coverage import (
    HazardCoverageClass,
    HazardCoverageSlab,
    assess_hazard_coverage,
)
from touhou_control.local_pipeline_oracle import LocalPipelineRoot
from touhou_control.pipeline_identity import VersionIdentity
from touhou_control.prepublication import (
    build_causal_prepublication_filter,
)
from touhou_control.viability_types import SafetyValueQuery, ViabilityQuery


ACTIONS = ("stay", "left", "right", "up", "down")
VELOCITIES = {
    "stay": (0.0, 0.0),
    "left": (-4.0, 0.0),
    "right": (4.0, 0.0),
    "up": (0.0, -4.0),
    "down": (0.0, 4.0),
}
HAZARD_VERSION = VersionIdentity.from_mapping(
    "fixture-hazard-source",
    {"revision": 1},
)


class _RectangularSafetyPolicy:
    x_axis = np.arange(8.0, 377.0, 8.0)
    y_axis = np.arange(16.0, 433.0, 8.0)
    config = SimpleNamespace(required_clearance=0.0)
    horizon_frames = 8

    def __init__(
        self,
        *,
        viable_x_max: float,
    ) -> None:
        self.viable_x_max = viable_x_max

    def query(self, *, frame, x, y, active_action):
        del frame
        action_values = tuple(
            (
                action,
                self.viable_x_max
                - min(
                    float(self.x_axis[-1]),
                    max(
                        float(self.x_axis[0]),
                        x + VELOCITIES[action][0],
                    ),
                ),
            )
            for action in ACTIONS
        )
        return SafetyValueQuery(
            available=True,
            layer=0,
            row=0,
            column=0,
            active_action=active_action,
            state_value=max(value for _, value in action_values),
            action_values=action_values,
            best_actions=tuple(
                action
                for action, value in action_values
                if value == max(item[1] for item in action_values)
            ),
            position_error=0.0,
            reason="fixture",
        )


class _RectangularRecoveryPolicy:
    x_axis = _RectangularSafetyPolicy.x_axis
    y_axis = _RectangularSafetyPolicy.y_axis

    def __init__(self, *, viable_x_max: float, recovery_target_x: float):
        self.viable_x_max = viable_x_max
        self.recovery_target_x = recovery_target_x

    def query(self, *, frame, x, y, active_action):
        del frame, y
        state_viable = x <= self.viable_x_max
        recovery = tuple(
            (
                action,
                abs(
                    min(
                        float(self.x_axis[-1]),
                        max(
                            float(self.x_axis[0]),
                            x + VELOCITIES[action][0],
                        ),
                    )
                    - self.recovery_target_x
                ),
            )
            for action in ACTIONS
        )
        return ViabilityQuery(
            available=True,
            layer=0,
            row=0,
            column=0,
            active_action=active_action,
            state_viable=state_viable,
            safe_actions=ACTIONS if state_viable else (),
            repair_volumes=(),
            position_error=0.0,
            reason="fixture",
            recovery_distances=() if state_viable else recovery,
        )


class _ConstantSafetyPolicy:
    x_axis = _RectangularSafetyPolicy.x_axis
    y_axis = _RectangularSafetyPolicy.y_axis
    config = SimpleNamespace(required_clearance=0.0)
    horizon_frames = 8

    def __init__(
        self,
        *,
        state_value: float,
        position_error: float,
        retain_action_values: bool = True,
    ):
        self.state_value = state_value
        self.position_error = position_error
        self.retain_action_values = retain_action_values

    def query(self, *, frame, x, y, active_action):
        del frame, x, y
        return SafetyValueQuery(
            available=True,
            layer=0,
            row=0,
            column=0,
            active_action=active_action,
            state_value=self.state_value,
            action_values=(
                tuple((action, self.state_value) for action in ACTIONS)
                if self.retain_action_values
                else ()
            ),
            best_actions=ACTIONS,
            position_error=self.position_error,
            reason="fixture",
        )


def _coverage(*, complete: bool):
    coverage_class = (
        HazardCoverageClass.BOUNDED_ENVELOPE
        if complete
        else HazardCoverageClass.UNKNOWN
    )
    return assess_hazard_coverage(
        root_frame=100,
        horizon_frame=112,
        slabs=(
            HazardCoverageSlab(
                start_frame=101,
                end_frame=112,
                coverage_class=coverage_class,
                source="fixture",
                version=HAZARD_VERSION,
                rationale="fixture",
            ),
        ),
    )


class CausalPrepublicationFilterTests(unittest.TestCase):
    def _build(self, **overrides):
        arguments = {
            "enabled": True,
            "root": LocalPipelineRoot("stay", "stay"),
            "selected_actions": ACTIONS,
            "action_velocities": VELOCITIES,
            "delay_frames": (0, 1, 2, 3),
            "current_frame": 100,
            "publication_frame": 104,
            "prefix_certified_frames": 4,
            "prefix_safe_actions": ACTIONS,
            "start_x": 40.0,
            "start_y": 400.0,
            "future_safety_policy": _RectangularSafetyPolicy(
                viable_x_max=40.0,
            ),
            "future_recovery_policy": _RectangularRecoveryPolicy(
                viable_x_max=40.0,
                recovery_target_x=24.0,
            ),
            "hazard_coverage": _coverage(complete=True),
            "required_hazard_version": HAZARD_VERSION,
        }
        arguments.update(overrides)
        return build_causal_prepublication_filter(**arguments)

    def test_every_pickup_branch_must_reach_future_viable_set(self):
        result = self._build()

        self.assertTrue(result.authority_eligible)
        self.assertTrue(result.applicable)
        self.assertIn("left", result.allowed_actions or ())
        self.assertNotIn("right", result.allowed_actions or ())
        by_action = {action.action: action for action in result.actions}
        self.assertEqual(by_action["left"].branch_count, 4)
        self.assertEqual(
            by_action["left"].viable_branch_count,
            by_action["left"].branch_count,
        )
        self.assertLess(
            by_action["right"].viable_branch_count,
            by_action["right"].branch_count,
        )

    def test_held_mask_is_no_write_and_preserves_pending_command(self):
        result = self._build(
            root=LocalPipelineRoot(
                active_action="right",
                held_desired_action="left",
                pending_action="left",
                remaining_delay_support=(2, 3),
            ),
            publication_frame=102,
        )

        by_action = {action.action: action for action in result.actions}
        self.assertEqual(by_action["left"].branch_count, 2)
        self.assertEqual(by_action["right"].branch_count, 8)

    def test_unknown_future_hazards_never_gain_action_authority(self):
        result = self._build(hazard_coverage=_coverage(complete=False))

        self.assertFalse(result.authority_eligible)
        self.assertFalse(result.applicable)
        self.assertIsNone(result.allowed_actions)
        self.assertTrue(result.candidate_viable_actions)
        self.assertEqual(result.reason, "future_hazard_coverage_unknown")

    def test_directional_recovery_survives_zero_scalar_reserve(self):
        result = self._build(
            start_x=376.0,
            future_safety_policy=_RectangularSafetyPolicy(
                viable_x_max=24.0,
            ),
            future_recovery_policy=_RectangularRecoveryPolicy(
                viable_x_max=24.0,
                recovery_target_x=24.0,
            ),
        )

        self.assertEqual(result.candidate_viable_actions, ())
        self.assertEqual(result.recovery_actions, ("left",))
        distances = {
            action.action: action.worst_recovery_distance
            for action in result.actions
        }
        self.assertTrue(math.isfinite(distances["left"]))
        self.assertLess(distances["left"], distances["stay"])
        self.assertLess(distances["left"], distances["right"])

    def test_missing_future_policy_fails_closed(self):
        result = self._build(future_safety_policy=None)

        self.assertFalse(result.authority_eligible)
        self.assertEqual(result.reason, "future_safety_policy_unavailable")

    def test_complete_coverage_with_wrong_version_fails_closed(self):
        wrong_version = VersionIdentity.from_mapping(
            "fixture-hazard-source",
            {"revision": 2},
        )

        result = self._build(required_hazard_version=wrong_version)

        self.assertFalse(result.authority_eligible)
        self.assertIsNone(result.allowed_actions)
        self.assertEqual(result.reason, "future_hazard_version_mismatch")

    def test_off_grid_error_is_subtracted_from_every_hard_certificate(self):
        result = self._build(
            future_safety_policy=_ConstantSafetyPolicy(
                state_value=1.0,
                position_error=2.0,
            ),
        )

        self.assertEqual(result.candidate_viable_actions, ())
        self.assertEqual(
            result.reason,
            "prepublication_viable_predecessor_empty",
        )
        self.assertTrue(
            all(
                action.worst_certified_margin == -1.0
                for action in result.actions
            )
        )

    def test_pending_terminal_requires_retained_action_values(self):
        result = self._build(
            root=LocalPipelineRoot(
                active_action="right",
                held_desired_action="left",
                pending_action="left",
                remaining_delay_support=(3,),
            ),
            publication_frame=102,
            future_safety_policy=_ConstantSafetyPolicy(
                state_value=100.0,
                position_error=0.0,
                retain_action_values=False,
            ),
        )

        self.assertEqual(result.candidate_viable_actions, ())
        self.assertTrue(
            all(
                action.unavailable_branch_count > 0
                for action in result.actions
            )
        )

    def test_prefix_hazard_set_is_part_of_the_predecessor(self):
        result = self._build(prefix_safe_actions=("right",))

        self.assertEqual(result.candidate_viable_actions, ())
        self.assertFalse(result.applicable)
        self.assertEqual(
            result.reason,
            "prepublication_viable_predecessor_empty",
        )

    def test_short_prefix_certificate_fails_closed(self):
        result = self._build(prefix_certified_frames=3)

        self.assertFalse(result.authority_eligible)
        self.assertIsNone(result.allowed_actions)
        self.assertEqual(
            result.reason,
            "prefix_hazard_certificate_unavailable",
        )
