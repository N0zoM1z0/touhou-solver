#!/usr/bin/env python3
"""Replay physical decision roots through bounded prewarm scheduling."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

import numpy as np

from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_PLAYFIELD,
    TH08_VIABILITY_ACTIONS,
)
from th08_live_dodge_agent import _action_name_from_mask
from touhou_control.pipeline_root_schedule import (
    schedule_pipeline_frontier,
)
from touhou_control.query_survival import (
    PendingCommand,
    ReachablePipelineRoot,
    SurvivalQueryProblem,
    enumerate_next_decision_roots,
)
from touhou_control.viability import ViabilityConfig


SCHEDULING_FRAMES = (2, 3, 4, 5, 6, 7, 8, 9)
LEGACY_SCHEDULING_FRAMES = (4, 5, 6)


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


def _pending(raw: object) -> PendingCommand | None:
    if not isinstance(raw, dict):
        return None
    action = raw.get("desired_action")
    remaining = raw.get("remaining_frames")
    if (
        not isinstance(action, str)
        or not isinstance(remaining, list)
        or not remaining
    ):
        return None
    return PendingCommand(
        action,
        tuple(int(value) for value in remaining),
    )


def _problem(delay_frames: tuple[int, ...]) -> SurvivalQueryProblem:
    x_axis = np.linspace(
        TH08_PLAYFIELD.left,
        TH08_PLAYFIELD.right,
        int(
            round(
                (TH08_PLAYFIELD.right - TH08_PLAYFIELD.left)
                / TH08_CORRIDOR_CONFIG.grid_step
            )
        )
        + 1,
        dtype=np.float32,
    )
    y_axis = np.linspace(
        TH08_PLAYFIELD.top,
        TH08_PLAYFIELD.bottom,
        int(
            round(
                (TH08_PLAYFIELD.bottom - TH08_PLAYFIELD.top)
                / TH08_CORRIDOR_CONFIG.grid_step
            )
        )
        + 1,
        dtype=np.float32,
    )
    return SurvivalQueryProblem(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=np.zeros(
            (
                TH08_CORRIDOR_CONFIG.horizon_frames + 1,
                len(y_axis),
                len(x_axis),
            ),
            dtype=np.float32,
        ),
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=delay_frames,
        nominal_delay=delay_frames[len(delay_frames) // 2],
        config=ViabilityConfig(
            frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
            required_clearance=TH08_CORRIDOR_CONFIG.required_clearance,
            clamp_to_bounds=True,
            repair_radius_cells=1,
        ),
    )


def _trace_rows(path: Path) -> list[dict[str, object]]:
    rows = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("kind") != "decision":
                continue
            corridor = row.get("corridor")
            if not isinstance(corridor, dict):
                continue
            viability = corridor.get("viability")
            player = row.get("player")
            if (
                not isinstance(viability, dict)
                or not viability.get("available")
                or not isinstance(player, dict)
            ):
                continue
            rows.append(row)
    return rows


def replay(path: Path, *, root_limit: int) -> dict[str, object]:
    rows = _trace_rows(path)
    problems: dict[tuple[int, ...], SurvivalQueryProblem] = {}
    counts: Counter[str] = Counter()
    candidate_counts: list[float] = []
    scheduled_counts: list[float] = []
    observed_deltas: list[float] = []
    issue_offsets: list[float] = []
    preferred_frames: list[float] = []
    prediction_errors: list[float] = []
    observed_by_preferred: dict[int, Counter[int]] = {}

    def root_for(
        row: dict[str, object],
        problem: SurvivalQueryProblem,
    ) -> ReachablePipelineRoot:
        corridor = row["corridor"]
        viability = corridor["viability"]
        player = row["player"]
        row_index, column, _ = problem.project_to_lattice(
            x=float(player["projected_x"]),
            y=float(player["projected_y"]),
        )
        return ReachablePipelineRoot(
            frame=int(viability["age"]),
            row=row_index,
            column=column,
            observed_action=str(viability["observed_input_action"]),
            pending_command=_pending(corridor.get("pending_command")),
        )

    for current, following in zip(rows, rows[1:]):
        current_corridor = current["corridor"]
        following_corridor = following["corridor"]
        if (
            current_corridor.get("source_frame")
            != following_corridor.get("source_frame")
        ):
            continue
        delay_frames = tuple(
            int(value)
            for value in current_corridor["viability"]["delay_frames"]
        )
        problem = problems.get(delay_frames)
        if problem is None:
            problem = _problem(delay_frames)
            problems[delay_frames] = problem
        root = root_for(current, problem)
        observed = root_for(following, problem)
        if observed.frame <= root.frame:
            continue
        issue_offset = int(
            current["deadline_guard"]["post_capture_advance"]
        )
        previous_iteration = current["timing_ms"].get(
            "previous_iteration"
        )
        preferred_frame = max(
            2,
            min(
                9,
                round(
                    (
                        float(previous_iteration)
                        if isinstance(previous_iteration, (int, float))
                        else 50.0
                    )
                    / (1000.0 / 60.0)
                )
                + 1,
            ),
        )
        schedule = schedule_pipeline_frontier(
            problem=problem,
            root=root,
            selected_action=_action_name_from_mask(int(current["mask"])),
            physical_x=float(current["player"]["projected_x"]),
            physical_y=float(current["player"]["projected_y"]),
            command_issue_offset=issue_offset,
            preferred_decision_frame=preferred_frame,
            scheduling_frame_support=SCHEDULING_FRAMES,
            root_limit=root_limit,
        )
        legacy = enumerate_next_decision_roots(
            x_axis=problem.x_axis,
            y_axis=problem.y_axis,
            actions=problem.actions,
            delay_frames=problem.delay_frames,
            decision_frame_support=LEGACY_SCHEDULING_FRAMES,
            config=problem.config,
            start_frame=root.frame,
            horizon_frame=problem.horizon_frames,
            row=root.row,
            column=root.column,
            observed_action=root.observed_action,
            selected_action=_action_name_from_mask(int(current["mask"])),
            pending_command=root.pending_command,
        )
        counts["pairs"] += 1
        counts["legacy_frontier_hits"] += int(observed in legacy)
        counts["physical_frontier_hits"] += int(
            observed in schedule.candidates
        )
        for index in range(root_limit):
            counts[f"top_{index + 1}_hits"] += int(
                observed in schedule.roots[: index + 1]
            )
        candidate_counts.append(float(schedule.candidate_count))
        scheduled_counts.append(float(len(schedule.roots)))
        observed_deltas.append(float(observed.frame - root.frame))
        issue_offsets.append(float(issue_offset))
        actual_delta = observed.frame - root.frame
        preferred_frames.append(float(preferred_frame))
        prediction_errors.append(float(actual_delta - preferred_frame))
        observed_by_preferred.setdefault(
            preferred_frame,
            Counter(),
        )[actual_delta] += 1

    pair_count = counts["pairs"]
    return {
        "schema": "pipeline-prewarm-schedule-replay-v2",
        "scope": {
            "trace": str(path),
            "semantics": (
                "Counterfactual kinematic scheduling only. No survival label "
                "or collision claim is replayed. Top-K uses the current "
                "physical subcell position, read-to-issue offset, previous "
                "iteration cadence prediction, and one-frame nominal pickup."
            ),
            "scheduling_frame_support": SCHEDULING_FRAMES,
            "legacy_scheduling_frame_support": (
                LEGACY_SCHEDULING_FRAMES
            ),
            "root_limit": root_limit,
        },
        "pair_count": pair_count,
        "coverage": {
            "legacy_frontier": (
                counts["legacy_frontier_hits"] / pair_count
                if pair_count
                else None
            ),
            "physical_frontier": (
                counts["physical_frontier_hits"] / pair_count
                if pair_count
                else None
            ),
            **{
                f"top_{index + 1}": (
                    counts[f"top_{index + 1}_hits"] / pair_count
                    if pair_count
                    else None
                )
                for index in range(root_limit)
            },
        },
        "timing_context_frames": {
            "observed_decision_delta": _summary(observed_deltas),
            "read_to_issue_offset": _summary(issue_offsets),
            "predicted_decision_delta": _summary(preferred_frames),
            "prediction_error_actual_minus_predicted": _summary(
                prediction_errors
            ),
            "prediction_coverage": {
                "exact": (
                    sum(error == 0 for error in prediction_errors)
                    / pair_count
                    if pair_count
                    else None
                ),
                "within_1": (
                    sum(abs(error) <= 1 for error in prediction_errors)
                    / pair_count
                    if pair_count
                    else None
                ),
                "within_2": (
                    sum(abs(error) <= 2 for error in prediction_errors)
                    / pair_count
                    if pair_count
                    else None
                ),
            },
            "observed_support_by_prediction": {
                str(preferred): {
                    str(observed): count
                    for observed, count in sorted(counter.items())
                }
                for preferred, counter in sorted(
                    observed_by_preferred.items()
                )
            },
        },
        "root_counts": {
            "candidate": _summary(candidate_counts),
            "scheduled": _summary(scheduled_counts),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--root-limit", type=int, default=2)
    args = parser.parse_args(argv)
    if args.root_limit <= 0:
        raise ValueError("root limit must be positive")
    report = replay(args.trace, root_limit=args.root_limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
