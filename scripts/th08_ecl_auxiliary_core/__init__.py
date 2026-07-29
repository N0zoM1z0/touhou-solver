"""Modular implementation of the bounded auxiliary-ECL fire event."""

from .batch import (
    AuxiliaryLiteralFireBatch,
    AuxiliaryLiteralFireRequest,
    BATCH_RECORD_SCHEMA,
    lower_auxiliary_literal_fire_batch,
)
from .constants import (
    PHYSICAL_TIMING_AVAILABLE,
    PHYSICAL_TIMING_BUDGET_EXHAUSTED,
    PHYSICAL_TIMING_INVALID,
    PHYSICAL_TIMING_UNAVAILABLE,
)
from .cached_batch import (
    AuxiliaryLiteralFireBatchLowerer,
    AuxiliaryLiteralFireCacheStats,
    CachedAuxiliaryLiteralFireBatch,
)
from .image import build_exact_runtime_instruction_index
from .lowerer import lower_auxiliary_literal_fire_cycle
from .model import (
    AuxiliaryDirectFireIntent,
    AuxiliaryEclVmState,
    AuxiliaryLiteralFireResult,
    LiteralTransformDefinition,
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
