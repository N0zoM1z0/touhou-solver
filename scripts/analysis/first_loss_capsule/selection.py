"""Select one uninterrupted exact viable-to-losing trace bracket."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Mapping

from analysis.complete_mask_capsule.trace import (
    read_complete_mask_roots,
)
from analysis.complete_mask_capsule.types import CompleteMaskCapsuleRoot

from .types import FirstLossBracket, FirstLossSelection


def _scope_from_row(row: Mapping[str, object]) -> tuple[int, int] | None:
    epoch = row.get("gameplay_epoch")
    stage = row.get("stage_route_index")
    if type(epoch) is not int or type(stage) is not int:
        return None
    return epoch, stage


def _scope_from_root(
    root: CompleteMaskCapsuleRoot,
) -> tuple[int, int]:
    observation = root.identity.observation
    return observation.gameplay_epoch, observation.stage_route_index


def _root_gap_reason(
    row: Mapping[str, object],
    *,
    capsule_dir: Path,
    root: CompleteMaskCapsuleRoot | None,
) -> str | None:
    corridor = row.get("corridor")
    local_root = row.get("local_pipeline_root")
    if not isinstance(corridor, Mapping):
        return "corridor_record_missing"
    viability = corridor.get("viability")
    if not isinstance(viability, Mapping):
        return "viability_query_missing"
    if viability.get("available") is not True:
        return "viability_query_unavailable"
    if not isinstance(local_root, Mapping):
        return "canonical_root_missing"
    if local_root.get("canonical_status") != "available":
        return "canonical_root_unavailable"
    capsule = corridor.get("audit_capsule")
    if not isinstance(capsule, str) or not capsule:
        return "audit_capsule_missing"
    if root is None:
        return "joined_root_invalid"
    if not (capsule_dir / root.capsule).is_file():
        return "capsule_file_missing"
    return None


def _unresolved_record(
    *,
    line_number: int,
    row: Mapping[str, object],
    reason: str,
) -> dict[str, object]:
    corridor = row.get("corridor")
    viability = (
        corridor.get("viability")
        if isinstance(corridor, Mapping)
        else None
    )
    return {
        "line": line_number,
        "decision_frame": row.get("frame"),
        "gameplay_epoch": row.get("gameplay_epoch"),
        "stage_route_index": row.get("stage_route_index"),
        "query_frame": (
            viability.get("query_frame")
            if isinstance(viability, Mapping)
            else None
        ),
        "reason": reason,
    }


def select_first_loss_bracket(
    *,
    trace: Path,
    capsule_dir: Path,
    gameplay_epoch: int | None = None,
    stage_route_index: int | None = None,
) -> FirstLossSelection:
    """Return the exact loss bracket whose episode contains the first hit."""

    roots, failures = read_complete_mask_roots(trace)
    roots_by_line = {root.trace_line: root for root in roots}
    interruptions: Counter[str] = Counter()
    last_viable: CompleteMaskCapsuleRoot | None = None
    current_scope: tuple[int, int] | None = None
    observed_state: bool | None = None
    active_bracket: FirstLossBracket | None = None
    active_unresolved: dict[str, object] | None = None
    recovered_loss_episodes = 0

    with trace.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                interruptions["json_decode_error"] += 1
                last_viable = None
                observed_state = None
                active_bracket = None
                active_unresolved = None
                continue
            if not isinstance(row, Mapping) or row.get("kind") != "decision":
                continue

            root = roots_by_line.get(line_number)
            row_scope = _scope_from_row(row)
            scope = _scope_from_root(root) if root is not None else row_scope
            if scope is None:
                interruptions["physical_scope_missing"] += 1
                last_viable = None
                observed_state = None
                active_bracket = None
                active_unresolved = None
                continue
            if gameplay_epoch is not None and scope[0] != gameplay_epoch:
                continue
            if (
                stage_route_index is not None
                and scope[1] != stage_route_index
            ):
                continue
            if scope != current_scope:
                if current_scope is not None:
                    interruptions["physical_scope_changed"] += 1
                current_scope = scope
                last_viable = None
                observed_state = None
                active_bracket = None
                active_unresolved = None

            corridor = row.get("corridor")
            viability = (
                corridor.get("viability")
                if isinstance(corridor, Mapping)
                else None
            )
            explicit_state = (
                viability.get("state_viable")
                if isinstance(viability, Mapping)
                and viability.get("available") is True
                else None
            )
            if explicit_state is not None and type(explicit_state) is not bool:
                interruptions["non_boolean_viability_state"] += 1
                last_viable = None
                observed_state = None
                active_bracket = None
                active_unresolved = None
                continue

            gap_reason = _root_gap_reason(
                row,
                capsule_dir=capsule_dir,
                root=root,
            )
            if gap_reason is not None:
                interruptions[gap_reason] += 1
                last_viable = None
            elif root is not None and _scope_from_root(root) != scope:
                gap_reason = "joined_root_scope_mismatch"
                interruptions[gap_reason] += 1
                last_viable = None

            if explicit_state is True:
                if observed_state is False:
                    recovered_loss_episodes += 1
                observed_state = True
                active_bracket = None
                active_unresolved = None
                last_viable = root if gap_reason is None else None
            elif explicit_state is False:
                if observed_state is True:
                    if last_viable is not None and gap_reason is None:
                        assert root is not None
                        active_bracket = FirstLossBracket(
                            last_viable=last_viable,
                            first_losing=root,
                        )
                        active_unresolved = None
                    else:
                        active_bracket = None
                        active_unresolved = _unresolved_record(
                            line_number=line_number,
                            row=row,
                            reason=(
                                gap_reason
                                or "exact_viable_predecessor_missing"
                            ),
                        )
                elif observed_state is None and active_bracket is None:
                    active_unresolved = _unresolved_record(
                        line_number=line_number,
                        row=row,
                        reason=(
                            gap_reason
                            or "no_uninterrupted_exact_viable_predecessor"
                        ),
                    )
                elif gap_reason is not None:
                    active_bracket = None
                    if active_unresolved is None:
                        active_unresolved = _unresolved_record(
                            line_number=line_number,
                            row=row,
                            reason=gap_reason,
                        )
                observed_state = False
                last_viable = None
            else:
                observed_state = None
                active_bracket = None
                active_unresolved = None
                last_viable = None

            if row.get("hit_started") is True:
                hit_frame = (
                    int(row["frame"])
                    if type(row.get("frame")) is int
                    else None
                )
                if (
                    explicit_state is False
                    and gap_reason is None
                    and active_bracket is not None
                ):
                    return FirstLossSelection(
                        status="selected",
                        bracket=active_bracket,
                        interruption_counts=tuple(
                            sorted(interruptions.items())
                        ),
                        root_validation_failures=tuple(failures),
                        recovered_loss_episodes=(
                            recovered_loss_episodes
                        ),
                        target_hit_frame=hit_frame,
                    )
                return FirstLossSelection(
                    status="unresolved_pre_hit_loss",
                    bracket=None,
                    interruption_counts=tuple(
                        sorted(interruptions.items())
                    ),
                    root_validation_failures=tuple(failures),
                    recovered_loss_episodes=recovered_loss_episodes,
                    target_hit_frame=hit_frame,
                    unresolved=(
                        active_unresolved
                        or _unresolved_record(
                            line_number=line_number,
                            row=row,
                            reason=(
                                gap_reason
                                or "hit_has_no_persistent_exact_loss_bracket"
                            ),
                        )
                    ),
                )

    return FirstLossSelection(
        status="no_hit_observed",
        bracket=None,
        interruption_counts=tuple(sorted(interruptions.items())),
        root_validation_failures=tuple(failures),
        recovered_loss_episodes=recovered_loss_episodes,
        target_hit_frame=None,
    )


__all__ = ["select_first_loss_bracket"]
