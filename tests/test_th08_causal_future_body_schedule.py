from __future__ import annotations

import hashlib
import struct
import unittest

from th08_causal_future_body_schedule import (
    FAMILY_AUTHORITY,
    Route2CausalFutureBodyScheduleFamily,
    Route2ConditionedFutureBodySchedule,
    merge_route2_causal_future_body_observation_classes,
    project_route2_causal_future_body_decision_branches,
)
from th08_enemy_mode import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_CONTACT_ENABLED_FLAG,
)
from th08_future_body_schedule import (
    Route2FutureBodyFrame,
    Route2FutureBodySample,
    Route2FutureBodyScheduleBranch,
    Route2FutureBodyScheduleSet,
)
from touhou_control.ordered_input_transaction_oracle import (
    OrderedInputBelief,
    OrderedInputExactState,
)
from touhou_control.pipeline_identity import VersionIdentity


SUPPORTED = 0xF7
SHOT = 0x01
LEFT_SHOT = 0x21
RIGHT_SHOT = 0x41
ACTION_MASKS = {
    "shot": SHOT,
    "left_shot": LEFT_SHOT,
    "right_shot": RIGHT_SHOT,
}
HISTORIES = (
    (LEFT_SHOT, SHOT),
    (LEFT_SHOT, LEFT_SHOT),
    (LEFT_SHOT, RIGHT_SHOT),
)
BODY_FLAGS = ENEMY_ACTIVE_FLAG | ENEMY_CONTACT_ENABLED_FLAG


def _body(x: float) -> Route2FutureBodySample:
    return Route2FutureBodySample(
        identity=0x1000,
        base_flags=BODY_FLAGS,
        x=x,
        y=96.0,
        half_width=8.0,
        half_height=12.0,
        uncertainty=0.0,
    )


def _schedule(
    identity: str,
    *,
    final_x: float,
) -> Route2FutureBodyScheduleSet:
    branch = Route2FutureBodyScheduleBranch(
        (
            Route2FutureBodyFrame(1, (_body(32.0),)),
            Route2FutureBodyFrame(2, (_body(final_x),)),
        )
    )
    return Route2FutureBodyScheduleSet.from_branches(
        root_physical_update=400,
        clock_version=VersionIdentity.from_mapping(
            "causal-future-body-test-clock-v1",
            {"physical_update": True},
        ),
        source=identity,
        source_sha256=hashlib.sha256(
            identity.encode("ascii")
        ).hexdigest(),
        branches=(branch,),
    )


def _family(
    final_positions: dict[tuple[int, ...], float],
) -> Route2CausalFutureBodyScheduleFamily:
    return Route2CausalFutureBodyScheduleFamily.from_members(
        selected_action="right_shot",
        selected_mask=RIGHT_SHOT,
        members=tuple(
            Route2ConditionedFutureBodySchedule(
                history,
                _schedule(
                    f"history_{'_'.join(map(str, history))}",
                    final_x=final_positions[history],
                ),
            )
            for history in final_positions
        ),
    )


def _belief() -> OrderedInputBelief:
    return OrderedInputBelief.from_states(
        (OrderedInputExactState(LEFT_SHOT, LEFT_SHOT),)
    )


def _project(
    family: Route2CausalFutureBodyScheduleFamily,
):
    return project_route2_causal_future_body_decision_branches(
        family=family,
        input_belief=_belief(),
        selected_action="right_shot",
        action_masks=ACTION_MASKS,
        supported_mask=SUPPORTED,
        post_dispatch_delay_frames=(1, 2),
        dispatch_callback_count_support=(0,),
        decision_frame_support=(2,),
        initial_mode_state=(0, False, 0),
    )


def _float32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


class CausalFutureBodyScheduleTests(unittest.TestCase):
    def test_only_compatible_input_schedule_pairs_are_retained(self) -> None:
        positions = {
            HISTORIES[0]: 48.0,
            HISTORIES[1]: 16.0,
            HISTORIES[2]: 80.0,
        }
        family = _family(positions)
        branches = _project(family)
        schedule_by_history = {
            member.active_mask_history: member.schedule.digest
            for member in family.members
        }

        self.assertEqual(len(branches), 3)
        self.assertEqual(
            {
                branch.conditioned_active_mask_history
                for branch in branches
            },
            set(HISTORIES),
        )
        for branch in branches:
            history = tuple(
                frame.active_mask
                for frame in branch.mode_branch.hazard_branch.frames
            )
            self.assertEqual(
                history,
                branch.conditioned_active_mask_history,
            )
            self.assertEqual(
                branch.supplied_schedule_version,
                schedule_by_history[history],
            )
            self.assertEqual(
                branch.observed_body_state[0][2],
                _float32_bits(positions[history]),
            )

    def test_missing_or_extra_actuator_history_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "coverage differs"):
            _project(
                _family(
                    {
                        HISTORIES[0]: 48.0,
                        HISTORIES[1]: 16.0,
                    }
                )
            )
        with self.assertRaisesRegex(ValueError, "coverage differs"):
            _project(
                _family(
                    {
                        HISTORIES[0]: 48.0,
                        HISTORIES[1]: 16.0,
                        HISTORIES[2]: 80.0,
                        (LEFT_SHOT, 0x11): 96.0,
                    }
                )
            )

    def test_hidden_histories_merge_only_after_body_observation_converges(
        self,
    ) -> None:
        converged = _project(
            _family({history: 64.0 for history in HISTORIES})
        )
        converged_classes = (
            merge_route2_causal_future_body_observation_classes(
                converged,
                base_observation=lambda _branch, _frame: "same",
            )
        )
        diverged = _project(
            _family(
                {
                    HISTORIES[0]: 48.0,
                    HISTORIES[1]: 16.0,
                    HISTORIES[2]: 80.0,
                }
            )
        )
        diverged_classes = (
            merge_route2_causal_future_body_observation_classes(
                diverged,
                base_observation=lambda _branch, _frame: "same",
            )
        )

        self.assertEqual(len(converged_classes), 1)
        self.assertEqual(
            len(converged_classes[0].hidden_branches),
            3,
        )
        self.assertEqual(len(diverged_classes), 3)
        self.assertFalse(
            hasattr(
                converged_classes[0].key,
                "conditioned_active_mask_history",
            )
        )

    def test_family_digest_and_authority_bind_conditioned_schedules(
        self,
    ) -> None:
        first = _family({history: 64.0 for history in HISTORIES})
        same = _family({history: 64.0 for history in HISTORIES})
        changed = _family(
            {
                HISTORIES[0]: 64.0,
                HISTORIES[1]: 64.0,
                HISTORIES[2]: 65.0,
            }
        )

        self.assertEqual(first.digest, same.digest)
        self.assertNotEqual(first.digest, changed.digest)
        self.assertEqual(first.record()["authority"], FAMILY_AUTHORITY)
        self.assertFalse(first.record()["physical_predictive_authority"])

    def test_action_mask_and_family_version_mismatches_fail_closed(
        self,
    ) -> None:
        family = _family({history: 64.0 for history in HISTORIES})
        with self.assertRaisesRegex(ValueError, "action does not match"):
            project_route2_causal_future_body_decision_branches(
                family=family,
                input_belief=_belief(),
                selected_action="left_shot",
                action_masks=ACTION_MASKS,
                supported_mask=SUPPORTED,
                post_dispatch_delay_frames=(1, 2),
                dispatch_callback_count_support=(0,),
                decision_frame_support=(2,),
                initial_mode_state=(0, False, 0),
            )
        wrong_masks = dict(ACTION_MASKS)
        wrong_masks["right_shot"] = 0x51
        with self.assertRaisesRegex(ValueError, "mask does not match"):
            project_route2_causal_future_body_decision_branches(
                family=family,
                input_belief=_belief(),
                selected_action="right_shot",
                action_masks=wrong_masks,
                supported_mask=SUPPORTED,
                post_dispatch_delay_frames=(1, 2),
                dispatch_callback_count_support=(0,),
                decision_frame_support=(2,),
                initial_mode_state=(0, False, 0),
            )

        changed = _family(
            {
                HISTORIES[0]: 64.0,
                HISTORIES[1]: 64.0,
                HISTORIES[2]: 65.0,
            }
        )
        with self.assertRaisesRegex(ValueError, "different causal"):
            merge_route2_causal_future_body_observation_classes(
                _project(family) + _project(changed),
                base_observation=lambda _branch, _frame: "same",
            )

    def test_mutable_or_wrong_horizon_members_fail_closed(self) -> None:
        schedule = _schedule("mutable", final_x=64.0)
        member = Route2ConditionedFutureBodySchedule(
            HISTORIES[0],
            schedule,
        )
        with self.assertRaisesRegex(ValueError, "immutable member tuple"):
            Route2CausalFutureBodyScheduleFamily(
                selected_action="right_shot",
                selected_mask=RIGHT_SHOT,
                members=[member],
            )
        with self.assertRaisesRegex(ValueError, "equal schedule horizon"):
            Route2ConditionedFutureBodySchedule(
                (LEFT_SHOT,),
                schedule,
            )
        with self.assertRaisesRegex(ValueError, "sorted positive tuple"):
            project_route2_causal_future_body_decision_branches(
                family=_family(
                    {history: 64.0 for history in HISTORIES}
                ),
                input_belief=_belief(),
                selected_action="right_shot",
                action_masks=ACTION_MASKS,
                supported_mask=SUPPORTED,
                post_dispatch_delay_frames=(1, 2),
                dispatch_callback_count_support=(0,),
                decision_frame_support=(),
                initial_mode_state=(0, False, 0),
            )


if __name__ == "__main__":
    unittest.main()
