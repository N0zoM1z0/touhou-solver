"""Offline-only capture-aligned TH08 ECL shadow interpretation."""

from th08_ecl_shadow.interpreter import interpret_vm_local_shadow
from th08_ecl_shadow.model import (
    ECL_VM_LOCAL_SHADOW_SEMANTICS_VERSION,
    EclVmLocalShadowResult,
)


__all__ = [
    "ECL_VM_LOCAL_SHADOW_SEMANTICS_VERSION",
    "EclVmLocalShadowResult",
    "interpret_vm_local_shadow",
]
