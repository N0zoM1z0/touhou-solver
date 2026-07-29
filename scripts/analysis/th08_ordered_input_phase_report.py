#!/usr/bin/env python3
"""Audit what a TH08 trace can identify about ordered input publication."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from th08_runtime.game_state import SUPPORTED_INPUT_MASK
from touhou_control.ordered_input_transaction_oracle import ordered_mask_path


REPORT_SCHEMA = "th08-ordered-input-phase-report-v1"
BOMB_INPUT_BIT = 0x02
_MAX_RETAINED = 32
_MAX_AUDITED_MANAGER_GAP = 64


@dataclass(frozen=True)
class _Dispatch:
    previous_mask: int
    target_mask: int
    transition_masks: tuple[int, ...]
    write_required: bool


@dataclass(frozen=True)
class _Decision:
    line: int
    frame: int
    snapshot_frame: int
    action_lag: int
    gameplay_epoch: int
    stage_route_index: int
    raw_mask: int
    current_mask: int
    previous_mask: int
    coherent_current_mask: int | None
    selected_mask: int
    delay_support: tuple[int, ...]
    dispatch: _Dispatch
    pending_mask: int | None
    remaining_delay_support: tuple[int, ...]


@dataclass
class _Transaction:
    ordinal: int
    issue: _Decision
    final_observation: _Decision | None = None
    intermediate_observations: int = 0
    strong_edges: int = 0
    weak_edges: int = 0


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
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"line {line_number}: invalid JSON: {error}"
                ) from error
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number}: trace row is not an object")
            yield line_number, value


def _dict(
    value: object,
    *,
    line_number: int,
    field: str,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"line {line_number}: {field} must be an object")
    return value


def _integer(value: object, *, line_number: int, field: str) -> int:
    if type(value) is not int:
        raise ValueError(f"line {line_number}: {field} must be an integer")
    return value


def _boolean(value: object, *, line_number: int, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"line {line_number}: {field} must be a Boolean")
    return value


def _mask(value: object, *, line_number: int, field: str) -> int:
    result = _integer(value, line_number=line_number, field=field)
    if result < 0 or result & ~SUPPORTED_INPUT_MASK:
        raise ValueError(f"line {line_number}: {field} contains unsupported input bits")
    return result


def _support(
    value: object,
    *,
    line_number: int,
    field: str,
    allow_empty: bool,
) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise ValueError(f"line {line_number}: {field} must be a list")
    result = tuple(
        _integer(item, line_number=line_number, field=f"{field}[]") for item in value
    )
    minimum = 0 if allow_empty else 1
    if (
        (not result and not allow_empty)
        or tuple(sorted(set(result))) != result
        or (result and result[0] < minimum)
    ):
        raise ValueError(
            f"line {line_number}: {field} must be sorted, unique, "
            f"and {'nonnegative' if allow_empty else 'positive'}"
        )
    return result


def _transition_masks(
    previous_mask: int,
    transitions: object,
    *,
    line_number: int,
) -> tuple[int, ...]:
    if not isinstance(transitions, list):
        raise ValueError(
            f"line {line_number}: input_dispatch.transitions must be a list"
        )
    active = previous_mask
    masks: list[int] = []
    for index, raw_transition in enumerate(transitions):
        if not isinstance(raw_transition, list) or len(raw_transition) != 2:
            raise ValueError(f"line {line_number}: input transition {index} is invalid")
        bit = _mask(
            raw_transition[0],
            line_number=line_number,
            field=f"input transition {index} bit",
        )
        pressed = _boolean(
            raw_transition[1],
            line_number=line_number,
            field=f"input transition {index} pressed",
        )
        if bit == 0 or bit & (bit - 1):
            raise ValueError(
                f"line {line_number}: input transition {index} bit "
                "must be one supported bit"
            )
        active = active | bit if pressed else active & ~bit
        masks.append(active)
    return tuple(masks)


def _coherent_current(
    row: dict[str, object],
    *,
    line_number: int,
) -> int | None:
    capture = row.get("player_enemy_mode_capture")
    if not isinstance(capture, dict):
        return None
    if (
        capture.get("role") != "diagnostic_shadow"
        or capture.get("action_authority") is not False
        or capture.get("coherent") is not True
        or capture.get("status") != "coherent"
    ):
        return None
    before = _dict(
        capture.get("player_before"),
        line_number=line_number,
        field="player_enemy_mode_capture.player_before",
    )
    after = _dict(
        capture.get("player_after"),
        line_number=line_number,
        field="player_enemy_mode_capture.player_after",
    )
    before_mask = _mask(
        before.get("input_current"),
        line_number=line_number,
        field="player_before.input_current",
    )
    after_mask = _mask(
        after.get("input_current"),
        line_number=line_number,
        field="player_after.input_current",
    )
    return before_mask if before_mask == after_mask else None


def _decision(
    row: dict[str, object],
    *,
    line_number: int,
) -> _Decision:
    frame = _integer(row.get("frame"), line_number=line_number, field="frame")
    snapshot_frame = _integer(
        row.get("snapshot_frame"),
        line_number=line_number,
        field="snapshot_frame",
    )
    action_lag = _integer(
        row.get("action_lag"),
        line_number=line_number,
        field="action_lag",
    )
    if snapshot_frame > frame or action_lag != frame - snapshot_frame:
        raise ValueError(
            f"line {line_number}: snapshot/issue frame alignment is invalid"
        )

    snapshot = _dict(
        row.get("input_snapshot"),
        line_number=line_number,
        field="input_snapshot",
    )
    raw_mask = _mask(
        snapshot.get("raw"),
        line_number=line_number,
        field="input_snapshot.raw",
    )
    current_mask = _mask(
        snapshot.get("current"),
        line_number=line_number,
        field="input_snapshot.current",
    )
    previous_mask = _mask(
        snapshot.get("previous"),
        line_number=line_number,
        field="input_snapshot.previous",
    )
    selected_mask = _mask(
        row.get("mask"),
        line_number=line_number,
        field="mask",
    )
    delay_support = _support(
        row.get("control_delay_candidates"),
        line_number=line_number,
        field="control_delay_candidates",
        allow_empty=False,
    )

    raw_dispatch = _dict(
        row.get("input_dispatch"),
        line_number=line_number,
        field="input_dispatch",
    )
    dispatch_previous = _mask(
        raw_dispatch.get("previous_mask"),
        line_number=line_number,
        field="input_dispatch.previous_mask",
    )
    dispatch_target = _mask(
        raw_dispatch.get("target_mask"),
        line_number=line_number,
        field="input_dispatch.target_mask",
    )
    write_required = _boolean(
        raw_dispatch.get("write_required"),
        line_number=line_number,
        field="input_dispatch.write_required",
    )
    masks = _transition_masks(
        dispatch_previous,
        raw_dispatch.get("transitions"),
        line_number=line_number,
    )
    expected_masks = (
        ordered_mask_path(
            dispatch_previous,
            dispatch_target,
            supported_mask=SUPPORTED_INPUT_MASK,
            forbidden_mask=BOMB_INPUT_BIT,
        )
        if write_required
        else ()
    )
    if (
        dispatch_target != selected_mask
        or write_required != (dispatch_previous != dispatch_target)
        or masks != expected_masks
        or _integer(
            raw_dispatch.get("transition_count"),
            line_number=line_number,
            field="input_dispatch.transition_count",
        )
        != len(masks)
    ):
        raise ValueError(
            f"line {line_number}: input dispatch is not the declared "
            "ordered complete-mask transaction"
        )
    if (
        selected_mask & BOMB_INPUT_BIT
        or raw_mask & BOMB_INPUT_BIT
        or current_mask & BOMB_INPUT_BIT
        or previous_mask & BOMB_INPUT_BIT
    ):
        raise ValueError(f"line {line_number}: Bomb input is outside audit scope")

    pipeline = _dict(
        row.get("local_pipeline_root"),
        line_number=line_number,
        field="local_pipeline_root",
    )
    pending_value = pipeline.get("pending_mask")
    pending_mask = (
        None
        if pending_value is None
        else _mask(
            pending_value,
            line_number=line_number,
            field="local_pipeline_root.pending_mask",
        )
    )
    remaining = _support(
        pipeline.get("remaining_delay_support"),
        line_number=line_number,
        field="local_pipeline_root.remaining_delay_support",
        allow_empty=True,
    )

    return _Decision(
        line=line_number,
        frame=frame,
        snapshot_frame=snapshot_frame,
        action_lag=action_lag,
        gameplay_epoch=_integer(
            row.get("gameplay_epoch"),
            line_number=line_number,
            field="gameplay_epoch",
        ),
        stage_route_index=_integer(
            row.get("stage_route_index"),
            line_number=line_number,
            field="stage_route_index",
        ),
        raw_mask=raw_mask,
        current_mask=current_mask,
        previous_mask=previous_mask,
        coherent_current_mask=_coherent_current(
            row,
            line_number=line_number,
        ),
        selected_mask=selected_mask,
        delay_support=delay_support,
        dispatch=_Dispatch(
            previous_mask=dispatch_previous,
            target_mask=dispatch_target,
            transition_masks=masks,
            write_required=write_required,
        ),
        pending_mask=pending_mask,
        remaining_delay_support=remaining,
    )


def _edge_index(
    transaction: _Transaction,
    observation: _Decision,
) -> int | None:
    path = (
        transaction.issue.dispatch.previous_mask,
        *transaction.issue.dispatch.transition_masks,
    )
    pair = (observation.previous_mask, observation.current_mask)
    for index in range(len(path) - 1):
        if pair == path[index : index + 2]:
            return index
    return None


def _conditioned_remaining_at_issue(issue: _Decision) -> tuple[int, ...]:
    remaining = tuple(
        delay - issue.action_lag
        for delay in issue.delay_support
        if delay > issue.action_lag
    )
    # This mirrors AdaptiveControlDelay.pending_estimate's conservative
    # overdue carry. It remains an estimator coordinate, not a native
    # priority-17 callback deadline.
    return remaining or (1,)


def _transaction_summary(
    transaction: _Transaction,
    *,
    outcome: str,
) -> dict[str, object]:
    issue = transaction.issue
    final = transaction.final_observation
    result: dict[str, object] = {
        "ordinal": transaction.ordinal,
        "issue_line": issue.line,
        "source_snapshot_frame": issue.snapshot_frame,
        "issue_manager_frame": issue.frame,
        "action_lag": issue.action_lag,
        "dispatch_previous_mask": issue.dispatch.previous_mask,
        "target_mask": issue.dispatch.target_mask,
        "transition_masks": list(issue.dispatch.transition_masks),
        "issued_snapshot_to_visible_support": list(issue.delay_support),
        "conditioned_manager_remaining_at_issue": list(
            _conditioned_remaining_at_issue(issue)
        ),
        "outcome": outcome,
        "intermediate_observation_count": transaction.intermediate_observations,
        "strong_publication_edge_count": transaction.strong_edges,
        "weak_sequential_edge_count": transaction.weak_edges,
    }
    if final is not None:
        result.update(
            {
                "first_final_observation_line": final.line,
                "first_final_observation_snapshot_frame": final.snapshot_frame,
                "source_to_first_final_observation": (
                    final.snapshot_frame - issue.snapshot_frame
                ),
                "issue_to_first_final_observation": (
                    final.snapshot_frame - issue.frame
                ),
                "first_final_observation_within_issued_support": (
                    final.snapshot_frame - issue.snapshot_frame in issue.delay_support
                ),
            }
        )
    return result


def build_report(path: Path) -> dict[str, object]:
    """Build a source-hashed publication-edge and deadline audit."""

    row_counts: Counter[str] = Counter()
    transaction_outcomes: Counter[str] = Counter()
    edge_positions: Counter[str] = Counter()
    estimator_remaining_supports: Counter[str] = Counter()
    first_final_issue_deltas: Counter[str] = Counter()
    first_final_source_deltas: Counter[str] = Counter()
    retained_transactions: list[dict[str, object]] = []
    retained_strong_edges: list[dict[str, object]] = []
    retained_weak_edges: list[dict[str, object]] = []
    canonical_ce0193_edge: dict[str, object] | None = None
    active: _Transaction | None = None
    transaction_ordinal = 0
    decision_count = 0
    real_write_count = 0
    no_write_count = 0
    multiedge_write_count = 0
    coherent_current_count = 0
    coherent_snapshot_agreement_count = 0
    observed_intermediate_count = 0
    strong_edge_count = 0
    weak_edge_count = 0
    changed_pair_outside_active_path_count = 0
    final_observed_outside_support_count = 0
    summary_termination_reasons: list[str] = []

    def finish(transaction: _Transaction, *, outcome: str) -> None:
        nonlocal final_observed_outside_support_count
        transaction_outcomes[outcome] += 1
        summary = _transaction_summary(transaction, outcome=outcome)
        if transaction.final_observation is not None:
            source_delta = int(summary["source_to_first_final_observation"])
            issue_delta = int(summary["issue_to_first_final_observation"])
            first_final_source_deltas[str(source_delta)] += 1
            first_final_issue_deltas[str(issue_delta)] += 1
            if not summary["first_final_observation_within_issued_support"]:
                final_observed_outside_support_count += 1
        if len(retained_transactions) < _MAX_RETAINED and (
            transaction.intermediate_observations
            or transaction.strong_edges
            or outcome != "final_observed_before_replacement"
        ):
            retained_transactions.append(summary)

    for line_number, row in _records(path):
        kind = row.get("kind")
        kind_label = kind if isinstance(kind, str) else "missing"
        row_counts[kind_label] += 1
        if kind == "summary":
            reason = row.get("termination_reason")
            if isinstance(reason, str):
                summary_termination_reasons.append(reason)
            continue
        if kind in {
            "action_epoch_discontinuity",
            "sensor_epoch_discontinuity",
            "scene_inactive",
        }:
            if active is not None:
                finish(active, outcome="right_censored_by_trace_discontinuity")
                active = None
            continue
        if kind != "decision":
            continue

        decision_count += 1
        observation = _decision(row, line_number=line_number)
        if active is not None and (
            observation.gameplay_epoch != active.issue.gameplay_epoch
            or observation.stage_route_index != active.issue.stage_route_index
        ):
            finish(active, outcome="right_censored_by_epoch_or_stage_change")
            active = None
        if active is not None and not (
            0
            <= observation.snapshot_frame - active.issue.frame
            <= _MAX_AUDITED_MANAGER_GAP
        ):
            finish(active, outcome="right_censored_by_manager_gap")
            active = None
        if observation.coherent_current_mask is not None:
            coherent_current_count += 1
            coherent_snapshot_agreement_count += int(
                observation.coherent_current_mask == observation.current_mask
            )

        if active is not None and active.final_observation is None:
            transaction_path = active.issue.dispatch.transition_masks
            if observation.current_mask in transaction_path[:-1]:
                active.intermediate_observations += 1
                observed_intermediate_count += 1
            if observation.current_mask == active.issue.dispatch.target_mask:
                active.final_observation = observation

            if observation.previous_mask != observation.current_mask:
                edge_index = _edge_index(active, observation)
                if edge_index is None:
                    changed_pair_outside_active_path_count += 1
                else:
                    edge_label = (
                        f"{edge_index + 1}/"
                        f"{len(active.issue.dispatch.transition_masks)}"
                    )
                    edge_positions[edge_label] += 1
                    edge = {
                        "transaction_ordinal": active.ordinal,
                        "issue_line": active.issue.line,
                        "observation_line": observation.line,
                        "issue_manager_frame": active.issue.frame,
                        "observation_snapshot_frame": observation.snapshot_frame,
                        "previous_mask": observation.previous_mask,
                        "current_mask": observation.current_mask,
                        "raw_mask": observation.raw_mask,
                        "edge_position": edge_label,
                        "coherent_capture_current_mask": (
                            observation.coherent_current_mask
                        ),
                    }
                    strong = (
                        observation.raw_mask == observation.current_mask
                        and observation.coherent_current_mask
                        == observation.current_mask
                    )
                    if strong:
                        active.strong_edges += 1
                        strong_edge_count += 1
                        if (
                            canonical_ce0193_edge is None
                            and active.issue.dispatch.previous_mask == 0x65
                            and active.issue.dispatch.target_mask == 0x41
                            and observation.previous_mask == 0x65
                            and observation.current_mask == 0x61
                        ):
                            canonical_ce0193_edge = edge
                        if len(retained_strong_edges) < _MAX_RETAINED:
                            retained_strong_edges.append(edge)
                    else:
                        active.weak_edges += 1
                        weak_edge_count += 1
                        if len(retained_weak_edges) < _MAX_RETAINED:
                            retained_weak_edges.append(edge)

        dispatch = observation.dispatch
        if dispatch.write_required:
            if active is not None:
                finish(
                    active,
                    outcome=(
                        "final_observed_before_replacement"
                        if active.final_observation is not None
                        else "right_censored_by_real_write"
                    ),
                )
            transaction_ordinal += 1
            real_write_count += 1
            multiedge_write_count += int(len(dispatch.transition_masks) > 1)
            active = _Transaction(
                ordinal=transaction_ordinal,
                issue=observation,
            )
            estimator_remaining_supports[
                ",".join(
                    str(value) for value in _conditioned_remaining_at_issue(observation)
                )
            ] += 1
        else:
            no_write_count += 1
            if dispatch.transition_masks:
                raise AssertionError("validated no-write has transitions")

    if active is not None:
        finish(
            active,
            outcome=(
                "final_observed_before_trace_end"
                if active.final_observation is not None
                else "right_censored_by_trace_end"
            ),
        )

    integrity_errors = {
        "decision_count_zero": int(decision_count == 0),
        "real_write_count_zero": int(real_write_count == 0),
        "route_complete_summary_missing": int(
            not summary_termination_reasons
            or summary_termination_reasons[-1] != "route_complete"
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
                "observed_physical_posthoc_ordered_input_publication_phase"
            ),
            "observation_order": (
                "each decision input_snapshot is read before that row's "
                "issue-time enemy-manager frame observation and physical "
                "dispatch"
            ),
            "input_snapshot_atomicity": (
                "raw/current/previous are sequential process-memory reads, "
                "not one native atomic snapshot"
            ),
            "corroborated_sequential_publication_edge_contract": (
                "input_snapshot.previous->current is one consecutive edge of "
                "the currently outstanding ordered dispatch, raw equals "
                "current, and the later manager-frame-coherent diagnostic "
                "capture holds the same current mask"
            ),
            "issued_delay_support_contract": (
                "AdaptiveControlDelay snapshot-to-visible-input estimator "
                "coordinate; pending remaining support subtracts "
                "snapshot age"
            ),
            "first_final_observation_contract": (
                "first later decision capture that sees the final target "
                "before replacement; it is an observation upper bound, not "
                "the exact priority-17 publication callback"
            ),
            "audited_manager_gap": (
                f"0..{_MAX_AUDITED_MANAGER_GAP}; larger or negative gaps are "
                "censored rather than interpreted as publication latency"
            ),
            "manager_frame_universal_physical_clock_authority": False,
            "ordered_oracle_publication_deadline_adapter_ready": False,
            "action_authority": False,
            "hard_survival_authority": False,
        },
        "rows": {
            "counts": dict(sorted(row_counts.items())),
            "decision": decision_count,
            "coherent_later_current": coherent_current_count,
            "coherent_later_current_agrees_with_sequential_snapshot": (
                coherent_snapshot_agreement_count
            ),
            "summary_termination_reasons": summary_termination_reasons,
        },
        "transactions": {
            "real_writes": real_write_count,
            "no_writes": no_write_count,
            "multiedge_writes": multiedge_write_count,
            "outcome_counts": dict(sorted(transaction_outcomes.items())),
            "observed_intermediate_masks": observed_intermediate_count,
            "first_final_source_delta_counts": dict(
                sorted(
                    first_final_source_deltas.items(),
                    key=lambda item: int(item[0]),
                )
            ),
            "first_final_issue_delta_counts": dict(
                sorted(
                    first_final_issue_deltas.items(),
                    key=lambda item: int(item[0]),
                )
            ),
            "first_final_observed_outside_issued_support": (
                final_observed_outside_support_count
            ),
        },
        "publication_edges": {
            "native_atomic_edge_witnesses": 0,
            "corroborated_sequential_edge_witnesses": strong_edge_count,
            "uncorroborated_sequential_matches": weak_edge_count,
            "changed_pairs_outside_active_transaction_path": (
                changed_pair_outside_active_path_count
            ),
            "edge_position_counts": dict(sorted(edge_positions.items())),
            "canonical_ce0193_edge": canonical_ce0193_edge,
        },
        "estimator_coordinate": {
            "conditioned_remaining_at_issue_counts": dict(
                sorted(estimator_remaining_supports.items())
            ),
            "native_priority17_callback_deadline_identifiable": False,
            "reason": (
                "the trace has no priority-17 callback serial, issue-adjacent "
                "native publication marker, or atomic input triple; "
                "enemy-manager frames and asynchronous decision captures "
                "cannot recover skipped callback count"
            ),
        },
        "required_bounded_probe": {
            "status": "not_present_in_source_trace",
            "minimum_native_event": (
                "monotone priority-17 publication serial plus raw, old "
                "current, new current, and contemporaneous manager frame"
            ),
            "minimum_issue_event": (
                "pre-dispatch and post-dispatch publication serial bounds "
                "plus ordered edge/transaction identity"
            ),
            "runtime_contract": (
                "default-off trace-only bounded ring; overflow or read failure "
                "marks the interval unknown and must not stop a stage"
            ),
        },
        "retained_transactions": retained_transactions,
        "retained_strong_publication_edges": retained_strong_edges,
        "retained_weak_sequential_edges": retained_weak_edges,
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
