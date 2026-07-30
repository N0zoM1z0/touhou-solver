"""Causal action-conditioned TH08 future body schedule families."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable, Hashable, Mapping

from th08_enemy_mode import (
    Route2AsyncOrderedModeDecisionBranch,
    Route2ModeHazardFrame,
    project_route2_async_ordered_mode_decision_branches,
)
from th08_future_body_schedule import (
    Route2FutureBodyScheduleSet,
    Route2ObservedBodyState,
    project_route2_versioned_async_mode_decision_branches,
)
from touhou_control.ordered_input_transaction_oracle import (
    OrderedInputBelief,
)
from touhou_control.pipeline_identity import VersionIdentity


FAMILY_SCHEMA = "th08-route2-causal-future-body-family-v1"
FAMILY_AUTHORITY = "offline_conditioned_schedule_family_only"


def _sha256_record(record: dict[str, object]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class Route2ConditionedFutureBodySchedule:
    """One schedule support conditioned on one exact active-mask history."""

    active_mask_history: tuple[int, ...]
    schedule: Route2FutureBodyScheduleSet

    def __post_init__(self) -> None:
        if (
            type(self.active_mask_history) is not tuple
            or not self.active_mask_history
            or any(
                type(mask) is not int or not 0 <= mask <= 0xFFFFFFFF
                for mask in self.active_mask_history
            )
        ):
            raise ValueError(
                "conditioned active-mask history must be a nonempty u32 tuple"
            )
        if type(self.schedule) is not Route2FutureBodyScheduleSet:
            raise ValueError(
                "conditioned future schedule must be an immutable schedule set"
            )
        if len(self.active_mask_history) != self.schedule.horizon:
            raise ValueError(
                "conditioned active-mask history must equal schedule horizon"
            )

    def record(self) -> dict[str, object]:
        return {
            "active_mask_history": list(self.active_mask_history),
            "future_schedule_sha256": self.schedule.digest,
        }


@dataclass(frozen=True)
class Route2CausalFutureBodyScheduleFamily:
    """Complete supplied schedule mapping for one selected root action."""

    selected_action: str
    selected_mask: int
    members: tuple[Route2ConditionedFutureBodySchedule, ...]
    schema: str = FAMILY_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != FAMILY_SCHEMA:
            raise ValueError("unsupported causal future schedule schema")
        if type(self.selected_action) is not str or not self.selected_action:
            raise ValueError("causal future schedule action must not be empty")
        if (
            type(self.selected_mask) is not int
            or not 0 <= self.selected_mask <= 0xFFFFFFFF
        ):
            raise ValueError(
                "causal future schedule selected mask must fit u32"
            )
        if type(self.members) is not tuple or any(
            type(member) is not Route2ConditionedFutureBodySchedule
            for member in self.members
        ):
            raise ValueError(
                "causal future schedules must be an immutable member tuple"
            )
        if not self.members:
            raise ValueError("causal future schedule family cannot be empty")
        histories = tuple(
            member.active_mask_history for member in self.members
        )
        if histories != tuple(sorted(histories)):
            raise ValueError(
                "causal future schedule histories must be sorted"
            )
        if len(histories) != len(set(histories)):
            raise ValueError(
                "causal future schedule histories must be unique"
            )
        root_updates = {
            member.schedule.root_physical_update
            for member in self.members
        }
        if len(root_updates) != 1:
            raise ValueError(
                "causal future schedules must share one root update"
            )
        clock_records = {
            json.dumps(
                member.schedule.clock_version.record(),
                sort_keys=True,
                separators=(",", ":"),
            )
            for member in self.members
        }
        if len(clock_records) != 1:
            raise ValueError(
                "causal future schedules must share one clock version"
            )

    @classmethod
    def from_members(
        cls,
        *,
        selected_action: str,
        selected_mask: int,
        members: tuple[Route2ConditionedFutureBodySchedule, ...],
    ) -> Route2CausalFutureBodyScheduleFamily:
        return cls(
            selected_action=selected_action,
            selected_mask=selected_mask,
            members=tuple(
                sorted(
                    members,
                    key=lambda member: member.active_mask_history,
                )
            ),
        )

    @property
    def root_physical_update(self) -> int:
        return self.members[0].schedule.root_physical_update

    @property
    def clock_version(self) -> VersionIdentity:
        return self.members[0].schedule.clock_version

    def payload(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "authority": FAMILY_AUTHORITY,
            "physical_predictive_authority": False,
            "selected_action": self.selected_action,
            "selected_mask": self.selected_mask,
            "root_physical_update": self.root_physical_update,
            "clock_version": self.clock_version.record(),
            "members": [member.record() for member in self.members],
        }

    @property
    def digest(self) -> str:
        return _sha256_record(self.payload())

    def record(self) -> dict[str, object]:
        return {
            **self.payload(),
            "sha256": self.digest,
        }


@dataclass(frozen=True)
class Route2CausalAsyncModeDecisionBranch:
    """One compatible actuator/world history under a family version."""

    family_version: str
    conditioned_active_mask_history: tuple[int, ...]
    supplied_schedule_version: str
    supplied_schedule_branch: str
    observed_body_state: Route2ObservedBodyState
    mode_branch: Route2AsyncOrderedModeDecisionBranch


@dataclass(frozen=True)
class Route2CausalModeObservationKey:
    """Next observation key that hides the conditioned history."""

    base_observation: Hashable
    family_version: str
    physical_step: int
    active_mask: int
    held_desired_mask: int
    mode_state: tuple[int, bool, int]
    observed_body_state: Route2ObservedBodyState


@dataclass(frozen=True)
class Route2CausalAsyncModeObservationClass:
    """Non-clairvoyant merge across compatible actuator/world histories."""

    key: Route2CausalModeObservationKey
    successor_input_belief: OrderedInputBelief
    hidden_branches: tuple[Route2CausalAsyncModeDecisionBranch, ...]


def _active_mask_history(
    branch: Route2AsyncOrderedModeDecisionBranch,
) -> tuple[int, ...]:
    return tuple(
        frame.active_mask for frame in branch.hazard_branch.frames
    )


def _reachable_active_mask_histories(
    *,
    input_belief: OrderedInputBelief,
    selected_action: str,
    action_masks: Mapping[str, int],
    supported_mask: int,
    post_dispatch_delay_frames: tuple[int, ...],
    dispatch_callback_count_support: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    initial_mode_state: tuple[int, bool, int],
) -> frozenset[tuple[int, ...]]:
    if (
        type(decision_frame_support) is not tuple
        or not decision_frame_support
        or any(
            type(frames) is not int or frames <= 0
            for frames in decision_frame_support
        )
        or decision_frame_support
        != tuple(sorted(set(decision_frame_support)))
    ):
        raise ValueError(
            "decision-frame support must be a sorted positive tuple"
        )
    skeleton = project_route2_async_ordered_mode_decision_branches(
        input_belief=input_belief,
        selected_action=selected_action,
        action_masks=action_masks,
        supported_mask=supported_mask,
        post_dispatch_delay_frames=post_dispatch_delay_frames,
        dispatch_callback_count_support=(
            dispatch_callback_count_support
        ),
        decision_frame_support=decision_frame_support,
        initial_mode_state=initial_mode_state,
        enemy_flag_frames=((),) * decision_frame_support[-1],
    )
    return frozenset(_active_mask_history(branch) for branch in skeleton)


def project_route2_causal_future_body_decision_branches(
    *,
    family: Route2CausalFutureBodyScheduleFamily,
    input_belief: OrderedInputBelief,
    selected_action: str,
    action_masks: Mapping[str, int],
    supported_mask: int,
    post_dispatch_delay_frames: tuple[int, ...],
    dispatch_callback_count_support: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    initial_mode_state: tuple[int, bool, int],
) -> tuple[Route2CausalAsyncModeDecisionBranch, ...]:
    """Compose only schedules compatible with each exact input history."""

    if selected_action != family.selected_action:
        raise ValueError(
            "causal future schedule family action does not match selection"
        )
    if (
        selected_action not in action_masks
        or action_masks[selected_action] != family.selected_mask
    ):
        raise ValueError(
            "causal future schedule family mask does not match action map"
        )
    reachable = _reachable_active_mask_histories(
        input_belief=input_belief,
        selected_action=selected_action,
        action_masks=action_masks,
        supported_mask=supported_mask,
        post_dispatch_delay_frames=post_dispatch_delay_frames,
        dispatch_callback_count_support=(
            dispatch_callback_count_support
        ),
        decision_frame_support=decision_frame_support,
        initial_mode_state=initial_mode_state,
    )
    supplied = frozenset(
        member.active_mask_history for member in family.members
    )
    if supplied != reachable:
        missing = tuple(sorted(reachable - supplied))
        extra = tuple(sorted(supplied - reachable))
        raise ValueError(
            "causal future schedule history coverage differs from actuator "
            f"support: missing={missing}, extra={extra}"
        )

    results: list[Route2CausalAsyncModeDecisionBranch] = []
    for member in family.members:
        inner_branches = (
            project_route2_versioned_async_mode_decision_branches(
                future_schedule=member.schedule,
                input_belief=input_belief,
                selected_action=selected_action,
                action_masks=action_masks,
                supported_mask=supported_mask,
                post_dispatch_delay_frames=post_dispatch_delay_frames,
                dispatch_callback_count_support=(
                    dispatch_callback_count_support
                ),
                decision_frame_support=(
                    len(member.active_mask_history),
                ),
                initial_mode_state=initial_mode_state,
            )
        )
        compatible = tuple(
            branch
            for branch in inner_branches
            if _active_mask_history(branch.mode_branch)
            == member.active_mask_history
        )
        if not compatible:
            raise RuntimeError(
                "causal future schedule member has no compatible branch"
            )
        results.extend(
            Route2CausalAsyncModeDecisionBranch(
                family_version=family.digest,
                conditioned_active_mask_history=(
                    member.active_mask_history
                ),
                supplied_schedule_version=(
                    branch.future_schedule_version
                ),
                supplied_schedule_branch=(
                    branch.future_schedule_branch
                ),
                observed_body_state=branch.observed_body_state,
                mode_branch=branch.mode_branch,
            )
            for branch in compatible
        )
    return tuple(results)


def merge_route2_causal_future_body_observation_classes(
    branches: tuple[Route2CausalAsyncModeDecisionBranch, ...],
    *,
    base_observation: Callable[
        [Route2CausalAsyncModeDecisionBranch, Route2ModeHazardFrame],
        Hashable,
    ],
) -> tuple[Route2CausalAsyncModeObservationClass, ...]:
    """Merge compatible hidden histories under one immutable family."""

    if not branches:
        raise ValueError("at least one causal future body branch is required")
    family_versions = {branch.family_version for branch in branches}
    if len(family_versions) != 1:
        raise ValueError(
            "cannot merge different causal future schedule families"
        )
    grouped: dict[
        Route2CausalModeObservationKey,
        list[Route2CausalAsyncModeDecisionBranch],
    ] = {}
    for branch in branches:
        mode_branch = branch.mode_branch
        frame = mode_branch.hazard_branch.frames[-1]
        base = base_observation(branch, frame)
        try:
            hash(base)
        except TypeError as error:
            raise ValueError("base observation must be hashable") from error
        successor = mode_branch.successor_input_state
        key = Route2CausalModeObservationKey(
            base_observation=base,
            family_version=branch.family_version,
            physical_step=mode_branch.cadence_frames,
            active_mask=successor.active_mask,
            held_desired_mask=successor.held_desired_mask,
            mode_state=mode_branch.successor_mode_state,
            observed_body_state=branch.observed_body_state,
        )
        grouped.setdefault(key, []).append(branch)
    return tuple(
        Route2CausalAsyncModeObservationClass(
            key=key,
            successor_input_belief=OrderedInputBelief.from_states(
                hidden_branch.mode_branch.successor_input_state
                for hidden_branch in hidden
            ),
            hidden_branches=tuple(hidden),
        )
        for key, hidden in grouped.items()
    )


__all__ = [
    "FAMILY_AUTHORITY",
    "FAMILY_SCHEMA",
    "Route2CausalAsyncModeDecisionBranch",
    "Route2CausalAsyncModeObservationClass",
    "Route2CausalFutureBodyScheduleFamily",
    "Route2CausalModeObservationKey",
    "Route2ConditionedFutureBodySchedule",
    "merge_route2_causal_future_body_observation_classes",
    "project_route2_causal_future_body_decision_branches",
]
