"""ctypes ABI layouts and immutable results for native local planning."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass

import numpy as np


_C_FLOAT_POINTER = ctypes.POINTER(ctypes.c_float)
_C_DOUBLE_POINTER = ctypes.POINTER(ctypes.c_double)
_C_INT32_POINTER = ctypes.POINTER(ctypes.c_int32)
_C_UINT8_POINTER = ctypes.POINTER(ctypes.c_uint8)


@dataclass(frozen=True)
class DecodedBulletPool:
    """Owned structure-of-arrays output from the native slot decoder."""

    x: np.ndarray
    y: np.ndarray
    velocity_x: np.ndarray
    velocity_y: np.ndarray
    half_width: np.ndarray
    half_height: np.ndarray
    transform_flags: np.ndarray
    slots: np.ndarray
    speed: np.ndarray
    angle: np.ndarray
    callback_phase: np.ndarray
    callback_aux: np.ndarray
    original_transform_flags: np.ndarray

    def __len__(self) -> int:
        return len(self.x)



class LocalSupplementalNativeCancelledError(RuntimeError):
    """The complete native supplemental rollout was cancelled."""



class LocalSupplementalNativeDeadlineError(RuntimeError):
    """The complete native supplemental rollout missed its deadline."""



@dataclass(frozen=True)
class LocalSupplementalNativeResult:
    """Completed endpoint vectors from one all-or-nothing native rollout."""

    x: np.ndarray
    y: np.ndarray
    first_action: np.ndarray
    last_action: np.ndarray
    risk: np.ndarray
    collisions: np.ndarray
    minimum_clearance: np.ndarray
    immediate_clearance: np.ndarray

    def __len__(self) -> int:
        return len(self.x)



class _LocalSupplementalQueryV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("horizon", ctypes.c_int),
        ("action_hold_frames", ctypes.c_int),
        ("beam_width", ctypes.c_int),
        ("control_delay_frames", ctypes.c_int),
        ("action_count", ctypes.c_int),
        ("initial_x", ctypes.c_double),
        ("initial_y", ctypes.c_double),
        ("initial_first_action", ctypes.c_int32),
        ("initial_last_action", ctypes.c_int32),
        ("initial_risk", ctypes.c_double),
        ("initial_collisions", ctypes.c_int32),
        ("initial_minimum_clearance", ctypes.c_double),
        ("initial_immediate_clearance", ctypes.c_double),
        ("action_direction", _C_INT32_POINTER),
        ("action_dx", _C_DOUBLE_POINTER),
        ("action_dy", _C_DOUBLE_POINTER),
        ("action_focused", _C_UINT8_POINTER),
        ("action_allowed", _C_UINT8_POINTER),
        ("certificate_collisions", _C_INT32_POINTER),
        ("certificate_minimum", _C_DOUBLE_POINTER),
        ("survival_preferred", _C_UINT8_POINTER),
        ("safety_preferred", _C_UINT8_POINTER),
        ("recovery_distance", _C_DOUBLE_POINTER),
        ("repair_volume", _C_INT32_POINTER),
        ("bullet_offsets", _C_INT32_POINTER),
        ("bullet_x", _C_FLOAT_POINTER),
        ("bullet_y", _C_FLOAT_POINTER),
        ("bullet_half_width", _C_FLOAT_POINTER),
        ("bullet_half_height", _C_FLOAT_POINTER),
        ("bullet_transformed", _C_UINT8_POINTER),
        ("laser_offsets", _C_INT32_POINTER),
        ("laser_start_x", _C_FLOAT_POINTER),
        ("laser_start_y", _C_FLOAT_POINTER),
        ("laser_segment_x", _C_FLOAT_POINTER),
        ("laser_segment_y", _C_FLOAT_POINTER),
        ("laser_collision_radius", _C_FLOAT_POINTER),
        ("laser_base_uncertainty", _C_FLOAT_POINTER),
        ("laser_uncertainty_per_frame", _C_FLOAT_POINTER),
        ("body_count", ctypes.c_int),
        ("body_base_x", _C_FLOAT_POINTER),
        ("body_base_y", _C_FLOAT_POINTER),
        ("body_velocity_x", _C_FLOAT_POINTER),
        ("body_velocity_y", _C_FLOAT_POINTER),
        ("body_half_width", _C_FLOAT_POINTER),
        ("body_half_height", _C_FLOAT_POINTER),
        ("player_radius", ctypes.c_float),
        ("preserve_previous_direction_inertia", ctypes.c_int),
        ("previous_direction", ctypes.c_int32),
        ("previous_focused", ctypes.c_uint8),
        ("target_enabled", ctypes.c_int),
        ("target_x", ctypes.c_double),
        ("target_y", ctypes.c_double),
        ("target_deadline", ctypes.c_int),
        ("item_safety_clearance", ctypes.c_double),
        ("playfield_left", ctypes.c_double),
        ("playfield_right", ctypes.c_double),
        ("playfield_top", ctypes.c_double),
        ("playfield_bottom", ctypes.c_double),
        ("recovery_reserve_distance", ctypes.c_double),
        ("supplemental_reserve_distance", ctypes.c_double),
        ("diagonal_speed", ctypes.c_double),
        ("cardinal_speed", ctypes.c_double),
        ("timeout_nanoseconds", ctypes.c_uint64),
    ]



class _LocalSupplementalOutputV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("capacity", ctypes.c_int),
        ("x", _C_DOUBLE_POINTER),
        ("y", _C_DOUBLE_POINTER),
        ("first_action", _C_INT32_POINTER),
        ("last_action", _C_INT32_POINTER),
        ("risk", _C_DOUBLE_POINTER),
        ("collisions", _C_INT32_POINTER),
        ("minimum_clearance", _C_DOUBLE_POINTER),
        ("immediate_clearance", _C_DOUBLE_POINTER),
        ("count", _C_INT32_POINTER),
    ]



__all__ = [
    "DecodedBulletPool",
    "LocalSupplementalNativeCancelledError",
    "LocalSupplementalNativeDeadlineError",
    "LocalSupplementalNativeResult",
]
