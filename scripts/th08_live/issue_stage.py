"""Typed issue-time observation, dispatch, and actuator-state transaction."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable, Protocol

from th08_local_planner import Decision, LocalProposal
from th08_runtime.game_state import (
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_PLAYER,
    PLAYER_PREDEATH_COUNTER_OFFSET,
)
from touhou_control.epochs import ActionIssueAlignment

from .issue_controller import IssueController
from .iteration import CapturedIteration, FreshIssueResult


class DelayIssueRecorder(Protocol):
    """The actuator-delay mutation consumed by one physical issue."""

    def issued(
        self,
        *,
        snapshot_frame: int,
        issue_frame: int,
        expected_mask: int,
        support_high: int,
        support: tuple[int, ...],
    ) -> None: ...


@dataclass(frozen=True)
class ActionIssueObservation:
    """Native player/contact state and frame identity at issue time."""

    player_phase: int
    predeath_counter: int
    alignment: ActionIssueAlignment

    @property
    def issue_frame(self) -> int:
        return self.alignment.issue_frame


@dataclass(frozen=True)
class PhysicalIssueRequest:
    """All immutable inputs required after final input overrides."""

    capture: CapturedIteration
    proposal: LocalProposal
    decision: Decision
    alignment: ActionIssueAlignment
    previous_mask: int
    direction_mask: int
    pre_issue_action: str
    pre_issue_mask: int
    post_guard_action: str
    post_guard_mask: int
    planned_action: str
    planned_mask: int
    fresh_enemy_changed: bool
    recertification_ms: float
    issue_path_started: float
    iteration_started: float


@dataclass(frozen=True)
class PhysicalIssueCommit:
    """Committed issue result and next controller-owned actuator state."""

    issue: FreshIssueResult
    previous_mask: int
    previous_direction: int
    direction_mask: int

    def __post_init__(self) -> None:
        if self.previous_mask != self.issue.decision.mask:
            raise ValueError("next actuator mask does not match issued input")
        if self.previous_direction != self.previous_mask & self.direction_mask:
            raise ValueError("next actuator direction does not match mask")


def observe_action_issue(
    reader: Any,
    *,
    source_frame: int,
    capture_frame: int,
    delay_support: tuple[int, ...],
) -> ActionIssueObservation:
    """Read the fixed issue-time state in its historical physical order."""

    player_phase = reader.u8(ADDR_PLAYER)
    predeath_counter = reader.i32(
        ADDR_PLAYER + PLAYER_PREDEATH_COUNTER_OFFSET
    )
    issue_frame = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
    return ActionIssueObservation(
        player_phase=player_phase,
        predeath_counter=predeath_counter,
        alignment=ActionIssueAlignment(
            source_frame=source_frame,
            capture_frame=capture_frame,
            issue_frame=issue_frame,
            delay_support=delay_support,
        ),
    )


def commit_physical_issue(
    request: PhysicalIssueRequest,
    *,
    issue_controller: IssueController,
    delay_recorder: DelayIssueRecorder,
    clock: Callable[[], float] = time.perf_counter,
) -> PhysicalIssueCommit:
    """Dispatch once, register writes only, and return next actuator state."""

    dispatch = issue_controller.dispatch(
        request.previous_mask,
        request.decision.mask,
    )
    issue_path_ms = (clock() - request.issue_path_started) * 1000.0
    observe_to_issue_ms = (clock() - request.iteration_started) * 1000.0
    issue = FreshIssueResult(
        capture=request.capture,
        proposal=request.proposal,
        decision=request.decision,
        alignment=request.alignment,
        dispatch=dispatch,
        issue_frame=request.alignment.issue_frame,
        pre_issue_action=request.pre_issue_action,
        pre_issue_mask=request.pre_issue_mask,
        post_guard_action=request.post_guard_action,
        post_guard_mask=request.post_guard_mask,
        planned_action=request.planned_action,
        planned_mask=request.planned_mask,
        fresh_enemy_changed=request.fresh_enemy_changed,
        deadline_missed=request.alignment.deadline_missed,
        recertification_ms=request.recertification_ms,
        issue_path_ms=issue_path_ms,
        observe_to_issue_ms=observe_to_issue_ms,
    )
    if dispatch.transitions:
        delay_recorder.issued(
            snapshot_frame=request.capture.source_frame,
            issue_frame=request.alignment.issue_frame,
            expected_mask=request.decision.mask,
            support_high=request.alignment.support_high,
            support=request.alignment.delay_support,
        )
    return PhysicalIssueCommit(
        issue=issue,
        previous_mask=request.decision.mask,
        previous_direction=request.decision.mask & request.direction_mask,
        direction_mask=request.direction_mask,
    )


__all__ = [
    "ActionIssueObservation",
    "DelayIssueRecorder",
    "PhysicalIssueCommit",
    "PhysicalIssueRequest",
    "commit_physical_issue",
    "observe_action_issue",
]
