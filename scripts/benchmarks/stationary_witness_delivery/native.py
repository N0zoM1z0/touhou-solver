"""Same-process binding for the research-only native witness library."""

from __future__ import annotations

import ctypes
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import numpy as np

from touhou_control.partial_survival_witness import StationaryPolicyWitness
from touhou_control.query_survival import PendingCommand, SurvivalQueryProblem


PIPELINE_RESULT_CANCELLED = 5
PIPELINE_RESULT_DEADLINE = 6


class _NativeWitnessStep(ctypes.Structure):
    _fields_ = [
        ("frame", ctypes.c_int),
        ("row", ctypes.c_int),
        ("column", ctypes.c_int),
        ("active_action", ctypes.c_int),
        ("pending_action", ctypes.c_int),
        ("remaining_delay_mask", ctypes.c_uint64),
        ("selected_action", ctypes.c_int),
        ("hidden_remaining_before", ctypes.c_int),
        ("pickup_delay", ctypes.c_int),
        ("cadence", ctypes.c_int),
        ("prefix_bottleneck_margin", ctypes.c_float),
        ("state_frames", ctypes.c_uint16),
        ("state_margin", ctypes.c_float),
        ("failed", ctypes.c_int),
        ("successor_frame", ctypes.c_int),
        ("successor_row", ctypes.c_int),
        ("successor_column", ctypes.c_int),
        ("successor_active_action", ctypes.c_int),
        ("successor_pending_action", ctypes.c_int),
        ("successor_remaining_delay_mask", ctypes.c_uint64),
        ("successor_frames", ctypes.c_uint16),
        ("successor_margin", ctypes.c_float),
        ("merged_hidden_branch_count", ctypes.c_uint64),
    ]


class NativeWitnessStep(NamedTuple):
    frame: int
    row: int
    column: int
    active_action: int
    pending_action: int
    remaining_delay_mask: int
    selected_action: int
    hidden_remaining_before: int
    pickup_delay: int
    cadence: int
    prefix_bottleneck_margin: float
    state_frames: int
    state_margin: float
    failed: int
    successor_frame: int
    successor_row: int
    successor_column: int
    successor_active_action: int
    successor_pending_action: int
    successor_remaining_delay_mask: int
    successor_frames: int
    successor_margin: float
    merged_hidden_branch_count: int


@dataclass(frozen=True)
class NativeWitnessAction:
    status: int
    root_action: str
    guaranteed_frames: int
    bottleneck_margin: float
    steps: tuple[NativeWitnessStep, ...]
    evaluated_state_count: int
    native_call_ms: float = 0.0
    decode_ms: float = 0.0


@dataclass(frozen=True)
class NativeWitnessValidation:
    exact_scalar_path: bool


def _mask_from_support(support: tuple[int, ...]) -> int:
    mask = 0
    for value in support:
        mask |= 1 << value
    return mask


class NativeStationaryWitnessWorkspace:
    """One private, cancellable internal belief workspace."""

    def __init__(
        self,
        *,
        library: "NativeStationaryWitnessLibrary",
        problem: SurvivalQueryProblem,
        decision_frame_support: tuple[int, ...],
        continuation_action: str,
    ) -> None:
        self._library = library
        self._problem = problem
        self._names = tuple(action.name for action in problem.actions)
        self._indices = {
            name: index for index, name in enumerate(self._names)
        }
        continuation_index = self._indices[continuation_action]
        clearance = np.ascontiguousarray(
            problem.clearance_volume,
            dtype=np.float32,
        )
        velocity_x = np.ascontiguousarray(
            [action.velocity_x for action in problem.actions],
            dtype=np.float64,
        )
        velocity_y = np.ascontiguousarray(
            [action.velocity_y for action in problem.actions],
            dtype=np.float64,
        )
        delays = np.ascontiguousarray(problem.delay_frames, dtype=np.int32)
        cadences = np.ascontiguousarray(
            decision_frame_support,
            dtype=np.int32,
        )
        pointer = ctypes.c_void_p()
        status = library._create(
            clearance.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            clearance.shape[0],
            clearance.shape[1],
            clearance.shape[2],
            float(problem.x_axis[0]),
            float(problem.x_axis[1] - problem.x_axis[0]),
            float(problem.y_axis[0]),
            float(problem.y_axis[1] - problem.y_axis[0]),
            velocity_x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            velocity_y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            len(self._names),
            ctypes.c_uint64(1 << continuation_index),
            delays.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            len(delays),
            cadences.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            len(cadences),
            ctypes.c_float(problem.config.required_clearance),
            int(problem.config.clamp_to_bounds),
            ctypes.byref(pointer),
        )
        if status != 0 or not pointer.value:
            raise RuntimeError(
                f"native stationary workspace create failed with {status}"
            )
        self._pointer = pointer
        self._steps = (_NativeWitnessStep * clearance.shape[0])()
        self._closed = False

    def query(
        self,
        *,
        frame: int,
        row: int,
        column: int,
        observed_action: str,
        pending_command: PendingCommand | None,
        root_action: str,
        timeout_ms: int,
    ) -> NativeWitnessAction:
        if self._closed:
            raise RuntimeError("native stationary workspace is closed")
        pending_support = (
            ()
            if pending_command is None
            else pending_command.remaining_frames
        )
        pending_array = np.ascontiguousarray(
            pending_support,
            dtype=np.int32,
        )
        pending_pointer = (
            None
            if not pending_support
            else pending_array.ctypes.data_as(
                ctypes.POINTER(ctypes.c_int)
            )
        )
        step_count = ctypes.c_int()
        frames = ctypes.c_uint16()
        margin = ctypes.c_float()
        evaluated = ctypes.c_uint64()
        native_started = time.perf_counter()
        status = self._library._query(
            self._pointer,
            frame,
            row,
            column,
            self._indices[observed_action],
            (
                -1
                if pending_command is None
                else self._indices[pending_command.action]
            ),
            pending_pointer,
            len(pending_support),
            self._indices[root_action],
            timeout_ms,
            self._steps,
            len(self._steps),
            ctypes.byref(step_count),
            ctypes.byref(frames),
            ctypes.byref(margin),
            ctypes.byref(evaluated),
        )
        native_call_ms = (
            time.perf_counter() - native_started
        ) * 1000.0
        decode_started = time.perf_counter()
        decoded = (
            tuple(
                self._decode_step(self._steps[index])
                for index in range(step_count.value)
            )
            if status == 0
            else ()
        )
        decode_ms = (time.perf_counter() - decode_started) * 1000.0
        return NativeWitnessAction(
            status=status,
            root_action=root_action,
            guaranteed_frames=int(frames.value),
            bottleneck_margin=float(margin.value),
            steps=decoded,
            evaluated_state_count=int(evaluated.value),
            native_call_ms=native_call_ms,
            decode_ms=decode_ms,
        )

    def _decode_step(
        self,
        step: _NativeWitnessStep,
    ) -> NativeWitnessStep:
        return NativeWitnessStep(
            step.frame,
            step.row,
            step.column,
            step.active_action,
            step.pending_action,
            step.remaining_delay_mask,
            step.selected_action,
            step.hidden_remaining_before,
            step.pickup_delay,
            step.cadence,
            float(step.prefix_bottleneck_margin),
            int(step.state_frames),
            float(step.state_margin),
            step.failed,
            step.successor_frame,
            step.successor_row,
            step.successor_column,
            step.successor_active_action,
            step.successor_pending_action,
            step.successor_remaining_delay_mask,
            int(step.successor_frames),
            float(step.successor_margin),
            int(step.merged_hidden_branch_count),
        )

    def cancel(self) -> int:
        if self._closed:
            return 0
        return int(self._library._cancel(self._pointer))

    def close(self) -> None:
        if not self._closed:
            self._library._destroy(self._pointer)
            self._closed = True
            self._pointer = ctypes.c_void_p()


class NativeStationaryWitnessLibrary:
    """Load the separate benchmark DLL without touching production exports."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._dll = ctypes.CDLL(str(path))
        self._create = self._dll.touhou_benchmark_belief_workspace_create_v1
        self._create.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_int,
            ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
            ctypes.c_float,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self._create.restype = ctypes.c_int
        self._query = (
            self._dll
            .touhou_benchmark_belief_workspace_stationary_witness_v1
        )
        self._query.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(_NativeWitnessStep),
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_uint16),
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_uint64),
        ]
        self._query.restype = ctypes.c_int
        self._cancel = self._dll.touhou_benchmark_belief_workspace_cancel_v1
        self._cancel.argtypes = [ctypes.c_void_p]
        self._cancel.restype = ctypes.c_int
        self._destroy = (
            self._dll.touhou_benchmark_belief_workspace_destroy_v1
        )
        self._destroy.argtypes = [ctypes.c_void_p]
        self._destroy.restype = None
        step_size = self._dll.touhou_benchmark_stationary_witness_step_size_v1
        step_size.argtypes = []
        step_size.restype = ctypes.c_int
        native_size = int(step_size())
        python_size = ctypes.sizeof(_NativeWitnessStep)
        if native_size != python_size:
            raise RuntimeError(
                "native stationary step layout mismatch: "
                f"native={native_size}, ctypes={python_size}"
            )

    @classmethod
    def default(cls, root: Path | None = None) -> "NativeStationaryWitnessLibrary":
        repository = (
            Path(__file__).resolve().parents[3]
            if root is None
            else root
        )
        windows = os.name == "nt"
        path = (
            repository
            / "native"
            / "build"
            / ("windows-x86_64" if windows else "linux-x86_64")
            / (
                "belief_stationary_witness_benchmark.dll"
                if windows
                else "libbelief_stationary_witness_benchmark.so"
            )
        )
        return cls(path)

    def create_workspace(
        self,
        *,
        problem: SurvivalQueryProblem,
        decision_frame_support: tuple[int, ...],
        continuation_action: str,
    ) -> NativeStationaryWitnessWorkspace:
        return NativeStationaryWitnessWorkspace(
            library=self,
            problem=problem,
            decision_frame_support=decision_frame_support,
            continuation_action=continuation_action,
        )


def _close_margin(native: float, scalar: float, tolerance: float) -> bool:
    return (
        math.isinf(native)
        and math.isinf(scalar)
        and (native > 0) == (scalar > 0)
    ) or abs(native - scalar) <= tolerance


def validate_action_witness(
    native: NativeWitnessAction,
    scalar: StationaryPolicyWitness,
    *,
    problem: SurvivalQueryProblem,
    decision_frame_support: tuple[int, ...],
    margin_tolerance: float = 1e-5,
) -> NativeWitnessValidation:
    """Replay structure and compare the exact independent scalar root label.

    Equal-label nature ties may choose a different declared hidden branch
    after native float32 rounding.  Such a path remains valid when its own
    recurrence, state links, policy choices, and uncertainty membership all
    replay.  The return value records whether the deterministic scalar tie
    choice was identical.
    """

    if native.status != 0:
        raise ValueError(f"native witness status is {native.status}")
    if native.root_action != scalar.root_action:
        raise ValueError("native root action differs from scalar witness")
    if native.guaranteed_frames != scalar.label.guaranteed_frames or not (
        _close_margin(
            native.bottleneck_margin,
            scalar.label.bottleneck_margin,
            margin_tolerance,
        )
    ):
        raise ValueError("native root label differs from scalar witness")
    exact_scalar_path = len(native.steps) == len(scalar.worst_branch)
    if not native.steps:
        if native.guaranteed_frames != 0:
            raise ValueError("positive native label has an empty worst path")
        return NativeWitnessValidation(exact_scalar_path)

    action_indices = {
        action.name: index for index, action in enumerate(problem.actions)
    }
    first = native.steps[0]
    if (
        first.frame,
        first.row,
        first.column,
        first.active_action,
        first.pending_action,
        first.remaining_delay_mask,
    ) != (
        scalar.root.frame,
        scalar.root.row,
        scalar.root.column,
        action_indices[scalar.root.observed_action],
        (
            -1
            if scalar.root.pending_action is None
            else action_indices[scalar.root.pending_action]
        ),
        _mask_from_support(scalar.root.remaining_delay_support),
    ):
        raise ValueError("native worst path does not start at the scalar root")
    if (
        first.state_frames != native.guaranteed_frames
        or not _close_margin(
            first.state_margin,
            native.bottleneck_margin,
            margin_tolerance,
        )
    ):
        raise ValueError("native first-step label differs from its root label")

    for step_index, native_step in enumerate(native.steps):
        expected_action = (
            scalar.root_action
            if step_index == 0
            else scalar.continuation_action
        )
        if native_step.selected_action != action_indices[expected_action]:
            raise ValueError("native path violates the stationary policy")
        if (
            native_step.hidden_remaining_before < 0
            or not (
                native_step.remaining_delay_mask
                & (1 << native_step.hidden_remaining_before)
            )
        ):
            raise ValueError("native hidden delay is outside its belief support")
        if native_step.cadence not in decision_frame_support:
            raise ValueError("native cadence is outside its declared support")
        desired = (
            native_step.pending_action
            if native_step.pending_action >= 0
            else native_step.active_action
        )
        if native_step.selected_action == desired:
            if native_step.pickup_delay >= 0:
                raise ValueError("native no-write step sampled a pickup delay")
        elif native_step.pickup_delay not in problem.delay_frames:
            raise ValueError("native pickup delay is outside declared support")
        if (
            native_step.active_action < 0
            or native_step.active_action >= len(problem.actions)
            or native_step.selected_action < 0
            or native_step.selected_action >= len(problem.actions)
            or native_step.pending_action >= len(problem.actions)
        ):
            raise ValueError("native path contains an unknown action")
        if native_step.failed:
            if (
                step_index + 1 != len(native.steps)
                or native_step.successor_frame != -1
                or native_step.successor_row != -1
                or native_step.successor_column != -1
                or native_step.successor_active_action != -1
                or native_step.successor_pending_action != -1
                or native_step.successor_remaining_delay_mask != 0
                or native_step.successor_frames != 0
            ):
                raise ValueError("native failed branch is not terminal")
        else:
            if (
                native_step.successor_frame < 0
                or native_step.successor_row < 0
                or native_step.successor_column < 0
                or native_step.successor_active_action < 0
            ):
                raise ValueError("native successful branch lacks a successor")
            expected_frames = (
                native_step.successor_frame
                - native_step.frame
                + native_step.successor_frames
            )
            expected_margin = min(
                native_step.prefix_bottleneck_margin,
                native_step.successor_margin,
            )
            if (
                native_step.state_frames != expected_frames
                or not _close_margin(
                    native_step.state_margin,
                    expected_margin,
                    margin_tolerance,
                )
            ):
                raise ValueError("native worst-branch recurrence does not replay")
            if step_index + 1 < len(native.steps):
                child = native.steps[step_index + 1]
                if (
                    child.frame,
                    child.row,
                    child.column,
                    child.active_action,
                    child.pending_action,
                    child.remaining_delay_mask,
                    child.state_frames,
                ) != (
                    native_step.successor_frame,
                    native_step.successor_row,
                    native_step.successor_column,
                    native_step.successor_active_action,
                    native_step.successor_pending_action,
                    native_step.successor_remaining_delay_mask,
                    native_step.successor_frames,
                ) or not _close_margin(
                    child.state_margin,
                    native_step.successor_margin,
                    margin_tolerance,
                ):
                    raise ValueError("native worst-path child link is inconsistent")
        if step_index < len(scalar.worst_branch):
            scalar_step = scalar.worst_branch[step_index]
            exact_scalar_path = exact_scalar_path and (
                native_step.hidden_remaining_before,
                native_step.pickup_delay,
                native_step.cadence,
                native_step.successor_frame,
                native_step.successor_row,
                native_step.successor_column,
                native_step.successor_active_action,
                native_step.successor_pending_action,
                native_step.successor_remaining_delay_mask,
            ) == (
                scalar_step.hidden_remaining_before,
                (
                    -1
                    if scalar_step.pickup_delay is None
                    else scalar_step.pickup_delay
                ),
                scalar_step.cadence,
                (
                    -1
                    if scalar_step.successor_frame is None
                    else scalar_step.successor_frame
                ),
                (
                    -1
                    if scalar_step.successor_row is None
                    else scalar_step.successor_row
                ),
                (
                    -1
                    if scalar_step.successor_column is None
                    else scalar_step.successor_column
                ),
                (
                    -1
                    if scalar_step.successor_active_action is None
                    else action_indices[scalar_step.successor_active_action]
                ),
                (
                    -1
                    if scalar_step.successor_pending_action is None
                    else action_indices[scalar_step.successor_pending_action]
                ),
                _mask_from_support(
                    scalar_step.successor_remaining_delay_support
                ),
            )
    return NativeWitnessValidation(exact_scalar_path)


__all__ = [
    "NativeStationaryWitnessLibrary",
    "NativeStationaryWitnessWorkspace",
    "NativeWitnessAction",
    "NativeWitnessStep",
    "NativeWitnessValidation",
    "PIPELINE_RESULT_CANCELLED",
    "PIPELINE_RESULT_DEADLINE",
    "validate_action_witness",
]
