from __future__ import annotations

import unittest

from th08_future_body_identity import (
    Route2BodyGenerationIdentity,
    Route2SlotLifecycleEvent,
    Route2SlotLifetimeLedger,
    advance_route2_slot_lifetimes,
    lower_route2_generation_identity_to_future_body_sample,
)


def _event(
    *,
    update: int,
    sequence: int,
    kind: str,
    slot: int,
) -> Route2SlotLifecycleEvent:
    return Route2SlotLifecycleEvent(
        physical_update=update,
        sequence=sequence,
        kind=kind,
        slot=slot,
        source="test_native_order",
    )


class Route2BodyGenerationIdentityTests(unittest.TestCase):
    def test_generation_zero_preserves_legacy_slot_integer(self) -> None:
        identity = Route2BodyGenerationIdentity(
            slot=17,
            allocation_generation=0,
        )

        self.assertEqual(identity.encoded, 17)
        self.assertEqual(
            Route2BodyGenerationIdentity.from_encoded(identity.encoded),
            identity,
        )

    def test_reused_slot_has_an_injective_encoded_identity(self) -> None:
        first = Route2BodyGenerationIdentity(
            slot=17,
            allocation_generation=0,
        )
        second = Route2BodyGenerationIdentity(
            slot=17,
            allocation_generation=1,
        )

        self.assertNotEqual(first.encoded, second.encoded)
        self.assertEqual(
            Route2BodyGenerationIdentity.from_encoded(second.encoded),
            second,
        )

    def test_encoded_non_pool_slot_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "ordinary enemy slot"):
            Route2BodyGenerationIdentity.from_encoded(480)

    def test_future_sample_requires_exact_generation_object(self) -> None:
        identity = Route2BodyGenerationIdentity(
            slot=3,
            allocation_generation=2,
        )
        sample = lower_route2_generation_identity_to_future_body_sample(
            identity=identity,
            base_flags=1,
            x=1.0,
            y=2.0,
            half_width=3.0,
            half_height=4.0,
        )

        self.assertEqual(sample.identity, identity.encoded)
        with self.assertRaisesRegex(ValueError, "generational identity"):
            lower_route2_generation_identity_to_future_body_sample(
                identity=identity.encoded,
                base_flags=1,
                x=1.0,
                y=2.0,
                half_width=3.0,
                half_height=4.0,
            )


class Route2SlotLifetimeLedgerTests(unittest.TestCase):
    def test_same_update_immediate_retire_and_reuse_consumes_generation(
        self,
    ) -> None:
        root = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=100,
            active_slots=(),
        )
        step = advance_route2_slot_lifetimes(
            root,
            next_physical_update=101,
            events=(
                _event(update=101, sequence=0, kind="allocate", slot=7),
                _event(update=101, sequence=1, kind="retire", slot=7),
                _event(update=101, sequence=2, kind="allocate", slot=7),
            ),
            observed_active_slots=(7,),
        )

        self.assertEqual(
            tuple(
                identity.allocation_generation
                for identity in step.allocated_identities
            ),
            (0, 1),
        )
        self.assertEqual(
            step.retired_identities,
            (Route2BodyGenerationIdentity(7, 0),),
        )
        self.assertEqual(
            step.successor.identity_for_active_slot(7),
            Route2BodyGenerationIdentity(7, 1),
        )

    def test_root_active_lifetime_reallocation_starts_at_generation_one(
        self,
    ) -> None:
        root = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=20,
            active_slots=(9,),
        )
        step = advance_route2_slot_lifetimes(
            root,
            next_physical_update=21,
            events=(
                _event(update=21, sequence=0, kind="retire", slot=9),
                _event(update=21, sequence=1, kind="allocate", slot=9),
            ),
            observed_active_slots=(9,),
        )

        self.assertEqual(
            step.allocated_identities,
            (Route2BodyGenerationIdentity(9, 1),),
        )
        self.assertEqual(
            step.retired_identities,
            (Route2BodyGenerationIdentity(9, 0),),
        )

    def test_endpoint_active_bits_cannot_supply_a_missing_event(self) -> None:
        root = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=30,
            active_slots=(4,),
        )

        with self.assertRaisesRegex(ValueError, "events are incomplete"):
            advance_route2_slot_lifetimes(
                root,
                next_physical_update=31,
                events=(
                    _event(update=31, sequence=0, kind="retire", slot=4),
                ),
                observed_active_slots=(4,),
            )

    def test_invalid_native_order_fails_closed(self) -> None:
        root = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=40,
            active_slots=(),
        )

        with self.assertRaisesRegex(ValueError, "inactive slot"):
            advance_route2_slot_lifetimes(
                root,
                next_physical_update=41,
                events=(
                    _event(update=41, sequence=0, kind="retire", slot=1),
                ),
            )
        with self.assertRaisesRegex(ValueError, "contiguous from zero"):
            advance_route2_slot_lifetimes(
                root,
                next_physical_update=41,
                events=(
                    _event(update=41, sequence=1, kind="allocate", slot=1),
                ),
            )

    def test_ledger_version_distinguishes_hidden_reuse(self) -> None:
        root = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=50,
            active_slots=(2,),
        )
        unchanged = advance_route2_slot_lifetimes(
            root,
            next_physical_update=51,
            events=(),
            observed_active_slots=(2,),
        ).successor
        reused = advance_route2_slot_lifetimes(
            root,
            next_physical_update=51,
            events=(
                _event(update=51, sequence=0, kind="retire", slot=2),
                _event(update=51, sequence=1, kind="allocate", slot=2),
            ),
            observed_active_slots=(2,),
        ).successor

        self.assertEqual(
            tuple(identity.slot for identity in unchanged.active_identities),
            tuple(identity.slot for identity in reused.active_identities),
        )
        self.assertNotEqual(unchanged.active_identities, reused.active_identities)
        self.assertNotEqual(unchanged.digest, reused.digest)


if __name__ == "__main__":
    unittest.main()
