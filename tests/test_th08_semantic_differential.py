from __future__ import annotations

from dataclasses import replace
import threading
import time
import unittest

import numpy as np

import th08_live_dodge_agent as live
from analysis.th08_semantic_differential import evaluate_case
from th08_semantic_cases import (
    SemanticCase,
    generate_case,
    generate_cases,
    shrink_case,
)
from touhou_control import native_backend
from touhou_control.supplemental_local_beam import (
    ExactVersionSupplementalService,
    SupplementalNode,
)


def _native_available() -> bool:
    return (
        native_backend._load_local_supplemental_workspace_functions()
        is not None
    )


def _native_stress_query_arguments() -> dict[str, object]:
    action_count = len(live._PLANNER_ACTIONS)
    hazard_count = 250_000
    frame = (
        np.full(hazard_count, 192.0, dtype=np.float32),
        np.full(hazard_count, 300.0, dtype=np.float32),
        np.full(hazard_count, 2.0, dtype=np.float32),
        np.full(hazard_count, 2.0, dtype=np.float32),
        np.zeros(hazard_count, dtype=np.uint8),
    )
    empty_laser = tuple(
        np.empty(0, dtype=np.float32) for _ in range(7)
    )
    return {
        "horizon": 8,
        "action_hold_frames": 2,
        "beam_width": 4,
        "control_delay_frames": 2,
        "initial_x": 192.0,
        "initial_y": 300.0,
        "initial_first_action": 0,
        "initial_last_action": 0,
        "initial_risk": 0.0,
        "initial_collisions": 0,
        "initial_minimum_clearance": np.inf,
        "initial_immediate_clearance": np.inf,
        "action_direction": np.asarray(
            [action.direction for action in live._PLANNER_ACTIONS],
            dtype=np.int32,
        ),
        "action_dx": np.asarray(
            [action.dx for action in live._PLANNER_ACTIONS],
            dtype=np.float64,
        ),
        "action_dy": np.asarray(
            [action.dy for action in live._PLANNER_ACTIONS],
            dtype=np.float64,
        ),
        "action_focused": np.asarray(
            [action.focused for action in live._PLANNER_ACTIONS],
            dtype=np.uint8,
        ),
        "action_allowed": np.ones(action_count, dtype=np.uint8),
        "certificate_collisions": np.zeros(
            action_count,
            dtype=np.int32,
        ),
        "certificate_minimum": np.zeros(
            action_count,
            dtype=np.float64,
        ),
        "survival_preferred": np.ones(
            action_count,
            dtype=np.uint8,
        ),
        "safety_preferred": np.ones(
            action_count,
            dtype=np.uint8,
        ),
        "recovery_distance": np.zeros(
            action_count,
            dtype=np.float64,
        ),
        "repair_volume": np.arange(action_count, dtype=np.int32),
        "bullet_frames": (frame,) * 8,
        "laser_frames": (empty_laser,) * 8,
        "body_base_x": np.empty(0, dtype=np.float32),
        "body_base_y": np.empty(0, dtype=np.float32),
        "body_velocity_x": np.empty(0, dtype=np.float32),
        "body_velocity_y": np.empty(0, dtype=np.float32),
        "body_half_width": np.empty(0, dtype=np.float32),
        "body_half_height": np.empty(0, dtype=np.float32),
        "player_radius": live.PLAYER_RADIUS,
        "preserve_previous_direction_inertia": True,
        "previous_direction": live.LEFT,
        "previous_focused": True,
        "target_x": None,
        "target_y": None,
        "target_deadline": None,
        "item_safety_clearance": live.ITEM_SAFETY_CLEARANCE,
        "playfield_left": live.PLAYFIELD_LEFT,
        "playfield_right": live.PLAYFIELD_RIGHT,
        "playfield_top": live.PLAYFIELD_TOP,
        "playfield_bottom": live.PLAYFIELD_BOTTOM,
        "recovery_reserve_distance": 12.0,
        "supplemental_reserve_distance": 16.0,
        "diagonal_speed": live.UNFOCUSED_DIAGONAL_SPEED,
        "cardinal_speed": live.UNFOCUSED_CARDINAL_SPEED,
    }


@unittest.skipUnless(_native_available(), "native planner unavailable")
class SemanticDifferentialTests(unittest.TestCase):
    def test_async_publication_is_newest_wins_and_exact_identity(self) -> None:
        service = ExactVersionSupplementalService()
        older = SupplementalNode(1.0, 2.0, 0, 0, 3.0, 0, 4.0, 4.0)
        newest = SupplementalNode(5.0, 6.0, 1, 1, 7.0, 0, 8.0, 8.0)
        service.submit(
            ("version", 1),
            lambda _workspace: (time.sleep(0.01), [older])[1],
        )
        service.submit(
            ("version", 2),
            lambda _workspace: [newest],
        )
        deadline = time.monotonic() + 2.0
        publication = None
        while publication is None:
            publication = service.lookup(("version", 2))
            if publication is not None:
                break
            if time.monotonic() >= deadline:
                self.fail("newest supplemental publication timed out")
            time.sleep(0)
        self.assertIsNone(service.lookup(("version", 1)))
        self.assertEqual(publication.nodes, (newest,))
        service.close()

    def test_replay_roundtrip_and_all_family_quick_parity(self) -> None:
        cases = generate_cases(seed=0xCE0132, count=12, profile="quick")
        self.assertEqual(len({case.family for case in cases}), 12)
        for case in cases:
            replay = SemanticCase.from_payload(case.to_payload())
            self.assertEqual(replay.to_payload(), case.to_payload())
            result = evaluate_case(replay)
            self.assertTrue(result.passed, msg=result)

    def test_shrinker_retains_named_failure_predicate(self) -> None:
        case = generate_case(seed=0xCE0132, index=9, profile="quick")
        self.assertGreater(len(case.bullets), 0)
        shrunk, attempts = shrink_case(
            case,
            fails=lambda candidate: len(candidate.bullets) >= 1,
            maximum_attempts=128,
        )
        self.assertGreater(attempts, 0)
        self.assertEqual(len(shrunk.bullets), 1)
        self.assertLess(shrunk.horizon, case.horizon)
        self.assertEqual(shrunk.beam_width, 1)
        self.assertEqual(len(shrunk.allowed_first_actions), 1)
        self.assertEqual(len(shrunk.positions_x), 1)
        self.assertEqual(shrunk.bullets[0].velocity_changes, ())
        self.assertEqual(shrunk.bullets[0].vx, 0.0)
        self.assertEqual(shrunk.bullets[0].vy, 0.0)

    def test_absolute_deadline_returns_historical_action(self) -> None:
        common = {
            "player_x": 192.0,
            "player_y": 300.0,
            "bullets": (),
            "lasers": (),
            "previous_direction": live.LEFT,
            "previous_focus": True,
            "can_bomb": False,
            "control_delay_frames": 2,
            "control_delay_candidates": (1, 2, 3),
            "action_hold_frames": 4,
            "horizon": 4,
            "threat_horizon": 4,
            "beam_width": 1,
            "allowed_first_actions": ("left", "right"),
            "viability_repair_volumes": (
                ("left", 1),
                ("right", 9),
            ),
        }
        original = live._LOCAL_SUPPLEMENTAL_BACKEND
        try:
            live._configure_local_supplemental_backend("native")
            historical = live.choose_action(**common)
            decision = live.choose_action(
                **common,
                preloss_continuation_preference=True,
                preloss_supplemental_beam_width=1,
                preloss_supplemental_deadline_ms=0.000001,
            )
        finally:
            live._configure_local_supplemental_backend(original)
        self.assertEqual(decision.action, historical.action)
        self.assertEqual(decision.preloss_supplemental_status, "deadline")
        self.assertFalse(decision.preloss_supplemental_completed)
        self.assertTrue(
            decision.preloss_supplemental_historical_fallback
        )
        self.assertIsNone(decision.preloss_supplemental_failure)
        self.assertEqual(
            decision.preloss_supplemental_candidate_count,
            0,
        )

    def test_running_native_query_is_cooperatively_cancelled(self) -> None:
        workspace = native_backend.LocalSupplementalNativeWorkspace()
        errors: list[BaseException] = []

        def run() -> None:
            try:
                workspace.query(**_native_stress_query_arguments())
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=run)
        thread.start()
        deadline = time.monotonic() + 5.0
        while not workspace.active and thread.is_alive():
            if time.monotonic() >= deadline:
                self.fail("native supplemental query never became active")
            time.sleep(0)
        workspace.cancel()
        thread.join(timeout=5.0)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(
            errors[0],
            native_backend.LocalSupplementalNativeCancelledError,
        )
        self.assertFalse(workspace.active)
        workspace.close()

    def test_running_native_query_honors_absolute_deadline(self) -> None:
        workspace = native_backend.LocalSupplementalNativeWorkspace()
        errors: list[BaseException] = []
        observed_active = False

        def run() -> None:
            try:
                workspace.query(
                    **_native_stress_query_arguments(),
                    absolute_deadline_ns=(
                        time.perf_counter_ns() + 250_000_000
                    ),
                )
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=run)
        thread.start()
        deadline = time.monotonic() + 5.0
        while thread.is_alive():
            observed_active = observed_active or workspace.active
            if time.monotonic() >= deadline:
                self.fail("native supplemental deadline query hung")
            time.sleep(0)
        thread.join()
        self.assertTrue(observed_active)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(
            errors[0],
            native_backend.LocalSupplementalNativeDeadlineError,
        )
        self.assertFalse(workspace.active)
        workspace.close()


if __name__ == "__main__":
    unittest.main()
