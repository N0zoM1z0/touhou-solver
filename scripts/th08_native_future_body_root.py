"""Immutable native-root evidence slices for the TH08 future-body producer.

This module captures explicitly declared native byte regions under one
enemy-manager-frame bracket.  It versions evidence; it does not claim that
the current executor can consume every captured field or predict a complete
future schedule.
"""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from typing import Callable, Protocol

from th08_future_body_identity import Route2SlotLifetimeLedger
from th08_live.enemy_sensor import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_FLAGS_OFFSET,
    ENEMY_MANAGER_TEMPLATE_BASE,
    ENEMY_POOL_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_STRIDE,
)
from th08_runtime.game_state import ADDR_ENEMY_MANAGER_FRAME
from touhou_control.pipeline_identity import VersionIdentity


ROOT_SLICE_SCHEMA = "th08-native-future-body-root-slice-v2"
ROOT_COMPONENT_SCHEMA = "th08-native-future-body-root-component-v2"
ROOT_COMPONENT_CAPTURE_SCHEMA = (
    "th08-native-future-body-root-component-capture-v2"
)
ROOT_SLICE_AUTHORITY = "native_root_bytes_only_no_predictive_authority"
TH08_ENEMY_MANAGER_TEMPLATE_BASE = ENEMY_MANAGER_TEMPLATE_BASE
TH08_TIMELINE_RUNTIME_BASE = 0x00F5A0C0

MINIMUM_ROOT_REQUIREMENTS = (
    "damage_power_and_resources",
    "external_callback_and_transition_state",
    "gameplay_and_route_identity",
    "main_and_auxiliary_ecl_contexts",
    "motion_flag_and_lifecycle_state",
    "ordinary_enemy_template_and_pool",
    "physical_clock_and_scheduler_gates",
    "player_input_mode_and_shot_state",
    "shared_gameplay_rng",
    "timeline_runtime_state",
)
_EVIDENCE_STATES = frozenset({"revalidated", "inherited", "hypothesized"})


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_record(record: dict[str, object]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


class NativeRootReader(Protocol):
    def read(self, address: int, size: int) -> bytes:
        ...

    def u32(self, address: int) -> int:
        ...


@dataclass(frozen=True)
class Route2NativeRootComponentSpec:
    """One canonical byte region and the semantic requirements it supports."""

    name: str
    address: int
    size: int
    requirements: tuple[str, ...]
    layout_version: str
    evidence_state: str
    complete_requirement_coverage: bool = True
    schema: str = ROOT_COMPONENT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != ROOT_COMPONENT_SCHEMA:
            raise ValueError("unsupported native-root component schema")
        if type(self.name) is not str or not self.name:
            raise ValueError("native-root component name must not be empty")
        if type(self.address) is not int or self.address < 0:
            raise ValueError("native-root component address must be nonnegative")
        if type(self.size) is not int or self.size <= 0:
            raise ValueError("native-root component size must be positive")
        if self.address + self.size > 1 << 32:
            raise ValueError("native-root component exceeds the 32-bit address space")
        if (
            type(self.requirements) is not tuple
            or not self.requirements
            or any(
                type(requirement) is not str
                or requirement not in MINIMUM_ROOT_REQUIREMENTS
                for requirement in self.requirements
            )
        ):
            raise ValueError(
                "native-root requirements must be known immutable names"
            )
        if (
            self.requirements != tuple(sorted(set(self.requirements)))
        ):
            raise ValueError(
                "native-root requirements must be sorted and unique"
            )
        if type(self.layout_version) is not str or not self.layout_version:
            raise ValueError("native-root layout version must not be empty")
        if self.evidence_state not in _EVIDENCE_STATES:
            raise ValueError("unsupported native-root evidence state")
        if type(self.complete_requirement_coverage) is not bool:
            raise ValueError(
                "native-root requirement coverage must be an exact boolean"
            )

    def record(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "name": self.name,
            "address": self.address,
            "size": self.size,
            "requirements": list(self.requirements),
            "layout_version": self.layout_version,
            "evidence_state": self.evidence_state,
            "complete_requirement_coverage": (
                self.complete_requirement_coverage
            ),
        }


@dataclass(frozen=True)
class Route2NativeRootComponentCapture:
    """Exact bytes read for one declared native-root component."""

    spec: Route2NativeRootComponentSpec
    data: bytes
    schema: str = ROOT_COMPONENT_CAPTURE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != ROOT_COMPONENT_CAPTURE_SCHEMA:
            raise ValueError("unsupported root-component capture schema")
        if type(self.spec) is not Route2NativeRootComponentSpec:
            raise ValueError("root-component capture requires an exact spec")
        if type(self.data) is not bytes or len(self.data) != self.spec.size:
            raise ValueError("root-component capture size does not match its spec")

    @property
    def sha256(self) -> str:
        return _sha256_bytes(self.data)

    def record(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "spec": self.spec.record(),
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class Route2NativeFutureBodyRootSlice:
    """One content-addressed, frame-bracketed native root evidence slice."""

    root_identity: VersionIdentity
    clock_version: VersionIdentity
    frame_before: int
    frame_after: int
    attempts: int
    lifetime_ledger: Route2SlotLifetimeLedger
    components: tuple[Route2NativeRootComponentCapture, ...]
    schema: str = ROOT_SLICE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != ROOT_SLICE_SCHEMA:
            raise ValueError("unsupported native future-body root schema")
        for value, name in (
            (self.root_identity, "root identity"),
            (self.clock_version, "clock version"),
        ):
            if type(value) is not VersionIdentity:
                raise ValueError(f"native-root {name} must be immutable")
        if (
            type(self.frame_before) is not int
            or self.frame_before < 0
            or type(self.frame_after) is not int
            or self.frame_after < 0
        ):
            raise ValueError("native-root frame bracket must be nonnegative")
        if type(self.attempts) is not int or self.attempts <= 0:
            raise ValueError("native-root attempt count must be positive")
        if type(self.lifetime_ledger) is not Route2SlotLifetimeLedger:
            raise ValueError("native root requires a slot-lifetime ledger")
        if (
            self.lifetime_ledger.root_physical_update != self.frame_after
            or self.lifetime_ledger.current_physical_update != self.frame_after
        ):
            raise ValueError(
                "native-root lifetime ledger must begin at the captured root"
            )
        if type(self.components) is not tuple or any(
            type(component) is not Route2NativeRootComponentCapture
            for component in self.components
        ):
            raise ValueError(
                "native-root components must be immutable exact captures"
            )
        names = tuple(component.spec.name for component in self.components)
        if names != tuple(sorted(names)) or len(names) != len(set(names)):
            raise ValueError(
                "native-root components must be name-sorted and unique"
            )

    @property
    def coherent(self) -> bool:
        return self.frame_before == self.frame_after

    @property
    def revalidated_requirements(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    requirement
                    for component in self.components
                    if (
                        component.spec.evidence_state == "revalidated"
                        and component.spec.complete_requirement_coverage
                    )
                    for requirement in component.spec.requirements
                }
            )
        )

    @property
    def missing_requirements(self) -> tuple[str, ...]:
        covered = frozenset(self.revalidated_requirements)
        return tuple(
            requirement
            for requirement in MINIMUM_ROOT_REQUIREMENTS
            if requirement not in covered
        )

    @property
    def inventory_complete(self) -> bool:
        return self.coherent and not self.missing_requirements

    @property
    def authority_status(self) -> str:
        if not self.coherent:
            return "incoherent_native_root_slice"
        if self.missing_requirements:
            return "partial_native_root_inventory"
        return "complete_root_bytes_without_executor_authority"

    def payload(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "authority": ROOT_SLICE_AUTHORITY,
            "physical_predictive_authority": False,
            "root_identity": self.root_identity.record(),
            "clock_version": self.clock_version.record(),
            "frame_bracket": [self.frame_before, self.frame_after],
            "attempts": self.attempts,
            "lifetime_ledger": self.lifetime_ledger.record(),
            "components": [component.record() for component in self.components],
            "revalidated_requirements": list(self.revalidated_requirements),
            "missing_requirements": list(self.missing_requirements),
            "inventory_complete": self.inventory_complete,
            "authority_status": self.authority_status,
        }

    @property
    def digest(self) -> str:
        return _sha256_record(self.payload())

    def record(self) -> dict[str, object]:
        return {**self.payload(), "sha256": self.digest}


def _read_exact(
    reader: NativeRootReader,
    *,
    address: int,
    size: int,
) -> bytes:
    data = reader.read(address, size)
    if type(data) is not bytes or len(data) != size:
        raise RuntimeError(
            f"short native-root read at 0x{address:08x}: "
            f"expected {size}, got {len(data) if isinstance(data, bytes) else -1}"
        )
    return data


def decode_route2_ordinary_pool_active_slots(
    components: tuple[Route2NativeRootComponentCapture, ...],
    *,
    component_name: str = "ordinary_enemy_template_and_pool",
) -> tuple[int, ...]:
    """Decode exact native active bit0 from one full ordinary-pool component."""

    matches = tuple(
        component
        for component in components
        if component.spec.name == component_name
    )
    if len(matches) != 1:
        raise ValueError("native root requires exactly one ordinary-pool component")
    component = matches[0]
    data = component.data
    expected_size = ENEMY_POOL_SIZE * ENEMY_STRIDE
    if (
        component.spec.address == ENEMY_POOL_BASE
        and len(data) == expected_size
    ):
        pool_offset = 0
    elif (
        component.spec.address == TH08_ENEMY_MANAGER_TEMPLATE_BASE
        and len(data) == expected_size + ENEMY_STRIDE
    ):
        pool_offset = ENEMY_STRIDE
    else:
        raise ValueError(
            "ordinary-pool component must be the exact 480-slot pool or "
            "the revalidated template-plus-pool region"
        )
    return tuple(
        slot
        for slot in range(ENEMY_POOL_SIZE)
        if (
            struct.unpack_from(
                "<I",
                data,
                pool_offset + slot * ENEMY_STRIDE + ENEMY_FLAGS_OFFSET,
            )[0]
            & ENEMY_ACTIVE_FLAG
        )
    )


def route2_revalidated_native_root_component_specs(
) -> tuple[Route2NativeRootComponentSpec, ...]:
    """Return the current static native-root layout inventory.

    Partial entries deliberately do not satisfy their semantic requirement.
    They identify exact fixed bytes whose dynamic pointees or companion
    regions must still be captured in the same transaction.
    """

    specs = (
        Route2NativeRootComponentSpec(
            name="ordinary_enemy_template_and_pool",
            address=TH08_ENEMY_MANAGER_TEMPLATE_BASE,
            size=(ENEMY_POOL_SIZE + 1) * ENEMY_STRIDE,
            requirements=(
                "motion_flag_and_lifecycle_state",
                "ordinary_enemy_template_and_pool",
            ),
            layout_version=(
                "ida-0x42a4e0-template-plus-480x0x53d0-20260730"
            ),
            evidence_state="revalidated",
        ),
        Route2NativeRootComponentSpec(
            name="ordinary_enemy_ecl_and_callback_roots",
            address=ENEMY_POOL_BASE,
            size=ENEMY_POOL_SIZE * ENEMY_STRIDE,
            requirements=(
                "external_callback_and_transition_state",
                "main_and_auxiliary_ecl_contexts",
            ),
            layout_version=(
                "ida-0x42c660-main-vm-plus-aux-pointer-roots-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="timeline_runtime_clock_table",
            address=TH08_TIMELINE_RUNTIME_BASE,
            size=16 * 16,
            requirements=("timeline_runtime_state",),
            layout_version=(
                "ida-0x42c7c3-16x16-timeline-state-table-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="timeline_markers_and_spawn_suppression",
            address=0x00F54E1C,
            size=0x14,
            requirements=(
                "physical_clock_and_scheduler_gates",
                "timeline_runtime_state",
            ),
            layout_version=(
                "ida-0x42a944-0x42ac81-marker4-plus-suppression-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="indexed_enemy_registry",
            address=0x00F54CC0,
            size=8 * 4,
            requirements=("external_callback_and_transition_state",),
            layout_version="ida-0x42ac18-0x42ac6b-8xpointer-20260730",
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="runtime_ecl_file_context",
            address=0x004ECCB8,
            size=8,
            requirements=(
                "main_and_auxiliary_ecl_contexts",
                "timeline_runtime_state",
            ),
            layout_version="ida-0x418330-context-two-dwords-20260730",
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="gameplay_identity_prefix",
            address=0x0164D0A8,
            size=0x10,
            requirements=("gameplay_and_route_identity",),
            layout_version=(
                "ida-0x42c6d1-route-engine-identity-prefix-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="stage_route_and_enemy_clock",
            address=0x0164D2CC,
            size=0x44,
            requirements=(
                "gameplay_and_route_identity",
                "physical_clock_and_scheduler_gates",
            ),
            layout_version=(
                "ida-runtime-stage-route-through-enemy-frame-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="gameplay_rng_and_input_masks",
            address=0x0164D520,
            size=0x18,
            requirements=(
                "player_input_mode_and_shot_state",
                "shared_gameplay_rng",
            ),
            layout_version=(
                "ida-0x43ecc0-rng-state-calls-plus-input-masks-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="gameplay_rng_exact",
            address=0x0164D520,
            size=8,
            requirements=("shared_gameplay_rng",),
            layout_version="ida-0x43ecc0-u16-state-u32-call-count-20260730",
            evidence_state="revalidated",
        ),
        Route2NativeRootComponentSpec(
            name="player_state_through_resource_transitions",
            address=0x017D5EF8,
            size=0xE2A70,
            requirements=(
                "damage_power_and_resources",
                "player_input_mode_and_shot_state",
            ),
            layout_version=(
                "ida-0x44c390-player-through-predeath-lockout-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="run_state_inner_pointer",
            address=0x0160F510,
            size=4,
            requirements=("damage_power_and_resources",),
            layout_version=(
                "runtime-run-state-pointer-lives-bombs-power-pointee-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="scheduler_gate_globals",
            address=0x0160F428,
            size=0x118,
            requirements=("physical_clock_and_scheduler_gates",),
            layout_version=(
                "ida-frscreen-serial-pointer-freeze-difficulty-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="spell_transition_state",
            address=0x004EA670,
            size=0x114,
            requirements=("external_callback_and_transition_state",),
            layout_version=(
                "ida-spell-prefix-through-timer-elapsed-20260730"
            ),
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
        Route2NativeRootComponentSpec(
            name="global_gameplay_time_scale",
            address=0x017CE8E0,
            size=4,
            requirements=("external_callback_and_transition_state",),
            layout_version="ida-ecl-callback-global-f32-scale-20260730",
            evidence_state="revalidated",
            complete_requirement_coverage=False,
        ),
    )
    return tuple(sorted(specs, key=lambda spec: spec.name))


def capture_route2_native_future_body_root_slice(
    reader: NativeRootReader,
    *,
    root_identity: VersionIdentity,
    clock_version: VersionIdentity,
    component_specs: tuple[Route2NativeRootComponentSpec, ...],
    active_slots_from_components: Callable[
        [tuple[Route2NativeRootComponentCapture, ...]],
        tuple[int, ...],
    ],
    maximum_attempts: int = 3,
) -> Route2NativeFutureBodyRootSlice:
    """Capture declared native regions without issuing input or guessing gaps."""

    if type(component_specs) is not tuple or any(
        type(spec) is not Route2NativeRootComponentSpec
        for spec in component_specs
    ):
        raise ValueError("native-root component specs must be immutable")
    names = tuple(spec.name for spec in component_specs)
    if names != tuple(sorted(names)) or len(names) != len(set(names)):
        raise ValueError("native-root component specs must be name-sorted and unique")
    if type(maximum_attempts) is not int or maximum_attempts <= 0:
        raise ValueError("native-root maximum attempts must be positive")
    if not callable(active_slots_from_components):
        raise ValueError("native-root capture requires an active-slot decoder")

    last: Route2NativeFutureBodyRootSlice | None = None
    for attempt in range(1, maximum_attempts + 1):
        frame_before = int(reader.u32(ADDR_ENEMY_MANAGER_FRAME))
        components = tuple(
            Route2NativeRootComponentCapture(
                spec=spec,
                data=_read_exact(
                    reader,
                    address=spec.address,
                    size=spec.size,
                ),
            )
            for spec in component_specs
        )
        frame_after = int(reader.u32(ADDR_ENEMY_MANAGER_FRAME))
        active_slots = active_slots_from_components(components)
        ledger = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=frame_after,
            active_slots=active_slots,
        )
        last = Route2NativeFutureBodyRootSlice(
            root_identity=root_identity,
            clock_version=clock_version,
            frame_before=frame_before,
            frame_after=frame_after,
            attempts=attempt,
            lifetime_ledger=ledger,
            components=components,
        )
        if last.coherent:
            return last
    assert last is not None
    return last


__all__ = [
    "MINIMUM_ROOT_REQUIREMENTS",
    "ROOT_COMPONENT_CAPTURE_SCHEMA",
    "ROOT_COMPONENT_SCHEMA",
    "ROOT_SLICE_AUTHORITY",
    "ROOT_SLICE_SCHEMA",
    "TH08_ENEMY_MANAGER_TEMPLATE_BASE",
    "TH08_TIMELINE_RUNTIME_BASE",
    "NativeRootReader",
    "Route2NativeFutureBodyRootSlice",
    "Route2NativeRootComponentCapture",
    "Route2NativeRootComponentSpec",
    "capture_route2_native_future_body_root_slice",
    "decode_route2_ordinary_pool_active_slots",
    "route2_revalidated_native_root_component_specs",
]
