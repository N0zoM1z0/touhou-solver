#!/usr/bin/env python3
"""Audit canonical pipeline identity and native pickup continuity in traces."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SCHEMA = "th08-pipeline-pickup-audit-v1"
SHADOW_ROLE = "shadow_no_action_authority"


@dataclass(frozen=True)
class _Decision:
    index: int
    row: dict[str, object]
    frame: int
    snapshot_frame: int
    gameplay_epoch: int
    stage_route_index: int
    root: dict[str, object]
    dispatch: dict[str, object]


def _int(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} is not an integer")
    return value


def _bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} is not a Boolean")
    return value


def _mask(value: object, *, name: str, supported_mask: int) -> int:
    result = _int(value, name=name)
    if result < 0 or result & ~supported_mask:
        raise ValueError(f"{name} contains unsupported bits")
    return result


def _support(value: object, *, name: str) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} is not an array")
    result = tuple(_int(item, name=name) for item in value)
    if (
        any(item <= 0 for item in result)
        or result != tuple(sorted(set(result)))
    ):
        raise ValueError(f"{name} must be sorted, unique, and positive")
    return result


def _ordered_transitions(
    previous_mask: int,
    target_mask: int,
) -> tuple[tuple[int, bool], ...]:
    changed = previous_mask ^ target_mask
    releases = tuple(
        (1 << index, False)
        for index in range(16)
        if changed & previous_mask & (1 << index)
    )
    presses = tuple(
        (1 << index, True)
        for index in range(16)
        if changed & target_mask & (1 << index)
    )
    return releases + presses


def _transition_masks(
    previous_mask: int,
    transitions: tuple[tuple[int, bool], ...],
) -> tuple[int, ...]:
    mask = previous_mask
    masks: list[int] = []
    for bit, pressed in transitions:
        mask = (mask | bit) if pressed else (mask & ~bit)
        masks.append(mask)
    return tuple(masks)


def _identity_digest(identity: dict[str, object]) -> str:
    payload = {
        key: value
        for key, value in identity.items()
        if key not in {"sha256", "role"}
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _record_failure(
    failures: list[dict[str, object]],
    *,
    decision: _Decision,
    code: str,
    detail: str,
) -> None:
    failures.append(
        {
            "decision_index": decision.index,
            "frame": decision.frame,
            "snapshot_frame": decision.snapshot_frame,
            "code": code,
            "detail": detail,
        }
    )


def _parse_decisions(
    rows: Iterable[dict[str, object]],
) -> tuple[list[_Decision], int]:
    decisions: list[_Decision] = []
    skipped = 0
    for row in rows:
        if row.get("kind") != "decision":
            skipped += 1
            continue
        index = len(decisions)
        root = row.get("local_pipeline_root")
        dispatch = row.get("input_dispatch")
        if not isinstance(root, dict) or not isinstance(dispatch, dict):
            raise ValueError(
                f"decision {index} lacks G1 root or dispatch telemetry"
            )
        decisions.append(
            _Decision(
                index=index,
                row=row,
                frame=_int(row.get("frame"), name="decision frame"),
                snapshot_frame=_int(
                    row.get("snapshot_frame"),
                    name="snapshot frame",
                ),
                gameplay_epoch=_int(
                    row.get("gameplay_epoch"),
                    name="gameplay epoch",
                ),
                stage_route_index=_int(
                    row.get("stage_route_index"),
                    name="stage route index",
                ),
                root=root,
                dispatch=dispatch,
            )
        )
    return decisions, skipped


def _audit_root(
    decision: _Decision,
    *,
    supported_mask: int,
    counts: dict[str, int],
    failures: list[dict[str, object]],
) -> None:
    root = decision.root
    try:
        if root.get("role") != SHADOW_ROLE:
            raise ValueError("root role is not shadow-only")
        active = _mask(
            root.get("active_mask"),
            name="active mask",
            supported_mask=supported_mask,
        )
        held = _mask(
            root.get("held_desired_mask"),
            name="held desired mask",
            supported_mask=supported_mask,
        )
        pending_raw = root.get("pending_mask")
        pending = (
            None
            if pending_raw is None
            else _mask(
                pending_raw,
                name="pending mask",
                supported_mask=supported_mask,
            )
        )
        support = _support(
            root.get("remaining_delay_support", ()),
            name="remaining-delay support",
        )
        consistent = _bool(
            root.get("estimator_consistent"),
            name="estimator consistent",
        )
        if pending is None:
            semantic_consistent = not support and active == held
        else:
            semantic_consistent = pending == held and bool(support)
        if semantic_consistent != consistent:
            raise ValueError(
                "estimator flag disagrees with complete-mask invariant"
            )
        counts[
            "estimator_consistent_roots"
            if consistent
            else "estimator_inconsistent_roots"
        ] += 1
        counts["overdue_roots"] += int(bool(root.get("overdue")))
        counts["multikey_held_roots"] += int(
            (held & 0xF0).bit_count() > 1
        )

        identity = root.get("canonical_identity")
        if consistent:
            if (
                root.get("canonical_status") != "available"
                or not isinstance(identity, dict)
            ):
                raise ValueError(
                    "consistent root lacks canonical identity"
                )
            if identity.get("role") != SHADOW_ROLE:
                raise ValueError("canonical identity role is not shadow-only")
            digest = identity.get("sha256")
            if not isinstance(digest, str) or digest != _identity_digest(
                identity
            ):
                raise ValueError("canonical identity digest mismatch")
            canonical_root = identity.get("root")
            if not isinstance(canonical_root, dict):
                raise ValueError("canonical root is not an object")
            expected_root = {
                "supported_mask": supported_mask,
                "active_mask": active,
                "held_desired_mask": held,
                "pending_mask": pending,
                "remaining_delay_support": list(support),
            }
            if canonical_root != expected_root:
                raise ValueError(
                    "canonical root disagrees with direct root telemetry"
                )
            observation = identity.get("observation")
            if not isinstance(observation, dict):
                raise ValueError("canonical observation is not an object")
            if (
                observation.get("gameplay_epoch")
                != decision.gameplay_epoch
                or observation.get("stage_route_index")
                != decision.stage_route_index
                or observation.get("manager_frame")
                != decision.snapshot_frame
            ):
                raise ValueError(
                    "canonical observation disagrees with trace context"
                )
            versions = identity.get("versions")
            if not isinstance(versions, dict):
                raise ValueError("canonical versions are not an object")
            clock = versions.get("clock")
            if not isinstance(clock, dict):
                raise ValueError("canonical clock version is absent")
            components = clock.get("components")
            if (
                not isinstance(components, dict)
                or components.get("authority")
                != "shadow_no_reset_authority"
                or components.get("ce0120") != "open"
                or components.get("manager_frame_is_physical_clock")
                is not False
            ):
                raise ValueError("clock authority boundary is invalid")
            counts["canonical_identity_valid"] += 1
        elif identity is not None:
            raise ValueError(
                "inconsistent root must not publish canonical identity"
            )

        coverage = root.get("hazard_coverage")
        if not isinstance(coverage, dict):
            raise ValueError("hazard coverage record is absent")
        if coverage.get("role") != SHADOW_ROLE:
            raise ValueError("hazard coverage role is not shadow-only")
        if coverage.get("status") != "model_unknown":
            raise ValueError(
                "unseen future events were not retained as model unknown"
            )
        unknown_from = _int(
            coverage.get("unknown_from_frame"),
            name="unknown coverage frame",
        )
        covered_through = _int(
            coverage.get("covered_through_frame"),
            name="covered-through frame",
        )
        if (
            unknown_from != decision.snapshot_frame + 1
            or covered_through != decision.snapshot_frame
        ):
            raise ValueError(
                "unknown future coverage did not truncate at first transition"
            )
        slabs = coverage.get("slabs")
        if (
            not isinstance(slabs, list)
            or not slabs
            or not isinstance(slabs[0], dict)
            or slabs[0].get("coverage_class") != "UNKNOWN"
            or slabs[0].get("authority_eligible") is not False
        ):
            raise ValueError("unknown coverage slab became authority eligible")
        counts["model_unknown_roots"] += 1
    except ValueError as error:
        _record_failure(
            failures,
            decision=decision,
            code="root_contract",
            detail=str(error),
        )


def _audit_dispatch(
    decision: _Decision,
    *,
    supported_mask: int,
    counts: dict[str, int],
    failures: list[dict[str, object]],
) -> None:
    try:
        dispatch = decision.dispatch
        if dispatch.get("role") != "observed_issue_transaction":
            raise ValueError("dispatch role is invalid")
        previous = _mask(
            dispatch.get("previous_mask"),
            name="dispatch previous mask",
            supported_mask=supported_mask,
        )
        target = _mask(
            dispatch.get("target_mask"),
            name="dispatch target mask",
            supported_mask=supported_mask,
        )
        root_held = _mask(
            decision.root.get("held_desired_mask"),
            name="root held mask",
            supported_mask=supported_mask,
        )
        row_target = _mask(
            decision.row.get("mask"),
            name="row target mask",
            supported_mask=supported_mask,
        )
        if previous != root_held or target != row_target:
            raise ValueError("dispatch masks disagree with root or decision")
        transitions_raw = dispatch.get("transitions")
        if not isinstance(transitions_raw, list):
            raise ValueError("dispatch transitions are not an array")
        transitions: list[tuple[int, bool]] = []
        for item in transitions_raw:
            if (
                not isinstance(item, list)
                or len(item) != 2
                or type(item[0]) is not int
                or type(item[1]) is not bool
            ):
                raise ValueError("dispatch transition is malformed")
            transitions.append((item[0], item[1]))
        expected = _ordered_transitions(previous, target)
        if tuple(transitions) != expected:
            raise ValueError("dispatch key-edge order is incorrect")
        write_required = previous != target
        if (
            _bool(
                dispatch.get("write_required"),
                name="write-required flag",
            )
            != write_required
            or _bool(
                dispatch.get("estimator_issued"),
                name="estimator-issued flag",
            )
            != write_required
            or _int(
                dispatch.get("transition_count"),
                name="transition count",
            )
            != len(expected)
        ):
            raise ValueError("dispatch write/estimator flags are inconsistent")
        counts["writes" if write_required else "no_writes"] += 1
        counts["multikey_transactions"] += int(len(expected) > 1)
        movement_mask = supported_mask & 0x00F4
        projected_reissue = (
            write_required
            and previous & movement_mask == target & movement_mask
        )
        counts["projected_action_reissues"] += int(projected_reissue)
        counts["pending_projected_action_reissues"] += int(
            projected_reissue
            and decision.root.get("pending_mask") is not None
            and (
                _mask(
                    decision.root.get("active_mask"),
                    name="root active mask",
                    supported_mask=supported_mask,
                )
                & movement_mask
                != previous & movement_mask
            )
        )
        counts["release_edges"] += sum(
            1 for _bit, pressed in expected if not pressed
        )
        counts["press_edges"] += sum(
            1 for _bit, pressed in expected if pressed
        )
    except ValueError as error:
        _record_failure(
            failures,
            decision=decision,
            code="dispatch_contract",
            detail=str(error),
        )


def _root_state(
    decision: _Decision,
    *,
    supported_mask: int,
) -> tuple[int, int, int | None, tuple[int, ...], int | None, bool]:
    root = decision.root
    pending_raw = root.get("pending_mask")
    return (
        _mask(
            root.get("active_mask"),
            name="active mask",
            supported_mask=supported_mask,
        ),
        _mask(
            root.get("held_desired_mask"),
            name="held mask",
            supported_mask=supported_mask,
        ),
        (
            None
            if pending_raw is None
            else _mask(
                pending_raw,
                name="pending mask",
                supported_mask=supported_mask,
            )
        ),
        _support(
            root.get("remaining_delay_support", ()),
            name="remaining-delay support",
        ),
        (
            None
            if root.get("snapshot_age") is None
            else _int(root.get("snapshot_age"), name="snapshot age")
        ),
        bool(root.get("overdue")),
    )


def _audit_continuity(
    current: _Decision,
    successor: _Decision,
    *,
    supported_mask: int,
    counts: dict[str, int],
    failures: list[dict[str, object]],
) -> None:
    if (
        current.gameplay_epoch != successor.gameplay_epoch
        or current.stage_route_index != successor.stage_route_index
        or successor.snapshot_frame < current.snapshot_frame
    ):
        counts["context_boundary_pairs"] += 1
        return
    counts["continuity_pairs"] += 1
    try:
        (
            active,
            held,
            pending,
            support,
            snapshot_age,
            _overdue,
        ) = _root_state(current, supported_mask=supported_mask)
        (
            next_active,
            next_held,
            next_pending,
            next_support,
            next_snapshot_age,
            next_overdue,
        ) = _root_state(successor, supported_mask=supported_mask)
        target = _mask(
            current.dispatch.get("target_mask"),
            name="dispatch target",
            supported_mask=supported_mask,
        )
        write = _bool(
            current.dispatch.get("write_required"),
            name="write-required flag",
        )
        if next_held != target:
            raise ValueError("held desired did not carry to next root")

        if write:
            if pending is not None:
                counts["last_write_wins_replacements"] += 1
            transition_masks = _transition_masks(
                held,
                _ordered_transitions(held, target),
            )
            if next_active in transition_masks[:-1]:
                counts["ordered_partial_pickups"] += 1
            if next_active == target:
                if next_pending is not None:
                    raise ValueError(
                        "observed target pickup retained a pending command"
                    )
                if active == target:
                    counts["preexisting_target_matches"] += 1
                else:
                    counts["observed_pickups"] += 1
                return
            if next_pending != target:
                raise ValueError(
                    "newest unobserved write is not the pending command"
                )
            initial_support = _support(
                current.row.get("control_delay_candidates", ()),
                name="issued delay support",
            )
            if next_snapshot_age is None:
                raise ValueError("pending successor lacks snapshot age")
            expected = tuple(
                delay - next_snapshot_age
                for delay in initial_support
                if delay > next_snapshot_age
            )
            if not expected:
                expected = (1,)
            if next_support != expected:
                raise ValueError(
                    "new-write remaining support is discontinuous"
                )
            counts["unobserved_write_carries"] += 1
            return

        if target != held:
            raise ValueError("no-write transaction changed held mask")
        if pending is None:
            if next_pending is not None or next_active != held:
                raise ValueError(
                    "settled no-write root changed without a new issue"
                )
            counts["settled_no_write_carries"] += 1
            return
        counts["pending_no_write_carries"] += 1
        if next_active == pending:
            if next_pending is not None:
                raise ValueError(
                    "observed pending pickup retained pending state"
                )
            counts["observed_pickups"] += 1
            return
        if next_pending != pending:
            raise ValueError("no-write did not preserve older pending command")
        if snapshot_age is None or next_snapshot_age is None:
            raise ValueError("pending no-write lacks snapshot ages")
        age_delta = next_snapshot_age - snapshot_age
        if age_delta < 0:
            raise ValueError("pending snapshot age moved backwards")
        expected = tuple(
            remaining - age_delta
            for remaining in support
            if remaining > age_delta
        )
        if not expected:
            expected = (1,)
        if next_support != expected:
            raise ValueError("no-write remaining support is discontinuous")
        if next_overdue and expected != (1,):
            raise ValueError("overdue flag precedes support exhaustion")
    except ValueError as error:
        _record_failure(
            failures,
            decision=current,
            code="pipeline_continuity",
            detail=str(error),
        )


def audit_rows(
    rows: Iterable[dict[str, object]],
    *,
    supported_mask: int,
) -> dict[str, object]:
    decisions, skipped = _parse_decisions(rows)
    counter_names = (
        "canonical_identity_valid",
        "context_boundary_pairs",
        "continuity_pairs",
        "estimator_consistent_roots",
        "estimator_inconsistent_roots",
        "last_write_wins_replacements",
        "model_unknown_roots",
        "multikey_held_roots",
        "multikey_transactions",
        "no_writes",
        "observed_pickups",
        "ordered_partial_pickups",
        "overdue_roots",
        "pending_no_write_carries",
        "pending_projected_action_reissues",
        "preexisting_target_matches",
        "press_edges",
        "projected_action_reissues",
        "release_edges",
        "settled_no_write_carries",
        "unobserved_write_carries",
        "writes",
    )
    counts = {name: 0 for name in counter_names}
    failures: list[dict[str, object]] = []

    for decision in decisions:
        _audit_root(
            decision,
            supported_mask=supported_mask,
            counts=counts,
            failures=failures,
        )
        _audit_dispatch(
            decision,
            supported_mask=supported_mask,
            counts=counts,
            failures=failures,
        )
    for current, successor in zip(decisions, decisions[1:]):
        if (
            current.snapshot_frame == successor.snapshot_frame
            and current.gameplay_epoch != successor.gameplay_epoch
        ):
            _record_failure(
                failures,
                decision=current,
                code="clock_authority",
                detail=(
                    "gameplay epoch changed across a repeated manager frame"
                ),
            )
        _audit_continuity(
            current,
            successor,
            supported_mask=supported_mask,
            counts=counts,
            failures=failures,
        )

    integrity_passed = bool(decisions) and not failures
    promotion_blockers: list[str] = []
    if counts["pending_projected_action_reissues"]:
        promotion_blockers.append(
            "complete_mask_write_collapses_to_held_movement_action"
        )
    if counts["ordered_partial_pickups"]:
        promotion_blockers.append(
            "ordered_partial_transition_pickup_requires_expanded_root"
        )
    if counts["model_unknown_roots"]:
        promotion_blockers.append("future_hazard_coverage_is_model_unknown")
    promotion_blockers.append("ce0120_physical_clock_boundary_is_open")
    return {
        "schema": SCHEMA,
        "role": "offline_audit_no_action_authority",
        "evidence": "observed_trace_plus_deterministic_replay",
        "decision_rows": len(decisions),
        "skipped_nondecision_rows": skipped,
        "supported_mask": supported_mask,
        "counts": counts,
        "failure_count": len(failures),
        "failures": failures[:100],
        "failures_truncated": max(0, len(failures) - 100),
        "passed": integrity_passed,
        "live_pipeline_promotion_ready": (
            integrity_passed and not promotion_blockers
        ),
        "promotion_blockers": promotion_blockers,
        "interpretation": {
            "observed_pickups": (
                "native active mask changed to a previously non-active "
                "held/pending target"
            ),
            "preexisting_target_matches": (
                "target already matched native active input, so the write "
                "cannot prove a new physical pickup"
            ),
            "ordered_partial_pickups": (
                "native active input matched a non-final prefix of the "
                "recorded ordered key transaction"
            ),
            "model_unknown": (
                "unseen future hazard events truncate coverage and are not "
                "interpreted as free space"
            ),
            "projected_action_reissues": (
                "complete masks differ and cause a physical write even though "
                "their movement/focus projection is identical"
            ),
        },
    }


def audit_trace(path: Path, *, supported_mask: int) -> dict[str, object]:
    digest = hashlib.sha256()
    rows: list[dict[str, object]] = []
    with path.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if isinstance(row, dict):
                rows.append(row)
    return {
        "source": {
            "path": str(path),
            "sha256": digest.hexdigest(),
        },
        **audit_rows(rows, supported_mask=supported_mask),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--supported-mask", type=lambda value: int(value, 0))
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    supported_mask = (
        args.supported_mask if args.supported_mask is not None else 0x00F7
    )
    report = audit_trace(args.trace, supported_mask=supported_mask)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output is None:
        print(rendered)
    else:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
