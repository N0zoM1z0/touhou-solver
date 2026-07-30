"""Offline immutable TH08 future body/flag/geometry schedule sets."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import dataclass
from typing import Callable, Hashable, Mapping

from th08_enemy_mode import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG,
    ENEMY_SECONDARY_CHARACTER_SYNC_FLAG,
    Route2AsyncOrderedModeDecisionBranch,
    Route2EnemyModeBody,
    Route2EnemyModeStateKey,
    Route2ModeHazardFrame,
    project_route2_async_ordered_mode_decision_branches,
)
from touhou_control.ordered_input_transaction_oracle import (
    OrderedInputBelief,
)
from touhou_control.pipeline_identity import VersionIdentity


BRANCH_SCHEMA = "th08-route2-future-body-schedule-branch-v1"
SET_SCHEMA = "th08-route2-future-body-schedule-set-v1"
OFFLINE_AUTHORITY = "offline_fixture_or_retrospective_only"
Route2ObservedBodyState = tuple[
    tuple[int, int, int, int, int, int, int],
    ...,
]


def _binary32(value: float, *, name: str) -> tuple[float, str]:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a canonical finite binary32 value")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be a canonical finite binary32 value")
    packed = struct.pack("<f", numeric)
    canonical = struct.unpack("<f", packed)[0]
    if numeric != canonical:
        raise ValueError(f"{name} must be exactly representable as binary32")
    return canonical, f"0x{struct.unpack('<I', packed)[0]:08x}"


def _sha256_record(record: dict[str, object]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class Route2FutureBodySample:
    """One mode-independent body and binary32 geometry at one future step."""

    identity: int
    base_flags: int
    x: float
    y: float
    half_width: float
    half_height: float
    uncertainty: float = 0.0

    def __post_init__(self) -> None:
        if type(self.identity) is not int or self.identity < 0:
            raise ValueError("future body identity must be nonnegative")
        if (
            type(self.base_flags) is not int
            or not 0 <= self.base_flags <= 0xFFFFFFFF
        ):
            raise ValueError("future body flags must fit one u32 word")
        if (
            self.base_flags & ENEMY_ACTIVE_FLAG
            and self.base_flags & ENEMY_SECONDARY_CHARACTER_SYNC_FLAG
            and self.base_flags & ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG
        ):
            raise ValueError(
                "mode-independent synchronized body must clear flag 0x800"
            )
        for name, value in (
            ("x", self.x),
            ("y", self.y),
            ("half width", self.half_width),
            ("half height", self.half_height),
            ("uncertainty", self.uncertainty),
        ):
            canonical, _bits = _binary32(value, name=name)
            if name in ("half width", "half height", "uncertainty"):
                if canonical < 0.0:
                    raise ValueError(
                        "future body extents and uncertainty must be nonnegative"
                    )

    @property
    def mode_body(self) -> Route2EnemyModeBody:
        return Route2EnemyModeBody(
            identity=self.identity,
            raw_flags=self.base_flags,
        )

    def record(self) -> dict[str, object]:
        def bits(value: float, name: str) -> str:
            return _binary32(value, name=name)[1]

        return {
            "identity": self.identity,
            "base_flags": self.base_flags,
            "geometry_binary32": {
                "x": bits(self.x, "x"),
                "y": bits(self.y, "y"),
                "half_width": bits(self.half_width, "half width"),
                "half_height": bits(self.half_height, "half height"),
                "uncertainty": bits(self.uncertainty, "uncertainty"),
            },
        }


@dataclass(frozen=True)
class Route2FutureBodyFrame:
    """Complete body/flag/geometry set for one future physical update."""

    physical_step: int
    bodies: tuple[Route2FutureBodySample, ...]

    def __post_init__(self) -> None:
        if type(self.physical_step) is not int or self.physical_step <= 0:
            raise ValueError("future body frame step must be positive")
        if type(self.bodies) is not tuple or any(
            type(body) is not Route2FutureBodySample
            for body in self.bodies
        ):
            raise ValueError(
                "future body frame bodies must be an immutable sample tuple"
            )
        identities = tuple(body.identity for body in self.bodies)
        if identities != tuple(sorted(identities)):
            raise ValueError("future body identities must be sorted")
        if len(identities) != len(set(identities)):
            raise ValueError("future body identities must be unique")

    @property
    def mode_bodies(self) -> tuple[Route2EnemyModeBody, ...]:
        return tuple(body.mode_body for body in self.bodies)

    def record(self) -> dict[str, object]:
        return {
            "physical_step": self.physical_step,
            "bodies": [body.record() for body in self.bodies],
        }


@dataclass(frozen=True)
class Route2FutureBodyScheduleBranch:
    """One exact finite nature branch over future body states."""

    frames: tuple[Route2FutureBodyFrame, ...]
    schema: str = BRANCH_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != BRANCH_SCHEMA:
            raise ValueError("unsupported future body branch schema")
        if type(self.frames) is not tuple or any(
            type(frame) is not Route2FutureBodyFrame
            for frame in self.frames
        ):
            raise ValueError(
                "future schedule frames must be an immutable frame tuple"
            )
        if not self.frames:
            raise ValueError("future body schedule branch cannot be empty")
        steps = tuple(frame.physical_step for frame in self.frames)
        if steps != tuple(range(1, len(self.frames) + 1)):
            raise ValueError(
                "future body schedule steps must be contiguous from one"
            )

    def payload(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "frames": [frame.record() for frame in self.frames],
        }

    @property
    def digest(self) -> str:
        return _sha256_record(self.payload())


@dataclass(frozen=True)
class Route2FutureBodyScheduleSet:
    """One content-addressed offline-only finite future schedule support."""

    root_physical_update: int
    clock_version: VersionIdentity
    source: str
    source_sha256: str
    branches: tuple[Route2FutureBodyScheduleBranch, ...]
    schema: str = SET_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SET_SCHEMA:
            raise ValueError("unsupported future body schedule-set schema")
        if (
            type(self.root_physical_update) is not int
            or self.root_physical_update < 0
        ):
            raise ValueError("future schedule root update must be nonnegative")
        if (
            type(self.clock_version) is not VersionIdentity
            or type(self.clock_version.components) is not tuple
            or any(
                type(component) is not tuple
                for component in self.clock_version.components
            )
        ):
            raise ValueError(
                "future schedule clock version must be canonical and immutable"
            )
        if type(self.source) is not str or not self.source:
            raise ValueError("future schedule source must not be empty")
        if (
            type(self.source_sha256) is not str
            or
            len(self.source_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.source_sha256
            )
        ):
            raise ValueError("future schedule source SHA-256 is invalid")
        if type(self.branches) is not tuple or any(
            type(branch) is not Route2FutureBodyScheduleBranch
            for branch in self.branches
        ):
            raise ValueError(
                "future schedule branches must be an immutable branch tuple"
            )
        if not self.branches:
            raise ValueError("future schedule set cannot be empty")
        digests = tuple(branch.digest for branch in self.branches)
        if digests != tuple(sorted(digests)):
            raise ValueError("future schedule branches must be digest-sorted")
        if len(digests) != len(set(digests)):
            raise ValueError("future schedule branches must be unique")
        horizons = {len(branch.frames) for branch in self.branches}
        if len(horizons) != 1:
            raise ValueError(
                "future schedule branches must share one physical horizon"
            )

    @classmethod
    def from_branches(
        cls,
        *,
        root_physical_update: int,
        clock_version: VersionIdentity,
        source: str,
        source_sha256: str,
        branches: tuple[Route2FutureBodyScheduleBranch, ...],
    ) -> Route2FutureBodyScheduleSet:
        return cls(
            root_physical_update=root_physical_update,
            clock_version=clock_version,
            source=source,
            source_sha256=source_sha256,
            branches=tuple(sorted(branches, key=lambda branch: branch.digest)),
        )

    @property
    def horizon(self) -> int:
        return len(self.branches[0].frames)

    def payload(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "authority": OFFLINE_AUTHORITY,
            "physical_predictive_authority": False,
            "root_physical_update": self.root_physical_update,
            "clock_version": self.clock_version.record(),
            "source": self.source,
            "source_sha256": self.source_sha256,
            "branches": [
                {
                    **branch.payload(),
                    "sha256": branch.digest,
                }
                for branch in self.branches
            ],
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
class Route2VersionedAsyncModeDecisionBranch:
    """One hidden schedule/input branch under one immutable schedule set."""

    future_schedule_version: str
    future_schedule_branch: str
    observed_body_state: Route2ObservedBodyState
    mode_branch: Route2AsyncOrderedModeDecisionBranch


@dataclass(frozen=True)
class Route2VersionedModeObservationKey:
    """Next observation key including immutable future schedule identity."""

    base_observation: Hashable
    future_schedule_version: str
    physical_step: int
    active_mask: int
    held_desired_mask: int
    mode_state: Route2EnemyModeStateKey
    observed_body_state: Route2ObservedBodyState


@dataclass(frozen=True)
class Route2VersionedAsyncModeObservationClass:
    """Non-clairvoyant merge across hidden schedule and input branches."""

    key: Route2VersionedModeObservationKey
    successor_input_belief: OrderedInputBelief
    hidden_branches: tuple[Route2VersionedAsyncModeDecisionBranch, ...]


def project_route2_versioned_async_mode_decision_branches(
    *,
    future_schedule: Route2FutureBodyScheduleSet,
    input_belief: OrderedInputBelief,
    selected_action: str,
    action_masks: Mapping[str, int],
    supported_mask: int,
    post_dispatch_delay_frames: tuple[int, ...],
    dispatch_callback_count_support: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    initial_mode_state: Route2EnemyModeStateKey,
) -> tuple[Route2VersionedAsyncModeDecisionBranch, ...]:
    """Compose every hidden schedule branch under one uniform action."""

    if (
        not decision_frame_support
        or decision_frame_support[-1] > future_schedule.horizon
    ):
        raise ValueError(
            "immutable future schedule does not cover cadence support"
        )
    results: list[Route2VersionedAsyncModeDecisionBranch] = []
    for schedule_branch in future_schedule.branches:
        mode_branches = project_route2_async_ordered_mode_decision_branches(
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
            enemy_flag_frames=tuple(
                frame.mode_bodies for frame in schedule_branch.frames
            ),
        )
        for mode_branch in mode_branches:
            schedule_frame = schedule_branch.frames[
                mode_branch.cadence_frames - 1
            ]
            hazard_frame = mode_branch.hazard_branch.frames[-1]
            if tuple(
                body.identity for body in schedule_frame.bodies
            ) != tuple(
                projection.identity
                for projection in hazard_frame.body_projections
            ):
                raise RuntimeError(
                    "mode projection changed future body identity order"
                )
            observed_body_state = tuple(
                (
                    body.identity,
                    projection.projection.projected_flags,
                    int(_binary32(body.x, name="x")[1], 16),
                    int(_binary32(body.y, name="y")[1], 16),
                    int(
                        _binary32(
                            body.half_width,
                            name="half width",
                        )[1],
                        16,
                    ),
                    int(
                        _binary32(
                            body.half_height,
                            name="half height",
                        )[1],
                        16,
                    ),
                    int(
                        _binary32(
                            body.uncertainty,
                            name="uncertainty",
                        )[1],
                        16,
                    ),
                )
                for body, projection in zip(
                    schedule_frame.bodies,
                    hazard_frame.body_projections,
                    strict=True,
                )
            )
            results.append(
                Route2VersionedAsyncModeDecisionBranch(
                    future_schedule_version=future_schedule.digest,
                    future_schedule_branch=schedule_branch.digest,
                    observed_body_state=observed_body_state,
                    mode_branch=mode_branch,
                )
            )
    return tuple(results)


def merge_route2_versioned_async_mode_observation_classes(
    branches: tuple[Route2VersionedAsyncModeDecisionBranch, ...],
    *,
    base_observation: Callable[
        [Route2VersionedAsyncModeDecisionBranch, Route2ModeHazardFrame],
        Hashable,
    ],
) -> tuple[Route2VersionedAsyncModeObservationClass, ...]:
    """Merge hidden schedule/input histories without revealing branch ID."""

    if not branches:
        raise ValueError("at least one versioned mode branch is required")
    schedule_versions = {
        branch.future_schedule_version for branch in branches
    }
    if len(schedule_versions) != 1:
        raise ValueError("cannot merge different future schedule versions")
    grouped: dict[
        Route2VersionedModeObservationKey,
        list[Route2VersionedAsyncModeDecisionBranch],
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
        key = Route2VersionedModeObservationKey(
            base_observation=base,
            future_schedule_version=branch.future_schedule_version,
            physical_step=mode_branch.cadence_frames,
            active_mask=successor.active_mask,
            held_desired_mask=successor.held_desired_mask,
            mode_state=mode_branch.successor_mode_state,
            observed_body_state=branch.observed_body_state,
        )
        grouped.setdefault(key, []).append(branch)
    return tuple(
        Route2VersionedAsyncModeObservationClass(
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
    "BRANCH_SCHEMA",
    "OFFLINE_AUTHORITY",
    "Route2FutureBodyFrame",
    "Route2FutureBodySample",
    "Route2FutureBodyScheduleBranch",
    "Route2FutureBodyScheduleSet",
    "Route2ObservedBodyState",
    "Route2VersionedAsyncModeDecisionBranch",
    "Route2VersionedAsyncModeObservationClass",
    "Route2VersionedModeObservationKey",
    "SET_SCHEMA",
    "merge_route2_versioned_async_mode_observation_classes",
    "project_route2_versioned_async_mode_decision_branches",
]
