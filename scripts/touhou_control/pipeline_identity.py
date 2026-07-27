"""Canonical, content-addressed identities for observable input-pipeline roots.

The finite belief recurrence uses movement action names, while the physical
actuator decides whether to write by comparing complete supported input masks.
This module keeps those responsibilities separate: a canonical root retains
the complete masks and can then be joined with immutable observation, model,
hazard, policy, and clock versions.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import dataclass
from typing import Mapping


PIPELINE_IDENTITY_SCHEMA = "pipeline-query-identity-v1"

VersionScalar = str | int | bool | None


def _strict_int(value: object, *, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def float32_bits(value: float) -> str:
    """Return an exact, JSON-stable IEEE-754 binary32 identity."""

    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError("pipeline identity coordinates must be finite")
    bits = struct.unpack("<I", struct.pack("<f", numeric))[0]
    return f"0x{bits:08x}"


@dataclass(frozen=True)
class VersionIdentity:
    """A named immutable version with scalar, canonically ordered fields."""

    namespace: str
    components: tuple[tuple[str, VersionScalar], ...] = ()

    def __post_init__(self) -> None:
        if not self.namespace:
            raise ValueError("version namespace must not be empty")
        names = tuple(name for name, _value in self.components)
        if any(not name for name in names):
            raise ValueError("version component names must not be empty")
        if names != tuple(sorted(names)) or len(names) != len(set(names)):
            raise ValueError(
                "version components must have sorted, unique names"
            )
        for name, value in self.components:
            if not (
                value is None
                or type(value) in (str, int, bool)
            ):
                raise ValueError(
                    f"version component {name!r} must be a JSON scalar"
                )

    @classmethod
    def from_mapping(
        cls,
        namespace: str,
        components: Mapping[str, VersionScalar],
    ) -> VersionIdentity:
        return cls(namespace, tuple(sorted(components.items())))

    def record(self) -> dict[str, object]:
        return {
            "namespace": self.namespace,
            "components": {
                name: value for name, value in self.components
            },
        }


@dataclass(frozen=True)
class CanonicalPipelineRoot:
    """Complete actuator-visible root for one-pending last-write-wins."""

    supported_mask: int
    active_mask: int
    held_desired_mask: int
    pending_mask: int | None = None
    remaining_delay_support: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        supported = _strict_int(
            self.supported_mask,
            name="supported mask",
        )
        active = _strict_int(self.active_mask, name="active mask")
        held = _strict_int(
            self.held_desired_mask,
            name="held desired mask",
        )
        if active & ~supported or held & ~supported:
            raise ValueError("pipeline root contains unsupported mask bits")
        support = self.remaining_delay_support
        if (
            any(type(value) is not int or value <= 0 for value in support)
            or support != tuple(sorted(set(support)))
        ):
            raise ValueError(
                "remaining-delay support must be sorted, unique, and positive"
            )
        if self.pending_mask is None:
            if support:
                raise ValueError(
                    "no-pending root cannot retain delay support"
                )
            if active != held:
                raise ValueError(
                    "no-pending root requires held desired to equal active"
                )
            return
        pending = _strict_int(self.pending_mask, name="pending mask")
        if pending & ~supported:
            raise ValueError("pending mask contains unsupported bits")
        if pending != held:
            raise ValueError(
                "one-pending root requires pending to equal held desired"
            )
        if not support:
            raise ValueError("pending root requires remaining-delay support")

    def record(self) -> dict[str, object]:
        return {
            "supported_mask": self.supported_mask,
            "active_mask": self.active_mask,
            "held_desired_mask": self.held_desired_mask,
            "pending_mask": self.pending_mask,
            "remaining_delay_support": list(
                self.remaining_delay_support
            ),
        }


@dataclass(frozen=True)
class PipelineObservationIdentity:
    """Exact observable state used to specialize an immutable policy."""

    gameplay_epoch: int
    stage_route_index: int
    spell_id: int | None
    manager_frame: int
    query_frame: int
    target_frame: int
    player_x_bits: str
    player_y_bits: str

    def __post_init__(self) -> None:
        _strict_int(self.gameplay_epoch, name="gameplay epoch")
        _strict_int(self.stage_route_index, name="stage route index")
        if self.spell_id is not None:
            _strict_int(self.spell_id, name="spell id")
        _strict_int(self.manager_frame, name="manager frame")
        _strict_int(self.query_frame, name="query frame")
        _strict_int(self.target_frame, name="target frame")
        for name, value in (
            ("player x bits", self.player_x_bits),
            ("player y bits", self.player_y_bits),
        ):
            if (
                not isinstance(value, str)
                or len(value) != 10
                or not value.startswith("0x")
            ):
                raise ValueError(f"{name} must be an 8-digit hex word")
            try:
                int(value[2:], 16)
            except ValueError as exc:
                raise ValueError(
                    f"{name} must be an 8-digit hex word"
                ) from exc

    @classmethod
    def from_coordinates(
        cls,
        *,
        gameplay_epoch: int,
        stage_route_index: int,
        spell_id: int | None,
        manager_frame: int,
        query_frame: int,
        target_frame: int,
        player_x: float,
        player_y: float,
    ) -> PipelineObservationIdentity:
        return cls(
            gameplay_epoch=gameplay_epoch,
            stage_route_index=stage_route_index,
            spell_id=spell_id,
            manager_frame=manager_frame,
            query_frame=query_frame,
            target_frame=target_frame,
            player_x_bits=float32_bits(player_x),
            player_y_bits=float32_bits(player_y),
        )

    def record(self) -> dict[str, object]:
        return {
            "gameplay_epoch": self.gameplay_epoch,
            "stage_route_index": self.stage_route_index,
            "spell_id": self.spell_id,
            "manager_frame": self.manager_frame,
            "query_frame": self.query_frame,
            "target_frame": self.target_frame,
            "player_x_bits": self.player_x_bits,
            "player_y_bits": self.player_y_bits,
        }


@dataclass(frozen=True)
class PipelineQueryIdentity:
    """Content-addressed join of one observable root and all model versions."""

    observation: PipelineObservationIdentity
    root: CanonicalPipelineRoot
    observation_version: VersionIdentity
    hazard_version: VersionIdentity
    policy_version: VersionIdentity
    model_version: VersionIdentity
    clock_version: VersionIdentity
    schema: str = PIPELINE_IDENTITY_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != PIPELINE_IDENTITY_SCHEMA:
            raise ValueError("unsupported pipeline identity schema")

    def payload(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "observation": self.observation.record(),
            "root": self.root.record(),
            "versions": {
                "observation": self.observation_version.record(),
                "hazard": self.hazard_version.record(),
                "policy": self.policy_version.record(),
                "model": self.model_version.record(),
                "clock": self.clock_version.record(),
            },
        }

    @property
    def digest(self) -> str:
        encoded = json.dumps(
            self.payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
        return hashlib.sha256(encoded).hexdigest()

    def record(self) -> dict[str, object]:
        return {
            **self.payload(),
            "sha256": self.digest,
            "role": "shadow_no_action_authority",
        }


__all__ = [
    "CanonicalPipelineRoot",
    "PIPELINE_IDENTITY_SCHEMA",
    "PipelineObservationIdentity",
    "PipelineQueryIdentity",
    "VersionIdentity",
    "float32_bits",
]
