"""Chronological exact-root and fail-closed coverage reconstruction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from th08_pipeline_actions import th08_complete_mask_token
from touhou_control.hazard_coverage import (
    HazardCoverageAssessment,
    HazardCoverageClass,
    HazardCoverageSlab,
    assess_hazard_coverage,
)
from touhou_control.pipeline_identity import (
    CanonicalPipelineRoot,
    PipelineObservationIdentity,
    PipelineQueryIdentity,
    VersionIdentity,
)

from .types import CompleteMaskCapsuleRoot


def _version(record: object) -> VersionIdentity:
    if not isinstance(record, Mapping):
        raise ValueError("pipeline version record is missing")
    namespace = record.get("namespace")
    components = record.get("components")
    if not isinstance(namespace, str) or not isinstance(components, Mapping):
        raise ValueError("pipeline version record is malformed")
    normalized: dict[str, str | int | bool | None] = {}
    for name, value in components.items():
        if not isinstance(name, str) or not (
            value is None or type(value) in (str, int, bool)
        ):
            raise ValueError("pipeline version components are malformed")
        normalized[name] = value
    return VersionIdentity.from_mapping(namespace, normalized)


def identity_from_record(record: object) -> PipelineQueryIdentity:
    if not isinstance(record, Mapping):
        raise ValueError("canonical pipeline identity is missing")
    observation = record.get("observation")
    root = record.get("root")
    versions = record.get("versions")
    if not all(
        isinstance(value, Mapping)
        for value in (observation, root, versions)
    ):
        raise ValueError("canonical pipeline identity is malformed")
    assert isinstance(observation, Mapping)
    assert isinstance(root, Mapping)
    assert isinstance(versions, Mapping)
    identity = PipelineQueryIdentity(
        observation=PipelineObservationIdentity(
            gameplay_epoch=int(observation["gameplay_epoch"]),
            stage_route_index=int(observation["stage_route_index"]),
            spell_id=(
                None
                if observation.get("spell_id") is None
                else int(observation["spell_id"])
            ),
            manager_frame=int(observation["manager_frame"]),
            query_frame=int(observation["query_frame"]),
            target_frame=int(observation["target_frame"]),
            player_x_bits=str(observation["player_x_bits"]),
            player_y_bits=str(observation["player_y_bits"]),
        ),
        root=CanonicalPipelineRoot(
            supported_mask=int(root["supported_mask"]),
            active_mask=int(root["active_mask"]),
            held_desired_mask=int(root["held_desired_mask"]),
            pending_mask=(
                None
                if root.get("pending_mask") is None
                else int(root["pending_mask"])
            ),
            remaining_delay_support=tuple(
                int(value)
                for value in root.get("remaining_delay_support", ())
            ),
        ),
        observation_version=_version(versions.get("observation")),
        hazard_version=_version(versions.get("hazard")),
        policy_version=_version(versions.get("policy")),
        model_version=_version(versions.get("model")),
        clock_version=_version(versions.get("clock")),
        schema=str(record.get("schema")),
    )
    if record.get("sha256") != identity.digest:
        raise ValueError("canonical pipeline identity digest mismatch")
    return identity


def coverage_from_record(record: object) -> HazardCoverageAssessment:
    if not isinstance(record, Mapping):
        raise ValueError("hazard coverage record is missing")
    slabs_raw = record.get("slabs")
    if not isinstance(slabs_raw, list):
        raise ValueError("hazard coverage slabs are missing")
    if any(not isinstance(slab, Mapping) for slab in slabs_raw):
        raise ValueError("hazard coverage slab is malformed")
    slabs = tuple(
        HazardCoverageSlab(
            start_frame=int(slab["start_frame"]),
            end_frame=int(slab["end_frame"]),
            coverage_class=HazardCoverageClass(
                str(slab["coverage_class"])
            ),
            source=str(slab["source"]),
            version=_version(slab["version"]),
            rationale=str(slab["rationale"]),
        )
        for slab in slabs_raw
    )
    assessment = assess_hazard_coverage(
        root_frame=int(record["root_frame"]),
        horizon_frame=int(record["horizon_frame"]),
        slabs=slabs,
    )
    if assessment.record() != dict(record):
        raise ValueError("hazard coverage record does not replay")
    return assessment


def _capsule_name(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value.replace("\\", "/").rsplit("/", 1)[-1]


def read_complete_mask_roots(
    trace: Path,
) -> tuple[list[CompleteMaskCapsuleRoot], list[str]]:
    roots: list[CompleteMaskCapsuleRoot] = []
    failures: list[str] = []
    with trace.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                failures.append(
                    f"line {line_number}: JSONDecodeError: {error.msg}"
                )
                continue
            if not isinstance(row, Mapping):
                failures.append(
                    f"line {line_number}: ValueError: trace row is not an object"
                )
                continue
            if row.get("kind") != "decision":
                continue
            corridor = row.get("corridor")
            local_root = row.get("local_pipeline_root")
            if not isinstance(corridor, Mapping) or not isinstance(
                local_root, Mapping
            ):
                continue
            viability = corridor.get("viability")
            capsule = _capsule_name(corridor.get("audit_capsule"))
            if (
                capsule is None
                or not isinstance(viability, Mapping)
                or not viability.get("available")
                or local_root.get("canonical_status") != "available"
            ):
                continue
            try:
                identity = identity_from_record(
                    local_root.get("canonical_identity")
                )
                coverage = coverage_from_record(
                    local_root.get("hazard_coverage")
                )
                if identity.observation.query_frame != int(
                    viability["query_frame"]
                ):
                    raise ValueError(
                        "pipeline and viability query frames differ"
                    )
                if coverage.root_frame != identity.observation.query_frame:
                    raise ValueError(
                        "coverage and pipeline root frames differ"
                    )
                active_token = th08_complete_mask_token(
                    identity.root.active_mask
                )
                held_token = th08_complete_mask_token(
                    identity.root.held_desired_mask
                )
                pending_token = (
                    None
                    if identity.root.pending_mask is None
                    else th08_complete_mask_token(
                        identity.root.pending_mask
                    )
                )
                delays = tuple(
                    sorted(
                        set(
                            int(value)
                            for value in row["control_delay_candidates"]
                        )
                    )
                )
                if (
                    not delays
                    or any(delay <= 0 for delay in delays)
                ):
                    raise ValueError(
                        "control-delay candidates must be positive"
                    )
                nominal_delay = int(row["control_delay_frames"])
                if nominal_delay not in delays:
                    raise ValueError(
                        "nominal control delay is outside its support"
                    )
                state_viable = viability["state_viable"]
                if type(state_viable) is not bool:
                    raise ValueError(
                        "trace state viability must be Boolean"
                    )
                roots.append(
                    CompleteMaskCapsuleRoot(
                        trace_line=line_number,
                        decision_frame=int(row["frame"]),
                        source_frame=int(corridor["source_frame"]),
                        capsule=capsule,
                        identity=identity,
                        coverage=coverage,
                        active_token=active_token,
                        held_token=held_token,
                        pending_token=pending_token,
                        remaining_delay_support=(
                            identity.root.remaining_delay_support
                        ),
                        delay_frames=delays,
                        nominal_delay=nominal_delay,
                        trace_state_viable=state_viable,
                        issued_mask=int(row["mask"]),
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                failures.append(
                    f"line {line_number}, frame {row.get('frame')}: "
                    f"{type(error).__name__}: {error}"
                )
    return roots, failures


__all__ = [
    "coverage_from_record",
    "identity_from_record",
    "read_complete_mask_roots",
]
