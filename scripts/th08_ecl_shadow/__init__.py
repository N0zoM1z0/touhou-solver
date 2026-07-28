"""Offline-only capture-aligned TH08 ECL shadow interpretation."""

from th08_ecl_shadow.interpreter import interpret_vm_local_shadow
from th08_ecl_shadow.model import EclVmLocalShadowResult


__all__ = ["EclVmLocalShadowResult", "interpret_vm_local_shadow"]
