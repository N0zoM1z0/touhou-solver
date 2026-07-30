from __future__ import annotations

import unittest

from th08_enemy_mode import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_CONTACT_ENABLED_FLAG,
    ENEMY_MANAGER_BLOCKING_FLAGS,
    ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG,
    ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG,
    ENEMY_SECONDARY_CHARACTER_SYNC_FLAG,
)
from th08_future_body_schedule import (
    OFFLINE_AUTHORITY,
    Route2FutureBodyFrame,
    Route2FutureBodySample,
    Route2FutureBodyScheduleBranch,
    Route2FutureBodyScheduleSet,
    merge_route2_versioned_async_mode_observation_classes,
    project_route2_versioned_async_mode_decision_branches,
)
from touhou_control.ordered_input_transaction_oracle import (
    OrderedInputBelief,
    OrderedInputExactState,
)
from touhou_control.pipeline_identity import VersionIdentity


SUPPORTED = 0xF7
SYNC_CONTACT_DAMAGE = (
    ENEMY_ACTIVE_FLAG
    | ENEMY_CONTACT_ENABLED_FLAG
    | ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG
    | ENEMY_SECONDARY_CHARACTER_SYNC_FLAG
)
PLAIN_CONTACT = ENEMY_ACTIVE_FLAG | ENEMY_CONTACT_ENABLED_FLAG
ACTION_MASKS = {
    "shot": 0x01,
    "focus_shot": 0x05,
}


def _body(
    identity: int,
    flags: int,
    *,
    x: float = 32.0,
) -> Route2FutureBodySample:
    return Route2FutureBodySample(
        identity=identity,
        base_flags=flags,
        x=x,
        y=64.0,
        half_width=8.0,
        half_height=12.0,
        uncertainty=0.5,
    )


def _branch(
    *frames: tuple[Route2FutureBodySample, ...],
) -> Route2FutureBodyScheduleBranch:
    return Route2FutureBodyScheduleBranch(
        tuple(
            Route2FutureBodyFrame(
                physical_step=index,
                bodies=bodies,
            )
            for index, bodies in enumerate(frames, start=1)
        )
    )


def _schedule(
    *branches: Route2FutureBodyScheduleBranch,
) -> Route2FutureBodyScheduleSet:
    return Route2FutureBodyScheduleSet.from_branches(
        root_physical_update=100,
        clock_version=VersionIdentity.from_mapping(
            "th08-player-enemy-update-clock-test-v1",
            {"fixture": 1},
        ),
        source="deterministic_test_fixture",
        source_sha256="1" * 64,
        branches=tuple(branches),
    )


def _settled(mask: int) -> OrderedInputBelief:
    return OrderedInputBelief.from_states(
        (OrderedInputExactState(mask, mask),)
    )


def _oracle_body_sets(
    bodies: tuple[Route2FutureBodySample, ...],
    *,
    secondary_active: bool,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    contacts = []
    damage = []
    for body in bodies:
        flags = body.base_flags
        if (
            flags & ENEMY_ACTIVE_FLAG
            and flags & ENEMY_SECONDARY_CHARACTER_SYNC_FLAG
        ):
            if secondary_active:
                flags |= ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG
            else:
                flags &= ~ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG
        manager_open = bool(
            flags & ENEMY_ACTIVE_FLAG
            and not flags & ENEMY_MANAGER_BLOCKING_FLAGS
        )
        if manager_open and flags & ENEMY_CONTACT_ENABLED_FLAG:
            contacts.append(body.identity)
        if manager_open and flags & ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG:
            damage.append(body.identity)
    return tuple(contacts), tuple(damage)


class ImmutableFutureBodyScheduleTests(unittest.TestCase):
    def test_digest_covers_flags_geometry_clock_and_provenance(self) -> None:
        first = _schedule(_branch((_body(0x1000, SYNC_CONTACT_DAMAGE),)))
        same = _schedule(_branch((_body(0x1000, SYNC_CONTACT_DAMAGE),)))
        changed_geometry = _schedule(
            _branch((_body(0x1000, SYNC_CONTACT_DAMAGE, x=33.0),))
        )
        changed_flags = _schedule(
            _branch((_body(0x1000, PLAIN_CONTACT),))
        )

        self.assertEqual(first.digest, same.digest)
        self.assertNotEqual(first.digest, changed_geometry.digest)
        self.assertNotEqual(first.digest, changed_flags.digest)
        self.assertEqual(first.record()["authority"], OFFLINE_AUTHORITY)
        self.assertFalse(first.record()["physical_predictive_authority"])

    def test_invalid_or_action_conditioned_schedule_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly representable"):
            _body(0x1000, PLAIN_CONTACT, x=0.1)
        with self.assertRaisesRegex(ValueError, "must clear flag 0x800"):
            _body(
                0x1000,
                SYNC_CONTACT_DAMAGE
                | ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG,
            )
        with self.assertRaisesRegex(ValueError, "must be sorted"):
            _branch(
                (
                    _body(0x2000, PLAIN_CONTACT),
                    _body(0x1000, PLAIN_CONTACT),
                )
            )
        with self.assertRaisesRegex(ValueError, "share one physical horizon"):
            _schedule(
                _branch((_body(0x1000, PLAIN_CONTACT),)),
                _branch(
                    (_body(0x1000, PLAIN_CONTACT),),
                    (_body(0x1000, PLAIN_CONTACT),),
                ),
            )

    def test_mutable_container_inputs_fail_closed(self) -> None:
        body = _body(0x1000, PLAIN_CONTACT)
        with self.assertRaisesRegex(ValueError, "immutable sample tuple"):
            Route2FutureBodyFrame(1, [body])
        frame = Route2FutureBodyFrame(1, (body,))
        with self.assertRaisesRegex(ValueError, "immutable frame tuple"):
            Route2FutureBodyScheduleBranch([frame])
        branch = Route2FutureBodyScheduleBranch((frame,))
        with self.assertRaisesRegex(ValueError, "immutable branch tuple"):
            Route2FutureBodyScheduleSet(
                root_physical_update=100,
                clock_version=VersionIdentity("clock"),
                source="test",
                source_sha256="1" * 64,
                branches=[branch],
            )
        with self.assertRaisesRegex(ValueError, "canonical and immutable"):
            Route2FutureBodyScheduleSet(
                root_physical_update=100,
                clock_version=VersionIdentity(
                    "clock",
                    [("mutable", True)],
                ),
                source="test",
                source_sha256="1" * 64,
                branches=(branch,),
            )

    def test_versioned_projection_matches_independent_body_set_oracle(
        self,
    ) -> None:
        schedule = _schedule(
            _branch(
                (
                    _body(0x1000, SYNC_CONTACT_DAMAGE),
                    _body(0x2000, PLAIN_CONTACT),
                ),
                (
                    _body(0x1000, SYNC_CONTACT_DAMAGE),
                    _body(0x2000, PLAIN_CONTACT),
                ),
            )
        )
        branches = project_route2_versioned_async_mode_decision_branches(
            future_schedule=schedule,
            input_belief=_settled(0x01),
            selected_action="focus_shot",
            action_masks=ACTION_MASKS,
            supported_mask=SUPPORTED,
            post_dispatch_delay_frames=(1,),
            dispatch_callback_count_support=(1,),
            decision_frame_support=(2,),
            initial_mode_state=(0, False, 4),
        )

        self.assertTrue(branches)
        schedule_branch = schedule.branches[0]
        for versioned in branches:
            self.assertEqual(
                versioned.future_schedule_version,
                schedule.digest,
            )
            for frame in versioned.mode_branch.hazard_branch.frames:
                bodies = schedule_branch.frames[
                    frame.physical_step - 1
                ].bodies
                expected_contact, expected_damage = _oracle_body_sets(
                    bodies,
                    secondary_active=frame.mode_state_after[1],
                )
                self.assertEqual(
                    frame.contact_body_ids,
                    expected_contact,
                )
                self.assertEqual(
                    frame.player_shot_damage_body_ids,
                    expected_damage,
                )

    def test_hidden_schedule_branch_is_not_controller_observation(
        self,
    ) -> None:
        converged = (_body(0x1000, PLAIN_CONTACT, x=48.0),)
        schedule = _schedule(
            _branch(
                (_body(0x1000, PLAIN_CONTACT, x=32.0),),
                converged,
            ),
            _branch(
                (_body(0x1000, PLAIN_CONTACT, x=40.0),),
                converged,
            ),
        )
        branches = project_route2_versioned_async_mode_decision_branches(
            future_schedule=schedule,
            input_belief=_settled(0x01),
            selected_action="shot",
            action_masks=ACTION_MASKS,
            supported_mask=SUPPORTED,
            post_dispatch_delay_frames=(),
            dispatch_callback_count_support=(),
            decision_frame_support=(2,),
            initial_mode_state=(0, False, 0),
        )
        classes = merge_route2_versioned_async_mode_observation_classes(
            branches,
            base_observation=lambda _branch, _frame: "same_observation",
        )

        self.assertEqual(len(branches), 2)
        self.assertEqual(len(classes), 1)
        self.assertEqual(len(classes[0].hidden_branches), 2)
        self.assertEqual(
            {
                branch.future_schedule_branch
                for branch in classes[0].hidden_branches
            },
            {branch.digest for branch in schedule.branches},
        )
        self.assertEqual(
            classes[0].key.future_schedule_version,
            schedule.digest,
        )

    def test_different_observed_geometry_cannot_be_omitted_from_merge(
        self,
    ) -> None:
        schedule = _schedule(
            _branch((_body(0x1000, PLAIN_CONTACT, x=32.0),)),
            _branch((_body(0x1000, PLAIN_CONTACT, x=40.0),)),
        )
        branches = project_route2_versioned_async_mode_decision_branches(
            future_schedule=schedule,
            input_belief=_settled(0x01),
            selected_action="shot",
            action_masks=ACTION_MASKS,
            supported_mask=SUPPORTED,
            post_dispatch_delay_frames=(),
            dispatch_callback_count_support=(),
            decision_frame_support=(1,),
            initial_mode_state=(0, False, 0),
        )
        classes = merge_route2_versioned_async_mode_observation_classes(
            branches,
            base_observation=lambda _branch, _frame: "same_other_fields",
        )

        self.assertEqual(len(branches), 2)
        self.assertEqual(len(classes), 2)
        self.assertEqual(
            len(
                {
                    observation.key.observed_body_state
                    for observation in classes
                }
            ),
            2,
        )

    def test_short_schedule_and_cross_version_merge_fail_closed(self) -> None:
        first = _schedule(_branch((_body(0x1000, PLAIN_CONTACT),)))
        with self.assertRaisesRegex(ValueError, "does not cover cadence"):
            project_route2_versioned_async_mode_decision_branches(
                future_schedule=first,
                input_belief=_settled(0x01),
                selected_action="shot",
                action_masks=ACTION_MASKS,
                supported_mask=SUPPORTED,
                post_dispatch_delay_frames=(),
                dispatch_callback_count_support=(),
                decision_frame_support=(2,),
                initial_mode_state=(0, False, 0),
            )

        second = _schedule(
            _branch((_body(0x1000, PLAIN_CONTACT, x=33.0),))
        )
        first_branches = project_route2_versioned_async_mode_decision_branches(
            future_schedule=first,
            input_belief=_settled(0x01),
            selected_action="shot",
            action_masks=ACTION_MASKS,
            supported_mask=SUPPORTED,
            post_dispatch_delay_frames=(),
            dispatch_callback_count_support=(),
            decision_frame_support=(1,),
            initial_mode_state=(0, False, 0),
        )
        second_branches = (
            project_route2_versioned_async_mode_decision_branches(
                future_schedule=second,
                input_belief=_settled(0x01),
                selected_action="shot",
                action_masks=ACTION_MASKS,
                supported_mask=SUPPORTED,
                post_dispatch_delay_frames=(),
                dispatch_callback_count_support=(),
                decision_frame_support=(1,),
                initial_mode_state=(0, False, 0),
            )
        )
        with self.assertRaisesRegex(ValueError, "different future schedule"):
            merge_route2_versioned_async_mode_observation_classes(
                first_branches + second_branches,
                base_observation=lambda _branch, _frame: "same",
            )


if __name__ == "__main__":
    unittest.main()
