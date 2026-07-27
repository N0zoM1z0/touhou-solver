"""Exact finite-model solve for one joined complete-mask root."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from analysis.partial_witness_capsule.audit import _validate_native
from analysis.partial_witness_capsule.serialization import (
    file_sha256,
    label_record,
    witness_record,
)
from analysis.viability_differential_audit import (
    BASE,
    _clearance,
    _variant_config,
)
from th08_pipeline_actions import TH08_COMPLETE_MASK_ACTION_SPACE
from touhou_control.partial_survival_witness import (
    build_stationary_witness_portfolio,
    replay_stationary_worst_branch,
)
from touhou_control.query_survival import (
    PendingCommand,
    SurvivalQueryProblem,
)
from touhou_control.viability import ViabilityConfig
from touhou_control.viability_audit_capsule import (
    read_viability_audit_capsule,
)

from .types import CompleteMaskCapsuleRoot


def build_problem(
    root: CompleteMaskCapsuleRoot,
    *,
    capsule_dir: Path,
    horizon: int,
) -> tuple[SurvivalQueryProblem, dict[str, object], float]:
    capsule_path = capsule_dir / root.capsule
    capsule = read_viability_audit_capsule(capsule_path)
    if int(capsule.metadata.get("source_frame", -1)) != root.source_frame:
        raise ValueError("capsule source frame does not match joined root")
    hazard_components = dict(root.identity.hazard_version.components)
    if (
        hazard_components.get("source_frame") is not None
        and int(hazard_components["source_frame"]) != root.source_frame
    ):
        raise ValueError("hazard version source frame does not match capsule")
    if (
        hazard_components.get("snapshot_frame") is not None
        and int(capsule.metadata.get("snapshot_frame", -1))
        != int(hazard_components["snapshot_frame"])
    ):
        raise ValueError(
            "hazard version snapshot frame does not match capsule"
        )
    start = root.query_frame - root.source_frame
    corridor_config = _variant_config(BASE)
    x_axis, y_axis, source_clearance = _clearance(
        capsule,
        corridor_config,
        variant=BASE,
    )
    if start < 0 or start + horizon >= source_clearance.shape[0]:
        raise ValueError("root horizon is outside the retained capsule")
    clearance = np.ascontiguousarray(
        source_clearance[start : start + horizon + 1],
        dtype=np.float32,
    )
    row = int(np.argmin(np.abs(y_axis - root.player_y)))
    column = int(np.argmin(np.abs(x_axis - root.player_x)))
    position_error = float(
        np.hypot(
            float(x_axis[column]) - root.player_x,
            float(y_axis[row]) - root.player_y,
        )
    )
    problem = SurvivalQueryProblem(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance,
        actions=TH08_COMPLETE_MASK_ACTION_SPACE.control_actions,
        delay_frames=root.delay_frames,
        nominal_delay=root.nominal_delay,
        config=ViabilityConfig(
            frames_per_layer=BASE.frames_per_layer,
            required_clearance=corridor_config.required_clearance,
            clamp_to_bounds=True,
            repair_radius_cells=1,
        ),
    )
    pending = (
        None
        if root.pending_token is None
        else PendingCommand(
            root.pending_token,
            root.remaining_delay_support,
        )
    )
    return (
        problem,
        {
            "frame": 0,
            "row": row,
            "column": column,
            "observed_action": root.active_token,
            "pending_command": pending,
        },
        position_error,
    )


def audit_root(
    root: CompleteMaskCapsuleRoot,
    *,
    capsule_dir: Path,
    horizon: int,
    decision_frame_support: tuple[int, ...],
) -> dict[str, object]:
    problem, query, position_error = build_problem(
        root,
        capsule_dir=capsule_dir,
        horizon=horizon,
    )
    portfolio = build_stationary_witness_portfolio(
        problem=problem,
        decision_frame_support=decision_frame_support,
        continuation_candidates=(root.held_token,),
        unrestricted_status="unresolved",
        **query,
    )
    expected_actions = tuple(action.name for action in problem.actions)
    if (
        not portfolio.complete
        or portfolio.complete_root_actions != expected_actions
    ):
        raise RuntimeError("complete-mask root-action portfolio is incomplete")
    for witness in portfolio.action_witnesses:
        if replay_stationary_worst_branch(witness) != witness.label:
            raise RuntimeError("complete-mask worst path did not replay")
    native = _validate_native(
        problem=problem,
        portfolio=portfolio,
        decision_frame_support=decision_frame_support,
    )
    if native["mismatch_count"]:
        raise RuntimeError("complete-mask scalar/native label mismatch")

    unknown_from = root.coverage.unknown_from_frame
    physical_model_status = (
        "model_unknown"
        if unknown_from is not None
        and unknown_from <= root.query_frame + horizon
        else "coverage_complete"
    )
    capsule_path = capsule_dir / root.capsule
    best = set(portfolio.best_actions)
    return {
        "root_identity": root.identity.record(),
        "hazard_coverage": root.coverage.record(),
        "physical_model_status": physical_model_status,
        "finite_model_authority": (
            "exact restricted stationary lower witness"
        ),
        "physical_action_authority": "none",
        "trace": {
            "decision_frame": root.decision_frame,
            "source_frame": root.source_frame,
            "trace_boolean_state_viable": root.trace_state_viable,
            "issued_mask": root.issued_mask,
        },
        "query": {
            "frame": query["frame"],
            "row": query["row"],
            "column": query["column"],
            "active_token": root.active_token,
            "held_token": root.held_token,
            "pending_token": root.pending_token,
            "remaining_delay_support": root.remaining_delay_support,
            "position_error_hex": position_error.hex(),
        },
        "capsule": {
            "path": str(capsule_path),
            "bytes": capsule_path.stat().st_size,
            "sha256": file_sha256(capsule_path),
        },
        "problem_digest": portfolio.problem_digest,
        "portfolio_digest": portfolio.portfolio_digest,
        "continuation_candidates": portfolio.continuation_candidates,
        "complete_root_actions": portfolio.complete_root_actions,
        "state_label": label_record(portfolio.state_label),
        "best_actions": portfolio.best_actions,
        "native_parity": native,
        "action_witnesses": [
            {
                **witness_record(witness),
                "best_root_action": witness.root_action in best,
            }
            for witness in portfolio.action_witnesses
        ],
        "margin_finite": math.isfinite(
            portfolio.state_label.bottleneck_margin
        ),
    }


__all__ = ["audit_root", "build_problem"]
