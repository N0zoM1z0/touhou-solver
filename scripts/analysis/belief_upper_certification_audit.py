#!/usr/bin/env python3
"""Replay incumbent-seeded belief upper certificates on physical capsules.

The live Boolean policy remains authoritative.  This program reconstructs a
small deterministic cohort of exact roots from one ignored JSONL trace and
its ignored viability capsules.  For each root it computes an attainable
slow-action continuation lower bound and asks whether the unrestricted
revealed-delay upper can strictly beat that incumbent.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from analysis.viability_differential_audit import (
    BASE,
    _clearance,
    _variant_config,
)
from th08_corridor_adapter import TH08_VIABILITY_ACTIONS
from touhou_control.query_survival import (
    PendingCommand,
    PipelineWorkspaceDeadlineError,
    SurvivalQueryProblem,
)
from touhou_control.viability import ViabilityConfig
from touhou_control.viability_audit_capsule import (
    read_viability_audit_capsule,
)


@dataclass(frozen=True)
class Root:
    decision_frame: int
    query_frame: int
    source_frame: int
    capsule: str
    spell_id: int
    x: float
    y: float
    observed_action: str
    pending: PendingCommand | None
    delay_frames: tuple[int, ...]
    nominal_delay: int
    trace_state_viable: bool
    issued_action: str


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _summary(values: list[float]) -> dict[str, float | None]:
    return {
        "median": statistics.median(values) if values else None,
        "p95": _p95(values),
        "max": max(values) if values else None,
    }


def _capsule_name(raw: object) -> str | None:
    if not isinstance(raw, str) or not raw:
        return None
    return raw.replace("\\", "/").rsplit("/", 1)[-1]


def _pending(raw: object) -> PendingCommand | None:
    if not isinstance(raw, dict):
        return None
    action = raw.get("desired_action")
    remaining = raw.get("remaining_frames")
    if not isinstance(action, str) or not isinstance(remaining, list):
        return None
    values = tuple(sorted(set(int(value) for value in remaining)))
    return PendingCommand(action, values)


def _read_roots(
    trace: Path,
) -> tuple[list[Root], list[int]]:
    roots: list[Root] = []
    hit_frames: list[int] = []
    with trace.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("kind") != "decision":
                continue
            if row.get("hit_started"):
                hit_frames.append(int(row["frame"]))
            corridor = row.get("corridor")
            if not isinstance(corridor, dict):
                continue
            viability = corridor.get("viability")
            capsule = _capsule_name(corridor.get("audit_capsule"))
            if (
                capsule is None
                or not isinstance(viability, dict)
                or not viability.get("available")
            ):
                continue
            player = row.get("player")
            spell = row.get("spell")
            delays_raw = row.get("control_delay_candidates")
            if (
                not isinstance(player, dict)
                or not isinstance(spell, dict)
                or not isinstance(delays_raw, list)
            ):
                continue
            delays = tuple(sorted(set(int(value) for value in delays_raw)))
            nominal = int(row["control_delay_frames"])
            if nominal not in delays:
                nominal = min(
                    delays,
                    key=lambda value: abs(value - nominal),
                )
            roots.append(
                Root(
                    decision_frame=int(row["frame"]),
                    query_frame=int(viability["query_frame"]),
                    source_frame=int(corridor["source_frame"]),
                    capsule=capsule,
                    spell_id=int(spell["spell_id"]),
                    x=float(player["projected_x"]),
                    y=float(player["projected_y"]),
                    observed_action=str(
                        viability["observed_input_action"]
                    ),
                    pending=_pending(corridor.get("pending_command")),
                    delay_frames=delays,
                    nominal_delay=nominal,
                    trace_state_viable=bool(
                        viability["state_viable"]
                    ),
                    issued_action=str(row["action"]),
                )
            )
    return roots, hit_frames


def _select_roots(
    roots: list[Root],
    hit_frames: list[int],
    *,
    limit: int,
    pre_hit_lead: int,
    horizon: int,
) -> tuple[tuple[Root, int | None], ...]:
    eligible = [
        root
        for root in roots
        if 0 <= root.query_frame - root.source_frame
        and root.query_frame - root.source_frame + horizon <= BASE.horizon_frames
    ]
    selected: list[tuple[Root, int | None]] = []
    keys: set[tuple[object, ...]] = set()

    def key(root: Root) -> tuple[object, ...]:
        return (
            root.capsule,
            root.query_frame,
            root.x,
            root.y,
            root.observed_action,
            root.pending,
        )

    def add(root: Root, hit_frame: int | None) -> None:
        identity = key(root)
        if len(selected) < limit and identity not in keys:
            selected.append((root, hit_frame))
            keys.add(identity)

    for hit_frame in hit_frames:
        candidates = [
            root
            for root in eligible
            if 0
            < hit_frame - root.query_frame
            <= max(horizon, 2 * pre_hit_lead)
        ]
        if candidates:
            add(
                min(
                    candidates,
                    key=lambda root: (
                        abs(
                            hit_frame
                            - root.query_frame
                            - pre_hit_lead
                        ),
                        -root.query_frame,
                    ),
                ),
                hit_frame,
            )

    remainder = [root for root in eligible if key(root) not in keys]
    if remainder and len(selected) < limit:
        count = min(limit - len(selected), len(remainder))
        indices = np.rint(
            np.linspace(0, len(remainder) - 1, count)
        ).astype(np.int64)
        for index in indices:
            add(remainder[int(index)], None)
    return tuple(selected)


def _audit_root(
    root: Root,
    *,
    capsule_dir: Path,
    horizon: int,
    cadence: tuple[int, ...],
    lower_timeout_ms: int,
    certificate_timeout_ms: int,
    hit_frame: int | None,
) -> dict[str, object]:
    capsule = read_viability_audit_capsule(capsule_dir / root.capsule)
    start = root.query_frame - root.source_frame
    corridor_config = _variant_config(BASE)
    clearance_started = time.perf_counter()
    x_axis, y_axis, source_clearance = _clearance(
        capsule,
        corridor_config,
        variant=BASE,
    )
    clearance = np.ascontiguousarray(
        source_clearance[start : start + horizon + 1],
        dtype=np.float32,
    )
    clearance_ms = (time.perf_counter() - clearance_started) * 1000.0
    row = int(np.argmin(np.abs(y_axis - root.y)))
    column = int(np.argmin(np.abs(x_axis - root.x)))
    position_error = float(
        np.hypot(
            float(x_axis[column]) - root.x,
            float(y_axis[row]) - root.y,
        )
    )
    problem = SurvivalQueryProblem(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance,
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=root.delay_frames,
        nominal_delay=root.nominal_delay,
        config=ViabilityConfig(
            frames_per_layer=BASE.frames_per_layer,
            required_clearance=corridor_config.required_clearance,
            clamp_to_bounds=True,
            repair_radius_cells=1,
        ),
    )
    query = {
        "frame": 0,
        "row": row,
        "column": column,
        "observed_action": root.observed_action,
        "pending_command": root.pending,
    }
    version = (
        root.capsule,
        root.query_frame,
        root.x,
        root.y,
        root.observed_action,
        root.pending,
        root.delay_frames,
        horizon,
        cadence,
    )
    try:
        with problem.build_belief_pipeline_workspace(
            policy_version=("lower", version),
            decision_frame_support=cadence,
            continuation_actions=tuple(
                action.name for action in TH08_VIABILITY_ACTIONS[:9]
            ),
        ) as lower_workspace:
            started = time.perf_counter()
            lower = lower_workspace.query_cell(
                policy_version=("lower", version),
                timeout_ms=lower_timeout_ms,
                **query,
            )
            lower_ms = (time.perf_counter() - started) * 1000.0
        with problem.build_belief_pipeline_workspace(
            policy_version=("upper", version),
            decision_frame_support=cadence,
            reveal_remaining_delay=True,
        ) as upper_workspace:
            started = time.perf_counter()
            certificate = upper_workspace.certify_upper_bound(
                policy_version=("upper", version),
                lower_bound=lower.state_label,
                timeout_ms=certificate_timeout_ms,
                **query,
            )
            certificate_ms = (time.perf_counter() - started) * 1000.0
    except PipelineWorkspaceDeadlineError:
        return {
            "status": "timeout",
            "decision_frame": root.decision_frame,
            "query_frame": root.query_frame,
            "source_frame": root.source_frame,
            "hit_frame": hit_frame,
            "frames_to_hit": (
                hit_frame - root.query_frame
                if hit_frame is not None
                else None
            ),
            "spell_id": root.spell_id,
            "capsule": root.capsule,
            "clearance_ms": clearance_ms,
            "position_error": position_error,
        }
    return {
        "status": "completed",
        "decision_frame": root.decision_frame,
        "query_frame": root.query_frame,
        "source_frame": root.source_frame,
        "hit_frame": hit_frame,
        "frames_to_hit": (
            hit_frame - root.query_frame
            if hit_frame is not None
            else None
        ),
        "spell_id": root.spell_id,
        "capsule": root.capsule,
        "trace_state_viable": root.trace_state_viable,
        "issued_action": root.issued_action,
        "position": [root.x, root.y],
        "position_error": position_error,
        "observed_action": root.observed_action,
        "pending_command": (
            {
                "action": root.pending.action,
                "remaining_frames": list(
                    root.pending.remaining_frames
                ),
            }
            if root.pending is not None
            else None
        ),
        "delay_frames": list(root.delay_frames),
        "clearance_ms": clearance_ms,
        "lower_ms": lower_ms,
        "certificate_ms": certificate_ms,
        "total_bound_ms": lower_ms + certificate_ms,
        "lower_label": {
            "frames": lower.state_label.guaranteed_frames,
            "margin": lower.state_label.bottleneck_margin,
        },
        "lower_best_actions": list(lower.best_actions),
        "certified": certificate.certified,
        "certificate_deadline_expired": (
            certificate.deadline_expired
        ),
        "unresolved_actions": list(
            certificate.unresolved_actions
        ),
        "certificate_stats": {
            field: int(value)
            for field, value in vars(
                certificate.workspace_stats
            ).items()
        },
    }


def audit(
    *,
    trace: Path,
    capsule_dir: Path,
    query_limit: int,
    pre_hit_lead: int,
    horizon: int,
    cadence: tuple[int, ...],
    lower_timeout_ms: int,
    certificate_timeout_ms: int,
) -> dict[str, object]:
    roots, hit_frames = _read_roots(trace)
    selected = _select_roots(
        roots,
        hit_frames,
        limit=query_limit,
        pre_hit_lead=pre_hit_lead,
        horizon=horizon,
    )
    observations = []
    for index, (root, hit_frame) in enumerate(selected, 1):
        print(
            f"[{index}/{len(selected)}] belief certificate "
            f"frame {root.query_frame}",
            flush=True,
        )
        observations.append(
            _audit_root(
                root,
                capsule_dir=capsule_dir,
                horizon=horizon,
                cadence=cadence,
                lower_timeout_ms=lower_timeout_ms,
                certificate_timeout_ms=certificate_timeout_ms,
                hit_frame=hit_frame,
            )
        )
    completed = [
        item for item in observations if item["status"] == "completed"
    ]
    certificate_times = [
        float(item["certificate_ms"]) for item in completed
    ]
    lower_times = [float(item["lower_ms"]) for item in completed]
    total_times = [
        float(item["total_bound_ms"]) for item in completed
    ]
    certified = [item for item in completed if item["certified"]]
    unresolved_counts = [
        len(item["unresolved_actions"]) for item in completed
    ]
    pre_hit = [
        item for item in completed if item["hit_frame"] is not None
    ]
    return {
        "schema": "th08-belief-upper-certification-audit-v1",
        "scope": {
            "trace": str(trace),
            "capsule_dir": str(capsule_dir),
            "available_root_count": len(roots),
            "native_hit_count": len(hit_frames),
            "selected_root_count": len(selected),
            "query_limit": query_limit,
            "pre_hit_lead": pre_hit_lead,
            "horizon": horizon,
            "decision_frame_support": list(cadence),
            "lower_timeout_ms": lower_timeout_ms,
            "certificate_timeout_ms": certificate_timeout_ms,
            "lower_policy": (
                "all 17 root actions; nine slow continuation actions; B=0"
            ),
            "upper_policy": (
                "all 17 unrestricted actions with revealed remaining delay"
            ),
            "authority": "offline/shadow only",
        },
        "summary": {
            "completed_count": len(completed),
            "timeout_count": len(observations) - len(completed),
            "certified_count": len(certified),
            "certification_rate": (
                len(certified) / len(completed) if completed else None
            ),
            "certificate_deadline_count": sum(
                bool(item["certificate_deadline_expired"])
                for item in completed
            ),
            "pre_hit_completed_count": len(pre_hit),
            "pre_hit_certified_count": sum(
                bool(item["certified"]) for item in pre_hit
            ),
            "unresolved_action_count": _summary(
                [float(value) for value in unresolved_counts]
            ),
            "timing_ms": {
                "lower": _summary(lower_times),
                "certificate": _summary(certificate_times),
                "lower_plus_certificate": _summary(total_times),
            },
        },
        "observations": observations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("capsules", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--query-limit", type=int, default=32)
    parser.add_argument(
        "--pre-hit-lead",
        type=int,
        default=30,
        help=(
            "select the available root closest to this many frames before "
            "each hit"
        ),
    )
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument(
        "--cadence",
        type=int,
        nargs="+",
        default=(4, 5, 6),
    )
    parser.add_argument("--lower-timeout-ms", type=int, default=3000)
    parser.add_argument(
        "--certificate-timeout-ms",
        type=int,
        default=100,
    )
    args = parser.parse_args(argv)
    if min(
        args.query_limit,
        args.pre_hit_lead,
        args.horizon,
        args.lower_timeout_ms,
        args.certificate_timeout_ms,
        *args.cadence,
    ) <= 0:
        parser.error("limits, horizon, cadence, and timeout must be positive")
    cadence = tuple(sorted(set(args.cadence)))
    report = audit(
        trace=args.trace,
        capsule_dir=args.capsules,
        query_limit=args.query_limit,
        pre_hit_lead=args.pre_hit_lead,
        horizon=args.horizon,
        cadence=cadence,
        lower_timeout_ms=args.lower_timeout_ms,
        certificate_timeout_ms=args.certificate_timeout_ms,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
