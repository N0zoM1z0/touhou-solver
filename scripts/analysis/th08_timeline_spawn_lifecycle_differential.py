#!/usr/bin/env python3
"""Compare timeline spawn lifecycles with an independent scalar oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from th08_enemy_spawn_lifecycle import (
    execute_route2_timeline_spawn_lifecycles,
)
from th08_future_body_identity import (
    Route2SlotLifecycleEvent,
    Route2SlotLifetimeLedger,
    advance_route2_slot_lifetimes,
)
from th08_timeline_model import TimelineSpawnRequest


def _spawn(offset: int) -> TimelineSpawnRequest:
    return TimelineSpawnRequest(
        timeline_index=0,
        instruction_offset=offset,
        instruction_time=0,
        opcode=0,
        subroutine=offset // 0x10,
        x=0.0,
        y=0.0,
        z=0.0,
        field_2dfc=1,
        byte_3304=2,
        field_2e08=3,
        variant=False,
    )


def _oracle(
    ledger: Route2SlotLifetimeLedger,
    returns: tuple[int, ...],
) -> dict[str, object]:
    active = list(ledger.active)
    seen = list(ledger.seen_lifetime)
    generations = list(ledger.generations)
    events: list[list[object]] = []
    outcomes: list[list[object]] = []
    for result in returns:
        slot = next(
            (index for index, value in enumerate(active) if not value),
            None,
        )
        if slot is None:
            outcomes.append(["pool_full", None, None])
            continue
        if seen[slot]:
            generations[slot] += 1
        else:
            seen[slot] = True
        generation = generations[slot]
        active[slot] = True
        events.append(["allocate", slot, generation])
        outcomes.append(["allocated", slot, generation, result])
        if result == -1:
            active[slot] = False
            events.append(["retire", slot, generation])
    return {
        "events": events,
        "outcomes": outcomes,
        "active": [
            [slot, generations[slot]]
            for slot, value in enumerate(active)
            if value
        ],
    }


def _product(
    ledger: Route2SlotLifetimeLedger,
    returns: tuple[int, ...],
) -> dict[str, object]:
    iterator = iter(returns)
    step = execute_route2_timeline_spawn_lifecycles(
        ledger,
        next_physical_update=ledger.current_physical_update + 1,
        spawns=tuple(_spawn(0x10 * (index + 1)) for index in range(len(returns))),
        initial_vm_executor=lambda _request, _identity: next(iterator),
    )
    events = []
    for outcome in step.outcomes:
        if outcome.pool_full:
            continue
        assert outcome.identity is not None
        events.append(
            [
                "allocate",
                outcome.identity.slot,
                outcome.identity.allocation_generation,
            ]
        )
        if not outcome.survived_initial_vm:
            events.append(
                [
                    "retire",
                    outcome.identity.slot,
                    outcome.identity.allocation_generation,
                ]
            )
    return {
        "events": events,
        "outcomes": [
            (
                ["pool_full", None, None]
                if outcome.pool_full
                else [
                    "allocated",
                    outcome.identity.slot,
                    outcome.identity.allocation_generation,
                    outcome.initial_vm_return,
                ]
            )
            for outcome in step.outcomes
        ],
        "active": [
            [identity.slot, identity.allocation_generation]
            for identity in step.lifecycle.successor.active_identities
        ],
    }


def _retired_root_slot() -> Route2SlotLifetimeLedger:
    root = Route2SlotLifetimeLedger.from_root_active_slots(
        root_physical_update=0,
        active_slots=(0,),
    )
    return advance_route2_slot_lifetimes(
        root,
        next_physical_update=1,
        events=(
            Route2SlotLifecycleEvent(
                physical_update=1,
                sequence=0,
                kind="retire",
                slot=0,
                source="oracle_fixture",
            ),
        ),
    ).successor


def build_report() -> dict[str, object]:
    cases = (
        (
            "ascending_first_inactive",
            Route2SlotLifetimeLedger.from_root_active_slots(
                root_physical_update=0,
                active_slots=(0, 1),
            ),
            (0, 0),
        ),
        (
            "same_update_initial_minus_one_reuse",
            Route2SlotLifetimeLedger.from_root_active_slots(
                root_physical_update=0,
                active_slots=(),
            ),
            (-1, 0),
        ),
        ("post_root_reuse_advances_generation", _retired_root_slot(), (0,)),
        (
            "pool_full",
            Route2SlotLifetimeLedger.from_root_active_slots(
                root_physical_update=0,
                active_slots=tuple(range(480)),
            ),
            (0,),
        ),
    )
    rows = []
    for name, ledger, returns in cases:
        product = _product(ledger, returns)
        oracle = _oracle(ledger, returns)
        rows.append(
            {
                "name": name,
                "initial_vm_returns": list(returns),
                "product": product,
                "oracle": oracle,
                "match": product == oracle,
            }
        )
    report = {
        "schema": "th08-timeline-spawn-lifecycle-differential-v1",
        "authority": "offline_native_order_differential_only",
        "native_evidence": {
            "allocator": "0x0042A4E0",
            "first_inactive_test": "0x0042A54E",
            "initial_vm_start": "0x0042A5CE",
            "initial_vm_step": "0x0042A5E4",
            "initial_minus_one_retirement": "0x0042A5F5",
        },
        "case_count": len(rows),
        "match_count": sum(bool(row["match"]) for row in rows),
        "cases": rows,
    }
    payload = json.dumps(
        report,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    report["payload_sha256"] = hashlib.sha256(payload).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    report = build_report()
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "case_count": report["case_count"],
                "match_count": report["match_count"],
                "payload_sha256": report["payload_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["case_count"] == report["match_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
