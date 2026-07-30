"""Focused tests for native-order timeline allocation lifecycles."""

from __future__ import annotations

import unittest

from analysis.th08_timeline_spawn_lifecycle_differential import build_report
from th08_enemy_spawn_lifecycle import (
    execute_route2_timeline_spawn_lifecycles,
)
from th08_future_body_identity import Route2SlotLifetimeLedger
from th08_timeline_model import TimelineSpawnRequest


def _spawn(offset: int, subroutine: int = 0) -> TimelineSpawnRequest:
    return TimelineSpawnRequest(
        timeline_index=0,
        instruction_offset=offset,
        instruction_time=0,
        opcode=0,
        subroutine=subroutine,
        x=0.0,
        y=0.0,
        z=0.0,
        field_2dfc=1,
        byte_3304=2,
        field_2e08=3,
        variant=False,
    )


class TimelineSpawnLifecycleTests(unittest.TestCase):
    def test_first_inactive_slot_and_surviving_initial_vm(self) -> None:
        ledger = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=10,
            active_slots=(0, 1),
        )
        calls = []

        def initial_vm(request, identity):
            calls.append((request.instruction_offset, identity.encoded))
            return 0

        step = execute_route2_timeline_spawn_lifecycles(
            ledger,
            next_physical_update=11,
            spawns=(_spawn(0x20),),
            initial_vm_executor=initial_vm,
            observed_active_slots=(0, 1, 2),
        )

        self.assertEqual(calls, [(0x20, 2)])
        self.assertEqual(
            tuple((event.kind, event.slot) for event in step.lifecycle.events),
            (("allocate", 2),),
        )
        self.assertEqual(
            tuple(identity.encoded for identity in step.lifecycle.allocated_identities),
            (2,),
        )
        self.assertTrue(step.outcomes[0].survived_initial_vm)

    def test_initial_minus_one_reuses_slot_in_same_update(self) -> None:
        ledger = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=20,
            active_slots=(),
        )
        returns = iter((-1, 0))

        step = execute_route2_timeline_spawn_lifecycles(
            ledger,
            next_physical_update=21,
            spawns=(_spawn(0x10), _spawn(0x30)),
            initial_vm_executor=lambda _request, _identity: next(returns),
            observed_active_slots=(0,),
        )

        self.assertEqual(
            tuple((event.kind, event.slot) for event in step.lifecycle.events),
            (("allocate", 0), ("retire", 0), ("allocate", 0)),
        )
        self.assertEqual(
            tuple(
                outcome.identity.allocation_generation
                for outcome in step.outcomes
                if outcome.identity is not None
            ),
            (0, 1),
        )
        self.assertEqual(
            step.lifecycle.successor.identity_for_active_slot(0).encoded,
            (1 << 32),
        )

    def test_pool_full_does_not_call_initial_vm_or_emit_event(self) -> None:
        ledger = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=30,
            active_slots=tuple(range(480)),
        )
        calls = 0

        def initial_vm(_request, _identity):
            nonlocal calls
            calls += 1
            return 0

        step = execute_route2_timeline_spawn_lifecycles(
            ledger,
            next_physical_update=31,
            spawns=(_spawn(0x40),),
            initial_vm_executor=initial_vm,
            observed_active_slots=tuple(range(480)),
        )

        self.assertEqual(calls, 0)
        self.assertEqual(step.lifecycle.events, ())
        self.assertTrue(step.outcomes[0].pool_full)
        self.assertIsNone(step.outcomes[0].identity)

    def test_endpoint_snapshot_cannot_hide_missing_lifecycle(self) -> None:
        ledger = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=40,
            active_slots=(),
        )
        with self.assertRaisesRegex(
            ValueError,
            "ordered lifecycle events are incomplete",
        ):
            execute_route2_timeline_spawn_lifecycles(
                ledger,
                next_physical_update=41,
                spawns=(_spawn(0x50),),
                initial_vm_executor=lambda _request, _identity: 0,
                observed_active_slots=(),
            )

    def test_independent_scalar_differential_matches_all_cases(self) -> None:
        report = build_report()
        self.assertEqual(report["case_count"], 4)
        self.assertEqual(report["match_count"], 4)
        self.assertTrue(all(case["match"] for case in report["cases"]))


if __name__ == "__main__":
    unittest.main()
