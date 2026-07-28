"""Exact static/runtime program binding for auxiliary event delivery."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from th08_ecl_auxiliary import build_exact_runtime_instruction_index
from th08_ecl_runtime import RuntimeEclInstruction
from th08_ecl_tool.core import EclFile, parse_ecl
from th08_live.runtime_ecl_identity import RuntimeEclAcceptedVersion


DEFAULT_TARGET_HORIZONS = ((69, 16), (72, 16), (73, 60))


@dataclass(frozen=True, slots=True)
class AuxiliaryEclEventConfiguration:
    static_path: Path
    expected_static_sha256: str
    expected_route_id: int
    expected_difficulty_index: int
    expected_stage_route_index: int
    target_horizons: tuple[tuple[int, int], ...] = DEFAULT_TARGET_HORIZONS
    maximum_instructions: int = 64


@dataclass(frozen=True, slots=True)
class BoundAuxiliaryEclProgram:
    version_key: tuple[object, ...]
    instruction_index: dict[int, RuntimeEclInstruction]
    instruction_owner: dict[int, int]


class AuxiliaryEclEventProgram:
    """Validate one static image and bind it to an accepted runtime base."""

    def __init__(self, configuration: AuxiliaryEclEventConfiguration) -> None:
        if configuration.expected_route_id < 0:
            raise ValueError("auxiliary event route cannot be negative")
        if configuration.expected_difficulty_index < 0:
            raise ValueError("auxiliary event difficulty cannot be negative")
        if configuration.expected_stage_route_index < 0:
            raise ValueError("auxiliary event stage cannot be negative")
        if configuration.maximum_instructions <= 0:
            raise ValueError(
                "auxiliary event instruction limit must be positive"
            )
        target_horizons = dict(configuration.target_horizons)
        if (
            not target_horizons
            or len(target_horizons) != len(configuration.target_horizons)
            or any(target < 0 for target in target_horizons)
            or any(horizon < 0 for horizon in target_horizons.values())
        ):
            raise ValueError("auxiliary event target horizons are invalid")
        expected_sha256 = configuration.expected_static_sha256.lower()
        if (
            len(expected_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in expected_sha256
            )
        ):
            raise ValueError("auxiliary event static SHA-256 is invalid")
        static_image = configuration.static_path.read_bytes()
        actual_sha256 = hashlib.sha256(static_image).hexdigest()
        if actual_sha256 != expected_sha256:
            raise ValueError(
                "auxiliary event static image does not match its digest"
            )
        self.configuration = configuration
        self.static_image = static_image
        self.static_sha256 = actual_sha256
        self.ecl: EclFile = parse_ecl(configuration.static_path)
        self.target_horizons = target_horizons
        self._bound: BoundAuxiliaryEclProgram | None = None

    @staticmethod
    def _version_key(
        version: RuntimeEclAcceptedVersion,
    ) -> tuple[object, ...]:
        return (
            version.runtime_base,
            version.image_length,
            version.relocated_sha256,
            version.normalized_sha256,
            version.static_sha256,
            version.route_id,
            version.difficulty_index,
            version.stage_route_index,
            version.gameplay_epoch,
        )

    def version_matches(
        self,
        version: RuntimeEclAcceptedVersion,
        *,
        gameplay_epoch: int,
        stage_route_index: int,
    ) -> bool:
        return (
            version.static_sha256 == self.static_sha256
            and version.normalized_sha256 == self.static_sha256
            and version.image_length == len(self.static_image)
            and version.route_id == self.configuration.expected_route_id
            and version.difficulty_index
            == self.configuration.expected_difficulty_index
            and version.stage_route_index
            == self.configuration.expected_stage_route_index
            and version.stage_route_index == stage_route_index
            and version.gameplay_epoch == gameplay_epoch
        )

    def bind(
        self,
        version: RuntimeEclAcceptedVersion,
    ) -> BoundAuxiliaryEclProgram:
        key = self._version_key(version)
        if self._bound is not None and self._bound.version_key == key:
            return self._bound
        instruction_index = build_exact_runtime_instruction_index(
            self.ecl,
            self.static_image,
            runtime_base=version.runtime_base,
            expected_sha256=self.static_sha256,
        )
        instruction_owner: dict[int, int] = {}
        for subroutine in self.ecl.subroutines:
            for instruction in subroutine.instructions:
                instruction_owner[
                    version.runtime_base + instruction.offset
                ] = subroutine.index
        self._bound = BoundAuxiliaryEclProgram(
            version_key=key,
            instruction_index=instruction_index,
            instruction_owner=instruction_owner,
        )
        return self._bound


__all__ = [
    "AuxiliaryEclEventConfiguration",
    "AuxiliaryEclEventProgram",
    "BoundAuxiliaryEclProgram",
    "DEFAULT_TARGET_HORIZONS",
]
