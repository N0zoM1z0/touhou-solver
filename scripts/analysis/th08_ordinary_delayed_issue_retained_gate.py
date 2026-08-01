#!/usr/bin/env python3
"""Regress delayed-issue causal authority on retained ordinary roots."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from analysis.th08_ordinary_future_source_retained_gate import (  # noqa: E402
    DECISION_FRAMES,
    ECL_PATH,
    FUTURE_SOURCE_HORIZON_FRAMES,
    OBSERVATION_FRAMES,
    PICKUP_DELAY_FRAMES,
    _load_trace_rows,
    _native_payload,
)
from th08_ecl_tool.core import parse_ecl  # noqa: E402
from th08_live.controller import (  # noqa: E402
    _contiguous_integer_ranges,
    _delayed_issue_action_certificates,
    _ordinary_terminal_probe_actions,
)
from th08_live.enemy_sensor import enemy_body_contact_enabled  # noqa: E402
from th08_live.models import EnemyBody  # noqa: E402
from th08_ordinary_future_sources import (  # noqa: E402
    project_ordinary_future_sources,
)
from th08_time_scale import (  # noqa: E402
    TH08_UNIT_TIME_SCALE_BITS,
    Th08TimeScaleSchedule,
)
from th08_trace_replay import (  # noqa: E402
    bullet_from_trace,
    laser_from_trace,
    local_pipeline_root_from_trace,
)
from touhou_control.local_pipeline_oracle import (  # noqa: E402
    enumerate_delayed_issue_pipeline_branches,
)


HORIZON_FRAMES = 80
# Retained physical rows have issue age 0/1.  Keep the deterministic chain's
# compact low-age slab independent from the live 24..48 latency slab.
ISSUE_DELAY_FRAMES = tuple(range(25))
REPORT = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_ordinary_delayed_issue_retained_gate_20260801.json"
)


def _point(
    decision_frame: int,
    observation_frame: int,
    trace_row: dict[str, object],
    ecl: object,
) -> dict[str, object]:
    _, _, payload = _native_payload(observation_frame)
    compact = payload["compact_state"]
    root, held_mask, actual_issue_age, _ = local_pipeline_root_from_trace(
        trace_row
    )
    closure = project_ordinary_future_sources(
        payload,
        ecl,
        horizon_frames=FUTURE_SOURCE_HORIZON_FRAMES,
    )
    bullets = tuple(
        bullet_from_trace(values) for values in payload["bullets"]
    )
    lasers = tuple(
        laser_from_trace(values) for values in payload["lasers"]
    )
    hostile_bodies = tuple(
        body
        for body in (
            EnemyBody(**values) for values in payload["enemy_bodies"]
        )
        if enemy_body_contact_enabled(body)
    )
    scale = Th08TimeScaleSchedule.constant(
        TH08_UNIT_TIME_SCALE_BITS,
        horizon=FUTURE_SOURCE_HORIZON_FRAMES,
        provenance="retained_delayed_issue_unit_scale",
        source_frame=observation_frame,
    )
    actions = _ordinary_terminal_probe_actions(
        held_action=root.held_desired_action,
        recovery_distances=(),
    )
    started = time.perf_counter()
    certificates, projections = _delayed_issue_action_certificates(
        root=root,
        actions=actions,
        issue_delay_frames=ISSUE_DELAY_FRAMES,
        pickup_delay_frames=PICKUP_DELAY_FRAMES,
        horizon_frames=HORIZON_FRAMES,
        player_x=float(compact["player_x"]),
        player_y=float(compact["player_y"]),
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=hostile_bodies,
        snapshot_lag=0,
        player_scale_bits=scale.player_scale_bits[:HORIZON_FRAMES],
        laser_scale_bits=scale.laser_scale_bits[:HORIZON_FRAMES],
        future_hazard_projection=closure.projection,
        source_frame=observation_frame,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    safe_ranges = {
        action.name: _contiguous_integer_ranges(
            tuple(
                issue_delay
                for issue_delay, row in certificates.items()
                if (
                    action.name in row
                    and row[action.name].worst_collisions == 0
                    and row[action.name].min_clearance > 0.0
                )
            )
        )
        for action in actions
    }
    actual_row = certificates.get(actual_issue_age, {})
    actual_safe = tuple(
        action.name
        for action in actions
        if (
            action.name in actual_row
            and actual_row[action.name].worst_collisions == 0
            and actual_row[action.name].min_clearance > 0.0
        )
    )
    pending_count = max(1, len(root.remaining_delay_support))
    branch_contract = all(
        len(
            enumerate_delayed_issue_pipeline_branches(
                root=root,
                selected_action=action.name,
                issue_delay_frames=(issue_delay,),
                pickup_delay_frames=PICKUP_DELAY_FRAMES,
                horizon_frames=HORIZON_FRAMES,
            )
        )
        == (
            pending_count
            * (
                1
                if action.name == root.held_desired_action
                else len(PICKUP_DELAY_FRAMES)
            )
        )
        for issue_delay in ISSUE_DELAY_FRAMES
        for action in actions
    )
    return {
        "decision_frame": decision_frame,
        "observation_frame": observation_frame,
        "pipeline_root": {
            "active_action": root.active_action,
            "held_desired_action": root.held_desired_action,
            "pending_action": root.pending_action,
            "remaining_delay_support": root.remaining_delay_support,
        },
        "actual_issue_age": actual_issue_age,
        "actions": tuple(action.name for action in actions),
        "safe_issue_age_ranges": safe_ranges,
        "actual_issue_safe_actions": actual_safe,
        "branch_contract_exact": branch_contract,
        "row_count": len(certificates),
        "conditioned_projection_count": len(projections),
        "source_closure_complete": closure.projection.source_closure_complete,
        "coverage_complete": closure.projection.coverage.complete,
        "elapsed_ms": elapsed_ms,
    }


def build_report() -> dict[str, object]:
    rows = _load_trace_rows()
    ecl = parse_ecl(ECL_PATH)
    points = [
        _point(
            decision_frame,
            observation_frame,
            rows[decision_frame],
            ecl,
        )
        for decision_frame, observation_frame in zip(
            DECISION_FRAMES, OBSERVATION_FRAMES
        )
    ]
    checks = {
        "complete_future_coverage": all(
            point["source_closure_complete"]
            and point["coverage_complete"]
            for point in points
        ),
        "complete_issue_delay_table": all(
            point["row_count"] == len(ISSUE_DELAY_FRAMES)
            for point in points
        ),
        "held_no_write_and_write_branch_counts_exact": all(
            point["branch_contract_exact"] for point in points
        ),
        "retained_actual_issue_ages_covered": all(
            point["actual_issue_age"] in ISSUE_DELAY_FRAMES
            for point in points
        ),
    }
    return {
        "schema": "th08-ordinary-delayed-issue-retained-gate-v1",
        "scope": "ordinary_nonspell_only",
        "authority": "deterministic_native_replay_regression",
        "contract": {
            "horizon_frames": HORIZON_FRAMES,
            "issue_delay_frames": ISSUE_DELAY_FRAMES,
            "pickup_delay_frames": PICKUP_DELAY_FRAMES,
            "action_selection": (
                "after_issue_age_observation_from_that_exact_table_row"
            ),
            "held_complete_mask": "no_write_preserves_pending",
        },
        "chain": points,
        "checks": checks,
        "hard_gate_passed": all(checks.values()),
    }


def main() -> int:
    report = build_report()
    REPORT.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(REPORT)
    print(json.dumps(report["checks"], indent=2))
    for point in report["chain"]:
        print(
            point["decision_frame"],
            f"{point['elapsed_ms']:.1f}ms",
            point["safe_issue_age_ranges"],
            "actual",
            point["actual_issue_age"],
            point["actual_issue_safe_actions"],
        )
    return 0 if report["hard_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
