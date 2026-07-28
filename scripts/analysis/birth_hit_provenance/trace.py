"""Validated streaming extraction of selected bullet activation generations."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from .types import ActivationEvidence, TraceScan

_EVENT_CODES = frozenset((2, 3, 4))
_EXPECTED_STATUS = {1: 1, 2: 2, 3: 2, 4: 3}
_REQUIRED_COLUMNS = (
    "slot",
    "code",
    "status",
    "state",
    "age",
    "previous_state",
    "previous_age",
    "geometry",
    "transform_flags",
    "geometry_finite",
)


def _integer(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _optional_integer(value: object, *, label: str) -> int | None:
    if value is None:
        return None
    return _integer(value, label=label)


def _validate_columns(evidence: dict[str, object], *, line: int) -> int:
    if evidence.get("format") != "columnar_v1":
        raise ValueError(f"line {line}: unsupported evidence format")
    lengths: dict[str, int] = {}
    for key in _REQUIRED_COLUMNS:
        column = evidence.get(key)
        if not isinstance(column, list):
            raise ValueError(f"line {line}: evidence.{key} must be a list")
        lengths[key] = len(column)
    if len(set(lengths.values())) != 1:
        raise ValueError(
            f"line {line}: inconsistent evidence column lengths {lengths}"
        )
    return lengths["slot"]


def _geometry(value: object, *, line: int, slot: int) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError(
            f"line {line}: slot {slot} geometry must have six values"
        )
    result = tuple(float(component) for component in value)
    if not all(math.isfinite(component) for component in result):
        raise ValueError(
            f"line {line}: slot {slot} geometry must be finite"
        )
    return result


def _support(
    observation: dict[str, object],
    *,
    line: int,
) -> tuple[int | None, int]:
    support_end = _integer(
        observation.get("frame_after"),
        label=f"line {line} observation.frame_after",
    )
    previous_end = _optional_integer(
        observation.get("previous_frame_after"),
        label=f"line {line} observation.previous_frame_after",
    )
    support_start = None if previous_end is None else previous_end + 1
    if support_start is not None and support_start > support_end:
        raise ValueError(
            f"line {line}: activation support starts after it ends"
        )
    return support_start, support_end


def scan_activation_evidence(
    trace: Path,
    *,
    target_slots: frozenset[int],
    target_hit_frames: frozenset[int],
    gameplay_epoch: int | None,
    stage_route_index: int | None,
) -> TraceScan:
    """Scan one immutable JSONL trace while hashing the exact input bytes."""

    digest = hashlib.sha256()
    byte_count = 0
    row_count = 0
    birth_row_count = 0
    invalid_timer_evidence_count = 0
    selected: dict[int, list[ActivationEvidence]] = defaultdict(list)
    hit_gameplay_epochs: dict[int, int] = {}

    with trace.open("rb") as stream:
        for trace_line, raw_line in enumerate(stream, start=1):
            digest.update(raw_line)
            byte_count += len(raw_line)
            row_count += 1
            try:
                row = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError(
                    f"line {trace_line}: invalid JSON: {error}"
                ) from error
            if not isinstance(row, dict):
                raise ValueError(f"line {trace_line}: row must be an object")
            kind = row.get("kind")
            if kind == "decision" and row.get("frame") in target_hit_frames:
                if row.get("hit_started") is not True:
                    raise ValueError(
                        f"line {trace_line}: dossier hit frame is not a hit"
                    )
                if (
                    stage_route_index is not None
                    and row.get("stage_route_index") != stage_route_index
                ):
                    continue
                epoch = _integer(
                    row.get("gameplay_epoch"),
                    label=f"line {trace_line} hit gameplay_epoch",
                )
                if gameplay_epoch is not None and epoch != gameplay_epoch:
                    continue
                frame = _integer(
                    row.get("frame"),
                    label=f"line {trace_line} hit frame",
                )
                if frame in hit_gameplay_epochs:
                    raise ValueError(
                        f"line {trace_line}: duplicate hit decision frame"
                    )
                hit_gameplay_epochs[frame] = epoch
                continue
            if kind != "bullet_birth_audit":
                continue
            if (
                gameplay_epoch is not None
                and row.get("gameplay_epoch") != gameplay_epoch
            ):
                continue
            if (
                stage_route_index is not None
                and row.get("stage_route_index") != stage_route_index
            ):
                continue
            birth_row_count += 1
            observation = row.get("observation")
            if not isinstance(observation, dict):
                raise ValueError(
                    f"line {trace_line}: observation must be an object"
                )
            evidence = observation.get("evidence")
            if not isinstance(evidence, dict):
                raise ValueError(
                    f"line {trace_line}: evidence must be an object"
                )
            count = _validate_columns(evidence, line=trace_line)
            declared_count = observation.get("evidence_count")
            if declared_count != count:
                raise ValueError(
                    f"line {trace_line}: evidence_count mismatch"
                )
            support_start, support_end = _support(
                observation,
                line=trace_line,
            )
            scope = row.get("scope")
            if not isinstance(scope, dict):
                raise ValueError(f"line {trace_line}: scope must be an object")
            omitted = scope.get("omitted_sources")
            if not isinstance(omitted, list) or not all(
                isinstance(value, str) for value in omitted
            ):
                raise ValueError(
                    f"line {trace_line}: omitted_sources must be strings"
                )
            for index in range(count):
                slot = _integer(
                    evidence["slot"][index],
                    label=f"line {trace_line} evidence.slot",
                )
                code = _integer(
                    evidence["code"][index],
                    label=f"line {trace_line} slot {slot} code",
                )
                status_code = _integer(
                    evidence["status"][index],
                    label=f"line {trace_line} slot {slot} status",
                )
                if _EXPECTED_STATUS.get(code) != status_code:
                    raise ValueError(
                        f"line {trace_line}: slot {slot} invalid code/status"
                    )
                if code == 1:
                    invalid_timer_evidence_count += 1
                if slot not in target_slots or code not in _EVENT_CODES:
                    continue
                finite = evidence["geometry_finite"][index]
                if not isinstance(finite, bool) or not finite:
                    raise ValueError(
                        f"line {trace_line}: slot {slot} geometry not finite"
                    )
                selected[slot].append(
                    ActivationEvidence(
                        trace_line=trace_line,
                        frame=_integer(
                            row.get("frame"),
                            label=f"line {trace_line} frame",
                        ),
                        snapshot_frame=_optional_integer(
                            row.get("snapshot_frame"),
                            label=f"line {trace_line} snapshot_frame",
                        ),
                        gameplay_epoch=_optional_integer(
                            row.get("gameplay_epoch"),
                            label=f"line {trace_line} gameplay_epoch",
                        ),
                        stage_route_index=_optional_integer(
                            row.get("stage_route_index"),
                            label=f"line {trace_line} stage_route_index",
                        ),
                        slot=slot,
                        code=code,
                        status_code=status_code,
                        state=_integer(
                            evidence["state"][index],
                            label=f"line {trace_line} slot {slot} state",
                        ),
                        age=_integer(
                            evidence["age"][index],
                            label=f"line {trace_line} slot {slot} age",
                        ),
                        previous_state=_integer(
                            evidence["previous_state"][index],
                            label=(
                                f"line {trace_line} slot {slot} "
                                "previous_state"
                            ),
                        ),
                        previous_age=_integer(
                            evidence["previous_age"][index],
                            label=(
                                f"line {trace_line} slot {slot} previous_age"
                            ),
                        ),
                        support_start=support_start,
                        support_end=support_end,
                        geometry=_geometry(
                            evidence["geometry"][index],
                            line=trace_line,
                            slot=slot,
                        ),
                        transform_flags=_integer(
                            evidence["transform_flags"][index],
                            label=(
                                f"line {trace_line} slot {slot} "
                                "transform_flags"
                            ),
                        ),
                        intent_available=row.get("intent") is not None,
                        spell_enemy_pointer=_optional_integer(
                            row.get("spell_enemy_pointer"),
                            label=(
                                f"line {trace_line} spell_enemy_pointer"
                            ),
                        ),
                        intent_scope=(
                            scope.get("intent")
                            if isinstance(scope.get("intent"), str)
                            else None
                        ),
                        omitted_sources=tuple(sorted(omitted)),
                        wave_evidence_count=count,
                    )
                )

    activations = {
        slot: tuple(
            sorted(
                records,
                key=lambda record: (
                    record.support_end,
                    record.frame,
                    record.trace_line,
                ),
            )
        )
        for slot, records in sorted(selected.items())
    }
    return TraceScan(
        activations=activations,
        hit_gameplay_epochs=dict(sorted(hit_gameplay_epochs.items())),
        trace_bytes=byte_count,
        trace_sha256=digest.hexdigest(),
        row_count=row_count,
        birth_row_count=birth_row_count,
        invalid_timer_evidence_count=invalid_timer_evidence_count,
    )


__all__ = ["scan_activation_evidence"]
