"""ctypes value objects for native local sensing."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


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


__all__ = ["DecodedBulletPool"]
