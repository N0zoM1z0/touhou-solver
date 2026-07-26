#!/usr/bin/env python3
"""Replay observed opposed writes with held and selected first actions."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from analysis.local_beam_stability_audit import (
    _decision,
    _decision_record,
    _even_sample,
    _hard_vector,
    _timing,
)
from analysis.local_control_stability_audit import horizontal_sign
from analysis.local_pipeline_certificate_audit import (
    ReconstructedRoot,
    _read_decisions,
    _reconstruct_roots,
)


def _eligible_switch(
    root: ReconstructedRoot,
) -> tuple[str, str] | None:
    row = root.row
    root_record = row.get("local_pipeline_root")
    shadow = row.get("local_pipeline_certificate_shadow")
    if (
        not isinstance(root_record, dict)
        or not isinstance(shadow, dict)
        or shadow.get("status") != "complete"
    ):
        return None
    held_mask = int(root_record.get("held_desired_mask", 0))
    selected_mask = int(row.get("mask", 0))
    held_sign = horizontal_sign(held_mask)
    selected_sign = horizontal_sign(selected_mask)
    if held_sign == 0 or selected_sign != -held_sign:
        return None
    held_action = str(root_record.get("held_desired_action", ""))
    selected_action = str(row.get("action", "")).split("+", 1)[0]
    certificate_actions = {
        str(certificate.get("action"))
        for certificate in shadow.get("certificates", ())
        if isinstance(certificate, dict)
    }
    if (
        not held_action
        or not selected_action
        or held_action not in certificate_actions
        or selected_action not in certificate_actions
    ):
        return None
    return held_action, selected_action


def _soft_vector(decision) -> tuple[float, float, float]:
    return (
        decision.robust_cvar_risk,
        -decision.robust_min_clearance,
        decision.score,
    )


def _relation(left, right) -> str:
    left_hard = _hard_vector(left)
    right_hard = _hard_vector(right)
    if left_hard < right_hard:
        return "held_hard_better"
    if left_hard > right_hard:
        return "held_hard_worse"
    left_soft = _soft_vector(left)
    right_soft = _soft_vector(right)
    if left_soft < right_soft:
        return "hard_equal_held_soft_better"
    if left_soft > right_soft:
        return "hard_equal_held_soft_worse"
    return "hard_and_soft_equal"


def _certificate_for(
    row: dict[str, object],
    action: str,
) -> dict[str, object] | None:
    shadow = row.get("local_pipeline_certificate_shadow")
    if not isinstance(shadow, dict):
        return None
    return next(
        (
            certificate
            for certificate in shadow.get("certificates", ())
            if (
                isinstance(certificate, dict)
                and certificate.get("action") == action
            )
        ),
        None,
    )


def _globally_allowed(
    row: dict[str, object],
    action: str,
) -> bool | None:
    guidance = row.get("planner_guidance")
    if not isinstance(guidance, dict):
        return None
    allowed = guidance.get("allowed_first_actions")
    if allowed is None:
        return True
    if not isinstance(allowed, (list, tuple)):
        return False
    return action in allowed


def audit_trace(
    trace: Path,
    *,
    maximum_roots: int,
    beam_width: int,
    wide_beam: int,
) -> dict[str, object]:
    rows, digest = _read_decisions(trace)
    roots, population = _reconstruct_roots(rows)
    eligible = [
        root for root in roots if _eligible_switch(root) is not None
    ]
    sampled = _even_sample(eligible, maximum_roots)
    relation_counts = {
        width: {
            name: 0
            for name in (
                "held_hard_better",
                "held_hard_worse",
                "hard_equal_held_soft_better",
                "hard_equal_held_soft_worse",
                "hard_and_soft_equal",
            )
        }
        for width in ("nominal", "wide")
    }
    baseline_matches_recorded = 0
    both_globally_allowed = 0
    relation_agreement = 0
    held_hard_nonworse_both_widths = 0
    held_hard_equal_both_widths = 0
    nominal_timing: list[float] = []
    wide_timing: list[float] = []
    examples: list[dict[str, object]] = []

    for root in sampled:
        eligible_actions = _eligible_switch(root)
        assert eligible_actions is not None
        held_action, selected_action = eligible_actions

        baseline = _decision(
            root,
            beam_dedup_mode="quantized",
            beam_width=beam_width,
        )
        baseline_matches_recorded += int(
            baseline.action == selected_action
        )

        started = time.perf_counter()
        nominal_held = _decision(
            root,
            beam_dedup_mode="exact_first_action",
            beam_width=beam_width,
            forced_first_action=held_action,
        )
        nominal_selected = _decision(
            root,
            beam_dedup_mode="exact_first_action",
            beam_width=beam_width,
            forced_first_action=selected_action,
        )
        nominal_timing.append((time.perf_counter() - started) * 1000.0)

        started = time.perf_counter()
        wide_held = _decision(
            root,
            beam_dedup_mode="exact_first_action",
            beam_width=wide_beam,
            forced_first_action=held_action,
        )
        wide_selected = _decision(
            root,
            beam_dedup_mode="exact_first_action",
            beam_width=wide_beam,
            forced_first_action=selected_action,
        )
        wide_timing.append((time.perf_counter() - started) * 1000.0)

        nominal_relation = _relation(nominal_held, nominal_selected)
        wide_relation = _relation(wide_held, wide_selected)
        relation_counts["nominal"][nominal_relation] += 1
        relation_counts["wide"][wide_relation] += 1
        relation_agreement += int(nominal_relation == wide_relation)
        nominal_hard = _hard_vector(nominal_held)
        nominal_selected_hard = _hard_vector(nominal_selected)
        wide_hard = _hard_vector(wide_held)
        wide_selected_hard = _hard_vector(wide_selected)
        held_hard_nonworse_both_widths += int(
            nominal_hard <= nominal_selected_hard
            and wide_hard <= wide_selected_hard
        )
        held_hard_equal_both_widths += int(
            nominal_hard == nominal_selected_hard
            and wide_hard == wide_selected_hard
        )
        held_allowed = _globally_allowed(root.row, held_action)
        selected_allowed = _globally_allowed(root.row, selected_action)
        both_globally_allowed += int(
            held_allowed is True and selected_allowed is True
        )

        if len(examples) < 20:
            examples.append(
                {
                    "frame": int(root.row["frame"]),
                    "prehit_240f": root.prehit,
                    "held_action": held_action,
                    "selected_action": selected_action,
                    "held_globally_allowed": held_allowed,
                    "selected_globally_allowed": selected_allowed,
                    "baseline_replay_action": baseline.action,
                    "short_certificate": {
                        "held": _certificate_for(
                            root.row,
                            held_action,
                        ),
                        "selected": _certificate_for(
                            root.row,
                            selected_action,
                        ),
                    },
                    "nominal": {
                        "relation": nominal_relation,
                        "held": _decision_record(nominal_held),
                        "selected": _decision_record(nominal_selected),
                    },
                    "wide": {
                        "relation": wide_relation,
                        "held": _decision_record(wide_held),
                        "selected": _decision_record(wide_selected),
                    },
                }
            )

    return {
        "trace": str(trace),
        "trace_sha256": digest,
        "population": population,
        "selection": {
            "eligible_opposed_explicit_root_writes": len(eligible),
            "sample_count": len(sampled),
            "maximum_roots": maximum_roots,
            "nominal_beam_width": beam_width,
            "wide_beam_width": wide_beam,
        },
        "results": {
            "baseline_replay_matches_recorded_action": (
                baseline_matches_recorded
            ),
            "both_actions_globally_allowed": both_globally_allowed,
            "relation_counts": relation_counts,
            "nominal_wide_relation_agreement": relation_agreement,
            "held_hard_nonworse_both_widths": (
                held_hard_nonworse_both_widths
            ),
            "held_hard_equal_both_widths": held_hard_equal_both_widths,
        },
        "timing": {
            "nominal_forced_pair": (
                _timing(nominal_timing) if nominal_timing else None
            ),
            "wide_forced_pair": (
                _timing(wide_timing) if wide_timing else None
            ),
        },
        "examples": examples,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--maximum-roots", type=int, default=64)
    parser.add_argument("--beam-width", type=int, default=24)
    parser.add_argument("--wide-beam", type=int, default=256)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if min(args.maximum_roots, args.beam_width, args.wide_beam) <= 0:
        raise ValueError("root and beam limits must be positive")
    report = {
        "schema": "th08-local-hysteresis-replay-audit-v1",
        "claim_boundary": {
            "source": (
                "observed opposed writes with direct explicit pipeline roots "
                "and post-issue exact short certificates"
            ),
            "comparison": (
                "independent forced-held and forced-selected continuation "
                "beams at the recorded immutable root"
            ),
            "approximation": (
                "beam continuation is proposal-only and has unknown-direction "
                "error; agreement across widths is sensitivity evidence, not "
                "an exact recurrence certificate"
            ),
            "authority": (
                "offline stability diagnosis only; no hysteresis action "
                "authority"
            ),
        },
        "traces": [
            audit_trace(
                trace,
                maximum_roots=args.maximum_roots,
                beam_width=args.beam_width,
                wide_beam=args.wide_beam,
            )
            for trace in args.traces
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
