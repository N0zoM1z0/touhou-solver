"""Bounded JSONL ingestion and scope selection for offline dossiers."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from analysis.dossier.schema import compact_decision


TraceRow = dict[str, object]
TraceRowConsumer = Callable[[TraceRow], None]


@dataclass(frozen=True)
class JsonlScan:
    sha256: str
    size_bytes: int
    parse_errors: int


@dataclass(frozen=True)
class TraceProvenance:
    path: str
    sha256: str
    size_bytes: int
    parse_errors: int
    decision_count: int
    first_frame: int | None
    last_frame: int | None
    summary: dict[str, object] | None
    runtime_errors: tuple[dict[str, object], ...]
    wall_auto_confirm_frames: tuple[int, ...]
    controller_configs: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class PracticeTrace:
    path: str
    sha256: str
    size_bytes: int
    parse_errors: int
    identity: dict[str, object] | None
    controller_configs: tuple[dict[str, object], ...]
    raw_kind_counts: dict[str, int]
    raw_summary: dict[str, object] | None
    decisions: tuple[dict[str, object], ...]
    end_event: dict[str, object]
    scene_events: tuple[dict[str, object], ...]
    frame_epoch_index: int
    frame_epoch_count: int
    pre_scope_decision_count: int
    post_scope_decision_count: int


def scan_jsonl(path: Path, consume: TraceRowConsumer) -> JsonlScan:
    """Stream valid JSON objects while retaining whole-file provenance."""
    digest = hashlib.sha256()
    parse_errors = 0
    with path.open("rb") as source:
        for binary_line in source:
            digest.update(binary_line)
            try:
                row = json.loads(binary_line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                parse_errors += 1
                continue
            consume(row)
    return JsonlScan(
        sha256=digest.hexdigest(),
        size_bytes=path.stat().st_size,
        parse_errors=parse_errors,
    )


def read_trace(
    path: Path,
    *,
    trace_index: int,
) -> tuple[TraceProvenance, list[dict[str, object]]]:
    """Read one stitched-run trace without retaining raw decision rows."""
    summary = None
    runtime_errors = []
    wall_auto_confirm_frames = []
    controller_configs = []
    decisions = []

    def consume(row: TraceRow) -> None:
        nonlocal summary
        kind = row.get("kind")
        if kind == "decision":
            if row.get("stage_route_index") is None:
                raise ValueError(f"{path}: decision lacks stage_route_index")
            decisions.append(
                compact_decision(
                    row,
                    trace_index=trace_index,
                    trace_path=path,
                )
            )
        elif kind == "summary":
            summary = row
        elif kind == "runtime_error":
            runtime_errors.append(row)
        elif kind == "auto_confirm_wall_pulse":
            wall_auto_confirm_frames.append(int(row["frame"]))
        elif kind == "controller_config":
            controller_configs.append(row)

    scan = scan_jsonl(path, consume)
    return (
        TraceProvenance(
            path=str(path),
            sha256=scan.sha256,
            size_bytes=scan.size_bytes,
            parse_errors=scan.parse_errors,
            decision_count=len(decisions),
            first_frame=int(decisions[0]["frame"]) if decisions else None,
            last_frame=int(decisions[-1]["frame"]) if decisions else None,
            summary=summary,
            runtime_errors=tuple(runtime_errors),
            wall_auto_confirm_frames=tuple(wall_auto_confirm_frames),
            controller_configs=tuple(controller_configs),
        ),
        decisions,
    )


def extract_scope(
    rows: list[dict[str, object]],
    *,
    trace_path: Path,
) -> tuple[
    list[dict[str, object]],
    dict[str, object],
    list[dict[str, object]],
    int,
]:
    """Extract one stage-bounded practice scope."""
    decisions: list[dict[str, object]] = []
    scene_events: list[dict[str, object]] = []
    end_event: dict[str, object] | None = None
    stage: int | None = None
    previous_frame: int | None = None
    post_scope_decisions = 0

    for row in rows:
        kind = row.get("kind")
        if kind in {"scene_inactive", "scene_resumed"} and end_event is None:
            scene_events.append(row)
        if kind == "runtime_error" and end_event is None:
            end_event = {
                "reason": "runtime_error",
                "error_type": row.get("error_type"),
                "error": row.get("error"),
                "last_frame": row.get("last_frame", previous_frame),
                "stage_route_index": stage,
            }
            continue
        if kind != "decision":
            continue
        frame = int(row["frame"])
        row_stage = int(row["stage_route_index"])
        if end_event is not None:
            post_scope_decisions += 1
            continue
        if stage is None:
            stage = row_stage
        elif row_stage != stage:
            end_event = {
                "reason": "stage_change",
                "previous_stage_route_index": stage,
                "next_stage_route_index": row_stage,
                "next_frame": frame,
            }
            post_scope_decisions += 1
            continue
        if previous_frame is not None and frame < previous_frame:
            end_event = {
                "reason": "frame_counter_regression",
                "previous_frame": previous_frame,
                "next_frame": frame,
                "stage_route_index": row_stage,
            }
            post_scope_decisions += 1
            continue
        compact = compact_decision(
            row,
            trace_index=0,
            trace_path=trace_path,
        )
        corridor = row.get("corridor")
        if isinstance(corridor, dict):
            compact["corridor_source_frame"] = int(corridor["source_frame"])
            compact["corridor_solve_ms"] = float(corridor.get("solve_ms", 0.0))
            compact["corridor_age"] = int(corridor.get("age", 0))
            compact["corridor_stale"] = bool(corridor.get("stale"))
        decisions.append(compact)
        previous_frame = frame

    if not decisions:
        raise ValueError(f"{trace_path}: no scoped decisions")
    if end_event is None:
        end_event = {
            "reason": "raw_trace_end",
            "last_frame": int(decisions[-1]["frame"]),
            "stage_route_index": int(decisions[-1]["stage_route_index"]),
        }
    first_frame = int(decisions[0]["frame"])
    last_frame = int(decisions[-1]["frame"])
    scene_events = [
        row
        for row in scene_events
        if first_frame <= int(row.get("frame", -1)) <= last_frame
    ]
    return decisions, end_event, scene_events, post_scope_decisions


def select_frame_epoch(
    rows: list[dict[str, object]],
    selector: str | int,
) -> tuple[list[dict[str, object]], int, int, int, int]:
    """Select one monotone gameplay-frame epoch from a multi-attempt trace."""
    starts = [0]
    previous_decision_frame: int | None = None
    previous_stage: int | None = None
    pending_event_boundary: int | None = None
    decision_indices: list[int] = []

    for index, row in enumerate(rows):
        frame = row.get("frame")
        if not isinstance(frame, int):
            continue
        if (
            previous_decision_frame is not None
            and frame < previous_decision_frame
            and pending_event_boundary is None
        ):
            pending_event_boundary = index
        if row.get("kind") != "decision":
            continue
        decision_indices.append(index)
        stage = int(row["stage_route_index"])
        if previous_decision_frame is not None and (
            frame < previous_decision_frame or stage != previous_stage
        ):
            starts.append(
                pending_event_boundary if pending_event_boundary is not None else index
            )
        previous_decision_frame = frame
        previous_stage = stage
        pending_event_boundary = None

    if not decision_indices:
        raise ValueError("trace contains no decisions")
    epoch_count = len(starts)
    if isinstance(selector, str):
        if selector == "first":
            epoch_index = 0
        elif selector == "last":
            epoch_index = epoch_count - 1
        else:
            try:
                epoch_index = int(selector)
            except ValueError as exc:
                raise ValueError(
                    "frame epoch must be 'first', 'last', or a zero-based index"
                ) from exc
    else:
        epoch_index = selector
    if not 0 <= epoch_index < epoch_count:
        raise ValueError(f"frame epoch {epoch_index} is outside 0..{epoch_count - 1}")

    start = starts[epoch_index]
    end = starts[epoch_index + 1] if epoch_index + 1 < epoch_count else len(rows)
    selected = rows[start:end]
    selected_decisions = sum(row.get("kind") == "decision" for row in selected)
    pre_decisions = sum(row.get("kind") == "decision" for row in rows[:start])
    post_decisions = len(decision_indices) - pre_decisions - selected_decisions
    return selected, epoch_index, epoch_count, pre_decisions, post_decisions


def read_practice_trace(
    path: Path,
    *,
    frame_epoch: str | int | None = None,
) -> PracticeTrace:
    """Read and scope a standalone practice/live-stage trace."""
    rows: list[dict[str, object]] = []
    identity = None
    controller_configs = []
    raw_summary = None
    kind_counts: Counter[str] = Counter()

    def consume(row: TraceRow) -> None:
        nonlocal identity, raw_summary
        rows.append(row)
        kind = str(row.get("kind", "unknown"))
        kind_counts[kind] += 1
        if kind == "identity":
            identity = row
        elif kind == "controller_config":
            controller_configs.append(row)
        elif kind == "summary":
            raw_summary = row

    scan = scan_jsonl(path, consume)
    epoch_index = 0
    epoch_count = 1
    pre_scope_decisions = 0
    epoch_post_decisions = 0
    scoped_rows = rows
    if frame_epoch is not None:
        (
            scoped_rows,
            epoch_index,
            epoch_count,
            pre_scope_decisions,
            epoch_post_decisions,
        ) = select_frame_epoch(rows, frame_epoch)
    (
        decisions,
        end_event,
        scene_events,
        post_scope_decisions,
    ) = extract_scope(
        scoped_rows,
        trace_path=path,
    )
    return PracticeTrace(
        path=str(path),
        sha256=scan.sha256,
        size_bytes=scan.size_bytes,
        parse_errors=scan.parse_errors,
        identity=identity,
        controller_configs=tuple(controller_configs),
        raw_kind_counts=dict(kind_counts),
        raw_summary=raw_summary,
        decisions=tuple(decisions),
        end_event=end_event,
        scene_events=tuple(scene_events),
        frame_epoch_index=epoch_index,
        frame_epoch_count=epoch_count,
        pre_scope_decision_count=pre_scope_decisions,
        post_scope_decision_count=(post_scope_decisions + epoch_post_decisions),
    )
