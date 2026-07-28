"""Deterministic next-observation join for derived-pattern source evidence."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Sequence
from typing import Any

from .model import ActivationGroup, ActivationMember, SourceCandidate


ORIGIN_CLUSTER_TOLERANCE_PX = 0.05
STATIONARY_PARENT_TOLERANCE_PX = 1.0
MAX_SAMPLES = 20


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _required_integer(value: object, *, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    return value


def _source_candidates(
    audit: dict[str, Any],
    *,
    row_index: int,
) -> tuple[SourceCandidate, ...]:
    observation = audit.get("derived_source_observation")
    if not isinstance(observation, dict):
        return ()
    capture_end = _required_integer(
        observation.get("frame_after"),
        label="derived source frame_after",
    )
    raw_candidates = observation.get("candidates")
    if not isinstance(raw_candidates, list):
        raise ValueError("derived source candidates must be a list")
    result: list[SourceCandidate] = []
    for raw in raw_candidates:
        if not isinstance(raw, dict):
            raise ValueError("derived source candidate must be an object")
        position = raw.get("position")
        x: float | None = None
        y: float | None = None
        if position is not None:
            if (
                not isinstance(position, list)
                or len(position) != 2
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    for value in position
                )
            ):
                raise ValueError("derived source position is invalid")
            x, y = (float(position[0]), float(position[1]))
        pattern = raw.get("pattern")
        if not isinstance(pattern, dict):
            raise ValueError("derived source candidate omits pattern")
        result.append(
            SourceCandidate(
                row_index=row_index,
                frame=_required_integer(audit.get("frame"), label="frame"),
                gameplay_epoch=_required_integer(
                    audit.get("gameplay_epoch"),
                    label="gameplay_epoch",
                ),
                stage_route_index=_required_integer(
                    audit.get("stage_route_index"),
                    label="stage_route_index",
                ),
                capture_end=capture_end,
                slot=_required_integer(raw.get("slot"), label="source slot"),
                x=x,
                y=y,
                predicted_child_count=_required_integer(
                    pattern.get("predicted_child_count"),
                    label="predicted_child_count",
                ),
            )
        )
    return tuple(result)


def _column(
    evidence: dict[str, Any],
    name: str,
    *,
    count: int,
) -> list[Any]:
    value = evidence.get(name)
    if not isinstance(value, list) or len(value) != count:
        raise ValueError(f"activation evidence column {name} is invalid")
    return value


def _activation_members(
    audit: dict[str, Any],
) -> tuple[tuple[ActivationMember, ...], int, int]:
    observation = audit.get("observation")
    if not isinstance(observation, dict):
        return (), 0, 0
    evidence = observation.get("evidence")
    if not isinstance(evidence, dict):
        return (), 0, 0
    if evidence.get("format") != "columnar_v1":
        raise ValueError("derived source join requires columnar evidence")
    count = _required_integer(
        observation.get("evidence_count"),
        label="evidence_count",
    )
    codes = _column(evidence, "code", count=count)
    slots = _column(evidence, "slot", count=count)
    ages = _column(evidence, "age", count=count)
    geometry = _column(evidence, "geometry", count=count)
    finite = _column(evidence, "geometry_finite", count=count)
    previous_end = _required_integer(
        observation.get("previous_frame_after"),
        label="previous_frame_after",
    )
    support_end = _required_integer(
        observation.get("frame_after"),
        label="frame_after",
    )
    support_start = previous_end + 1
    if support_start > support_end:
        raise ValueError("activation support interval regresses")

    result: list[ActivationMember] = []
    for index in range(count):
        if codes[index] != 3:
            continue
        if finite[index] is not True:
            continue
        slot = _required_integer(slots[index], label="activation slot")
        age = _required_integer(ages[index], label="activation age")
        values = geometry[index]
        if (
            age < 0
            or not isinstance(values, list)
            or len(values) != 6
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in values
            )
        ):
            raise ValueError("activation geometry is invalid")
        x, y, velocity_x, velocity_y = (
            float(value) for value in values[:4]
        )
        result.append(
            ActivationMember(
                slot=slot,
                age=age,
                origin_x=x - velocity_x * age,
                origin_y=y - velocity_y * age,
            )
        )
    return tuple(result), support_start, support_end


def _activation_groups(
    audit: dict[str, Any],
) -> tuple[ActivationGroup, ...]:
    members, support_start, support_end = _activation_members(audit)
    if not members:
        return ()
    parent = list(range(len(members)))

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = root(left)
        right_root = root(right)
        if left_root != right_root:
            parent[right_root] = left_root

    tolerance_squared = ORIGIN_CLUSTER_TOLERANCE_PX**2
    for left, left_member in enumerate(members):
        for right in range(left + 1, len(members)):
            right_member = members[right]
            if left_member.age != right_member.age:
                continue
            distance_squared = (
                (left_member.origin_x - right_member.origin_x) ** 2
                + (left_member.origin_y - right_member.origin_y) ** 2
            )
            if distance_squared <= tolerance_squared:
                union(left, right)

    components: dict[int, list[ActivationMember]] = {}
    for index, member in enumerate(members):
        components.setdefault(root(index), []).append(member)
    frame = _required_integer(audit.get("frame"), label="frame")
    gameplay_epoch = _required_integer(
        audit.get("gameplay_epoch"),
        label="gameplay_epoch",
    )
    stage_route_index = _required_integer(
        audit.get("stage_route_index"),
        label="stage_route_index",
    )
    groups: list[ActivationGroup] = []
    for component in components.values():
        ordered = tuple(sorted(component, key=lambda member: member.slot))
        groups.append(
            ActivationGroup(
                frame=frame,
                gameplay_epoch=gameplay_epoch,
                stage_route_index=stage_route_index,
                support_start=support_start,
                support_end=support_end,
                age=ordered[0].age,
                origin_x=sum(member.origin_x for member in ordered)
                / len(ordered),
                origin_y=sum(member.origin_y for member in ordered)
                / len(ordered),
                members=ordered,
            )
        )
    return tuple(
        sorted(
            groups,
            key=lambda group: (
                group.support_end,
                group.age,
                group.members[0].slot,
            ),
        )
    )


def build_derived_pattern_source_join(
    audits: Sequence[dict[str, Any]],
) -> dict[str, object]:
    """Join each ready source row only to the next accepted pool observation."""

    source_sightings = 0
    source_rows = 0
    next_observation_discontinuities = 0
    activation_groups = 0
    groups_with_count_candidates = 0
    groups_with_geometry_candidates = 0
    groups_with_unique_geometry_candidate = 0
    groups_with_ambiguous_geometry_candidates = 0
    unmatched_source_sightings = 0
    group_sizes: Counter[int] = Counter()
    match_samples: list[dict[str, object]] = []
    unmatched_samples: list[dict[str, object]] = []
    digest_edges: list[dict[str, object]] = []

    for row_index, audit in enumerate(audits):
        sources = _source_candidates(audit, row_index=row_index)
        if not sources:
            continue
        source_rows += 1
        source_sightings += len(sources)
        if row_index + 1 >= len(audits):
            unmatched_source_sightings += len(sources)
            continue
        next_audit = audits[row_index + 1]
        same_scope = (
            next_audit.get("gameplay_epoch")
            == sources[0].gameplay_epoch
            and next_audit.get("stage_route_index")
            == sources[0].stage_route_index
        )
        observation = next_audit.get("observation")
        previous_end = (
            observation.get("previous_frame_after")
            if isinstance(observation, dict)
            else None
        )
        if not same_scope or previous_end != sources[0].capture_end:
            next_observation_discontinuities += 1
            unmatched_source_sightings += len(sources)
            continue

        groups = _activation_groups(next_audit)
        activation_groups += len(groups)
        matched_source_slots: set[int] = set()
        for group in groups:
            group_sizes[len(group.members)] += 1
            count_candidates = [
                source
                for source in sources
                if source.predicted_child_count == len(group.members)
            ]
            if count_candidates:
                groups_with_count_candidates += 1
            geometry_candidates: list[tuple[SourceCandidate, float]] = []
            for source in count_candidates:
                if source.x is None or source.y is None:
                    continue
                distance = math.hypot(
                    source.x - group.origin_x,
                    source.y - group.origin_y,
                )
                edge = {
                    "source_frame": source.frame,
                    "source_capture_end": source.capture_end,
                    "source_slot": source.slot,
                    "activation_frame": group.frame,
                    "activation_support": [
                        group.support_start,
                        group.support_end,
                    ],
                    "activation_slots": [
                        member.slot for member in group.members
                    ],
                    "age": group.age,
                    "predicted_child_count": source.predicted_child_count,
                    "backprojected_origin": [
                        group.origin_x,
                        group.origin_y,
                    ],
                    "source_position": [source.x, source.y],
                    "stationary_parent_distance_px": distance,
                    "stationary_parent_consistent": (
                        distance <= STATIONARY_PARENT_TOLERANCE_PX
                    ),
                }
                digest_edges.append(edge)
                if distance <= STATIONARY_PARENT_TOLERANCE_PX:
                    geometry_candidates.append((source, distance))
                    matched_source_slots.add(source.slot)
            if geometry_candidates:
                groups_with_geometry_candidates += 1
                if len(geometry_candidates) == 1:
                    groups_with_unique_geometry_candidate += 1
                else:
                    groups_with_ambiguous_geometry_candidates += 1
            if (
                (count_candidates or geometry_candidates)
                and len(match_samples) < MAX_SAMPLES
            ):
                match_samples.append(
                    {
                        "source_frame": sources[0].frame,
                        "activation_frame": group.frame,
                        "activation_support": [
                            group.support_start,
                            group.support_end,
                        ],
                        "activation_slots": [
                            member.slot for member in group.members
                        ],
                        "age": group.age,
                        "backprojected_origin": [
                            group.origin_x,
                            group.origin_y,
                        ],
                        "count_candidate_slots": [
                            source.slot for source in count_candidates
                        ],
                        "geometry_candidate_slots": [
                            source.slot
                            for source, _distance in geometry_candidates
                        ],
                        "geometry_candidate_distances_px": [
                            distance
                            for _source, distance in geometry_candidates
                        ],
                    }
                )
        unmatched = [
            source.slot
            for source in sources
            if source.slot not in matched_source_slots
        ]
        unmatched_source_sightings += len(unmatched)
        if unmatched and len(unmatched_samples) < MAX_SAMPLES:
            unmatched_samples.append(
                {
                    "source_frame": sources[0].frame,
                    "source_capture_end": sources[0].capture_end,
                    "source_slots": unmatched,
                    "next_activation_frame": next_audit.get("frame"),
                    "next_activation_group_count": len(groups),
                }
            )

    return {
        "schema": "th08-derived-pattern-source-next-observation-join-v1",
        "parameters": {
            "origin_cluster_tolerance_px": ORIGIN_CLUSTER_TOLERANCE_PX,
            "stationary_parent_tolerance_px": (
                STATIONARY_PARENT_TOLERANCE_PX
            ),
            "join_horizon": "next_accepted_pool_observation_only",
        },
        "source_rows": source_rows,
        "source_sightings": source_sightings,
        "activation_groups_after_source_rows": activation_groups,
        "activation_group_sizes": {
            str(key): value for key, value in sorted(group_sizes.items())
        },
        "groups_with_count_candidates": groups_with_count_candidates,
        "groups_with_stationary_geometry_candidates": (
            groups_with_geometry_candidates
        ),
        "groups_with_unique_stationary_geometry_candidate": (
            groups_with_unique_geometry_candidate
        ),
        "groups_with_ambiguous_stationary_geometry_candidates": (
            groups_with_ambiguous_geometry_candidates
        ),
        "unmatched_source_sightings": unmatched_source_sightings,
        "next_observation_discontinuities": (
            next_observation_discontinuities
        ),
        "match_samples": match_samples,
        "unmatched_source_samples": unmatched_samples,
        "complete_edge_digest": _canonical_digest(digest_edges),
        "semantics": {
            "backprojected_origin": (
                "observed_position_minus_observed_velocity_times_age"
            ),
            "stationary_geometry_candidate": (
                "diagnostic compatibility under a stationary-parent proxy; "
                "parent motion and update order remain unresolved"
            ),
            "source_attribution_authority": "none",
            "future_hazard_coverage": "unknown",
            "hit_outcome_used": False,
        },
    }


__all__ = [
    "ORIGIN_CLUSTER_TOLERANCE_PX",
    "STATIONARY_PARENT_TOLERANCE_PX",
    "build_derived_pattern_source_join",
]
