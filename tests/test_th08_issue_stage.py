#!/usr/bin/env python3
"""Tests for the typed live physical-issue stage."""

from __future__ import annotations

from types import SimpleNamespace
import unittest

from runtime_agent import InputTransition
from th08_live.issue_controller import InputDispatch
from th08_live.issue_stage import (
    PhysicalIssueRequest,
    commit_physical_issue,
    observe_action_issue,
)
from th08_runtime.game_state import (
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_PLAYER,
    PLAYER_PREDEATH_COUNTER_OFFSET,
)
from th08_live import CapturedIteration
from touhou_control.delay import DelayEstimate
from touhou_control.epochs import ActionIssueAlignment
from touhou_control.epochs import FrameWindow, HazardEpochAlignment


class _Reader:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def u8(self, address: int) -> int:
        self.calls.append(("u8", address))
        return 2

    def i32(self, address: int) -> int:
        self.calls.append(("i32", address))
        return 14

    def u32(self, address: int) -> int:
        self.calls.append(("u32", address))
        return 13


class _IssueController:
    def __init__(
        self,
        transitions: tuple[InputTransition, ...],
    ) -> None:
        self.transitions = transitions
        self.calls: list[tuple[int, int]] = []

    def dispatch(
        self,
        previous_mask: int,
        target_mask: int,
    ) -> InputDispatch:
        self.calls.append((previous_mask, target_mask))
        return InputDispatch(
            previous_mask=previous_mask,
            target_mask=target_mask,
            transitions=self.transitions,
            input_ms=0.25,
        )


class _DelayRecorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def issued(self, **arguments: object) -> None:
        self.calls.append(arguments)


class IssueStageTests(unittest.TestCase):
    @staticmethod
    def _capture() -> CapturedIteration:
        return CapturedIteration(
            gameplay_epoch=3,
            stage_route_index=1,
            spell_id=7,
            context_key=(3, 1, 7),
            source_frame=10,
            snapshot_frame=12,
            player_x=100.0,
            player_y=200.0,
            projected_player_x=101.0,
            projected_player_y=200.0,
            native_active_mask=0x05,
            held_desired_mask=0x45,
            previous_direction=0x40,
            can_bomb=False,
            power=80.0,
            bombs=2.0,
            bullets=(),
            lasers=(),
            enemy_bodies=(),
            items=(),
            hazard_alignment=HazardEpochAlignment(
                source_frame=10,
                hazard_window=FrameWindow(10, 11),
                current_frame=12,
            ),
            snapshot_lag=2,
            player_to_hazard_lag=1,
            hazard_snapshot_age=1,
            delay_estimate=DelayEstimate(
                nominal=2,
                support=(1, 2, 3),
                computation_samples=0,
                pickup_samples=0,
                end_to_end_samples=0,
                guard_active=False,
                overruns=0,
                censored=0,
            ),
            control_delay_frames=2,
            context_changed=False,
        )

    def _request(self) -> PhysicalIssueRequest:
        capture = self._capture()
        proposal = SimpleNamespace(
            decision=SimpleNamespace(mask=0x45),
        )
        decision = SimpleNamespace(mask=0x54)
        alignment = ActionIssueAlignment(
            source_frame=10,
            capture_frame=12,
            issue_frame=13,
            delay_support=(1, 2, 3),
        )
        return PhysicalIssueRequest(
            capture=capture,
            proposal=proposal,
            decision=decision,
            alignment=alignment,
            previous_mask=0x45,
            direction_mask=0xF0,
            pre_issue_action="left",
            pre_issue_mask=0x45,
            post_guard_action="right",
            post_guard_mask=0x54,
            planned_action="right",
            planned_mask=0x54,
            fresh_enemy_changed=True,
            recertification_ms=0.5,
            issue_path_started=1.0,
            iteration_started=0.5,
        )

    def test_observation_preserves_read_order_and_frame_identity(self) -> None:
        reader = _Reader()
        observation = observe_action_issue(
            reader,
            source_frame=10,
            capture_frame=12,
            delay_support=(1, 2, 3),
        )
        self.assertEqual(
            reader.calls,
            [
                ("u8", ADDR_PLAYER),
                (
                    "i32",
                    ADDR_PLAYER + PLAYER_PREDEATH_COUNTER_OFFSET,
                ),
                ("u32", ADDR_ENEMY_MANAGER_FRAME),
            ],
        )
        self.assertEqual(observation.player_phase, 2)
        self.assertEqual(observation.predeath_counter, 14)
        self.assertEqual(observation.issue_frame, 13)
        self.assertEqual(observation.alignment.action_lag, 3)

    def test_write_dispatch_registers_delay_and_next_actuator_state(
        self,
    ) -> None:
        transition = InputTransition(0x10, True)
        controller = _IssueController((transition,))
        recorder = _DelayRecorder()
        ticks = iter((1.004, 1.006))
        committed = commit_physical_issue(
            self._request(),
            issue_controller=controller,  # type: ignore[arg-type]
            delay_recorder=recorder,
            clock=lambda: next(ticks),
        )
        self.assertEqual(controller.calls, [(0x45, 0x54)])
        self.assertEqual(
            recorder.calls,
            [
                {
                    "snapshot_frame": 10,
                    "issue_frame": 13,
                    "expected_mask": 0x54,
                    "support_high": 3,
                    "support": (1, 2, 3),
                }
            ],
        )
        self.assertEqual(committed.issue.dispatch.transitions, (transition,))
        self.assertAlmostEqual(committed.issue.issue_path_ms, 4.0)
        self.assertAlmostEqual(committed.issue.observe_to_issue_ms, 506.0)
        self.assertEqual(committed.previous_mask, 0x54)
        self.assertEqual(committed.previous_direction, 0x50)

    def test_no_write_preserves_pending_delay_recorder_state(self) -> None:
        controller = _IssueController(())
        recorder = _DelayRecorder()
        ticks = iter((1.001, 1.002))
        committed = commit_physical_issue(
            self._request(),
            issue_controller=controller,  # type: ignore[arg-type]
            delay_recorder=recorder,
            clock=lambda: next(ticks),
        )
        self.assertEqual(recorder.calls, [])
        self.assertEqual(committed.issue.dispatch.transitions, ())
        self.assertEqual(committed.previous_mask, 0x54)
        self.assertEqual(committed.previous_direction, 0x50)


if __name__ == "__main__":
    unittest.main()
