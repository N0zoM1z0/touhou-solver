from __future__ import annotations

import random
import unittest

import numpy as np

from analysis.local_pipeline_certificate_audit import (
    _direct_root_from_trace,
)
from th08_live_dodge_agent import (
    Bullet,
    DOWN,
    EnemyBody,
    FOCUS,
    Laser,
    PLAYFIELD_BOTTOM,
    PLAYFIELD_LEFT,
    PLAYFIELD_RIGHT,
    PLAYFIELD_TOP,
    RIGHT,
    SHOT,
    _PLANNER_ACTIONS,
    _LocalCertificateTimingAccumulator,
    _boundary_risk,
    _boundary_risk_for_positions,
    _build_bullet_frames,
    _build_packed_laser_collision_frames,
    _hazards_for_positions,
    _legacy_robust_action_certificates,
    _robust_action_certificates,
    _direct_root_certificate_shadow,
)
from touhou_control.local_pipeline_oracle import (
    LocalPipelineRoot,
    scalar_local_pipeline_certificates,
)


class Th08LocalPipelineCertificateTests(unittest.TestCase):
    def test_explicit_root_certificate_reports_segmented_timing(self) -> None:
        root = LocalPipelineRoot(
            active_action="stay",
            held_desired_action="right",
            pending_action="right",
            remaining_delay_support=(1, 2),
        )
        timing = _LocalCertificateTimingAccumulator()
        certificates = _robust_action_certificates(
            player_x=192.0,
            player_y=400.0,
            previous_mask=SHOT | FOCUS | RIGHT,
            actions=_PLANNER_ACTIONS,
            delay_frames=(1, 2),
            action_hold_frames=2,
            bullets=(),
            lasers=(),
            enemy_bodies=(),
            snapshot_lag=0,
            pipeline_root=root,
            timing_accumulator=timing,
        )

        snapshot = timing.snapshot()
        self.assertEqual(snapshot.calls, 1)
        self.assertEqual(snapshot.explicit_root_calls, 1)
        self.assertGreater(
            snapshot.maximum_branch_count,
            len(_PLANNER_ACTIONS),
        )
        self.assertEqual(set(certificates), {
            action.name for action in _PLANNER_ACTIONS
        })
        segmented = (
            snapshot.validation_ms
            + snapshot.hazard_projection_ms
            + snapshot.branch_setup_ms
            + snapshot.geometry_kernel_ms
            + snapshot.reduction_ms
        )
        self.assertAlmostEqual(
            snapshot.certificate_total_ms,
            segmented,
            places=6,
        )

        shadow = _direct_root_certificate_shadow(
            root=root,
            player_x=192.0,
            player_y=400.0,
            previous_mask=SHOT | FOCUS | RIGHT,
            delay_frames=(1, 2),
            action_hold_frames=2,
            bullets=(),
            lasers=(),
            enemy_bodies=(),
            snapshot_lag=0,
        )
        self.assertEqual(
            shadow["role"],
            "post_issue_shadow_no_action_authority",
        )
        self.assertTrue(shadow["computed_after_input"])
        self.assertEqual(shadow["timing"]["explicit_root_calls"], 1)

    def test_direct_trace_root_is_cross_checked(self) -> None:
        active_mask = SHOT | FOCUS | RIGHT
        held_mask = SHOT | FOCUS | DOWN | RIGHT
        row = {
            "input_snapshot": {"current": active_mask},
            "local_pipeline_root": {
                "role": "shadow_no_action_authority",
                "active_action": "right",
                "active_mask": active_mask,
                "held_desired_action": "down_right",
                "held_desired_mask": held_mask,
                "pending_action": "down_right",
                "pending_mask": held_mask,
                "remaining_delay_support": [1, 3],
                "issue_age": 2,
                "overdue": False,
                "estimator_consistent": True,
            },
        }

        root, parsed_held_mask, issue_age, overdue = (
            _direct_root_from_trace(row)
        )

        self.assertEqual(root.active_action, "right")
        self.assertEqual(root.pending_action, "down_right")
        self.assertEqual(root.remaining_delay_support, (1, 3))
        self.assertEqual(parsed_held_mask, held_mask)
        self.assertEqual(issue_age, 2)
        self.assertFalse(overdue)

        row["local_pipeline_root"]["active_action"] = "left"
        with self.assertRaises(ValueError):
            _direct_root_from_trace(row)

        aliased_stay_row = {
            "input_snapshot": {"current": SHOT},
            "local_pipeline_root": {
                "role": "shadow_no_action_authority",
                "active_action": "stay",
                "active_mask": SHOT,
                "held_desired_action": "stay",
                "held_desired_mask": SHOT | FOCUS,
                "pending_action": None,
                "pending_mask": None,
                "remaining_delay_support": [],
                "issue_age": None,
                "overdue": False,
                "estimator_consistent": True,
            },
        }
        with self.assertRaises(ValueError):
            _direct_root_from_trace(aliased_stay_row)

    def test_vectorized_boundary_risk_matches_scalar(self) -> None:
        positions_x = np.asarray(
            [32.0, 39.5, 192.0, 344.5, 352.0],
            dtype=np.float32,
        )
        positions_y = np.asarray(
            [16.0, 27.0, 240.0, 437.5, 448.0],
            dtype=np.float32,
        )

        expected = np.fromiter(
            (
                _boundary_risk(float(x), float(y))
                for x, y in zip(positions_x, positions_y)
            ),
            dtype=np.float64,
        )
        actual = _boundary_risk_for_positions(
            positions_x,
            positions_y,
        )

        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=0.0)

    def test_hazard_batch_is_invariant_to_companion_positions(self) -> None:
        bullets = (
            Bullet(190.0, 210.0, 0.0, 0.0, 3.0, 3.0),
            Bullet(305.0, 310.0, 0.0, 0.0, 4.0, 4.0),
        )
        bullet_frame = _build_bullet_frames(
            bullets,
            horizon=3,
            snapshot_lag=0,
        )[2]
        laser_frame = _build_packed_laser_collision_frames(
            (Laser(120.0, 260.0, 0.0, 0.0, 100.0, 6.0),),
            horizon=3,
        )[2]
        positions_x = np.asarray([82.0, 300.0], dtype=np.float32)
        positions_y = np.asarray([165.0, 390.0], dtype=np.float32)

        batch = _hazards_for_positions(
            positions_x,
            positions_y,
            step=3,
            bullet_frame=bullet_frame,
            lasers=laser_frame,
            enemy_bodies=(),
        )
        scalar = tuple(
            np.concatenate(
                [
                    _hazards_for_positions(
                        positions_x[index : index + 1],
                        positions_y[index : index + 1],
                        step=3,
                        bullet_frame=bullet_frame,
                        lasers=laser_frame,
                        enemy_bodies=(),
                    )[field]
                    for index in range(len(positions_x))
                ]
            )
            for field in range(3)
        )

        np.testing.assert_allclose(batch[0], scalar[0], rtol=0.0, atol=0.0)
        np.testing.assert_array_equal(batch[1], scalar[1])
        np.testing.assert_allclose(batch[2], scalar[2], rtol=0.0, atol=0.0)

    def scalar_certificates(
        self,
        *,
        root: LocalPipelineRoot,
        bullets: tuple[Bullet, ...],
        enemy_bodies: tuple[EnemyBody, ...],
        delay_frames: tuple[int, ...],
        action_hold_frames: int,
        player_x: float,
        player_y: float,
        snapshot_lag: int = 0,
    ):
        horizon = action_hold_frames + max(delay_frames)
        bullet_frames = _build_bullet_frames(
            bullets,
            horizon=horizon,
            snapshot_lag=-max(0, snapshot_lag),
        )
        laser_frames = _build_packed_laser_collision_frames(
            (),
            horizon=horizon,
        )

        def sample(
            x: float,
            y: float,
            step: int,
        ) -> tuple[float, int, float]:
            risk, collisions, clearance = _hazards_for_positions(
                np.asarray([x], dtype=np.float32),
                np.asarray([y], dtype=np.float32),
                step=step,
                bullet_frame=bullet_frames[step - 1],
                lasers=laser_frames[step - 1],
                enemy_bodies=enemy_bodies,
            )
            return (
                float(risk[0]),
                int(collisions[0]),
                float(clearance[0]),
            )

        return scalar_local_pipeline_certificates(
            root=root,
            selected_actions=tuple(
                action.name for action in _PLANNER_ACTIONS
            ),
            action_velocities={
                **{
                    action.name: (action.dx, action.dy)
                    for action in _PLANNER_ACTIONS
                },
                "stay_unfocused": (0.0, 0.0),
            },
            delay_frames=delay_frames,
            horizon_frames=horizon,
            start_x=player_x,
            start_y=player_y,
            bounds=(
                PLAYFIELD_LEFT,
                PLAYFIELD_RIGHT,
                PLAYFIELD_TOP,
                PLAYFIELD_BOTTOM,
            ),
            hazard_sample=sample,
            boundary_risk=_boundary_risk,
        )

    def test_unfocused_stay_is_a_distinct_write_identity(self) -> None:
        root = LocalPipelineRoot(
            active_action="right_fast",
            held_desired_action="stay_unfocused",
            pending_action="stay_unfocused",
            remaining_delay_support=(2,),
        )
        common = {
            "player_x": 190.0,
            "player_y": 260.0,
            "previous_mask": SHOT,
            "actions": _PLANNER_ACTIONS,
            "delay_frames": (1, 3),
            "action_hold_frames": 2,
            "bullets": (
                Bullet(205.0, 260.0, 0.0, 0.0, 4.0, 4.0),
            ),
            "lasers": (),
            "enemy_bodies": (),
            "snapshot_lag": 0,
        }
        packed = _robust_action_certificates(
            **common,
            pipeline_root=root,
        )
        scalar = self.scalar_certificates(
            root=root,
            bullets=common["bullets"],
            enemy_bodies=(),
            delay_frames=common["delay_frames"],
            action_hold_frames=common["action_hold_frames"],
            player_x=common["player_x"],
            player_y=common["player_y"],
        )

        self.assertTrue(packed["stay"].write_required)
        self.assertEqual(
            packed["stay"].pipeline_branch_count,
            len(common["delay_frames"]),
        )
        self.assertEqual(
            packed["stay"].worst_collisions,
            scalar["stay"].worst_collisions,
        )
        self.assertAlmostEqual(
            packed["stay"].min_clearance,
            scalar["stay"].min_clearance,
            places=5,
        )

    def test_pending_hold_matches_independent_scalar_oracle(self) -> None:
        root = LocalPipelineRoot(
            active_action="stay",
            held_desired_action="left",
            pending_action="left",
            remaining_delay_support=(1, 2, 3),
        )
        bullets = (
            Bullet(178.0, 375.0, 0.0, 2.0, 3.0, 3.0),
            Bullet(212.0, 390.0, -1.0, 1.0, 4.0, 4.0),
        )
        enemy_bodies = (
            EnemyBody(
                1,
                192.0,
                350.0,
                0.0,
                1.0,
                8.0,
                8.0,
                0,
            ),
        )
        arguments = dict(
            root=root,
            bullets=bullets,
            enemy_bodies=enemy_bodies,
            delay_frames=(2, 3, 4),
            action_hold_frames=4,
            player_x=192.0,
            player_y=400.0,
            snapshot_lag=1,
        )

        expected = self.scalar_certificates(**arguments)
        actual = _robust_action_certificates(
            player_x=arguments["player_x"],
            player_y=arguments["player_y"],
            previous_mask=0,
            actions=_PLANNER_ACTIONS,
            delay_frames=arguments["delay_frames"],
            action_hold_frames=arguments["action_hold_frames"],
            bullets=bullets,
            lasers=(),
            enemy_bodies=enemy_bodies,
            snapshot_lag=arguments["snapshot_lag"],
            pipeline_root=root,
        )

        for action in _PLANNER_ACTIONS:
            scalar = expected[action.name]
            packed = actual[action.name]
            self.assertEqual(
                packed.worst_collisions,
                scalar.worst_collisions,
                action.name,
            )
            self.assertAlmostEqual(
                packed.min_clearance,
                scalar.min_clearance,
                delta=1e-3,
                msg=action.name,
            )
            self.assertAlmostEqual(
                packed.cvar_risk,
                scalar.cvar_risk,
                delta=1e-1,
                msg=action.name,
            )
            self.assertEqual(
                packed.write_required,
                scalar.write_required,
                action.name,
            )
            self.assertEqual(
                packed.pipeline_branch_count,
                scalar.branch_count,
                action.name,
            )
            self.assertEqual(
                packed.worst_delay,
                scalar.worst_new_delay,
                action.name,
            )
            self.assertEqual(
                packed.worst_pending_remaining,
                scalar.worst_pending_remaining,
                action.name,
            )

    def test_randomized_pipeline_roots_match_scalar_oracle(self) -> None:
        randomizer = random.Random(20260726)
        action_names = tuple(action.name for action in _PLANNER_ACTIONS)
        for seed in range(24):
            active = action_names[seed % len(action_names)]
            if seed % 3:
                held = action_names[(seed * 5 + 1) % len(action_names)]
                root = LocalPipelineRoot(
                    active_action=active,
                    held_desired_action=held,
                    pending_action=held,
                    remaining_delay_support=(
                        (1, 2, 4) if seed % 2 else (2, 3)
                    ),
                )
            else:
                root = LocalPipelineRoot(
                    active_action=active,
                    held_desired_action=active,
                )
            player_x = randomizer.uniform(40.0, 344.0)
            player_y = randomizer.uniform(80.0, 432.0)
            bullets = tuple(
                Bullet(
                    randomizer.uniform(20.0, 364.0),
                    randomizer.uniform(40.0, 448.0),
                    randomizer.uniform(-2.0, 2.0),
                    randomizer.uniform(-1.0, 3.0),
                    randomizer.uniform(1.0, 5.0),
                    randomizer.uniform(1.0, 5.0),
                )
                for _ in range(5)
            )
            enemy_bodies = tuple(
                EnemyBody(
                    index + 1,
                    randomizer.uniform(20.0, 364.0),
                    randomizer.uniform(40.0, 448.0),
                    randomizer.uniform(-1.0, 1.0),
                    randomizer.uniform(-1.0, 1.0),
                    randomizer.uniform(3.0, 12.0),
                    randomizer.uniform(3.0, 12.0),
                    0,
                    randomizer.uniform(0.0, 1.0),
                )
                for index in range(2)
            )
            delay_frames = (1, 2, 3)
            action_hold_frames = 3
            expected = self.scalar_certificates(
                root=root,
                bullets=bullets,
                enemy_bodies=enemy_bodies,
                delay_frames=delay_frames,
                action_hold_frames=action_hold_frames,
                player_x=player_x,
                player_y=player_y,
            )
            actual = _robust_action_certificates(
                player_x=player_x,
                player_y=player_y,
                previous_mask=0,
                actions=_PLANNER_ACTIONS,
                delay_frames=delay_frames,
                action_hold_frames=action_hold_frames,
                bullets=bullets,
                lasers=(),
                enemy_bodies=enemy_bodies,
                snapshot_lag=0,
                pipeline_root=root,
            )
            for action in _PLANNER_ACTIONS:
                scalar = expected[action.name]
                packed = actual[action.name]
                self.assertEqual(
                    packed.worst_collisions,
                    scalar.worst_collisions,
                    (seed, action.name),
                )
                self.assertAlmostEqual(
                    packed.min_clearance,
                    scalar.min_clearance,
                    delta=1e-3,
                    msg=str((seed, action.name)),
                )
                self.assertAlmostEqual(
                    packed.cvar_risk,
                    scalar.cvar_risk,
                    delta=1e-1,
                    msg=str((seed, action.name)),
                )

    def test_no_pending_root_preserves_legacy_hard_labels(self) -> None:
        common = dict(
            player_x=192.0,
            player_y=400.0,
            previous_mask=0x04,
            actions=_PLANNER_ACTIONS,
            delay_frames=(2, 3, 4),
            action_hold_frames=3,
            bullets=(
                Bullet(192.0, 370.0, 0.0, 2.5, 3.0, 3.0),
            ),
            lasers=(),
            enemy_bodies=(),
            snapshot_lag=0,
        )

        legacy = _legacy_robust_action_certificates(**common)
        packed = _robust_action_certificates(**common)

        for action in _PLANNER_ACTIONS:
            self.assertEqual(
                packed[action.name].worst_collisions,
                legacy[action.name].worst_collisions,
                action.name,
            )
            self.assertAlmostEqual(
                packed[action.name].min_clearance,
                legacy[action.name].min_clearance,
                delta=1e-3,
                msg=action.name,
            )


if __name__ == "__main__":
    unittest.main()
