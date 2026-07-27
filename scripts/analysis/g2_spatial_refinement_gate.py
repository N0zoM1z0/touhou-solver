#!/usr/bin/env python3
"""Run the offline G2 lower/reference/upper gate on retained spatial roots."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_PLAYFIELD,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control.corridor import (
    ActionMaskBounds,
    RobustControlSpec,
    build_policy_candidate_guide,
    build_query_local_refinement_patch,
    build_robust_corridor_induction,
    build_spatial_cell_partition,
    check_fine_reference_inclusion,
    prepare_corridor_problem,
    prepare_dual_bound_scope,
    solve_query_local_dual_bounds_vectorized,
    trivial_coarse_action_bounds,
)
from touhou_control.corridor.clearance import hazard_clearance_volume
from touhou_control.corridor.grid import axis
from touhou_control.viability import (
    ViabilityConfig,
    build_robust_viability_policy,
)
from touhou_control.viability_audit_capsule import (
    ViabilityAuditCapsule,
    read_viability_audit_capsule,
)


DEFAULT_DOSSIER = Path(
    "artifacts/viability_audit/hard_stage4a_20260726_202439_exact_root_dossier.json"
)
DEFAULT_CAPSULE_DIR = Path(
    "artifacts/viability_audit/raw/hard_route2_stage4a_unattended_20260726_202439"
)
DEFAULT_OUTPUT = Path(
    "artifacts/viability_audit/g2_spatial_refinement_gate_20260727.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _prepared_problem(capsule: ViabilityAuditCapsule):
    metadata = capsule.metadata
    config = replace(
        TH08_CORRIDOR_CONFIG,
        grid_step=16.0,
        frames_per_layer=8,
        horizon_frames=80,
    )
    delays = tuple(int(value) for value in metadata["control_delay_candidates"])
    nominal_delay = int(metadata["nominal_control_delay"])
    if nominal_delay not in delays:
        nominal_delay = min(
            delays,
            key=lambda delay: abs(delay - nominal_delay),
        )
    control = RobustControlSpec(
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=delays,
        nominal_delay=nominal_delay,
        active_action=str(metadata["active_action"]),
    )
    return prepare_corridor_problem(
        bounds=TH08_PLAYFIELD,
        config=config,
        robust_control=control,
        aabbs=capsule.aabbs,
        piecewise_aabbs=capsule.piecewise_aabbs,
        segment_trajectories=capsule.segment_trajectories,
        packed_segments=capsule.packed_segments,
    )


def _dense_reference(
    *,
    prepared,
    fine_step: float,
):
    config = replace(
        prepared.config,
        grid_step=fine_step,
    )
    x_axis = axis(
        prepared.bounds.left,
        prepared.bounds.right,
        fine_step,
    )
    y_axis = axis(
        prepared.bounds.top,
        prepared.bounds.bottom,
        fine_step,
    )
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    clearance = hazard_clearance_volume(
        grid_x,
        grid_y,
        aabbs=prepared.aabbs,
        aabb_trajectories=prepared.aabb_trajectories,
        piecewise_aabbs=prepared.piecewise_aabbs,
        segments=prepared.segments,
        segment_trajectories=prepared.segment_trajectories,
        packed_segments=prepared.packed_segments,
        config=config,
    )
    policy = build_robust_viability_policy(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance,
        actions=prepared.robust_control.actions,
        delay_frames=prepared.robust_control.delay_frames,
        nominal_delay=prepared.robust_control.nominal_delay,
        config=ViabilityConfig(
            frames_per_layer=prepared.config.frames_per_layer,
            required_clearance=prepared.config.required_clearance,
            clamp_to_bounds=True,
        ),
        backend="native",
    )
    return policy


def _action_names(mask: int) -> list[str]:
    return [
        action.name
        for index, action in enumerate(TH08_VIABILITY_ACTIONS)
        if mask & (1 << index)
    ]


def _solve_resolution(
    *,
    prepared,
    scope,
    guide: np.ndarray,
    root: dict[str, object],
    fine_step: float,
    guide_empty_expansion_layers: int,
) -> dict[str, object]:
    patch_started = time.perf_counter()
    patch = build_query_local_refinement_patch(
        prepared_problem=prepared,
        scope=scope,
        incoming_bounds=trivial_coarse_action_bounds(prepared_problem=prepared),
        fine_step=fine_step,
        coarse_candidate_states=guide,
        coarse_candidate_halo_cells=(1 if fine_step <= 4.0 else 0),
        state_halo_cells=1,
        allow_full_field=False,
    )
    patch_ms = (time.perf_counter() - patch_started) * 1000.0
    result = solve_query_local_dual_bounds_vectorized(
        prepared_problem=prepared,
        patch=patch,
        backend="native",
    )
    reference_started = time.perf_counter()
    reference = _dense_reference(
        prepared=prepared,
        fine_step=fine_step,
    )
    reference_ms = (time.perf_counter() - reference_started) * 1000.0
    identity = build_spatial_cell_partition(
        coarse_x=patch.fine_x,
        coarse_y=patch.fine_y,
        fine_x=patch.fine_x,
        fine_y=patch.fine_y,
    )
    inclusion = check_fine_reference_inclusion(
        bounds=ActionMaskBounds(
            lower=result.lower_action_masks,
            upper=result.upper_action_masks,
            action_count=len(TH08_VIABILITY_ACTIONS),
        ),
        fine_reference_masks=reference.safe_action_masks,
        partition=identity,
    )
    query = root["query"]
    root_frame = int(query["query_frame"]) - int(
        root["capsule"]["contract"]["source_frame"]
    )
    reference_query = reference.query(
        frame=root_frame,
        x=float(query["projected_x"]),
        y=float(query["projected_y"]),
        active_action=str(query["active_action"]),
    )
    return {
        "fine_step": fine_step,
        "guide_empty_expansion_layers": guide_empty_expansion_layers,
        "coarse_candidate_halo_cells": (1 if fine_step <= 4.0 else 0),
        "patch_ms": patch_ms,
        "solve_ms": result.elapsed_ms,
        "reference_ms": reference_ms,
        "patch_spatial_fraction": patch.spatial_fraction,
        "clearance_rectangle": {
            "rows": patch.clearance_row_end - patch.clearance_row_start,
            "columns": (patch.clearance_column_end - patch.clearance_column_start),
        },
        "requested_state_count": int(np.count_nonzero(patch.requested_states)),
        "root_point_lower_mask": result.root_point_lower_mask,
        "root_point_lower_actions": _action_names(result.root_point_lower_mask),
        "root_point_upper_mask": result.root_point_upper_mask,
        "root_point_upper_actions": _action_names(result.root_point_upper_mask),
        "root_cell_lower_mask": result.root_lower_mask,
        "root_cell_upper_mask": result.root_upper_mask,
        "reference_root_mask": (
            sum(
                1 << index
                for index, action in enumerate(TH08_VIABILITY_ACTIONS)
                if action.name in reference_query.safe_actions
            )
        ),
        "reference_root_actions": list(reference_query.safe_actions),
        "false_safe_action_count": inclusion.false_safe_action_count,
        "missing_upper_action_count": (inclusion.missing_upper_action_count),
        "branch_bound_mode": "trivial_zero_to_all",
        "branch_false_safe_action_count": 0,
        "branch_missing_upper_action_count": 0,
        "root_recovered_by_lower": result.root_point_lower_mask != 0,
        "passed_inclusion": inclusion.passed,
    }


def run_gate(
    *,
    dossier_path: Path,
    capsule_dir: Path,
) -> dict[str, object]:
    dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    spatial_roots = [
        root
        for root in dossier["roots"]
        if root["primary_classification"]["code"] == "SPATIAL_AMBIGUITY"
    ]
    cases: list[dict[str, object]] = []
    for root in spatial_roots:
        capsule_path = capsule_dir / root["capsule"]["name"]
        capsule = read_viability_audit_capsule(capsule_path)
        prepared = _prepared_problem(capsule)
        query = root["query"]
        root_frame = int(query["query_frame"]) - int(capsule.metadata["source_frame"])
        scope = prepare_dual_bound_scope(
            prepared_problem=prepared,
            start_x=float(query["projected_x"]),
            start_y=float(query["projected_y"]),
            root_frame=root_frame,
            root_active_action=str(query["active_action"]),
        )
        coarse_started = time.perf_counter()
        induction = build_robust_corridor_induction(
            prepared_problem=prepared,
            start_x=float(query["projected_x"]),
            start_y=float(query["projected_y"]),
        )
        coarse_ms = (time.perf_counter() - coarse_started) * 1000.0
        guides: dict[int, np.ndarray] = {}

        def guide(expansion_layers: int) -> np.ndarray:
            if expansion_layers not in guides:
                guides[expansion_layers] = build_policy_candidate_guide(
                    policy=induction.policy,
                    scope=scope,
                    empty_expansion_layers=expansion_layers,
                )
            return guides[expansion_layers]

        resolutions: list[dict[str, object]] = []
        error = None
        for fine_step, expansion_layers in (
            (8.0, 1),
            (4.0, 1),
            (4.0, 2),
        ):
            try:
                resolution = _solve_resolution(
                    prepared=prepared,
                    scope=scope,
                    guide=guide(expansion_layers),
                    root=root,
                    fine_step=fine_step,
                    guide_empty_expansion_layers=expansion_layers,
                )
            except (RuntimeError, ValueError) as failure:
                error = f"{type(failure).__name__}: {failure}"
                break
            resolutions.append(resolution)
            if resolution["root_recovered_by_lower"]:
                break
        cases.append(
            {
                "root_id": root["root_id"],
                "capsule": root["capsule"],
                "root_contract_sha256": root["root_contract_sha256"],
                "query": query,
                "coarse_ms": coarse_ms,
                "coarse_query_state_viable": bool(
                    induction.policy.query(
                        frame=root_frame,
                        x=float(query["projected_x"]),
                        y=float(query["projected_y"]),
                        active_action=str(query["active_action"]),
                    ).state_viable
                ),
                "guide_state_counts": {
                    str(expansion_layers): int(np.count_nonzero(candidate_guide))
                    for expansion_layers, candidate_guide in guides.items()
                },
                "resolutions": resolutions,
                "error": error,
                "recovered_by_lower": bool(
                    resolutions and resolutions[-1]["root_recovered_by_lower"]
                ),
                "passed_inclusion": bool(
                    resolutions
                    and all(
                        resolution["passed_inclusion"] for resolution in resolutions
                    )
                ),
            }
        )
    return {
        "schema": "touhou-g2-spatial-refinement-gate-v1",
        "authority": "offline_finite_model_only",
        "dossier": {
            "path": str(dossier_path),
            "sha256": _sha256(dossier_path),
            "content_sha256": dossier["dossier_content_sha256"],
        },
        "capsule_directory": str(capsule_dir),
        "case_count": len(cases),
        "cases": cases,
        "gate": {
            "expected_case_count": 6,
            "all_cases_recovered_by_lower": all(
                case["recovered_by_lower"] for case in cases
            ),
            "all_inclusions_passed": all(case["passed_inclusion"] for case in cases),
            "full_field_patch_count": sum(
                "forbidden full field" in (case["error"] or "") for case in cases
            ),
            "passed": (
                len(cases) == 6
                and all(case["recovered_by_lower"] for case in cases)
                and all(case["passed_inclusion"] for case in cases)
                and all(case["error"] is None for case in cases)
            ),
        },
        "limitations": [
            "The vectorized rectangle solver reuses the dense native "
            "recurrence and is not the independent scalar oracle.",
            "Retained hidden-branch bounds are the sound but trivial "
            "zero-to-all interval; generated scalar cases test tightened "
            "branch bounds.",
            "No result is published or consumed by the live controller.",
            "Solve and patch timings are offline measurements, not a "
            "Windows delivery gate.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument(
        "--capsule-dir",
        type=Path,
        default=DEFAULT_CAPSULE_DIR,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args(argv)
    report = run_gate(
        dossier_path=arguments.dossier,
        capsule_dir=arguments.capsule_dir,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["gate"], sort_keys=True))
    return 0 if report["gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
