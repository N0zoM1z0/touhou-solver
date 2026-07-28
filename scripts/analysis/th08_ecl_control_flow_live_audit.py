#!/usr/bin/env python3
"""Validate live fail-closed ECL callback control metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from analysis.th08_ecl_trace_support import (
    LEGACY_INCOMPLETE_REASONS,
    compact_summary as _summary,
    lookahead_metadata_errors as _metadata_errors,
    spell_key as _spell_key,
)


SCHEMA = "th08-ecl-control-flow-live-audit-v1"


def audit_live_trace(trace_path: Path) -> dict[str, object]:
    trace_digest = hashlib.sha256()
    decision_rows = 0
    callback_rows = 0
    lookahead_errors = 0
    metadata_error_count = 0
    metadata_error_samples: list[dict[str, object]] = []
    statuses: Counter[str] = Counter()
    stop_reasons: Counter[str] = Counter()
    lowering_statuses: Counter[str] = Counter()
    per_spell: dict[str, Counter[str]] = defaultdict(Counter)
    per_spell_instructions: dict[str, list[float]] = defaultdict(list)
    per_spell_timing: dict[str, list[float]] = defaultdict(list)
    phase_end_rows = 0
    phase_end_valid_rows = 0

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
            spell = _spell_key(decision)
            frame = decision.get("frame")
            if lookahead.get("error") is not None:
                lookahead_errors += 1
            status = str(lookahead.get("coverage_status"))
            reason = str(lookahead.get("stop_reason"))
            lowering = str(lookahead.get("lowering_status"))
            statuses[status] += 1
            stop_reasons[reason] += 1
            lowering_statuses[lowering] += 1
            per_spell[spell]["rows"] += 1
            per_spell[spell][f"status:{status}"] += 1
            per_spell[spell][f"stop:{reason}"] += 1
            instructions = lookahead.get("instructions_scanned")
            if isinstance(instructions, int):
                per_spell_instructions[spell].append(float(instructions))
            timing = decision.get("timing_ms")
            if isinstance(timing, dict):
                read_ms = timing.get("read_ecl_lookahead")
                if isinstance(read_ms, (int, float)):
                    per_spell_timing[spell].append(float(read_ms))

            spell_record = decision.get("spell")
            phase_end = (
                isinstance(spell_record, dict)
                and isinstance(spell_record.get("flags"), int)
                and bool(int(spell_record["flags"]) & 0x800)
            )
            if phase_end:
                phase_end_rows += 1

            errors = _metadata_errors(lookahead)
            if not errors and lookahead.get("error") is None:
                if phase_end:
                    phase_end_valid_rows += 1
            else:
                metadata_error_count += len(errors)
                if len(metadata_error_samples) < 20:
                    metadata_error_samples.append(
                        {
                            "frame": frame,
                            "spell": spell,
                            "errors": errors,
                            "lookahead_error": lookahead.get("error"),
                        }
                    )

    spell_records: dict[str, object] = {}
    for spell, counts in sorted(per_spell.items()):
        spell_records[spell] = {
            "rows": counts["rows"],
            "coverage_status_rows": dict(
                sorted(
                    (
                        key.removeprefix("status:"),
                        value,
                    )
                    for key, value in counts.items()
                    if key.startswith("status:")
                )
            ),
            "stop_reason_rows": dict(
                sorted(
                    (
                        key.removeprefix("stop:"),
                        value,
                    )
                    for key, value in counts.items()
                    if key.startswith("stop:")
                )
            ),
            "instructions_scanned": _summary(
                per_spell_instructions[spell]
            ),
            "read_ecl_lookahead_ms": _summary(per_spell_timing[spell]),
        }

    gates = {
        "callback_rows_present": callback_rows > 0,
        "no_lookahead_errors": lookahead_errors == 0,
        "coverage_metadata_consistent": metadata_error_count == 0,
        "no_legacy_budget_or_repeat_stop": not any(
            stop_reasons[reason] for reason in LEGACY_INCOMPLETE_REASONS
        ),
        "hidden_control_is_unknown": (
            stop_reasons["unsupported_control_flow"] > 0
        ),
        "spell57_stops_at_control_with_under_64_instructions": (
            per_spell["57"]["rows"] > 0
            and per_spell["57"]["stop:unsupported_control_flow"]
            == per_spell["57"]["rows"]
            and max(per_spell_instructions["57"], default=256.0) < 64
        ),
        "spell61_control_boundary_observed": (
            per_spell["61"]["stop:unsupported_control_flow"] > 0
        ),
        "spell65_control_boundary_observed": (
            per_spell["65"]["stop:unsupported_control_flow"] > 0
        ),
        "spell73_dynamic_control_boundary_observed": (
            per_spell["73"]["stop:unsupported_control_flow"] > 0
        ),
        "phase_end_runtime_rows_observed_and_valid": (
            phase_end_rows > 0
            and phase_end_rows == phase_end_valid_rows
        ),
    }
    return {
        "schema": SCHEMA,
        "source": {
            "trace_name": trace_path.name,
            "trace_sha256": trace_digest.hexdigest(),
        },
        "counts": {
            "decision_rows": decision_rows,
            "callback_rows": callback_rows,
            "lookahead_errors": lookahead_errors,
            "metadata_error_count": metadata_error_count,
            "coverage_status_rows": dict(sorted(statuses.items())),
            "stop_reason_rows": dict(sorted(stop_reasons.items())),
            "lowering_status_rows": dict(sorted(lowering_statuses.items())),
            "phase_end_rows": phase_end_rows,
            "phase_end_valid_rows": phase_end_valid_rows,
        },
        "per_spell": spell_records,
        "violations": {
            "metadata_error_samples": metadata_error_samples,
        },
        "gates": gates,
        "passed": all(gates.values()),
        "authority": {
            "callback_schedule": "complete_rows_only",
            "physical_action": "none_added",
            "survival": "not_claimed",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = audit_live_trace(arguments.trace)
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
