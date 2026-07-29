"""Public compatibility facade for bounded TH08 auxiliary-ECL lowering.

The implementation is split by responsibility under
``th08_ecl_auxiliary_core``.  Existing callers intentionally retain this
stable import path.
"""

from th08_ecl_auxiliary_core import (
    PHYSICAL_TIMING_AVAILABLE,
    PHYSICAL_TIMING_BUDGET_EXHAUSTED,
    PHYSICAL_TIMING_INVALID,
    PHYSICAL_TIMING_UNAVAILABLE,
    AuxiliaryDirectFireIntent,
    AuxiliaryEclVmState,
    AuxiliaryLiteralFireBatch,
    AuxiliaryLiteralFireBatchLowerer,
    AuxiliaryLiteralFireCacheStats,
    AuxiliaryLiteralFireRequest,
    AuxiliaryLiteralFireResult,
    BATCH_RECORD_SCHEMA,
    CachedAuxiliaryLiteralFireBatch,
    LiteralTransformDefinition,
    build_exact_runtime_instruction_index,
    lower_auxiliary_literal_fire_batch,
    lower_auxiliary_literal_fire_cycle,
)

__all__ = [
    "AuxiliaryDirectFireIntent",
    "AuxiliaryEclVmState",
    "AuxiliaryLiteralFireBatch",
    "AuxiliaryLiteralFireBatchLowerer",
    "AuxiliaryLiteralFireCacheStats",
    "AuxiliaryLiteralFireRequest",
    "AuxiliaryLiteralFireResult",
    "BATCH_RECORD_SCHEMA",
    "CachedAuxiliaryLiteralFireBatch",
    "LiteralTransformDefinition",
    "PHYSICAL_TIMING_AVAILABLE",
    "PHYSICAL_TIMING_BUDGET_EXHAUSTED",
    "PHYSICAL_TIMING_INVALID",
    "PHYSICAL_TIMING_UNAVAILABLE",
    "build_exact_runtime_instruction_index",
    "lower_auxiliary_literal_fire_batch",
    "lower_auxiliary_literal_fire_cycle",
]
