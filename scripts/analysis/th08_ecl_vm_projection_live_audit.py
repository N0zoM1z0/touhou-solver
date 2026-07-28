#!/usr/bin/env python3
"""Audit capture-aligned ECL VM-local projections in a live trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from analysis.th08_ecl_trace_support import (
    lookahead_metadata_errors,
    spell_key,
    timing_summary,
)
from th08_ecl_vm_state import (
    ECL_VM_LOCAL_PROJECTION_LAYOUT,
    ECL_VM_LOCAL_PROJECTION_SIZE,
)


SCHEMA = "th08-ecl-vm-projection-live-audit-v1"
WORKLOAD_PROFILE_STAGE4A = "stage4a"
WORKLOAD_PROFILE_CORE = "core"
WORKLOAD_PROFILES = (
    WORKLOAD_PROFILE_STAGE4A,
    WORKLOAD_PROFILE_CORE,
)


def _int_summary(values: list[int]) -> dict[str, object]:
    if not values:
        return {
            "count": 0,
            "min": None,
            "median": None,
            "p95": None,
            "max": None,
            "unique_count": 0,
            "most_common": [],
        }
    ordered = sorted(values)
    p95_index = round((len(ordered) - 1) * 0.95)
    counts = Counter(values)
    return {
        "count": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "p95": ordered[p95_index],
        "max": max(values),
        "unique_count": len(counts),
        "most_common": [
            [value, count] for value, count in counts.most_common(16)
        ],
    }


def _float_bit_class(bits: int) -> str:
    exponent = (bits >> 23) & 0xFF
    mantissa = bits & 0x7FFFFF
    if exponent == 0xFF:
        return "infinity" if mantissa == 0 else "nan"
    if exponent == 0:
        return "zero" if mantissa == 0 else "subnormal"
    return "normal"


def _projection_errors(
    projection: object,
    *,
    tag_mask: object,
) -> list[str]:
    if not isinstance(projection, dict):
        return ["missing_projection"]
    errors: list[str] = []
    if projection.get("layout") != ECL_VM_LOCAL_PROJECTION_LAYOUT:
        errors.append("invalid_layout")
    if projection.get("capture_bytes") != ECL_VM_LOCAL_PROJECTION_SIZE:
        errors.append("invalid_capture_bytes")
    integer_locals = projection.get("integer_locals")
    float_local_bits = projection.get("float_local_bits")
    scratch_integers = projection.get("scratch_integers")
    if (
        not isinstance(integer_locals, list)
        or len(integer_locals) != 8
        or not all(
            type(value) is int and -(1 << 31) <= value < (1 << 31)
            for value in integer_locals
        )
    ):
        errors.append("invalid_integer_locals")
    if (
        not isinstance(float_local_bits, list)
        or len(float_local_bits) != 8
        or not all(
            type(value) is int and 0 <= value <= 0xFFFFFFFF
            for value in float_local_bits
        )
    ):
        errors.append("invalid_float_local_bits")
    if (
        not isinstance(scratch_integers, list)
        or len(scratch_integers) != 4
        or not all(
            type(value) is int and -(1 << 31) <= value < (1 << 31)
            for value in scratch_integers
        )
    ):
        errors.append("invalid_scratch_integers")
    if (
        isinstance(integer_locals, list)
        and len(integer_locals) == 8
        and type(integer_locals[0]) is int
        and type(tag_mask) is int
        and integer_locals[0] & 0xFFFFFFFF != tag_mask
    ):
        errors.append("tag_mask_mismatch")
    return errors


def audit_vm_projection_trace(
    trace_path: Path,
    *,
    workload_profile: str = WORKLOAD_PROFILE_STAGE4A,
) -> dict[str, object]:
    if workload_profile not in WORKLOAD_PROFILES:
        raise ValueError(
            f"unknown ECL projection workload profile {workload_profile!r}"
        )
    trace_digest = hashlib.sha256()
    decision_rows = 0
    callback_rows = 0
    projection_rows = 0
    statuses: Counter[str] = Counter()
    stop_reasons: Counter[str] = Counter()
    stop_reasons_by_spell: dict[str, Counter[str]] = defaultdict(Counter)
    projection_errors: Counter[str] = Counter()
    metadata_errors: Counter[str] = Counter()
    violation_samples: list[dict[str, object]] = []
    counter_10036: dict[str, list[int]] = defaultdict(list)
    timing_by_spell: dict[str, list[float]] = defaultdict(list)
    projection_payload_bytes: list[float] = []
    float_bit_classes: Counter[str] = Counter()

    with trace_path.open("rb") as stream:
        for raw_line in stream:
            trace_digest.update(raw_line)
            try:
                decision = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if decision.get("kind") != "decision":
                continue
            decision_rows += 1
            lookahead = decision.get("bullet_velocity_lookahead")
            if not isinstance(lookahead, dict):
                continue
            callback_rows += 1
            spell = spell_key(decision)
            statuses[str(lookahead.get("coverage_status"))] += 1
            stop_reason = str(lookahead.get("stop_reason"))
            stop_reasons[stop_reason] += 1
            stop_reasons_by_spell[spell][stop_reason] += 1
            row_metadata_errors = lookahead_metadata_errors(lookahead)
            metadata_errors.update(row_metadata_errors)
            projection = lookahead.get("vm_local_projection")
            row_projection_errors = _projection_errors(
                projection,
                tag_mask=lookahead.get("tag_mask"),
            )
            projection_errors.update(row_projection_errors)
            if not row_projection_errors:
                assert isinstance(projection, dict)
                projection_rows += 1
                scratch = projection["scratch_integers"]
                bits = projection["float_local_bits"]
                assert isinstance(scratch, list)
                assert isinstance(bits, list)
                counter_10036[spell].append(int(scratch[0]))
                float_bit_classes.update(
                    _float_bit_class(int(value)) for value in bits
                )
                projection_payload_bytes.append(
                    float(
                        len(
                            json.dumps(
                                {"vm_local_projection": projection},
                                separators=(",", ":"),
                                sort_keys=True,
                            ).encode("utf-8")
                        )
                    )
                )
            timing = decision.get("timing_ms")
            if isinstance(timing, dict):
                read_ms = timing.get("read_ecl_lookahead")
                if isinstance(read_ms, (int, float)):
                    timing_by_spell[spell].append(float(read_ms))
            if (
                row_metadata_errors or row_projection_errors
            ) and len(violation_samples) < 20:
                violation_samples.append(
                    {
                        "frame": decision.get("frame"),
                        "spell": spell,
                        "metadata_errors": row_metadata_errors,
                        "projection_errors": row_projection_errors,
                    }
                )

    required_spell_rows = {
        spell: len(counter_10036[spell]) for spell in ("57", "61", "65")
    }
    gates = {
        "callback_rows_present": callback_rows > 0,
        "projection_present_on_every_callback_row": (
            projection_rows == callback_rows
        ),
        "projection_layout_and_ranges_valid": not projection_errors,
        "legacy_tag_mask_bit_exact": projection_errors["tag_mask_mismatch"] == 0,
        "lookahead_metadata_unchanged_and_consistent": not metadata_errors,
        "complete_and_unknown_rows_observed": (
            statuses["complete"] > 0 and statuses["unknown"] > 0
        ),
        "hidden_control_remains_unknown": (
            stop_reasons["unsupported_control_flow"] > 0
        ),
    }
    if workload_profile == WORKLOAD_PROFILE_STAGE4A:
        gates.update(
            {
                "stage4_loop_counter_workloads_observed": all(
                    count > 0 for count in required_spell_rows.values()
                ),
                "spell73_dynamic_control_remains_unknown": (
                    stop_reasons_by_spell["73"][
                        "unsupported_control_flow"
                    ]
                    > 0
                ),
            }
        )
    return {
        "schema": SCHEMA,
        "workload_profile": workload_profile,
        "source": {
            "trace_name": trace_path.name,
            "trace_sha256": trace_digest.hexdigest(),
        },
        "counts": {
            "decision_rows": decision_rows,
            "callback_rows": callback_rows,
            "projection_rows": projection_rows,
            "coverage_status_rows": dict(sorted(statuses.items())),
            "stop_reason_rows": dict(sorted(stop_reasons.items())),
            "stop_reason_rows_by_spell": {
                spell: dict(sorted(counts.items()))
                for spell, counts in sorted(stop_reasons_by_spell.items())
            },
            "projection_errors": dict(sorted(projection_errors.items())),
            "metadata_errors": dict(sorted(metadata_errors.items())),
            "float_local_bit_classes": dict(
                sorted(float_bit_classes.items())
            ),
        },
        "counter_10036_by_spell": {
            spell: _int_summary(values)
            for spell, values in sorted(counter_10036.items())
        },
        "read_ecl_lookahead_ms_by_spell": {
            spell: timing_summary(values)
            for spell, values in sorted(timing_by_spell.items())
        },
        "projection_trace_payload_bytes": timing_summary(
            projection_payload_bytes
        ),
        "violations": violation_samples,
        "gates": gates,
        "passed": all(gates.values()),
        "authority": {
            "projection": "trace_only",
            "callback_schedule": "unchanged_complete_rows_only",
            "physical_action": "none_added",
            "survival": "not_claimed",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument(
        "--workload-profile",
        choices=WORKLOAD_PROFILES,
        default=WORKLOAD_PROFILE_STAGE4A,
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = audit_vm_projection_trace(
        arguments.trace,
        workload_profile=arguments.workload_profile,
    )
    encoded = json.dumps(
        report,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    if arguments.output is None:
        print(encoded, end="")
    else:
        arguments.output.write_text(encoded, encoding="utf-8", newline="\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
