"""Exact static/runtime program binding for auxiliary event delivery."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct

from th08_ecl_auxiliary import build_exact_runtime_instruction_index
from th08_ecl_auxiliary_core.constants import (
    ECL_OP_DEFINE_BULLET_TRANSFORM,
    ECL_OP_FIRST_DIRECT_FIRE,
    ECL_OP_JUMP,
    ECL_OP_LAST_DIRECT_FIRE,
    ECL_OP_TERMINATE,
)
from th08_ecl_runtime import RuntimeEclInstruction
from th08_ecl_tool.core import EclFile, parse_ecl
from th08_live.runtime_ecl_identity import RuntimeEclAcceptedVersion

from .model import MAXIMUM_RUNTIME_ADDRESS, MINIMUM_RUNTIME_ADDRESS


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
    maximum_physical_steps: int = 65536
    cache_capacity: int = 512


@dataclass(frozen=True, slots=True)
class BoundAuxiliaryEclProgram:
    version_key: tuple[object, ...]
    instruction_index: dict[int, RuntimeEclInstruction]
    instruction_owner: dict[int, int]
    prevalidated_instruction_count: int
    bound_instruction_count: int


@dataclass(frozen=True, slots=True)
class _RelativeInstruction:
    offset: int
    time: int
    opcode: int
    size: int
    difficulty_mask: int
    parameter_mask: int
    payload: bytes
    owner: int


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
        if configuration.maximum_physical_steps <= 0:
            raise ValueError(
                "auxiliary event physical-step limit must be positive"
            )
        if configuration.cache_capacity <= 0:
            raise ValueError(
                "auxiliary event cache capacity must be positive"
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
        validated = build_exact_runtime_instruction_index(
            self.ecl,
            self.static_image,
            runtime_base=MINIMUM_RUNTIME_ADDRESS,
            expected_sha256=self.static_sha256,
        )
        target_set = set(target_horizons)
        relative: list[_RelativeInstruction] = []
        for subroutine in self.ecl.subroutines:
            if subroutine.index not in target_set:
                continue
            for parsed in subroutine.instructions:
                instruction = validated[
                    MINIMUM_RUNTIME_ADDRESS + parsed.offset
                ]
                relative.append(
                    _RelativeInstruction(
                        offset=parsed.offset,
                        time=instruction.time,
                        opcode=instruction.opcode,
                        size=instruction.size,
                        difficulty_mask=instruction.difficulty_mask,
                        parameter_mask=instruction.parameter_mask,
                        payload=instruction.payload,
                        owner=subroutine.index,
                    )
                )
        if not relative or set(item.owner for item in relative) != target_set:
            raise ValueError(
                "auxiliary event targets lack prevalidated instructions"
            )
        self._validate_target_closure(
            relative,
            active_difficulty_mask=(
                1 << configuration.expected_difficulty_index
            ),
        )
        self.prevalidated_instruction_count = len(validated)
        self._relative_instructions = tuple(relative)
        self._bound: BoundAuxiliaryEclProgram | None = None

    @staticmethod
    def _validate_target_closure(
        instructions: list[_RelativeInstruction],
        *,
        active_difficulty_mask: int,
    ) -> None:
        """Prove every executable successor stays in its target subroutine."""

        owner_by_offset = {
            instruction.offset: instruction.owner
            for instruction in instructions
        }

        def require_same_owner_successor(
            instruction: _RelativeInstruction,
            successor: int,
        ) -> None:
            if owner_by_offset.get(successor) != instruction.owner:
                raise ValueError(
                    "auxiliary event target closure has an escaping successor"
                )

        for instruction in instructions:
            eligible = (
                active_difficulty_mask & instruction.difficulty_mask
            ) == active_difficulty_mask
            if not eligible:
                require_same_owner_successor(
                    instruction,
                    instruction.offset + instruction.size,
                )
                continue
            if instruction.opcode == ECL_OP_TERMINATE:
                continue
            if instruction.opcode == ECL_OP_JUMP:
                if instruction.parameter_mask or len(instruction.payload) != 8:
                    continue
                target_elapsed, relative_offset = struct.unpack(
                    "<ii",
                    instruction.payload,
                )
                if target_elapsed < 0:
                    continue
                require_same_owner_successor(
                    instruction,
                    instruction.offset + relative_offset,
                )
                continue
            if (
                instruction.opcode == ECL_OP_DEFINE_BULLET_TRANSFORM
                or ECL_OP_FIRST_DIRECT_FIRE
                <= instruction.opcode
                <= ECL_OP_LAST_DIRECT_FIRE
            ):
                require_same_owner_successor(
                    instruction,
                    instruction.offset + instruction.size,
                )

    @staticmethod
    def version_key(
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
        )

    @staticmethod
    def program_identity_record(
        version: RuntimeEclAcceptedVersion,
    ) -> dict[str, object]:
        return {
            "runtime_base": version.runtime_base,
            "image_length": version.image_length,
            "relocated_sha256": version.relocated_sha256,
            "normalized_sha256": version.normalized_sha256,
            "static_sha256": version.static_sha256,
            "route_id": version.route_id,
            "difficulty_index": version.difficulty_index,
            "stage_route_index": version.stage_route_index,
        }

    @classmethod
    def program_identity_key(
        cls,
        version: RuntimeEclAcceptedVersion,
    ) -> list[object]:
        return list(cls.version_key(version))

    def version_matches(
        self,
        version: RuntimeEclAcceptedVersion,
        *,
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
        )

    def bind(
        self,
        version: RuntimeEclAcceptedVersion,
    ) -> BoundAuxiliaryEclProgram:
        key = self.version_key(version)
        if self._bound is not None and self._bound.version_key == key:
            return self._bound
        if not (
            MINIMUM_RUNTIME_ADDRESS
            <= version.runtime_base
            <= MAXIMUM_RUNTIME_ADDRESS
        ):
            raise ValueError(
                "runtime ECL base is outside the supported address range"
            )
        instruction_index: dict[int, RuntimeEclInstruction] = {}
        instruction_owner: dict[int, int] = {}
        for relative in self._relative_instructions:
            address = version.runtime_base + relative.offset
            if address > MAXIMUM_RUNTIME_ADDRESS:
                raise ValueError("runtime ECL instruction address overflows")
            if address in instruction_index:
                raise ValueError("duplicate runtime ECL instruction address")
            instruction_index[address] = RuntimeEclInstruction(
                address=address,
                time=relative.time,
                opcode=relative.opcode,
                size=relative.size,
                difficulty_mask=relative.difficulty_mask,
                parameter_mask=relative.parameter_mask,
                payload=relative.payload,
            )
            instruction_owner[address] = relative.owner
        self._bound = BoundAuxiliaryEclProgram(
            version_key=key,
            instruction_index=instruction_index,
            instruction_owner=instruction_owner,
            prevalidated_instruction_count=(
                self.prevalidated_instruction_count
            ),
            bound_instruction_count=len(instruction_index),
        )
        return self._bound


__all__ = [
    "AuxiliaryEclEventConfiguration",
    "AuxiliaryEclEventProgram",
    "BoundAuxiliaryEclProgram",
    "DEFAULT_TARGET_HORIZONS",
]
