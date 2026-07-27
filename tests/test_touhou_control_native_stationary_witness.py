#!/usr/bin/env python3
"""Differential tests for the internal native stationary witness path."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import unittest

import numpy as np

from touhou_control.partial_survival_witness import (
    build_stationary_policy_witness,
)
from touhou_control.query_survival import (
    PendingCommand,
    SurvivalQueryProblem,
)
from touhou_control.viability import ControlAction, ViabilityConfig


ROOT = Path(__file__).resolve().parents[1]
PROBE = (
    ROOT
    / "native"
    / "build"
    / ("windows-x86_64" if os.name == "nt" else "linux-x86_64")
    / (
        "belief_stationary_witness_probe.exe"
        if os.name == "nt"
        else "belief_stationary_witness_probe"
    )
)


def _support_from_mask(mask: int) -> tuple[int, ...]:
    return tuple(index for index in range(63) if mask & (1 << index))


def _float32_bits(value: float) -> bytes:
    return np.float32(value).tobytes()


def _run_probe(
    *,
    problem: SurvivalQueryProblem,
    decision_frame_support: tuple[int, ...],
    frame: int,
    row: int,
    column: int,
    observed_action: str,
    root_action: str,
    continuation_action: str,
    pending_command: PendingCommand | None = None,
) -> tuple[tuple[int, float, int, int], tuple[tuple[str, ...], ...]]:
    action_indices = {
        action.name: index for index, action in enumerate(problem.actions)
    }
    pending_index = (
        -1
        if pending_command is None
        else action_indices[pending_command.action]
    )
    pending_support = (
        ()
        if pending_command is None
        else pending_command.remaining_frames
    )
    x_step = float(problem.x_axis[1] - problem.x_axis[0])
    y_step = float(problem.y_axis[1] - problem.y_axis[0])
    header = (
        problem.clearance_volume.shape[0],
        problem.clearance_volume.shape[1],
        problem.clearance_volume.shape[2],
        len(problem.actions),
        float(problem.x_axis[0]),
        x_step,
        float(problem.y_axis[0]),
        y_step,
        problem.config.required_clearance,
        int(problem.config.clamp_to_bounds),
        1 << action_indices[continuation_action],
    )
    fields: list[object] = [*header]
    fields.extend((len(problem.delay_frames), *problem.delay_frames))
    fields.extend(
        (len(decision_frame_support), *decision_frame_support)
    )
    fields.extend(action.velocity_x for action in problem.actions)
    fields.extend(action.velocity_y for action in problem.actions)
    fields.extend(
        np.asarray(
            problem.clearance_volume,
            dtype=np.float32,
            order="C",
        ).ravel(order="C")
    )
    fields.extend(
        (
            frame,
            row,
            column,
            action_indices[observed_action],
            pending_index,
            len(pending_support),
            *pending_support,
            action_indices[root_action],
        )
    )
    completed = subprocess.run(
        [str(PROBE)],
        input=" ".join(str(value) for value in fields),
        text=True,
        capture_output=True,
        check=True,
    )
    lines = tuple(
        tuple(line.split())
        for line in completed.stdout.splitlines()
        if line.strip()
    )
    if not lines:
        raise AssertionError("native witness probe produced no output")
    status = int(lines[0][0])
    if status != 0:
        raise AssertionError(f"native witness probe failed with {status}")
    summary = (
        int(lines[0][1]),
        float(lines[0][2]),
        int(lines[0][3]),
        int(lines[0][4]),
    )
    return summary, lines[1:]


@unittest.skipUnless(PROBE.exists(), "native stationary witness probe is not built")
class NativeStationaryWitnessTests(unittest.TestCase):
    def assert_witness_parity(
        self,
        *,
        problem: SurvivalQueryProblem,
        decision_frame_support: tuple[int, ...],
        frame: int,
        row: int,
        column: int,
        observed_action: str,
        root_action: str,
        continuation_action: str,
        pending_command: PendingCommand | None = None,
    ) -> None:
        witness = build_stationary_policy_witness(
            problem=problem,
            decision_frame_support=decision_frame_support,
            frame=frame,
            row=row,
            column=column,
            observed_action=observed_action,
            root_action=root_action,
            continuation_action=continuation_action,
            pending_command=pending_command,
        )
        summary, rows = _run_probe(
            problem=problem,
            decision_frame_support=decision_frame_support,
            frame=frame,
            row=row,
            column=column,
            observed_action=observed_action,
            root_action=root_action,
            continuation_action=continuation_action,
            pending_command=pending_command,
        )
        self.assertEqual(summary[0], witness.label.guaranteed_frames)
        self.assertEqual(
            _float32_bits(summary[1]),
            _float32_bits(witness.label.bottleneck_margin),
        )
        self.assertEqual(summary[2], len(witness.worst_branch))
        self.assertGreater(summary[3], 0)
        self.assertEqual(len(rows), len(witness.worst_branch))

        action_names = tuple(action.name for action in problem.actions)
        for native, scalar in zip(rows, witness.worst_branch, strict=True):
            self.assertEqual(len(native), 23)
            self.assertEqual(
                (int(native[0]), int(native[1]), int(native[2])),
                (scalar.frame, scalar.row, scalar.column),
            )
            self.assertEqual(action_names[int(native[3])], scalar.active_action)
            self.assertEqual(
                None if int(native[4]) < 0 else action_names[int(native[4])],
                scalar.pending_action,
            )
            self.assertEqual(
                _support_from_mask(int(native[5])),
                scalar.remaining_delay_support,
            )
            self.assertEqual(
                action_names[int(native[6])],
                scalar.selected_action,
            )
            self.assertEqual(
                int(native[7]),
                scalar.hidden_remaining_before,
            )
            self.assertEqual(
                None if int(native[8]) < 0 else int(native[8]),
                scalar.pickup_delay,
            )
            self.assertEqual(int(native[9]), scalar.cadence)
            self.assertEqual(
                _float32_bits(float(native[10])),
                _float32_bits(scalar.prefix_bottleneck_margin),
            )
            self.assertEqual(
                int(native[11]),
                scalar.state_label.guaranteed_frames,
            )
            self.assertEqual(
                _float32_bits(float(native[12])),
                _float32_bits(scalar.state_label.bottleneck_margin),
            )
            self.assertEqual(bool(int(native[13])), scalar.failed)
            self.assertEqual(
                None if int(native[14]) < 0 else int(native[14]),
                scalar.successor_frame,
            )
            self.assertEqual(
                None if int(native[15]) < 0 else int(native[15]),
                scalar.successor_row,
            )
            self.assertEqual(
                None if int(native[16]) < 0 else int(native[16]),
                scalar.successor_column,
            )
            self.assertEqual(
                None if int(native[17]) < 0 else action_names[int(native[17])],
                scalar.successor_active_action,
            )
            self.assertEqual(
                None if int(native[18]) < 0 else action_names[int(native[18])],
                scalar.successor_pending_action,
            )
            self.assertEqual(
                _support_from_mask(int(native[19])),
                scalar.successor_remaining_delay_support,
            )
            if scalar.successor_label is None:
                self.assertTrue(scalar.failed)
            else:
                self.assertEqual(
                    int(native[20]),
                    scalar.successor_label.guaranteed_frames,
                )
                self.assertEqual(
                    _float32_bits(float(native[21])),
                    _float32_bits(
                        scalar.successor_label.bottleneck_margin
                    ),
                )
            self.assertEqual(
                int(native[22]),
                scalar.merged_hidden_branch_count,
            )

    def test_randomized_all_root_actions_match_full_worst_paths(self) -> None:
        actions = (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        for seed in range(4):
            random = np.random.default_rng(seed)
            clearance = np.where(
                random.random((8, 2, 4)) < 0.2,
                -1.0,
                1.0,
            ).astype(np.float32)
            clearance[0, :, 2] = 1.0
            problem = SurvivalQueryProblem(
                x_axis=np.arange(4, dtype=np.float32),
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
            for root_action in actions:
                with self.subTest(seed=seed, root=root_action.name):
                    self.assert_witness_parity(
                        problem=problem,
                        decision_frame_support=(2, 3),
                        frame=0,
                        row=0,
                        column=2,
                        observed_action="stay",
                        root_action=root_action.name,
                        continuation_action="stay",
                    )

    def test_pending_no_write_path_matches(self) -> None:
        actions = (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
        )
        clearance = np.ones((5, 2, 4), dtype=np.float32)
        clearance[4, :, 2] = -1.0
        problem = SurvivalQueryProblem(
            x_axis=np.arange(4, dtype=np.float32),
            y_axis=np.arange(2, dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(1, 3),
            nominal_delay=1,
            config=ViabilityConfig(
                frames_per_layer=1,
                required_clearance=0.0,
                clamp_to_bounds=True,
            ),
        )
        self.assert_witness_parity(
            problem=problem,
            decision_frame_support=(1, 2),
            frame=0,
            row=0,
            column=2,
            observed_action="stay",
            root_action="left",
            continuation_action="left",
            pending_command=PendingCommand("left", (1, 2)),
        )

    def test_unsafe_root_returns_the_empty_path(self) -> None:
        clearance = np.ones((3, 2, 3), dtype=np.float32)
        clearance[0, 0, 1] = -1.0
        problem = SurvivalQueryProblem(
            x_axis=np.arange(3, dtype=np.float32),
            y_axis=np.arange(2, dtype=np.float32),
            clearance_volume=clearance,
            actions=(ControlAction("stay", 0.0, 0.0),),
            delay_frames=(0,),
            nominal_delay=0,
            config=ViabilityConfig(
                frames_per_layer=1,
                required_clearance=0.0,
                clamp_to_bounds=True,
            ),
        )
        self.assert_witness_parity(
            problem=problem,
            decision_frame_support=(1,),
            frame=0,
            row=0,
            column=1,
            observed_action="stay",
            root_action="stay",
            continuation_action="stay",
        )
