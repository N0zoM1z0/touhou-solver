"""Canonical commitments for the declared auxiliary timer recurrence."""

from __future__ import annotations

import hashlib
import json

from th08_ecl_auxiliary import (
    AuxiliaryLiteralFireBatch,
    AuxiliaryLiteralFireResult,
)


AUXILIARY_LITERAL_FIRE_RESULT_COMMITMENT_SCHEMA = (
    "th08-auxiliary-literal-fire-result-commitment-v1"
)


def auxiliary_literal_fire_result_core(
    result: AuxiliaryLiteralFireResult,
) -> dict[str, object]:
    """Return exactly the production fields reproduced by the byte oracle."""

    return {
        "events": [
            [
                intent.timer_tick_offset,
                intent.physical_frame_offset,
                intent.instruction_address,
                intent.opcode,
                intent.parameter_mask,
            ]
            for intent in result.intents
        ],
        "transforms": [
            [
                definition.timer_tick_offset,
                definition.physical_frame_offset,
                definition.instruction_address,
                definition.index,
            ]
            for definition in result.transform_definitions
        ],
        "instructions_scanned": result.instructions_scanned,
        "stop_reason": result.stop_reason,
        "horizon_covered": result.horizon_covered,
        "requested_timer_tick_horizon": (
            result.requested_timer_tick_horizon
        ),
        "stop_timer_tick": result.stop_timer_tick,
        "physical_timing_status": result.physical_timing_status,
    }


def canonical_result_core_sha256(
    core: dict[str, object],
) -> str:
    encoded = json.dumps(
        core,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class AuxiliaryLiteralFireResultCommitter:
    """Reuse hashes only within one immutable bound-program lifetime."""

    def __init__(self) -> None:
        self._hashes: dict[AuxiliaryLiteralFireResult, str] = {}

    def commit(
        self,
        batch: AuxiliaryLiteralFireBatch,
    ) -> dict[str, object]:
        hashes: list[str] = []
        for result in batch.unique_results:
            digest = self._hashes.get(result)
            if digest is None:
                digest = canonical_result_core_sha256(
                    auxiliary_literal_fire_result_core(result)
                )
                self._hashes[result] = digest
            hashes.append(digest)
        return {
            "schema": AUXILIARY_LITERAL_FIRE_RESULT_COMMITMENT_SCHEMA,
            "request_count": len(batch.results),
            "unique_result_count": len(batch.unique_results),
            "result_indices": list(batch.result_indices),
            "unique_result_sha256": hashes,
        }


__all__ = [
    "AUXILIARY_LITERAL_FIRE_RESULT_COMMITMENT_SCHEMA",
    "AuxiliaryLiteralFireResultCommitter",
    "auxiliary_literal_fire_result_core",
    "canonical_result_core_sha256",
]
