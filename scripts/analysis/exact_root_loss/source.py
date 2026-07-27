"""Read and content-address retained trace and capsule evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from touhou_control.viability_audit_capsule import (
    read_viability_audit_metadata,
)


@dataclass(frozen=True)
class KernelSample:
    decision_frame: int
    query_frame: int
    state_viable: bool
    capsule: str
    capsule_source_frame: int
    projected_x: float
    projected_y: float
    active_action: str
    current_delay_support: tuple[int, ...]
    gameplay_epoch: int | None
    stage_route_index: int | None
    spell_id: int | None
    policy_status: str | None

    def payload(self) -> dict[str, Any]:
        result = asdict(self)
        result["current_delay_support"] = list(self.current_delay_support)
        result["projected_x_hex"] = self.projected_x.hex()
        result["projected_y_hex"] = self.projected_y.hex()
        return result


@dataclass(frozen=True)
class TraceEvidence:
    hit_frames: tuple[int, ...]
    samples: tuple[KernelSample, ...]
    target_samples: dict[int, KernelSample]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def capsule_basename(raw: object) -> str:
    text = str(raw or "").replace("\\", "/")
    return text.rsplit("/", 1)[-1]


def _optional_int(raw: object) -> int | None:
    return None if raw is None else int(raw)


def _sample(row: dict[str, Any]) -> KernelSample | None:
    corridor = row.get("corridor")
    if not isinstance(corridor, dict):
        return None
    viability = corridor.get("viability")
    player = row.get("player")
    if (
        not isinstance(viability, dict)
        or viability.get("available") is not True
        or not isinstance(player, dict)
    ):
        return None
    capsule = capsule_basename(corridor.get("audit_capsule"))
    if not capsule:
        return None
    raw_delays = row.get("control_delay_candidates")
    if not isinstance(raw_delays, (list, tuple)):
        raw_delays = viability.get("current_delay_frames", ())
    spell = row.get("spell")
    return KernelSample(
        decision_frame=int(row["frame"]),
        query_frame=int(viability["query_frame"]),
        state_viable=bool(viability["state_viable"]),
        capsule=capsule,
        capsule_source_frame=int(corridor["source_frame"]),
        projected_x=float(player["projected_x"]),
        projected_y=float(player["projected_y"]),
        active_action=str(viability["active_action"]),
        current_delay_support=tuple(int(value) for value in raw_delays),
        gameplay_epoch=_optional_int(row.get("gameplay_epoch")),
        stage_route_index=_optional_int(row.get("stage_route_index")),
        spell_id=(
            _optional_int(spell.get("spell_id"))
            if isinstance(spell, dict)
            else None
        ),
        policy_status=(
            str(corridor["policy_status"])
            if corridor.get("policy_status") is not None
            else None
        ),
    )


def read_trace_evidence(
    trace_path: Path,
    *,
    target_decision_frames: set[int],
) -> TraceEvidence:
    hit_frames: list[int] = []
    samples: list[KernelSample] = []
    target_samples: dict[int, KernelSample] = {}
    with trace_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{trace_path}:{line_number}: invalid JSON"
                ) from exc
            if row.get("hit_started") is True:
                hit_frames.append(int(row["frame"]))
            sample = _sample(row)
            if sample is None:
                continue
            samples.append(sample)
            if sample.decision_frame in target_decision_frames:
                if sample.decision_frame in target_samples:
                    raise ValueError(
                        f"duplicate target frame {sample.decision_frame}"
                    )
                target_samples[sample.decision_frame] = sample
    missing = target_decision_frames - target_samples.keys()
    if missing:
        raise ValueError(
            "trace is missing dossier decision frames: "
            + ", ".join(str(frame) for frame in sorted(missing))
        )
    return TraceEvidence(
        hit_frames=tuple(hit_frames),
        samples=tuple(samples),
        target_samples=target_samples,
    )


def transition_evidence(
    trace: TraceEvidence,
    *,
    minimum_pre_hit_frames: int,
) -> list[dict[str, Any]]:
    """Find the latest viable-to-empty boundary before every retained hit."""

    transitions: list[dict[str, Any]] = []
    for hit_frame in trace.hit_frames:
        prior = [
            sample
            for sample in trace.samples
            if sample.decision_frame < hit_frame
        ]
        if not prior:
            raise ValueError(f"hit {hit_frame} has no prior kernel samples")
        terminal = prior[-1]
        comparable = [
            sample
            for sample in prior
            if sample.gameplay_epoch == terminal.gameplay_epoch
            and sample.stage_route_index == terminal.stage_route_index
        ]
        boundaries = [
            (left, right)
            for left, right in zip(comparable, comparable[1:])
            if left.state_viable and not right.state_viable
        ]
        boundary = boundaries[-1] if boundaries else None
        window_start = hit_frame - minimum_pre_hit_frames
        if boundary is not None:
            window_start = min(window_start, boundary[0].decision_frame)
        transitions.append(
            {
                "hit_frame": hit_frame,
                "minimum_pre_hit_frames": minimum_pre_hit_frames,
                "window_start_frame": window_start,
                "window_span_frames": hit_frame - window_start,
                "terminal_pre_hit_sample": terminal.payload(),
                "nonempty_to_empty": (
                    {
                        "nonempty": boundary[0].payload(),
                        "first_empty": boundary[1].payload(),
                        "lead_frames": (
                            hit_frame - boundary[1].decision_frame
                        ),
                        "evidence_level": "observed",
                    }
                    if boundary is not None
                    else None
                ),
                "conclusion": {
                    "code": (
                        "NONEMPTY_TO_EMPTY_BOUNDARY"
                        if boundary is not None
                        else "TRANSITION_NOT_OBSERVED"
                    ),
                    "evidence_level": (
                        "observed" if boundary is not None else "hypothesized"
                    ),
                    "claim": (
                        "Latest same-epoch published-kernel transition "
                        "before contact."
                        if boundary is not None
                        else "No same-epoch viable-to-empty boundary was "
                        "retained before contact."
                    ),
                },
            }
        )
    return transitions


def capsule_identity(
    path: Path,
    *,
    expected_source_frame: int,
    expected_snapshot_frame: int,
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    metadata = read_viability_audit_metadata(path)
    source_frame = int(metadata["source_frame"])
    snapshot_frame = int(metadata["snapshot_frame"])
    if source_frame != expected_source_frame:
        raise ValueError(
            f"{path.name}: source frame {source_frame} != "
            f"{expected_source_frame}"
        )
    if snapshot_frame != expected_snapshot_frame:
        raise ValueError(
            f"{path.name}: snapshot frame {snapshot_frame} != "
            f"{expected_snapshot_frame}"
        )
    contract = {
        "source_frame": source_frame,
        "snapshot_frame": snapshot_frame,
        "forecast_lead_frames": int(metadata["forecast_lead_frames"]),
        "context_key": metadata.get("context_key"),
        "active_action": str(metadata["active_action"]),
        "control_delay_candidates": [
            int(value) for value in metadata["control_delay_candidates"]
        ],
        "observed_control_delay_candidates": [
            int(value)
            for value in metadata.get(
                "observed_control_delay_candidates",
                metadata["control_delay_candidates"],
            )
        ],
        "nominal_control_delay": int(metadata["nominal_control_delay"]),
        "grid_step": float(metadata["grid_step"]),
        "frames_per_layer": int(metadata["frames_per_layer"]),
        "horizon_frames": int(metadata["horizon_frames"]),
    }
    return {
        "name": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "decoded": True,
        "contract": contract,
        "contract_sha256": canonical_sha256(contract),
    }


def capsule_dependency_identity(
    path: Path,
    *,
    expected_source_frame: int,
) -> dict[str, Any]:
    """Content-address a replay dependency not selected as a primary root."""

    if not path.is_file():
        raise FileNotFoundError(path)
    metadata = read_viability_audit_metadata(path)
    return capsule_identity(
        path,
        expected_source_frame=expected_source_frame,
        expected_snapshot_frame=int(metadata["snapshot_frame"]),
    )
