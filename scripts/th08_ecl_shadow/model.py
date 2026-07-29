"""Result model for offline TH08 ECL VM-local shadow interpretation."""

from __future__ import annotations

from dataclasses import dataclass

from th08_ecl_runtime import TaggedVelocityToggle
from th08_ecl_vm_state import EclVmLocalProjection, float32_from_bits
from th08_native_timer import TH08_NATIVE_TIMER_SEMANTICS_VERSION


ECL_VM_LOCAL_SHADOW_SEMANTICS_VERSION = (
    "th08-ecl-vm-local-shadow-v2-native-timer-components"
)


@dataclass(frozen=True)
class EclVmLocalShadowResult:
    """One exact supported prefix followed by completion or explicit unknown."""

    events: tuple[TaggedVelocityToggle, ...]
    instructions_scanned: int
    stop_reason: str
    horizon_covered: bool
    requested_horizon_frames: int
    stop_frame: int
    final_instruction_pointer: int
    final_timer_elapsed: int
    final_timer_fraction_bits: int
    final_projection: EclVmLocalProjection | None

    def __post_init__(self) -> None:
        if self.instructions_scanned < 0:
            raise ValueError("shadow instruction count cannot be negative")
        if self.requested_horizon_frames < 0:
            raise ValueError("shadow horizon cannot be negative")
        if not 0 <= self.stop_frame <= self.requested_horizon_frames:
            raise ValueError("shadow stop frame is outside its horizon")
        if not -(1 << 31) <= self.final_timer_elapsed < (1 << 31):
            raise ValueError("shadow timer elapsed is outside signed int32")
        if not 0 <= self.final_timer_fraction_bits <= 0xFFFFFFFF:
            raise ValueError("shadow timer fraction bits are outside uint32")
        complete_stop = self.stop_reason in {"horizon", "terminate"}
        if self.horizon_covered != complete_stop:
            raise ValueError("shadow completeness disagrees with its stop reason")

    @property
    def coverage_status(self) -> str:
        return "complete" if self.horizon_covered else "unknown"

    @property
    def complete_events(self) -> tuple[TaggedVelocityToggle, ...] | None:
        return self.events if self.horizon_covered else None

    @property
    def final_timer_value(self) -> float:
        """Compatibility diagnostic; never use as exact timer identity."""

        return self.final_timer_elapsed + float32_from_bits(
            self.final_timer_fraction_bits
        )

    @property
    def final_timer_identity(self) -> tuple[str, str, int, int]:
        return (
            ECL_VM_LOCAL_SHADOW_SEMANTICS_VERSION,
            TH08_NATIVE_TIMER_SEMANTICS_VERSION,
            self.final_timer_elapsed,
            self.final_timer_fraction_bits,
        )


__all__ = [
    "ECL_VM_LOCAL_SHADOW_SEMANTICS_VERSION",
    "EclVmLocalShadowResult",
]
