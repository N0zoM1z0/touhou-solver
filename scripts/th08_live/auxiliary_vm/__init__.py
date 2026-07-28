"""Trace-only TH08 auxiliary-ECL VM batch observation."""

from .model import (
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchRecord,
    BatchStatus,
    RecordStatus,
)
from .native import (
    NATIVE_CALL_MODE_GIL_HELD,
    NATIVE_CALL_MODE_GIL_RELEASED,
    NativeAuxiliaryVmBatchCapture,
    NativeAuxiliaryVmBatchDiagnostics,
    NativeAuxiliaryVmBatchError,
    native_auxiliary_vm_batch_available,
)
from .scalar import (
    decode_auxiliary_vm_batch_fixture,
    decode_auxiliary_vm_batch_owned_fixture,
)
from .trace_service import AuxiliaryVmBatchTraceService

__all__ = [
    "AuxiliaryVmBatchObservation",
    "AuxiliaryVmBatchRecord",
    "AuxiliaryVmBatchTraceService",
    "BatchStatus",
    "NATIVE_CALL_MODE_GIL_HELD",
    "NATIVE_CALL_MODE_GIL_RELEASED",
    "NativeAuxiliaryVmBatchCapture",
    "NativeAuxiliaryVmBatchDiagnostics",
    "NativeAuxiliaryVmBatchError",
    "RecordStatus",
    "decode_auxiliary_vm_batch_fixture",
    "decode_auxiliary_vm_batch_owned_fixture",
    "native_auxiliary_vm_batch_available",
]
