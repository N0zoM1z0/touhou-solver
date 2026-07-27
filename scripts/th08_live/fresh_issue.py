"""Fresh enemy-prefix recertification stage for one live issue transaction.

This module does not dispatch input or decide deadline, Bomb, or scene
behavior.  It owns the bounded issue-time sensor refresh and invokes the
controller-supplied hard recertification callback only when aligned enemy
geometry changed.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from th08_local_planner import Decision, IssuedDecision, LocalProposal

from .enemy_sensor import (
    capture_enemy_pool_prefix_contiguous,
    issue_enemy_snapshot_changes,
    merge_enemy_pool_prefix,
)
from .models import (
    EnemyBody,
    EnemyBodyModeMemory,
    EnemyPoolSnapshot,
)


@dataclass(frozen=True)
class FreshEnemyIssueDependencies:
    """Injected issue-time sensor and comparison operations."""

    capture_prefix: Callable[[Any], EnemyPoolSnapshot] = (
        capture_enemy_pool_prefix_contiguous
    )
    detect_changes: Callable[
        [
            EnemyPoolSnapshot,
            EnemyPoolSnapshot,
            EnemyPoolSnapshot,
            EnemyPoolSnapshot,
        ],
        tuple[str, ...],
    ] = issue_enemy_snapshot_changes
    merge_prefix: Callable[
        [tuple[EnemyBody, ...], tuple[EnemyBody, ...]],
        tuple[EnemyBody, ...],
    ] = merge_enemy_pool_prefix
    monotonic: Callable[[], float] = time.perf_counter


@dataclass(frozen=True)
class FreshEnemyIssueResult:
    """Fresh enemy observation and optional recertification outcome."""

    prefix_snapshot: EnemyPoolSnapshot
    prefix_bodies: tuple[EnemyBody, ...]
    dormant_pointers: frozenset[int]
    changes: tuple[str, ...]
    enemy_bodies_for_shadow: tuple[EnemyBody, ...]
    decision: Decision
    read_ms: float
    recertification_ms: float

    def __post_init__(self) -> None:
        for field, value in (
            ("fresh enemy read time", self.read_ms),
            ("fresh enemy recertification time", self.recertification_ms),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{field} must be finite and nonnegative")
        if not self.changes and self.recertification_ms != 0.0:
            raise ValueError(
                "unchanged fresh enemy geometry cannot have recertification time"
            )

    @property
    def changed(self) -> bool:
        return bool(self.changes)


def recertify_fresh_enemy_prefix(
    *,
    proposal: LocalProposal,
    reader: Any,
    memory: EnemyBodyModeMemory,
    alignment_frame: int,
    planned_prefix_snapshot: EnemyPoolSnapshot,
    planned_prefix_bodies: tuple[EnemyBody, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    commit: Callable[
        [LocalProposal, tuple[EnemyBody, ...]],
        IssuedDecision,
    ],
    read_started: float | None = None,
    dependencies: FreshEnemyIssueDependencies = (
        FreshEnemyIssueDependencies()
    ),
) -> FreshEnemyIssueResult:
    """Refresh the local enemy prefix and recertify only on a real change."""

    if read_started is None:
        read_started = dependencies.monotonic()
    prefix_snapshot = dependencies.capture_prefix(reader)
    read_ms = (dependencies.monotonic() - read_started) * 1000.0
    prefix_bodies, dormant_pointers = memory.merge_snapshot(
        prefix_snapshot,
        frame=alignment_frame,
    )
    planned_aligned = EnemyPoolSnapshot(
        alignment_frame,
        alignment_frame,
        planned_prefix_bodies,
        planned_prefix_snapshot.read_ms,
        planned_prefix_snapshot.attempts,
    )
    current_aligned = EnemyPoolSnapshot(
        alignment_frame,
        alignment_frame,
        prefix_bodies,
        prefix_snapshot.read_ms,
        prefix_snapshot.attempts,
    )
    changes = dependencies.detect_changes(
        planned_prefix_snapshot,
        prefix_snapshot,
        planned_aligned,
        current_aligned,
    )

    decision = proposal.decision
    enemy_bodies_for_shadow = enemy_bodies
    recertification_ms = 0.0
    if changes:
        enemy_bodies_for_shadow = dependencies.merge_prefix(
            enemy_bodies,
            prefix_bodies,
        )
        recertification_started = dependencies.monotonic()
        decision = commit(
            proposal,
            enemy_bodies_for_shadow,
        ).decision
        recertification_ms = (
            dependencies.monotonic() - recertification_started
        ) * 1000.0

    return FreshEnemyIssueResult(
        prefix_snapshot=prefix_snapshot,
        prefix_bodies=prefix_bodies,
        dormant_pointers=dormant_pointers,
        changes=changes,
        enemy_bodies_for_shadow=enemy_bodies_for_shadow,
        decision=decision,
        read_ms=read_ms,
        recertification_ms=recertification_ms,
    )


__all__ = [
    "FreshEnemyIssueDependencies",
    "FreshEnemyIssueResult",
    "recertify_fresh_enemy_prefix",
]
