"""Production-record to independent raw-byte-oracle comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from th08_ecl_tool.core import EclFile

from .oracle import oracle_literal_fire_schedule
from .replay_evidence import array, integer, mapping


@dataclass(frozen=True, slots=True)
class ReplayProgram:
    image: bytes
    runtime_base: int
    instruction_offsets: frozenset[int]
    instruction_owner: dict[int, int]

    @classmethod
    def from_ecl(
        cls,
        ecl: EclFile,
        image: bytes,
        *,
        runtime_base: int,
    ) -> ReplayProgram:
        offsets: set[int] = set()
        owners: dict[int, int] = {}
        for subroutine in ecl.subroutines:
            for instruction in subroutine.instructions:
                offsets.add(instruction.offset)
                owners[runtime_base + instruction.offset] = subroutine.index
        return cls(
            image=image,
            runtime_base=runtime_base,
            instruction_offsets=frozenset(offsets),
            instruction_owner=owners,
        )


def production_core(result: dict[str, Any]) -> dict[str, object]:
    intents = array(result.get("intents"), "result.intents")
    transforms = array(
        result.get("transform_definitions"),
        "result.transform_definitions",
    )
    return {
        "events": [
            [
                integer(intent.get("timer_tick_offset"), "intent.tick"),
                intent.get("physical_frame_offset"),
                integer(intent.get("instruction_address"), "intent.address"),
                integer(intent.get("opcode"), "intent.opcode"),
                integer(intent.get("parameter_mask"), "intent.parameter_mask"),
            ]
            for intent in (
                mapping(item, "result.intent") for item in intents
            )
        ],
        "transforms": [
            [
                integer(transform.get("timer_tick_offset"), "transform.tick"),
                transform.get("physical_frame_offset"),
                integer(
                    transform.get("instruction_address"),
                    "transform.address",
                ),
                integer(transform.get("index"), "transform.index"),
            ]
            for transform in (
                mapping(item, "result.transform") for item in transforms
            )
        ],
        "instructions_scanned": integer(
            result.get("instructions_scanned"),
            "result.instructions_scanned",
        ),
        "stop_reason": result.get("stop_reason"),
        "horizon_covered": result.get("horizon_covered"),
        "requested_timer_tick_horizon": integer(
            result.get("requested_timer_tick_horizon"),
            "result.requested_timer_tick_horizon",
        ),
        "stop_timer_tick": integer(
            result.get("stop_timer_tick"),
            "result.stop_timer_tick",
        ),
        "physical_timing_status": result.get("physical_timing_status"),
    }


def oracle_core(
    active_vm: bytes,
    program: ReplayProgram,
    *,
    horizon: int,
) -> dict[str, object]:
    oracle = oracle_literal_fire_schedule(
        active_vm,
        program.image,
        runtime_base=program.runtime_base,
        instruction_offsets=program.instruction_offsets,
        timer_tick_horizon=horizon,
        active_difficulty_mask=0x08,
        time_scale=None,
        max_instructions=64,
    )
    return {
        **oracle,
        "events": [list(event) for event in oracle["events"]],
        "transforms": [
            list(transform) for transform in oracle["transforms"]
        ],
    }


__all__ = ["ReplayProgram", "oracle_core", "production_core"]
