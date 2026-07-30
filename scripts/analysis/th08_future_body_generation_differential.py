#!/usr/bin/env python3
"""Independent differential for TH08 generational body identities."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from th08_future_body_identity import (
    Route2SlotLifecycleEvent,
    Route2SlotLifetimeLedger,
    advance_route2_slot_lifetimes,
)
from th08_native_future_body_root import (
    Route2NativeRootComponentSpec,
    capture_route2_native_future_body_root_slice,
)
from touhou_control.pipeline_identity import VersionIdentity


REPORT_SCHEMA = "th08-future-body-generation-differential-v1"


@dataclass(frozen=True)
class _Case:
    name: str
    root_active: tuple[int, ...]
    event_words: tuple[tuple[str, int], ...]


CASES = (
    _Case(
        name="inactive_allocate_immediate_end_reallocate",
        root_active=(),
        event_words=(
            ("allocate", 7),
            ("retire", 7),
            ("allocate", 7),
        ),
    ),
    _Case(
        name="root_active_retire_reallocate",
        root_active=(9,),
        event_words=(("retire", 9), ("allocate", 9)),
    ),
    _Case(
        name="root_active_unchanged",
        root_active=(2,),
        event_words=(),
    ),
    _Case(
        name="ordered_multi_slot_reuse",
        root_active=(1, 5),
        event_words=(
            ("retire", 1),
            ("allocate", 3),
            ("retire", 5),
            ("allocate", 1),
        ),
    ),
)


def _encode(slot: int, generation: int) -> int:
    return (generation << 32) | slot


def _oracle(
    case: _Case,
) -> dict[str, object]:
    """Structurally independent dictionary/list lifetime recurrence."""

    active = {slot: True for slot in case.root_active}
    seen = set(case.root_active)
    generations = {slot: 0 for slot in range(480)}
    allocated: list[int] = []
    retired: list[int] = []
    for kind, slot in case.event_words:
        if kind == "allocate":
            if active.get(slot, False):
                raise AssertionError("oracle allocation targeted active slot")
            if slot in seen:
                generations[slot] += 1
            else:
                seen.add(slot)
            active[slot] = True
            allocated.append(_encode(slot, generations[slot]))
        elif kind == "retire":
            if not active.get(slot, False):
                raise AssertionError("oracle retirement targeted inactive slot")
            retired.append(_encode(slot, generations[slot]))
            active[slot] = False
        else:
            raise AssertionError(f"unknown oracle event {kind}")
    final = [
        _encode(slot, generations[slot])
        for slot in range(480)
        if active.get(slot, False)
    ]
    return {
        "allocated": allocated,
        "retired": retired,
        "final": final,
    }


def _boundary_only_naive(case: _Case) -> list[int]:
    """Incorrect endpoint-only identity reconstruction retained as a foil."""

    final_active = set(case.root_active)
    for kind, slot in case.event_words:
        if kind == "allocate":
            final_active.add(slot)
        else:
            final_active.discard(slot)
    return [_encode(slot, 0) for slot in sorted(final_active)]


def _product(case: _Case) -> dict[str, object]:
    root = Route2SlotLifetimeLedger.from_root_active_slots(
        root_physical_update=1000,
        active_slots=case.root_active,
    )
    events = tuple(
        Route2SlotLifecycleEvent(
            physical_update=1001,
            sequence=sequence,
            kind=kind,
            slot=slot,
            source="independent_differential_fixture",
        )
        for sequence, (kind, slot) in enumerate(case.event_words)
    )
    oracle = _oracle(case)
    final_slots = tuple(
        encoded & 0xFFFFFFFF for encoded in oracle["final"]
    )
    step = advance_route2_slot_lifetimes(
        root,
        next_physical_update=1001,
        events=events,
        observed_active_slots=final_slots,
    )
    product = {
        "allocated": [
            identity.encoded for identity in step.allocated_identities
        ],
        "retired": [
            identity.encoded for identity in step.retired_identities
        ],
        "final": [
            identity.encoded
            for identity in step.successor.active_identities
        ],
    }
    naive = _boundary_only_naive(case)
    return {
        "name": case.name,
        "root_active_slots": list(case.root_active),
        "events": [
            {"sequence": sequence, "kind": kind, "slot": slot}
            for sequence, (kind, slot) in enumerate(case.event_words)
        ],
        "product": product,
        "oracle": oracle,
        "matches_oracle": product == oracle,
        "boundary_only_final": naive,
        "boundary_only_matches": naive == oracle["final"],
        "successor_ledger_sha256": step.successor.digest,
    }


class _RootReader:
    def __init__(self) -> None:
        self.frames = [500, 500]

    def u32(self, _address: int) -> int:
        return self.frames.pop(0)

    def read(self, address: int, size: int) -> bytes:
        return bytes((address + offset) & 0xFF for offset in range(size))


def _root_slice_record() -> dict[str, object]:
    specs = (
        Route2NativeRootComponentSpec(
            name="control_identity",
            address=0x1000,
            size=8,
            requirements=("gameplay_and_route_identity",),
            layout_version="fixture-control-v1",
            evidence_state="revalidated",
        ),
        Route2NativeRootComponentSpec(
            name="shared_rng",
            address=0x2000,
            size=6,
            requirements=("shared_gameplay_rng",),
            layout_version="fixture-rng-v1",
            evidence_state="revalidated",
        ),
    )
    root = capture_route2_native_future_body_root_slice(
        _RootReader(),
        root_identity=VersionIdentity.from_mapping(
            "th08-native-root-fixture",
            {"exe_sha256": "fixture"},
        ),
        clock_version=VersionIdentity.from_mapping(
            "th08-manager-clock-fixture",
            {"address": 0x0164D30C},
        ),
        component_specs=specs,
        active_slots_from_components=lambda _components: (1, 5),
    )
    return root.record()


def build_report() -> dict[str, object]:
    cases = [_product(case) for case in CASES]
    return {
        "schema": REPORT_SCHEMA,
        "authority": "offline_identity_and_capture_boundary_only",
        "physical_predictive_authority": False,
        "native_evidence": {
            "enemy_spawn_from_timeline": "0x0042A4E0",
            "first_inactive_test": "0x0042A54E",
            "immediate_end_active_clear": "0x0042A5F5",
            "finding": (
                "one manager update may contain allocation, immediate "
                "retirement, and later slot reuse"
            ),
        },
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "oracle_mismatch_count": sum(
                not bool(case["matches_oracle"]) for case in cases
            ),
            "boundary_only_mismatch_count": sum(
                not bool(case["boundary_only_matches"]) for case in cases
            ),
            "all_product_oracle_matches": all(
                bool(case["matches_oracle"]) for case in cases
            ),
        },
        "native_root_slice_fixture": _root_slice_record(),
        "open_boundary": {
            "complete_physical_root_captured": False,
            "allocation_event_producer_connected": False,
            "live_schedule_authority": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    arguments.output.write_text(
        json.dumps(build_report(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
