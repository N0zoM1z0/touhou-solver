from __future__ import annotations

import dataclasses
import unittest
from unittest.mock import patch

import th08_live_dodge_agent as live
from th08_local_planner import (
    ActuatorPipeline,
    CompletedServiceResults,
    GlobalGuidance,
    LocalPlannerRequest,
    ObjectiveContext,
    PhysicalHazardSnapshot,
    PlannerConfig,
)


class LocalPlannerRequestTests(unittest.TestCase):
    def test_request_groups_are_immutable(self) -> None:
        request = LocalPlannerRequest(
            physical=PhysicalHazardSnapshot(
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(),
            ),
            actuator=ActuatorPipeline(
                previous_direction=0,
                can_bomb=False,
            ),
        )

        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.config.horizon = 20  # type: ignore[misc]

    def test_grouped_request_preserves_flat_planner_contract(self) -> None:
        physical = PhysicalHazardSnapshot(
            player_x=190.0,
            player_y=399.0,
            bullets=("bullet",),
            lasers=("laser",),
            enemy_bodies=("enemy",),
            items=("item",),
            snapshot_lag=3,
        )
        actuator = ActuatorPipeline(
            previous_direction=0x40,
            can_bomb=False,
            previous_focus=False,
            local_pipeline_root="root",
            control_delay_frames=4,
            control_delay_candidates=(2, 4),
            action_hold_frames=5,
        )
        guidance = GlobalGuidance(
            target_x=180.0,
            target_y=300.0,
            target_deadline=9,
            allowed_first_actions=("left",),
            viability_repair_volumes=(("left", 3),),
            viability_recovery_distances=(("left", 1.5),),
            viability_safety_actions=("left",),
            viability_safety_state_value=2.0,
            viability_survival_actions=("left",),
            viability_survival_frames=12,
            viability_survival_bottleneck_margin=0.5,
            viability_position_error=0.25,
        )
        config = PlannerConfig(
            horizon=11,
            threat_horizon=15,
            beam_width=7,
            recovery_control_reserve=False,
            losing_control_reserve=True,
            preloss_continuation_preference=True,
            preloss_supplemental_beam_width=13,
            preserve_previous_direction_inertia=False,
            beam_dedup_mode="first_action",
            relax_stale_viability_contradiction=True,
            enforce_fresh_viability_intersection=False,
        )
        objective = ObjectiveContext(
            power=64.0,
            bombs=2.0,
            damage_target_x=200.0,
            damage_target_half_width=8.0,
            damageable=True,
        )
        completed = CompletedServiceResults(
            supplemental_deadline_ms=1.25,
            supplemental_async_service="service",
            supplemental_version=("version", 1),
        )
        sentinel = live.Decision(
            mask=live.SHOT,
            action="stay",
            min_clearance=1.0,
            immediate_clearance=1.0,
            score=0.0,
            bomb=False,
        )
        request = LocalPlannerRequest(
            physical=physical,
            actuator=actuator,
            guidance=guidance,
            config=config,
            objective=objective,
            completed_services=completed,
        )

        with patch.object(
            live,
            "choose_action_request",
            return_value=sentinel,
        ) as choose:
            result = live.choose_action(
                player_x=190.0,
                player_y=399.0,
                bullets=("bullet",),
                lasers=("laser",),
                previous_direction=0x40,
                can_bomb=False,
                enemy_bodies=("enemy",),
                items=("item",),
                power=64.0,
                bombs=2.0,
                previous_focus=False,
                local_pipeline_root="root",
                snapshot_lag=3,
                control_delay_frames=4,
                control_delay_candidates=(2, 4),
                action_hold_frames=5,
                horizon=11,
                threat_horizon=15,
                beam_width=7,
                target_x=180.0,
                target_y=300.0,
                target_deadline=9,
                allowed_first_actions=("left",),
                viability_repair_volumes=(("left", 3),),
                viability_recovery_distances=(("left", 1.5),),
                viability_safety_actions=("left",),
                viability_safety_state_value=2.0,
                viability_survival_actions=("left",),
                viability_survival_frames=12,
                viability_survival_bottleneck_margin=0.5,
                viability_position_error=0.25,
                damage_target_x=200.0,
                damage_target_half_width=8.0,
                damageable=True,
                recovery_control_reserve=False,
                losing_control_reserve=True,
                preloss_continuation_preference=True,
                preloss_supplemental_beam_width=13,
                preloss_supplemental_deadline_ms=1.25,
                preloss_supplemental_async_service="service",
                preloss_supplemental_version=("version", 1),
                preserve_previous_direction_inertia=False,
                beam_dedup_mode="first_action",
                relax_stale_viability_contradiction=True,
                enforce_fresh_viability_intersection=False,
            )

        self.assertIs(result, sentinel)
        choose.assert_called_once_with(request)

    def test_grouped_request_matches_flat_decision(self) -> None:
        request = LocalPlannerRequest(
            physical=PhysicalHazardSnapshot(
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(),
            ),
            actuator=ActuatorPipeline(
                previous_direction=0,
                can_bomb=False,
            ),
            config=PlannerConfig(horizon=3, beam_width=8),
        )

        grouped = live.choose_action_request(request)
        flat = live.choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            previous_direction=0,
            can_bomb=False,
            horizon=3,
            beam_width=8,
        )

        self.assertEqual(
            dataclasses.replace(
                grouped,
                local_certificate_timing=live.LocalCertificateTiming(),
            ),
            dataclasses.replace(
                flat,
                local_certificate_timing=live.LocalCertificateTiming(),
            ),
        )
        self.assertEqual(grouped.mask & live.BOMB, 0)

    def test_relaxed_viability_is_an_explicit_one_way_transition(self) -> None:
        request = LocalPlannerRequest(
            physical=PhysicalHazardSnapshot(
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(),
            ),
            actuator=ActuatorPipeline(
                previous_direction=0,
                can_bomb=False,
            ),
            guidance=GlobalGuidance(
                allowed_first_actions=("stay", "left"),
            ),
        )
        next_request = dataclasses.replace(
            request,
            guidance=dataclasses.replace(
                request.guidance,
                allowed_first_actions=None,
            ),
            mode=live.PlannerMode.RELAXED_VIABILITY,
        )
        current = live.Decision(
            mask=live.SHOT | live.FOCUS,
            action="stay",
            min_clearance=-1.0,
            immediate_clearance=-1.0,
            score=3.0,
            bomb=False,
            robust_collisions=1,
            robust_min_clearance=-1.0,
        )
        retry = dataclasses.replace(
            current,
            mask=live.SHOT | live.FOCUS | live.LEFT,
            action="left",
            min_clearance=2.0,
            immediate_clearance=2.0,
            score=1.0,
            robust_collisions=0,
            robust_min_clearance=2.0,
        )
        transition = live._PlannerModeTransition(
            current_decision=current,
            next_request=next_request,
            original_allowed_action_count=2,
        )

        with patch.object(
            live,
            "_run_local_planner_pass",
            side_effect=(transition, retry),
        ) as plan_once:
            result = live.choose_action_request(request)

        self.assertEqual(plan_once.call_count, 2)
        self.assertIs(plan_once.call_args_list[0].args[0], request)
        self.assertIs(plan_once.call_args_list[1].args[0], next_request)
        self.assertEqual(result.action, "left")
        self.assertTrue(result.viability_constraint_relaxed)
        self.assertEqual(result.viability_safe_action_count, 2)
        self.assertEqual(result.mask & live.BOMB, 0)


if __name__ == "__main__":
    unittest.main()
