#!/usr/bin/env python3
"""Audit a bounded TH08 priority-17 publication-probe trace."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable

from th08_runtime.game_state import SUPPORTED_INPUT_MASK
from th08_runtime.priority17_publication_probe import PROBE_SCHEMA
from touhou_control.ordered_input_transaction_oracle import ordered_mask_path


REPORT_SCHEMA = "th08-priority17-publication-report-v1"
BOMB_INPUT_BIT = 0x02
_MAX_RETAINED_WITNESSES = 32


@dataclass(frozen=True)
class _Event:
    serial: int
    manager_frame: int
    engine_flags: int
    raw_mask: int
    current_mask: int
    previous_mask: int
    replay_frame_counter: int
    source_line: int
    source_kind: str

    def compact_record(self) -> dict[str, object]:
        return {
            "serial": self.serial,
            "manager_frame": self.manager_frame,
            "engine_flags": self.engine_flags,
            "raw": self.raw_mask,
            "current": self.current_mask,
            "previous": self.previous_mask,
            "replay_frame_counter": self.replay_frame_counter,
            "source_line": self.source_line,
            "source_kind": self.source_kind,
        }


@dataclass(frozen=True)
class _Batch:
    status: str
    previous_serial: int | None
    observed_serial: int | None
    events: tuple[_Event, ...]
    dropped_event_count: int


@dataclass(frozen=True)
class _Write:
    ordinal: int
    decision_ordinal: int
    line: int
    frame: int
    stage_route_index: int
    previous_mask: int
    target_mask: int
    mask_path: tuple[int, ...]
    pre_serial: int | None
    post_serial: int | None
    bracket_status: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _records(path: Path) -> Iterable[tuple[int, dict[str, object]]]:
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"line {line_number}: invalid JSON: {error}"
                ) from error
            if not isinstance(row, dict):
                raise ValueError(
                    f"line {line_number}: trace row is not an object"
                )
            yield line_number, row


def _object(value: object, *, line: int, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"line {line}: {field} must be an object")
    return value


def _integer(value: object, *, line: int, field: str) -> int:
    if type(value) is not int:
        raise ValueError(f"line {line}: {field} must be an integer")
    return value


def _optional_integer(value: object, *, line: int, field: str) -> int | None:
    if value is None:
        return None
    return _integer(value, line=line, field=field)


def _boolean(value: object, *, line: int, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"line {line}: {field} must be a Boolean")
    return value


def _mask(value: object, *, line: int, field: str) -> int:
    mask = _integer(value, line=line, field=field)
    if mask < 0 or mask & ~SUPPORTED_INPUT_MASK:
        raise ValueError(
            f"line {line}: {field} contains unsupported input bits"
        )
    return mask


def _serial_distance(later: int, earlier: int) -> int:
    distance = (later - earlier) & 0xFFFFFFFF
    if distance >= 1 << 31:
        raise ValueError(
            f"publication serial moved backward: {earlier} -> {later}"
        )
    return distance


def _event(
    value: object,
    *,
    line: int,
    source_kind: str,
) -> _Event:
    raw = _object(value, line=line, field="publication event")
    event = _Event(
        serial=_integer(raw.get("serial"), line=line, field="event.serial"),
        manager_frame=_integer(
            raw.get("manager_frame"),
            line=line,
            field="event.manager_frame",
        ),
        engine_flags=_integer(
            raw.get("engine_flags"),
            line=line,
            field="event.engine_flags",
        ),
        raw_mask=_mask(raw.get("raw"), line=line, field="event.raw"),
        current_mask=_mask(
            raw.get("current"),
            line=line,
            field="event.current",
        ),
        previous_mask=_mask(
            raw.get("previous"),
            line=line,
            field="event.previous",
        ),
        replay_frame_counter=_integer(
            raw.get("replay_frame_counter"),
            line=line,
            field="event.replay_frame_counter",
        ),
        source_line=line,
        source_kind=source_kind,
    )
    if (
        event.raw_mask & BOMB_INPUT_BIT
        or event.current_mask & BOMB_INPUT_BIT
        or event.previous_mask & BOMB_INPUT_BIT
    ):
        raise ValueError(f"line {line}: probe observed forbidden Bomb input")
    return event


def _batch(
    value: object,
    *,
    line: int,
    source_kind: str,
) -> _Batch:
    raw = _object(value, line=line, field=source_kind)
    if raw.get("schema") != PROBE_SCHEMA:
        raise ValueError(f"line {line}: unexpected priority-17 probe schema")
    if raw.get("action_authority") is not False:
        raise ValueError(f"line {line}: probe record claims action authority")
    status = raw.get("status")
    if not isinstance(status, str):
        raise ValueError(f"line {line}: probe status must be a string")
    previous = _optional_integer(
        raw.get("previous_serial"),
        line=line,
        field="previous_serial",
    )
    observed = _optional_integer(
        raw.get("observed_serial"),
        line=line,
        field="observed_serial",
    )
    raw_events = raw.get("events")
    if not isinstance(raw_events, list):
        raise ValueError(f"line {line}: probe events must be a list")
    events = tuple(
        _event(item, line=line, source_kind=source_kind) for item in raw_events
    )
    dropped = _integer(
        raw.get("dropped_event_count"),
        line=line,
        field="dropped_event_count",
    )
    if dropped < 0:
        raise ValueError(f"line {line}: dropped event count is negative")

    if status == "baseline":
        if previous is not None or observed is None or events or dropped:
            raise ValueError(f"line {line}: invalid baseline batch")
        return _Batch(status, previous, observed, events, dropped)
    if status in {"read_error", "race_unknown"}:
        if observed is not None or events or dropped:
            raise ValueError(f"line {line}: invalid unknown probe batch")
        return _Batch(status, previous, observed, events, dropped)
    if status not in {"no_events", "exact", "overflow_or_trace_truncation"}:
        raise ValueError(f"line {line}: unknown probe batch status {status!r}")
    if previous is None or observed is None:
        raise ValueError(
            f"line {line}: complete probe batch lacks serial bounds"
        )
    distance = _serial_distance(observed, previous)
    if status == "no_events":
        if distance or events or dropped:
            raise ValueError(f"line {line}: invalid no-events batch")
    elif status == "exact":
        if dropped or len(events) != distance:
            raise ValueError(
                f"line {line}: exact probe batch has a serial gap"
            )
    elif not dropped or len(events) + dropped != distance:
        raise ValueError(f"line {line}: invalid overflow probe batch")
    if events:
        first = (observed - len(events) + 1) & 0xFFFFFFFF
        expected = tuple(
            (first + offset) & 0xFFFFFFFF for offset in range(len(events))
        )
        if tuple(event.serial for event in events) != expected:
            raise ValueError(
                f"line {line}: probe event serials are not contiguous"
            )
    return _Batch(status, previous, observed, events, dropped)


def _dispatch_path(
    row: dict[str, object],
    *,
    line: int,
) -> tuple[bool, int, int, tuple[int, ...]]:
    dispatch = _object(
        row.get("input_dispatch"),
        line=line,
        field="input_dispatch",
    )
    previous = _mask(
        dispatch.get("previous_mask"),
        line=line,
        field="input_dispatch.previous_mask",
    )
    target = _mask(
        dispatch.get("target_mask"),
        line=line,
        field="input_dispatch.target_mask",
    )
    write_required = _boolean(
        dispatch.get("write_required"),
        line=line,
        field="input_dispatch.write_required",
    )
    raw_transitions = dispatch.get("transitions")
    if not isinstance(raw_transitions, list):
        raise ValueError(f"line {line}: input transitions must be a list")
    active = previous
    observed_path = [previous]
    for index, value in enumerate(raw_transitions):
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError(
                f"line {line}: input transition {index} is invalid"
            )
        bit = _mask(value[0], line=line, field=f"transition {index} bit")
        pressed = _boolean(
            value[1],
            line=line,
            field=f"transition {index} pressed",
        )
        if not bit or bit & (bit - 1):
            raise ValueError(f"line {line}: transition bit is not one-hot")
        active = active | bit if pressed else active & ~bit
        observed_path.append(active)
    expected = (
        previous,
        *ordered_mask_path(
            previous,
            target,
            supported_mask=SUPPORTED_INPUT_MASK,
            forbidden_mask=BOMB_INPUT_BIT,
        ),
    )
    if (
        tuple(observed_path) != expected
        or active != target
        or write_required != (previous != target)
        or _mask(row.get("mask"), line=line, field="mask") != target
    ):
        raise ValueError(f"line {line}: dispatch is not the ordered mask path")
    if previous & BOMB_INPUT_BIT or target & BOMB_INPUT_BIT:
        raise ValueError(
            f"line {line}: dispatch contains forbidden Bomb input"
        )
    return write_required, previous, target, expected


def _events_in_interval(
    events: dict[int, _Event],
    *,
    after: int,
    through: int,
) -> tuple[_Event, ...]:
    total = _serial_distance(through, after)
    selected = [
        event
        for event in events.values()
        if 0 < _serial_distance(event.serial, after) <= total
    ]
    return tuple(
        sorted(
            selected,
            key=lambda event: _serial_distance(event.serial, after),
        )
    )


def build_report(path: Path) -> dict[str, object]:
    row_counts: Counter[str] = Counter()
    batch_statuses: Counter[str] = Counter()
    issue_statuses: Counter[str] = Counter()
    issue_advances: Counter[str] = Counter()
    manager_deltas: Counter[str] = Counter()
    replay_deltas: Counter[str] = Counter()
    engine_flags: Counter[str] = Counter()
    callback_pairs: Counter[str] = Counter()
    outcome_counts: Counter[str] = Counter()
    config_statuses: list[str] = []
    summary_reasons: list[str] = []
    summary_hits: list[int] = []
    events: dict[int, _Event] = {}
    writes: list[_Write] = []
    decision_capture_checkpoints: list[tuple[int, int]] = []
    capture_last_serial: int | None = None
    baseline_count = 0
    final_count = 0
    decision_count = 0
    no_write_count = 0
    unknown_batch_count = 0
    issue_unknown_count = 0
    cleanup_error_count = 0
    missing_decision_probe_count = 0
    bomb_decision_count = 0

    def accept_batch(batch: _Batch, *, line: int) -> None:
        nonlocal capture_last_serial, unknown_batch_count
        batch_statuses[batch.status] += 1
        if batch.status in {
            "read_error",
            "race_unknown",
            "overflow_or_trace_truncation",
        }:
            unknown_batch_count += 1
        if (
            capture_last_serial is not None
            and batch.previous_serial is not None
            and batch.previous_serial != capture_last_serial
        ):
            raise ValueError(
                f"line {line}: batch previous serial does not continue "
                f"{capture_last_serial}"
            )
        for event in batch.events:
            retained = events.get(event.serial)
            if retained is not None and retained != event:
                raise ValueError(
                    f"line {line}: conflicting duplicate event serial {event.serial}"
                )
            events[event.serial] = event
        if batch.observed_serial is not None:
            capture_last_serial = batch.observed_serial

    for line, row in _records(path):
        kind_value = row.get("kind")
        kind = kind_value if isinstance(kind_value, str) else "<invalid>"
        row_counts[kind] += 1
        if kind == "controller_config":
            probe = _object(
                row.get("priority17_publication_probe"),
                line=line,
                field="controller_config.priority17_publication_probe",
            )
            status = probe.get("status")
            if not isinstance(status, str):
                raise ValueError(
                    f"line {line}: installation status is invalid"
                )
            if probe.get("action_authority") is not False:
                raise ValueError(
                    f"line {line}: installed probe claims authority"
                )
            config_statuses.append(status)
        elif kind == "priority17_publication_probe_baseline":
            baseline_count += 1
            accept_batch(
                _batch(row, line=line, source_kind="baseline"),
                line=line,
            )
        elif kind == "decision":
            decision_count += 1
            if row.get("bomb") is True:
                bomb_decision_count += 1
            write_required, previous, target, path_masks = _dispatch_path(
                row,
                line=line,
            )
            probe_value = row.get("priority17_publication_probe")
            if not isinstance(probe_value, dict):
                missing_decision_probe_count += 1
                continue
            capture = _batch(
                probe_value.get("capture"),
                line=line,
                source_kind="decision_capture",
            )
            accept_batch(capture, line=line)
            if capture.observed_serial is not None:
                decision_capture_checkpoints.append(
                    (decision_count, capture.observed_serial)
                )
            issue = _object(
                probe_value.get("issue"),
                line=line,
                field="priority17_publication_probe.issue",
            )
            status = issue.get("status")
            if not isinstance(status, str):
                raise ValueError(
                    f"line {line}: issue bracket status is invalid"
                )
            issue_statuses[status] += 1
            pre = _optional_integer(
                issue.get("pre_dispatch_serial"),
                line=line,
                field="pre_dispatch_serial",
            )
            post = _optional_integer(
                issue.get("post_dispatch_serial"),
                line=line,
                field="post_dispatch_serial",
            )
            reported_advance = issue.get("serial_advance_during_dispatch")
            if write_required:
                if status == "complete":
                    if pre is None or post is None:
                        raise ValueError(
                            f"line {line}: complete issue bracket lacks serials"
                        )
                    advance = _serial_distance(post, pre)
                    if reported_advance != advance:
                        raise ValueError(
                            f"line {line}: issue serial advance is inconsistent"
                        )
                    issue_advances[str(advance)] += 1
                elif status == "read_error":
                    issue_unknown_count += 1
                else:
                    raise ValueError(
                        f"line {line}: real write has bracket status {status!r}"
                    )
                writes.append(
                    _Write(
                        ordinal=len(writes) + 1,
                        decision_ordinal=decision_count,
                        line=line,
                        frame=_integer(
                            row.get("frame"), line=line, field="frame"
                        ),
                        stage_route_index=_integer(
                            row.get("stage_route_index"),
                            line=line,
                            field="stage_route_index",
                        ),
                        previous_mask=previous,
                        target_mask=target,
                        mask_path=path_masks,
                        pre_serial=pre,
                        post_serial=post,
                        bracket_status=status,
                    )
                )
            else:
                no_write_count += 1
                if status != "no_write" or pre is not None or post is not None:
                    raise ValueError(f"line {line}: invalid no-write bracket")
        elif kind == "priority17_publication_probe_final":
            final_count += 1
            accept_batch(
                _batch(row, line=line, source_kind="final_after_key_release"),
                line=line,
            )
        elif kind == "priority17_publication_probe_cleanup_error":
            cleanup_error_count += 1
        elif kind == "summary":
            reason = row.get("termination_reason")
            if isinstance(reason, str):
                summary_reasons.append(reason)
            summary_hits.append(
                _integer(row.get("hit_count"), line=line, field="hit_count")
            )

    ordered_events = sorted(
        events.values(),
        key=lambda event: (
            _serial_distance(event.serial, min(events)) if events else 0
        ),
    )
    for event in ordered_events:
        engine_flags[f"0x{event.engine_flags:08x}"] += 1
        callback_pairs[
            f"0x{event.previous_mask:02x}->0x{event.current_mask:02x}"
        ] += 1
    for previous_event, event in zip(ordered_events, ordered_events[1:]):
        if _serial_distance(event.serial, previous_event.serial) != 1:
            continue
        manager_deltas[
            str(event.manager_frame - previous_event.manager_frame)
        ] += 1
        replay_deltas[
            str(
                (
                    event.replay_frame_counter
                    - previous_event.replay_frame_counter
                )
                & 0xFFFFFFFF
            )
        ] += 1

    retained_intermediate_witnesses: list[dict[str, object]] = []
    callbacks_during_dispatch = 0
    writes_with_callback_during_dispatch = 0
    exact_dispatch_intervals = 0
    incomplete_dispatch_intervals = 0
    native_intermediate_witness_count = 0
    final_observed_count = 0
    final_publication_steps: Counter[str] = Counter()
    final_manager_deltas: Counter[str] = Counter()

    for index, write in enumerate(writes):
        if (
            write.bracket_status == "complete"
            and write.pre_serial is not None
            and write.post_serial is not None
        ):
            during = _events_in_interval(
                events,
                after=write.pre_serial,
                through=write.post_serial,
            )
            advance = _serial_distance(write.post_serial, write.pre_serial)
            dispatch_interval_exact = len(during) == advance
            exact_dispatch_intervals += int(dispatch_interval_exact)
            incomplete_dispatch_intervals += int(not dispatch_interval_exact)
            callbacks_during_dispatch += advance
            writes_with_callback_during_dispatch += int(advance > 0)
            for event in during:
                if event.current_mask not in write.mask_path[1:-1]:
                    continue
                native_intermediate_witness_count += 1
                if (
                    len(retained_intermediate_witnesses)
                    < _MAX_RETAINED_WITNESSES
                ):
                    retained_intermediate_witnesses.append(
                        {
                            "transaction_ordinal": write.ordinal,
                            "issue_line": write.line,
                            "issue_frame": write.frame,
                            "stage_route_index": write.stage_route_index,
                            "mask_path": list(write.mask_path),
                            "edge_position": (
                                f"{write.mask_path.index(event.current_mask)}/"
                                f"{len(write.mask_path) - 1}"
                            ),
                            "event": event.compact_record(),
                            "classification": (
                                "observed_native_callback_exit_during_dispatch"
                            ),
                        }
                    )

        interval_end: int | None = None
        outcome_suffix = "trace_end"
        if index + 1 < len(writes):
            next_write = writes[index + 1]
            if next_write.pre_serial is not None:
                interval_end = next_write.pre_serial
                outcome_suffix = "replacement"
        if interval_end is None:
            later_checkpoints = [
                serial
                for ordinal, serial in decision_capture_checkpoints
                if ordinal > write.decision_ordinal
            ]
            if later_checkpoints:
                interval_end = later_checkpoints[-1]
        if write.pre_serial is None or interval_end is None:
            outcome_counts["unknown_or_right_censored"] += 1
            continue
        candidates = _events_in_interval(
            events,
            after=write.pre_serial,
            through=interval_end,
        )
        first_final = next(
            (
                event
                for event in candidates
                if event.current_mask == write.target_mask
            ),
            None,
        )
        if first_final is not None:
            outcome_counts[f"final_observed_before_{outcome_suffix}"] += 1
            final_observed_count += 1
            final_publication_steps[
                str(_serial_distance(first_final.serial, write.pre_serial))
            ] += 1
            final_manager_deltas[
                str(first_final.manager_frame - write.frame)
            ] += 1
        elif len(candidates) == _serial_distance(
            interval_end, write.pre_serial
        ):
            outcome_counts[f"final_not_observed_before_{outcome_suffix}"] += 1
        else:
            outcome_counts["unknown_or_right_censored"] += 1

    integrity_errors = {
        "installed_config_missing_or_ambiguous": int(
            config_statuses != ["installed"]
        ),
        "baseline_missing_or_ambiguous": int(baseline_count != 1),
        "final_drain_missing_or_ambiguous": int(final_count != 1),
        "decision_count_zero": int(decision_count == 0),
        "real_write_count_zero": int(not writes),
        "callback_event_count_zero": int(not events),
        "decision_probe_record_missing": missing_decision_probe_count,
        "unknown_or_overflow_capture_batches": unknown_batch_count,
        "unknown_issue_brackets": issue_unknown_count,
        "cleanup_errors": cleanup_error_count,
        "bomb_decisions": bomb_decision_count,
        "route_complete_summary_missing": int(
            not summary_reasons or summary_reasons[-1] != "route_complete"
        ),
    }
    return {
        "schema": REPORT_SCHEMA,
        "source": {
            "path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        },
        "scope": {
            "classification": (
                "observed_physical_native_priority17_callback_exit_instrumentation"
            ),
            "instrumentation": (
                "default-off reversible shipped-code detour with bounded ring"
            ),
            "perturbation_free": False,
            "callback_serial_coordinate": (
                "monotone callback-exit publication count; not manager-frame "
                "delay and not yet a live pending-delay adapter"
            ),
            "issue_bracket_coordinate": (
                "serial immediately before and after one ordered physical "
                "complete-mask dispatch"
            ),
            "negative_claim_rule": (
                "absence is meaningful only when every serial in the audited "
                "interval is retained"
            ),
            "final_drain_phase": (
                "after injected keys are released; its events are excluded "
                "from last-transaction pre-release conclusions unless a later "
                "decision checkpoint already bounds them"
            ),
            "manager_frame_universal_physical_clock_authority": False,
            "ordered_oracle_publication_deadline_adapter_ready": False,
            "action_authority": False,
            "hard_survival_authority": False,
        },
        "rows": {
            "counts": dict(sorted(row_counts.items())),
            "decision": decision_count,
            "summary_termination_reasons": summary_reasons,
            "summary_hit_counts": summary_hits,
            "installation_statuses": config_statuses,
        },
        "capture": {
            "batch_status_counts": dict(sorted(batch_statuses.items())),
            "unknown_or_overflow_batches": unknown_batch_count,
            "callback_events": len(events),
            "first_serial": ordered_events[0].serial
            if ordered_events
            else None,
            "last_serial": ordered_events[-1].serial
            if ordered_events
            else None,
            "engine_flag_counts": dict(sorted(engine_flags.items())),
            "callback_previous_current_counts": dict(
                sorted(callback_pairs.items())
            ),
        },
        "callback_clock": {
            "consecutive_manager_frame_delta_counts": dict(
                sorted(manager_deltas.items(), key=lambda item: int(item[0]))
            ),
            "same_manager_frame_publication_edges": manager_deltas["0"],
            "consecutive_replay_counter_delta_counts": dict(
                sorted(replay_deltas.items(), key=lambda item: int(item[0]))
            ),
            "interpretation": (
                "same-manager serial advances directly witness callback "
                "publication while enemy_manager_frame is unchanged"
            ),
        },
        "transactions": {
            "real_writes": len(writes),
            "no_writes": no_write_count,
            "multiedge_writes": sum(
                len(write.mask_path) > 2 for write in writes
            ),
            "issue_bracket_status_counts": dict(
                sorted(issue_statuses.items())
            ),
            "serial_advance_during_dispatch_counts": dict(
                sorted(issue_advances.items(), key=lambda item: int(item[0]))
            ),
            "callbacks_during_dispatch": callbacks_during_dispatch,
            "writes_with_callback_during_dispatch": (
                writes_with_callback_during_dispatch
            ),
            "exact_dispatch_intervals": exact_dispatch_intervals,
            "incomplete_dispatch_intervals": incomplete_dispatch_intervals,
            "native_intermediate_callback_exit_witnesses": (
                native_intermediate_witness_count
            ),
            "final_observed_count": final_observed_count,
            "outcome_counts": dict(sorted(outcome_counts.items())),
            "first_final_publication_step_counts": dict(
                sorted(
                    final_publication_steps.items(),
                    key=lambda item: int(item[0]),
                )
            ),
            "first_final_manager_delta_counts": dict(
                sorted(
                    final_manager_deltas.items(), key=lambda item: int(item[0])
                )
            ),
        },
        "retained_native_intermediate_witnesses": (
            retained_intermediate_witnesses
        ),
        "integrity": {
            "passed": not any(integrity_errors.values()),
            "errors": integrity_errors,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    report = build_report(args.trace)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if report["integrity"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
