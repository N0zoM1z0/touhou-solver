#!/usr/bin/env python3
"""Offline differential audit of pre-hit robust-viability queries.

Raw live traces identify the queried state but do not retain the complete
hazard epoch.  Run the controller with ``--viability-audit-dir`` (or the
unattended supervisor with ``--viability-audit``), then give this script that
ignored capsule directory.  The output is compact and suitable for review.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, OrderedDict
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from corridor_planner import (
    CorridorConfig,
    _axis,
    _hazard_clearance_volume,
)
from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_PLAYFIELD,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control import native_backend
from touhou_control.viability import (
    RobustViabilityPolicy,
    ViabilityConfig,
    build_robust_viability_policy,
)
from touhou_control.viability_audit_capsule import (
    ViabilityAuditCapsule,
    read_viability_audit_capsule,
    read_viability_audit_metadata,
)


@dataclass(frozen=True)
class AuditVariant:
    name: str
    grid_step: float
    frames_per_layer: int
    horizon_frames: int
    delay_mode: str = "exact"
    causal_role: str = "classification"


@dataclass(frozen=True)
class SolvedVariant:
    policy: RobustViabilityPolicy
    source_frame: int
    survival_frames: np.ndarray | None = None
    bottleneck_margins: np.ndarray | None = None
    best_action_masks: np.ndarray | None = None


BASE = AuditVariant("space16_time8_h80", 16.0, 8, 80)
SPACE_8 = AuditVariant("space8_time8_h80", 8.0, 8, 80)
SPACE_4 = AuditVariant("space4_time8_h80", 4.0, 8, 80)
TIME_4_CLIPPED = AuditVariant(
    "space8_time4_h80_delay_clipped",
    8.0,
    4,
    80,
    delay_mode="clip",
    causal_role="diagnostic_only",
)
SHORT_HORIZONS = tuple(
    AuditVariant(f"space16_time8_h{horizon}", 16.0, 8, horizon)
    for horizon in (32, 48, 64)
)


def _context(metadata: dict[str, object]) -> tuple[object, ...]:
    raw = metadata.get("context_key")
    return tuple(raw) if isinstance(raw, list) else ()


def _variant_config(variant: AuditVariant) -> CorridorConfig:
    return replace(
        TH08_CORRIDOR_CONFIG,
        grid_step=variant.grid_step,
        frames_per_layer=variant.frames_per_layer,
        horizon_frames=variant.horizon_frames,
    )


def _variant_delays(
    metadata: dict[str, object],
    variant: AuditVariant,
) -> tuple[tuple[int, ...], int]:
    raw = metadata["control_delay_candidates"]
    delays = tuple(int(value) for value in raw)
    nominal = int(metadata["nominal_control_delay"])
    if variant.delay_mode == "clip":
        delays = tuple(
            delay
            for delay in delays
            if delay <= variant.frames_per_layer
        )
        if not delays:
            raise ValueError("clipped delay support became empty")
        nominal = min(delays, key=lambda delay: abs(delay - nominal))
    elif delays[-1] > variant.frames_per_layer:
        raise ValueError(
            f"delay {delays[-1]} exceeds {variant.frames_per_layer}-frame "
            "layer without pending-command state"
        )
    return delays, nominal


def _clearance(
    capsule: ViabilityAuditCapsule,
    config: CorridorConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x_axis = _axis(
        TH08_PLAYFIELD.left,
        TH08_PLAYFIELD.right,
        config.grid_step,
    )
    y_axis = _axis(
        TH08_PLAYFIELD.top,
        TH08_PLAYFIELD.bottom,
        config.grid_step,
    )
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    volume = _hazard_clearance_volume(
        grid_x,
        grid_y,
        aabbs=capsule.aabbs,
        aabb_trajectories=(),
        piecewise_aabbs=capsule.piecewise_aabbs,
        segments=(),
        segment_trajectories=capsule.segment_trajectories,
        config=config,
    )
    return x_axis, y_axis, volume


class AuditSolver:
    def __init__(self, *, maximum_cached_solutions: int = 8) -> None:
        if maximum_cached_solutions <= 0:
            raise ValueError("solution cache size must be positive")
        self.maximum_cached_solutions = maximum_cached_solutions
        self._capsules: dict[Path, ViabilityAuditCapsule] = {}
        self._solutions: OrderedDict[
            tuple[Path, AuditVariant, Path | None, bool],
            SolvedVariant,
        ] = OrderedDict()

    def capsule(self, path: Path) -> ViabilityAuditCapsule:
        if path not in self._capsules:
            self._capsules[path] = read_viability_audit_capsule(path)
        return self._capsules[path]

    def solve(
        self,
        path: Path,
        variant: AuditVariant,
        *,
        survival_shadow: bool = False,
        continuation_path: Path | None = None,
    ) -> SolvedVariant:
        key = (
            path,
            variant,
            continuation_path,
            survival_shadow,
        )
        if key in self._solutions:
            solved = self._solutions.pop(key)
            self._solutions[key] = solved
            return solved
        capsule = self.capsule(path)
        config = _variant_config(variant)
        x_axis, y_axis, clearance = _clearance(capsule, config)
        delays, nominal = _variant_delays(capsule.metadata, variant)
        terminal_viable = None
        if continuation_path is not None:
            continuation = self.solve(continuation_path, variant)
            terminal_frame = (
                int(capsule.metadata["source_frame"])
                + variant.horizon_frames
            )
            continuation_source = int(
                self.capsule(continuation_path).metadata["source_frame"]
            )
            continuation_age = terminal_frame - continuation_source
            continuation_layer = (
                continuation_age // variant.frames_per_layer
            )
            if not 0 <= continuation_layer <= continuation.policy.layer_count:
                raise ValueError("continuation policy does not cover terminal")
            terminal_viable = continuation.policy.viable[
                continuation_layer
            ]
        viability_config = ViabilityConfig(
            frames_per_layer=variant.frames_per_layer,
            required_clearance=config.required_clearance,
            clamp_to_bounds=True,
            repair_radius_cells=1,
        )
        if survival_shadow and continuation_path is None:
            fused = native_backend.build_survival_viability_arrays(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance,
                velocity_x=np.asarray(
                    [
                        action.velocity_x
                        for action in TH08_VIABILITY_ACTIONS
                    ],
                    dtype=np.float64,
                ),
                velocity_y=np.asarray(
                    [
                        action.velocity_y
                        for action in TH08_VIABILITY_ACTIONS
                    ],
                    dtype=np.float64,
                ),
                delay_frames=np.asarray(delays, dtype=np.int32),
                frames_per_layer=variant.frames_per_layer,
                required_clearance=config.required_clearance,
                clamp_to_bounds=True,
            )
        else:
            fused = None
        if fused is not None:
            (
                survival_frames,
                bottleneck_margins,
                best_action_masks,
                viable,
                safe_action_masks,
            ) = fused
            policy = RobustViabilityPolicy(
                x_axis=x_axis,
                y_axis=y_axis,
                actions=TH08_VIABILITY_ACTIONS,
                delay_frames=delays,
                nominal_delay=nominal,
                config=viability_config,
                viable=viable,
                safe_action_masks=safe_action_masks,
                backend="native_fused_survival_shadow",
            )
            solved = SolvedVariant(
                policy=policy,
                source_frame=int(capsule.metadata["source_frame"]),
                survival_frames=survival_frames,
                bottleneck_margins=bottleneck_margins,
                best_action_masks=best_action_masks,
            )
        else:
            policy = build_robust_viability_policy(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance,
                actions=TH08_VIABILITY_ACTIONS,
                delay_frames=delays,
                nominal_delay=nominal,
                config=viability_config,
                backend="native",
                terminal_viable=terminal_viable,
            )
            solved = SolvedVariant(
                policy=policy,
                source_frame=int(capsule.metadata["source_frame"]),
            )
        self._solutions[key] = solved
        while len(self._solutions) > self.maximum_cached_solutions:
            self._solutions.popitem(last=False)
        return solved


def _read_trace(path: Path) -> list[dict[str, object]]:
    rows = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("kind") == "decision":
                rows.append(row)
    return rows


def _hit_slots(path: Path | None) -> dict[int, int]:
    if path is None:
        return {}
    report = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for case in report.get("cases", ()):
        candidate = case.get("observed_bullet_contact_candidate")
        if isinstance(candidate, dict) and "slot" in candidate:
            result[int(case["frame"])] = int(candidate["slot"])
    return result


def _capsule_basename(raw: object) -> str | None:
    if not isinstance(raw, str) or not raw:
        return None
    return raw.replace("\\", "/").rsplit("/", 1)[-1]


def _query_payload(
    solved: SolvedVariant,
    row: dict[str, object],
) -> dict[str, object]:
    corridor = row["corridor"]
    viability = corridor["viability"]
    player = row["player"]
    query = solved.policy.query(
        frame=int(viability["query_frame"])
        - solved.source_frame,
        x=float(player["projected_x"]),
        y=float(player["projected_y"]),
        active_action=str(viability["active_action"]),
    )
    result: dict[str, object] = {
        "available": query.available,
        "state_viable": query.state_viable,
        "safe_action_count": query.safe_action_count,
        "layer": query.layer,
        "row": query.row,
        "column": query.column,
        "position_error": query.position_error,
    }
    if (
        query.available
        and query.layer is not None
        and query.row is not None
        and query.column is not None
        and solved.survival_frames is not None
        and solved.bottleneck_margins is not None
        and solved.best_action_masks is not None
    ):
        active_index = next(
            index
            for index, action in enumerate(solved.policy.actions)
            if action.name == query.active_action
        )
        state_index = (
            query.layer,
            active_index,
            query.row,
            query.column,
        )
        result["survival_frames"] = int(
            solved.survival_frames[state_index]
        )
        result["bottleneck_margin"] = float(
            solved.bottleneck_margins[state_index]
        )
        result["best_action_mask"] = int(
            solved.best_action_masks[state_index]
        )
        result["best_actions"] = [
            action.name
            for index, action in enumerate(solved.policy.actions)
            if result["best_action_mask"] & (1 << index)
        ]
        result["remaining_frames"] = (
            solved.policy.horizon_frames
            - query.layer * solved.policy.config.frames_per_layer
        )
    return result


def _choose_continuation(
    current: Path,
    *,
    metadata: dict[Path, dict[str, object]],
    variant: AuditVariant,
) -> Path | None:
    current_metadata = metadata[current]
    current_source = int(current_metadata["source_frame"])
    terminal_frame = current_source + variant.horizon_frames
    candidates = [
        path
        for path, candidate in metadata.items()
        if path != current
        and _context(candidate) == _context(current_metadata)
        and current_source < int(candidate["source_frame"]) <= terminal_frame
        and (
            terminal_frame - int(candidate["source_frame"])
            <= variant.horizon_frames
        )
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda path: int(metadata[path]["source_frame"]),
    )


def _fresh_capsule(
    current: Path,
    *,
    query_frame: int,
    metadata: dict[Path, dict[str, object]],
) -> Path:
    current_context = _context(metadata[current])
    candidates = [
        path
        for path, candidate in metadata.items()
        if _context(candidate) == current_context
        and int(candidate["source_frame"]) <= query_frame
    ]
    return max(
        candidates,
        key=lambda path: int(metadata[path]["source_frame"]),
        default=current,
    )


def _birth_evidence(
    current: Path,
    *,
    until_frame: int,
    metadata: dict[Path, dict[str, object]],
) -> tuple[int, tuple[int, ...]]:
    current_metadata = metadata[current]
    current_slots = {
        int(slot)
        for slot in current_metadata.get("bullet_slots", ())
    }
    later_slots: set[int] = set()
    for candidate in metadata.values():
        if (
            _context(candidate) == _context(current_metadata)
            and int(current_metadata["source_frame"])
            < int(candidate["source_frame"])
            <= until_frame
        ):
            later_slots.update(
                int(slot)
                for slot in candidate.get("bullet_slots", ())
            )
    births = tuple(sorted(later_slots - current_slots))
    return len(births), births


def _classify_empty_query(
    *,
    trace_empty: bool,
    base_matches_trace: bool,
    base_viable: bool,
    spatial_variant_viable: bool,
    fresh_policy_differs: bool,
    fresh_viable: bool,
    short_horizon_viable: bool,
    collision_hazard_absent_at_source: bool,
) -> tuple[str | None, tuple[str, ...]]:
    """Separate the empty-set diagnosis from orthogonal model evidence."""

    classification = None
    if trace_empty and not base_matches_trace:
        classification = "policy_reconstruction_or_version_mismatch"
    elif trace_empty and not base_viable and spatial_variant_viable:
        classification = "spatial_coarse_false_empty"
    elif (
        trace_empty
        and not base_viable
        and fresh_policy_differs
        and fresh_viable
    ):
        classification = "stale_policy_version"
    elif trace_empty and not base_viable and short_horizon_viable:
        classification = "finite_horizon_collapse"
    elif trace_empty:
        classification = "modeled_losing_unresolved"
    evidence = (
        ("hazard_model_future_birth_gap",)
        if trace_empty and collision_hazard_absent_at_source
        else ()
    )
    return classification, evidence


def audit(
    *,
    trace_path: Path,
    capsule_dir: Path,
    regressions_path: Path | None,
    pre_hit_frames: int,
    max_queries_per_hit: int,
    maximum_cached_solutions: int = 2,
) -> dict[str, object]:
    rows = _read_trace(trace_path)
    hit_frames = [
        int(row["frame"])
        for row in rows
        if row.get("hit_started")
    ]
    hit_slot_by_frame = _hit_slots(regressions_path)
    capsule_paths = sorted(capsule_dir.glob("*.npz"))
    metadata = {
        path: read_viability_audit_metadata(path)
        for path in capsule_paths
    }
    paths_by_name = {path.name: path for path in capsule_paths}
    selected: list[tuple[int, dict[str, object]]] = []
    for hit_frame in hit_frames:
        candidates = []
        for row in rows:
            frame = int(row["frame"])
            if not hit_frame - pre_hit_frames <= frame < hit_frame:
                continue
            corridor = row.get("corridor")
            if not isinstance(corridor, dict):
                continue
            viability = corridor.get("viability")
            if not isinstance(viability, dict) or not viability.get(
                "available"
            ):
                continue
            if _capsule_basename(corridor.get("audit_capsule")) is None:
                continue
            candidates.append(row)
        selected.extend(
            (hit_frame, row)
            for row in candidates[-max_queries_per_hit:]
        )

    solver = AuditSolver(
        maximum_cached_solutions=maximum_cached_solutions,
    )
    observations = []
    missing_capsules = Counter()
    for hit_frame, row in selected:
        corridor = row["corridor"]
        viability = corridor["viability"]
        capsule_name = _capsule_basename(corridor.get("audit_capsule"))
        path = paths_by_name.get(capsule_name or "")
        if path is None:
            missing_capsules[capsule_name or "null"] += 1
            continue
        query_frame = int(viability["query_frame"])
        base_solved = solver.solve(path, BASE, survival_shadow=True)
        base = _query_payload(base_solved, row)
        variant_results = {
            BASE.name: base,
            SPACE_8.name: _query_payload(
                solver.solve(path, SPACE_8),
                row,
            ),
            SPACE_4.name: _query_payload(
                solver.solve(path, SPACE_4),
                row,
            ),
            TIME_4_CLIPPED.name: _query_payload(
                solver.solve(path, TIME_4_CLIPPED),
                row,
            ),
        }
        for variant in SHORT_HORIZONS:
            age = query_frame - int(corridor["source_frame"])
            if age < variant.horizon_frames:
                variant_results[variant.name] = _query_payload(
                    solver.solve(path, variant),
                    row,
                )
            else:
                variant_results[variant.name] = {
                    "available": False,
                    "reason": "query age exceeds short horizon",
                }

        continuation = _choose_continuation(
            path,
            metadata=metadata,
            variant=BASE,
        )
        if continuation is None:
            overlap = {
                "available": False,
                "reason": "no later same-context policy covers terminal",
            }
        else:
            overlap = _query_payload(
                solver.solve(
                    path,
                    BASE,
                    continuation_path=continuation,
                ),
                row,
            )
            overlap["continuation_capsule"] = continuation.name
            overlap["continuation_source_frame"] = int(
                metadata[continuation]["source_frame"]
            )

        fresh_path = _fresh_capsule(
            path,
            query_frame=query_frame,
            metadata=metadata,
        )
        fresh = _query_payload(solver.solve(fresh_path, BASE), row)
        birth_count, birth_slots = _birth_evidence(
            path,
            until_frame=hit_frame,
            metadata=metadata,
        )
        collision_slot = hit_slot_by_frame.get(hit_frame)
        source_slots = {
            int(slot)
            for slot in metadata[path].get("bullet_slots", ())
        }
        collision_birth = (
            collision_slot is not None
            and collision_slot not in source_slots
        )
        trace_empty = not bool(viability["state_viable"])
        base_matches_trace = bool(base["state_viable"]) == bool(
            viability["state_viable"]
        )
        short_winning = [
            name
            for name, result in variant_results.items()
            if name.startswith("space16_time8_h")
            and name != BASE.name
            and result.get("state_viable")
        ]
        classification, evidence_flags = _classify_empty_query(
            trace_empty=trace_empty,
            base_matches_trace=base_matches_trace,
            base_viable=bool(base["state_viable"]),
            spatial_variant_viable=bool(
                variant_results[SPACE_8.name]["state_viable"]
                or variant_results[SPACE_4.name]["state_viable"]
            ),
            fresh_policy_differs=fresh_path != path,
            fresh_viable=bool(fresh["state_viable"]),
            short_horizon_viable=bool(short_winning),
            collision_hazard_absent_at_source=collision_birth,
        )
        labels = (
            ([classification] if classification is not None else [])
            + list(evidence_flags)
        )
        observations.append(
            {
                "hit_frame": hit_frame,
                "decision_frame": int(row["frame"]),
                "query_frame": query_frame,
                "time_to_hit": hit_frame - query_frame,
                "spell_id": int(row["spell"]["spell_id"]),
                "capsule": path.name,
                "capsule_source_frame": int(
                    metadata[path]["source_frame"]
                ),
                "capsule_snapshot_frame": int(
                    metadata[path]["snapshot_frame"]
                ),
                "trace_state_viable": not trace_empty,
                "trace_layer": int(viability["layer"]),
                "trace_position_error": float(
                    viability["position_error"]
                ),
                "active_action": str(viability["active_action"]),
                "selected_recovery_action": viability.get(
                    "selected_action"
                ),
                "issued_action": row.get("action"),
                "variants": variant_results,
                "next_policy_overlap_terminal": overlap,
                "fresh_policy": {
                    **fresh,
                    "capsule": fresh_path.name,
                    "source_frame": int(
                        metadata[fresh_path]["source_frame"]
                    ),
                },
                "birth_evidence": {
                    "new_slot_count_before_hit": birth_count,
                    "new_slots_before_hit": birth_slots,
                    "collision_slot": collision_slot,
                    "collision_slot_absent_at_policy_source": (
                        collision_birth
                    ),
                    "limitation": (
                        "observed slot delta only; no hindsight/ECL birth "
                        "geometry injected into this audit"
                    ),
                },
                "primary_classification": classification,
                "evidence_flags": evidence_flags,
                "labels": labels,
            }
        )

    empty_observations = [
        observation
        for observation in observations
        if not observation["trace_state_viable"]
    ]
    classification_counts = Counter(
        observation["primary_classification"]
        for observation in empty_observations
        if observation["primary_classification"] is not None
    )
    evidence_counts = Counter(
        evidence
        for observation in empty_observations
        for evidence in observation["evidence_flags"]
    )
    terminal_cohort = [
        observation
        for observation in observations
        if observation["variants"][BASE.name]["state_viable"]
        and observation["next_policy_overlap_terminal"].get("available")
    ]
    terminal_rejections = sum(
        not observation["next_policy_overlap_terminal"]["state_viable"]
        for observation in terminal_cohort
    )
    return {
        "schema": "touhou-viability-differential-audit-v1",
        "scope": {
            "trace": str(trace_path),
            "capsule_dir": str(capsule_dir),
            "pre_hit_frames": pre_hit_frames,
            "max_queries_per_hit": max_queries_per_hit,
            "maximum_cached_solutions": maximum_cached_solutions,
            "hit_count": len(hit_frames),
            "selected_pre_hit_queries": len(selected),
            "audited_queries": len(observations),
            "audited_empty_queries": len(empty_observations),
            "missing_capsules": dict(missing_capsules),
        },
        "model_constraints": {
            "exact_comparable_variants": [
                BASE.name,
                SPACE_8.name,
                SPACE_4.name,
                *(variant.name for variant in SHORT_HORIZONS),
            ],
            "diagnostic_only_variants": [TIME_4_CLIPPED.name],
            "time4_limitation": (
                "The live delay support can exceed four frames. Exact "
                "four-frame layers require pending-command and remaining-"
                "delay state; clipping delay changes the game."
            ),
            "event_time_status": (
                "Not claimed. Exact nonuniform event layers require the same "
                "augmented pending-command state."
            ),
            "terminal_monotonicity": (
                "Next-policy overlap is a subset of instant-safe terminal "
                "states. It can reject a false winning state but cannot turn "
                "an empty state into a winning state."
            ),
            "terminal_phase_limitation": (
                "The continuation query uses the containing eight-frame "
                "layer. Exact overlap at an intra-layer terminal frame needs "
                "residual-frame propagation; this empty-only sample has no "
                "winning overlap cohort."
            ),
            "birth_status": (
                "Entity slot deltas are measured. Real ECL/timeline birth "
                "geometry is not yet injected, so birth-aware parity remains "
                "unresolved."
            ),
        },
        "classification_counts": dict(classification_counts),
        "orthogonal_evidence_counts": dict(evidence_counts),
        "terminal_overlap": {
            "instant_winning_with_comparable_overlap": len(
                terminal_cohort
            ),
            "rejected_by_next_policy_overlap": terminal_rejections,
        },
        "observations": observations,
    }


def _markdown(report: dict[str, object]) -> str:
    scope = report["scope"]
    lines = [
        "# Robust-Viability Differential Audit",
        "",
        (
            f"- Hits: {scope['hit_count']}; audited pre-hit queries: "
            f"{scope['audited_queries']}; empty: "
            f"{scope['audited_empty_queries']}."
        ),
        (
            "- Exact spatial comparisons preserve the 8-frame action layer: "
            "`16px`, `8px`, and `4px`."
        ),
        (
            "- The `8px/4f` result clips delays above four frames and is "
            "diagnostic only."
        ),
        (
            "- Birth evidence is observed slot delta, not an injected ECL "
            "birth oracle."
        ),
        "",
        "## Empty-query labels",
        "",
        "| Label | Count |",
        "| --- | ---: |",
    ]
    for label, count in sorted(
        report["classification_counts"].items()
    ):
        lines.append(f"| `{label}` | {count} |")
    lines.extend(
        [
            "",
            "## Orthogonal evidence",
            "",
            (
                "These flags do not by themselves explain why the queried "
                "kernel was empty."
            ),
            "",
            "| Evidence | Count |",
            "| --- | ---: |",
        ]
    )
    for label, count in sorted(
        report["orthogonal_evidence_counts"].items()
    ):
        lines.append(f"| `{label}` | {count} |")
    terminal = report["terminal_overlap"]
    lines.extend(
        [
            "",
            "## Terminal overlap",
            "",
            (
                f"- Comparable instant-winning queries: "
                f"{terminal['instant_winning_with_comparable_overlap']}."
            ),
            (
                f"- Rejected by next-policy overlap: "
                f"{terminal['rejected_by_next_policy_overlap']}."
            ),
            (
                "- Exact intra-layer overlap still needs residual-frame "
                "propagation; this empty-only sample cannot validate it."
            ),
            "",
            "## Witnesses",
            "",
            (
                "| Hit | Decision | Spell | Base survival | 8px | 4px | "
                "Fresh | Birth collision | Labels |"
            ),
            "| ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for observation in report["observations"]:
        if observation["trace_state_viable"]:
            continue
        variants = observation["variants"]
        base = variants[BASE.name]
        lines.append(
            "| "
            f"{observation['hit_frame']} | "
            f"{observation['decision_frame']} | "
            f"{observation['spell_id']} | "
            f"{base.get('survival_frames', '-')} | "
            f"{variants[SPACE_8.name]['state_viable']} | "
            f"{variants[SPACE_4.name]['state_viable']} | "
            f"{observation['fresh_policy']['state_viable']} | "
            f"{observation['birth_evidence']['collision_slot_absent_at_policy_source']} | "
            f"{', '.join(observation['labels'])} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("capsule_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--regressions", type=Path)
    parser.add_argument("--pre-hit-frames", type=int, default=32)
    parser.add_argument("--max-queries-per-hit", type=int, default=8)
    parser.add_argument("--solution-cache-size", type=int, default=2)
    args = parser.parse_args(argv)
    if (
        args.pre_hit_frames <= 0
        or args.max_queries_per_hit <= 0
        or args.solution_cache_size <= 0
    ):
        parser.error(
            "pre-hit window, query limit, and cache size must be positive"
        )
    report = audit(
        trace_path=args.trace,
        capsule_dir=args.capsule_dir,
        regressions_path=args.regressions,
        pre_hit_frames=args.pre_hit_frames,
        max_queries_per_hit=args.max_queries_per_hit,
        maximum_cached_solutions=args.solution_cache_size,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.output.with_suffix(".md").write_text(
        _markdown(report),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "scope": report["scope"],
                "classification_counts": (
                    report["classification_counts"]
                ),
                "orthogonal_evidence_counts": (
                    report["orthogonal_evidence_counts"]
                ),
                "terminal_overlap": report["terminal_overlap"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
