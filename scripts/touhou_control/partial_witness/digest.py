"""Content digest for an immutable stationary-witness problem."""

from __future__ import annotations

import hashlib
import json

import numpy as np

from ..query_survival import SurvivalQueryProblem
from .types import float_key


def stationary_witness_problem_digest(
    problem: SurvivalQueryProblem,
    *,
    decision_frame_support: tuple[int, ...],
) -> str:
    """Hash every numeric and semantic input consumed by the oracle."""

    if (
        not decision_frame_support
        or len(set(decision_frame_support)) != len(decision_frame_support)
        or tuple(sorted(decision_frame_support)) != decision_frame_support
        or decision_frame_support[0] <= 0
    ):
        raise ValueError(
            "decision frame support must be positive, sorted, and unique"
        )
    metadata = {
        "schema": "touhou-stationary-witness-problem-v1",
        "actions": [
            {
                "name": action.name,
                "velocity_x_hex": float_key(action.velocity_x),
                "velocity_y_hex": float_key(action.velocity_y),
            }
            for action in problem.actions
        ],
        "delay_frames": problem.delay_frames,
        "nominal_delay": problem.nominal_delay,
        "decision_frame_support": decision_frame_support,
        "frames_per_layer": problem.config.frames_per_layer,
        "required_clearance_hex": float_key(
            problem.config.required_clearance
        ),
        "clamp_to_bounds": problem.config.clamp_to_bounds,
        "repair_radius_cells": problem.config.repair_radius_cells,
        "shape": problem.clearance_volume.shape,
    }
    digest = hashlib.sha256(
        json.dumps(
            metadata,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    for name, source in (
        ("x_axis", problem.x_axis),
        ("y_axis", problem.y_axis),
        ("clearance_volume", problem.clearance_volume),
    ):
        array = np.ascontiguousarray(source, dtype=np.dtype("<f4"))
        digest.update(name.encode("ascii"))
        digest.update(
            json.dumps(
                array.shape,
                separators=(",", ":"),
            ).encode("ascii")
        )
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()
