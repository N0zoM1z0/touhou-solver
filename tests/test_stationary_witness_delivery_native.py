#!/usr/bin/env python3
"""Focused tests for the research-only same-process witness binding."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

import numpy as np

from benchmarks.stationary_witness_delivery.native import (
    NativeStationaryWitnessLibrary,
    validate_action_witness,
)
from touhou_control.partial_survival_witness import (
    build_stationary_policy_witness,
    replay_stationary_worst_branch,
)
from touhou_control.query_survival import SurvivalQueryProblem
from touhou_control.viability import ControlAction, ViabilityConfig


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = (
    ROOT
    / "native"
    / "build"
    / ("windows-x86_64" if os.name == "nt" else "linux-x86_64")
    / (
        "belief_stationary_witness_benchmark.dll"
        if os.name == "nt"
        else "libbelief_stationary_witness_benchmark.so"
    )
)


@unittest.skipUnless(LIBRARY.exists(), "witness benchmark library is not built")
class StationaryWitnessDeliveryNativeTests(unittest.TestCase):
    def test_same_process_all_root_actions_match_scalar_paths(self) -> None:
        actions = (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        generator = np.random.default_rng(0xCE0142)
        clearance = np.where(
            generator.random((9, 2, 5)) < 0.2,
            -1.0,
            1.0,
        ).astype(np.float32)
        clearance[0, :, 2] = 1.0
        problem = SurvivalQueryProblem(
            x_axis=np.arange(5, dtype=np.float32),
            y_axis=np.arange(2, dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0, 1),
            nominal_delay=0,
            config=ViabilityConfig(
                frames_per_layer=2,
                required_clearance=0.0,
                clamp_to_bounds=True,
            ),
        )
        library = NativeStationaryWitnessLibrary(LIBRARY)
        workspace = library.create_workspace(
            problem=problem,
            decision_frame_support=(2, 3),
            continuation_action="stay",
        )
        try:
            for action in actions:
                scalar = build_stationary_policy_witness(
                    problem=problem,
                    decision_frame_support=(2, 3),
                    frame=0,
                    row=0,
                    column=2,
                    observed_action="stay",
                    root_action=action.name,
                    continuation_action="stay",
                )
                self.assertEqual(
                    replay_stationary_worst_branch(scalar),
                    scalar.label,
                )
                native = workspace.query(
                    frame=0,
                    row=0,
                    column=2,
                    observed_action="stay",
                    pending_command=None,
                    root_action=action.name,
                    timeout_ms=0,
                )
                validate_action_witness(
                    native,
                    scalar,
                    problem=problem,
                    decision_frame_support=(2, 3),
                )
        finally:
            workspace.close()


if __name__ == "__main__":
    unittest.main()
