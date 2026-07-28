#!/usr/bin/env python3
"""Shared validation and summaries for retained TH08 ECL traces."""

from __future__ import annotations

import statistics


COMPLETE_REASONS = frozenset(("horizon", "terminate"))
LEGACY_INCOMPLETE_REASONS = frozenset(
    ("instruction_limit", "repeated_state")
)


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(
        len(ordered) - 1,
        max(0, int(round((len(ordered) - 1) * fraction))),
    )
    return ordered[index]


def compact_summary(
    values: list[float],
) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "median": None,
            "p95": None,
            "max": None,
        }
    return {
        "count": len(values),
        "median": statistics.median(values),
        "p95": percentile(values, 0.95),
        "max": max(values),
    }


def timing_summary(
    values: list[float],
) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "p50": None,
            "p95": None,
            "p99": None,
            "p99_9": None,
            "max": None,
        }
    return {
        "count": len(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "p99_9": percentile(values, 0.999),
        "max": max(values),
    }


def spell_key(decision: dict[str, object]) -> str:
    spell = decision.get("spell")
    if not isinstance(spell, dict) or not spell.get("active"):
        return "nonspell"
    return str(spell.get("spell_id"))


def lookahead_metadata_errors(lookahead: dict[str, object]) -> list[str]:
    errors: list[str] = []
    status = lookahead.get("coverage_status")
    reason = lookahead.get("stop_reason")
    covered = lookahead.get("horizon_covered")
    horizon = lookahead.get("requested_horizon_frames")
    covered_through = lookahead.get("covered_through_frame")
    unknown_from = lookahead.get("unknown_from_frame")
    result_kind = lookahead.get("result_kind")
    lowering = lookahead.get("lowering_status")
    lowered_events = lookahead.get("events")
    prefix_events = lookahead.get("prefix_events")
    instructions = lookahead.get("instructions_scanned")

    if not isinstance(instructions, int) or not 0 < instructions <= 256:
        errors.append("invalid_instruction_count")
    if not isinstance(prefix_events, list) or not isinstance(
        lowered_events,
        list,
    ):
        errors.append("missing_event_lists")
    if status == "complete":
        if (
            reason not in COMPLETE_REASONS
            or covered is not True
            or covered_through != horizon
            or unknown_from is not None
            or result_kind != "complete_schedule"
            or lowering != "complete_schedule_lowered"
        ):
            errors.append("inconsistent_complete_metadata")
    elif status == "unknown":
        if (
            reason in COMPLETE_REASONS
            or covered is not False
            or not isinstance(covered_through, int)
            or not isinstance(unknown_from, int)
            or (
                isinstance(covered_through, int)
                and isinstance(unknown_from, int)
                and unknown_from != covered_through + 1
            )
            or result_kind != "prefix_only"
            or lowering != "incomplete_prefix_not_lowered"
            or lowered_events != []
        ):
            errors.append("inconsistent_unknown_metadata")
    else:
        errors.append("invalid_coverage_status")
    return errors


__all__ = [
    "COMPLETE_REASONS",
    "LEGACY_INCOMPLETE_REASONS",
    "compact_summary",
    "lookahead_metadata_errors",
    "percentile",
    "spell_key",
    "timing_summary",
]
