"""One-pass aggregation and gates for combat-progress JSONL traces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics
from typing import Any

from .schema import (
    EnemyCombatProgressAuditError,
    OBSERVATION_SCHEMA,
    require_exact_int,
    require_finite_nonnegative,
    validate_inventory,
)


SCHEMA = "th08-enemy-combat-progress-physical-audit-v1"
TIMING_LIMITS_MS = {
    "p95": 0.10,
    "p99": 0.20,
    "max": 2.00,
}


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(fraction * len(ordered)))
    return ordered[index]


def _summary(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {
        "median": statistics.median(values),
        "p95": _percentile(values, 0.95),
        "p99": _percentile(values, 0.99),
        "max": max(values),
    }


def _timing_passes(summary: dict[str, float] | None) -> bool:
    return bool(
        summary is not None
        and summary["p95"] <= TIMING_LIMITS_MS["p95"]
        and summary["p99"] <= TIMING_LIMITS_MS["p99"]
        and summary["max"] <= TIMING_LIMITS_MS["max"]
    )


class _AuditAccumulator:
    def __init__(self) -> None:
        self.observation_count = 0
        self.stable_count = 0
        self.active_row_count = 0
        self.positive_frame_damage_rows = 0
        self.positive_hp_decrease_candidates = 0
        self.nonpositive_decision_deltas = 0
        self.decode_timings: list[float] = []
        self.record_timings: list[float] = []
        self.stage_timings: list[float] = []
        self.capture_timings: list[float] = []
        self.emit_timings: list[float] = []
        self.decision_deltas: list[float] = []
        self.observations_by_epoch: dict[str, int] = {}
        self.previous_rows: dict[tuple[int, int], dict[int, int]] = {}
        self.previous_decision: dict[tuple[int, int], int] = {}

    def retain_rows(
        self,
        rows: list[list[int | bool]],
        *,
        epoch_key: tuple[int, int],
    ) -> None:
        self.active_row_count += len(rows)
        self.positive_frame_damage_rows += sum(
            1 for row in rows if int(row[7]) > 0
        )
        current_rows = {int(row[0]): int(row[4]) for row in rows}
        for slot, current_health in current_rows.items():
            previous_health = self.previous_rows.get(epoch_key, {}).get(slot)
            if (
                previous_health is not None
                and previous_health > current_health >= 0
            ):
                self.positive_hp_decrease_candidates += 1
        self.previous_rows[epoch_key] = current_rows

    def retain_decision(
        self,
        *,
        stage_route_index: int,
        gameplay_epoch: int,
        decision_frame: int,
    ) -> None:
        epoch_key = (stage_route_index, gameplay_epoch)
        label = f"{stage_route_index}:{gameplay_epoch}"
        self.observations_by_epoch[label] = (
            self.observations_by_epoch.get(label, 0) + 1
        )
        if epoch_key in self.previous_decision:
            delta = decision_frame - self.previous_decision[epoch_key]
            self.decision_deltas.append(float(delta))
            if delta <= 0:
                self.nonpositive_decision_deltas += 1
        self.previous_decision[epoch_key] = decision_frame


def _validate_identity(
    record: dict[str, Any],
    *,
    line_number: int,
    expected_route_id: int,
    expected_difficulty_index: int,
    expected_stage_route_index: int,
) -> tuple[int, int, int, int, int]:
    route_id = require_exact_int(
        record.get("route_id"),
        line_number=line_number,
        field="route_id",
    )
    difficulty_index = require_exact_int(
        record.get("difficulty_index"),
        line_number=line_number,
        field="difficulty_index",
    )
    stage_route_index = require_exact_int(
        record.get("stage_route_index"),
        line_number=line_number,
        field="stage_route_index",
    )
    gameplay_epoch = require_exact_int(
        record.get("gameplay_epoch"),
        line_number=line_number,
        field="gameplay_epoch",
    )
    decision_frame = require_exact_int(
        record.get("decision_frame"),
        line_number=line_number,
        field="decision_frame",
    )
    if (
        route_id != expected_route_id
        or difficulty_index != expected_difficulty_index
        or stage_route_index != expected_stage_route_index
    ):
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: physical identity mismatch"
        )
    if gameplay_epoch < 0 or decision_frame < 0:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: negative epoch or decision frame"
        )
    return (
        route_id,
        difficulty_index,
        stage_route_index,
        gameplay_epoch,
        decision_frame,
    )


def _retain_observation(
    accumulator: _AuditAccumulator,
    record: dict[str, Any],
    *,
    line_number: int,
    expected_route_id: int,
    expected_difficulty_index: int,
    expected_stage_route_index: int,
) -> None:
    accumulator.observation_count += 1
    if record.get("schema") != OBSERVATION_SCHEMA:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: unexpected observation schema"
        )
    (
        _route_id,
        _difficulty_index,
        stage_route_index,
        gameplay_epoch,
        decision_frame,
    ) = _validate_identity(
        record,
        line_number=line_number,
        expected_route_id=expected_route_id,
        expected_difficulty_index=expected_difficulty_index,
        expected_stage_route_index=expected_stage_route_index,
    )
    frame_before = require_exact_int(
        record.get("frame_before"),
        line_number=line_number,
        field="frame_before",
    )
    frame_after = require_exact_int(
        record.get("frame_after"),
        line_number=line_number,
        field="frame_after",
    )
    capture_attempts = require_exact_int(
        record.get("capture_attempts"),
        line_number=line_number,
        field="capture_attempts",
    )
    if capture_attempts not in {1, 2}:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: invalid capture attempt count"
        )
    stable = record.get("stable")
    if type(stable) is not bool or stable is not (frame_before == frame_after):
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: stable flag disagrees with bracket"
        )
    if stable:
        accumulator.stable_count += 1
    accumulator.capture_timings.append(
        require_finite_nonnegative(
            record.get("capture_ms"),
            line_number=line_number,
            field="capture_ms",
        )
    )
    accumulator.stage_timings.append(
        require_finite_nonnegative(
            record.get("stage_ms"),
            line_number=line_number,
            field="stage_ms",
        )
    )
    previous_emit_ms = record.get("previous_emit_ms")
    if accumulator.observation_count == 1:
        if previous_emit_ms is not None:
            raise EnemyCombatProgressAuditError(
                f"line {line_number}: first previous emit timing is not null"
            )
    else:
        accumulator.emit_timings.append(
            require_finite_nonnegative(
                previous_emit_ms,
                line_number=line_number,
                field="previous_emit_ms",
            )
        )
    rows, decode_ms, record_ms = validate_inventory(
        record.get("inventory"),
        line_number=line_number,
    )
    accumulator.decode_timings.append(decode_ms)
    accumulator.record_timings.append(record_ms)
    epoch_key = (stage_route_index, gameplay_epoch)
    accumulator.retain_rows(rows, epoch_key=epoch_key)
    accumulator.retain_decision(
        stage_route_index=stage_route_index,
        gameplay_epoch=gameplay_epoch,
        decision_frame=decision_frame,
    )


def _build_report(
    accumulator: _AuditAccumulator,
    *,
    trace_sha256: str,
    line_count: int,
    expected_route_id: int,
    expected_difficulty_index: int,
    expected_stage_route_index: int,
) -> dict[str, Any]:
    timing = {
        "decode_ms": _summary(accumulator.decode_timings),
        "record_ms": _summary(accumulator.record_timings),
        "stage_ms": _summary(accumulator.stage_timings),
        "capture_ms": _summary(accumulator.capture_timings),
        "previous_emit_ms": _summary(accumulator.emit_timings),
        "decision_frame_delta": _summary(accumulator.decision_deltas),
    }
    gates = {
        "has_observations": accumulator.observation_count > 0,
        "all_brackets_stable": (
            accumulator.observation_count == accumulator.stable_count
        ),
        "has_active_rows": accumulator.active_row_count > 0,
        "has_positive_frame_damage": (
            accumulator.positive_frame_damage_rows > 0
        ),
        "has_positive_hp_decrease_candidate": (
            accumulator.positive_hp_decrease_candidates > 0
        ),
        "decision_frames_strictly_increase": (
            accumulator.nonpositive_decision_deltas == 0
        ),
        "decode_timing": _timing_passes(timing["decode_ms"]),
        "record_timing": _timing_passes(timing["record_ms"]),
    }
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "trace_sha256": trace_sha256,
        "expected_identity": {
            "route_id": expected_route_id,
            "difficulty_index": expected_difficulty_index,
            "stage_route_index": expected_stage_route_index,
        },
        "line_count": line_count,
        "observation_count": accumulator.observation_count,
        "stable_count": accumulator.stable_count,
        "active_row_count": accumulator.active_row_count,
        "positive_frame_damage_rows": (
            accumulator.positive_frame_damage_rows
        ),
        "positive_hp_decrease_candidates": (
            accumulator.positive_hp_decrease_candidates
        ),
        "nonpositive_decision_deltas": (
            accumulator.nonpositive_decision_deltas
        ),
        "observations_by_stage_epoch": dict(
            sorted(accumulator.observations_by_epoch.items())
        ),
        "timing": timing,
        "timing_limits_ms": TIMING_LIMITS_MS,
        "gates": gates,
        "passed": all(gates.values()),
        "authority": "trace_only_combat_progress",
        "generation_authority": "none",
        "end_reason_authority": "none",
        "kill_authority": "none",
        "targeting_authority": "none",
        "action_authority": "none",
    }
    digest_payload = json.dumps(
        report,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report["report_digest"] = hashlib.sha256(digest_payload).hexdigest()
    return report


def audit_enemy_combat_progress(
    trace_path: Path,
    *,
    expected_route_id: int,
    expected_difficulty_index: int,
    expected_stage_route_index: int,
) -> dict[str, Any]:
    trace_digest = hashlib.sha256()
    line_count = 0
    accumulator = _AuditAccumulator()
    with trace_path.open("rb") as source:
        for line_number, raw_line in enumerate(source, 1):
            trace_digest.update(raw_line)
            line_count = line_number
            try:
                record = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise EnemyCombatProgressAuditError(
                    f"line {line_number}: invalid JSON: {error}"
                ) from error
            if not isinstance(record, dict):
                raise EnemyCombatProgressAuditError(
                    f"line {line_number}: trace record must be an object"
                )
            if record.get("kind") == "enemy_combat_progress":
                _retain_observation(
                    accumulator,
                    record,
                    line_number=line_number,
                    expected_route_id=expected_route_id,
                    expected_difficulty_index=expected_difficulty_index,
                    expected_stage_route_index=expected_stage_route_index,
                )
    return _build_report(
        accumulator,
        trace_sha256=trace_digest.hexdigest(),
        line_count=line_count,
        expected_route_id=expected_route_id,
        expected_difficulty_index=expected_difficulty_index,
        expected_stage_route_index=expected_stage_route_index,
    )


__all__ = ["audit_enemy_combat_progress"]
