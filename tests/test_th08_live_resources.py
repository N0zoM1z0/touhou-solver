from __future__ import annotations

import unittest
from dataclasses import dataclass

from th08_live import LiveServiceResources


class _FakeExecutor:
    def __init__(
        self,
        events: list[object],
        *,
        max_workers: int,
        thread_name_prefix: str,
    ) -> None:
        self.events = events
        self.name = thread_name_prefix
        events.append(("open", self.name, max_workers))

    def submit(self, function, *args):
        self.events.append(("submit", self.name, function, args))
        return object()

    def shutdown(self, *, wait: bool, cancel_futures: bool = False) -> None:
        self.events.append(
            ("shutdown", self.name, wait, cancel_futures)
        )


class _FakeVerifier:
    def __init__(self, events: list[object], **kwargs: object) -> None:
        self.events = events
        events.append(("verifier_open", kwargs))

    def close(self) -> None:
        self.events.append("verifier_close")


class _FakeFuture:
    def __init__(
        self,
        events: list[object],
        name: str,
        *,
        completed: object | None = None,
    ) -> None:
        self.events = events
        self.name = name
        self.completed = completed

    def cancel(self) -> bool:
        self.events.append(("cancel", self.name))
        return self.completed is None

    def done(self) -> bool:
        return self.completed is not None

    def cancelled(self) -> bool:
        return False

    def result(self) -> object:
        self.events.append(("result", self.name))
        assert self.completed is not None
        return self.completed


@dataclass
class _Solution:
    pipeline_prewarm_service: object | None


class LiveServiceResourcesTests(unittest.TestCase):
    def make_resources(self, events: list[object]) -> LiveServiceResources:
        return LiveServiceResources(
            local_only=False,
            postpublished_survival_shadow=True,
            pipeline_prewarm_shadow=True,
            candidate_verifier_shadow=True,
            viability_audit_enabled=True,
            candidate_horizon_frames=32,
            candidate_decision_frames=(4, 5, 6),
            candidate_timeout_ms=10,
            close_pipeline_prewarms=lambda solutions: events.append(
                ("retire", solutions)
            ),
            executor_factory=lambda **kwargs: _FakeExecutor(
                events,
                **kwargs,
            ),
            candidate_verifier_factory=lambda **kwargs: _FakeVerifier(
                events,
                **kwargs,
            ),
        )

    def test_enabled_resources_have_one_owner_and_close_in_order(self) -> None:
        events: list[object] = []
        resources = self.make_resources(events)
        solution = _Solution(pipeline_prewarm_service=object())
        corridor = _FakeFuture(
            events,
            "corridor",
            completed=solution,
        )
        survival = _FakeFuture(events, "survival")
        enemy = _FakeFuture(events, "enemy")

        resources.close(
            corridor_future=corridor,
            survival_future=survival,
            enemy_future=enemy,
        )
        resources.close(
            corridor_future=corridor,
            survival_future=survival,
            enemy_future=enemy,
        )

        close_events = events[6:]
        self.assertEqual(close_events[0:5], [
            ("cancel", "corridor"),
            ("cancel", "survival"),
            ("shutdown", "th08-survival-shadow", True, True),
            "verifier_close",
            ("shutdown", "th08-corridor", True, True),
        ])
        self.assertEqual(close_events[5], ("result", "corridor"))
        self.assertEqual(close_events[6][0:2], (
            "submit",
            "th08-pipeline-retire",
        ))
        self.assertEqual(close_events[7:], [
            ("shutdown", "th08-pipeline-retire", True, False),
            ("shutdown", "th08-viability-audit", True, False),
            ("cancel", "enemy"),
            ("shutdown", "th08-enemy-sensor", True, True),
        ])

    def test_local_only_still_owns_audit_and_enemy_executors(self) -> None:
        events: list[object] = []
        resources = LiveServiceResources(
            local_only=True,
            postpublished_survival_shadow=True,
            pipeline_prewarm_shadow=True,
            candidate_verifier_shadow=True,
            viability_audit_enabled=True,
            candidate_horizon_frames=32,
            candidate_decision_frames=(4, 5, 6),
            candidate_timeout_ms=10,
            close_pipeline_prewarms=lambda _solutions: None,
            executor_factory=lambda **kwargs: _FakeExecutor(
                events,
                **kwargs,
            ),
        )

        self.assertIsNone(resources.corridor_executor)
        self.assertIsNone(resources.survival_executor)
        self.assertIsNone(resources.pipeline_retire_executor)
        self.assertIsNone(resources.candidate_verifier)
        self.assertIsNotNone(resources.audit_executor)
        self.assertIsNotNone(resources.enemy_executor)

        resources.close()
        self.assertEqual(
            events,
            [
                ("open", "th08-viability-audit", 1),
                ("open", "th08-enemy-sensor", 1),
                ("shutdown", "th08-viability-audit", True, False),
                ("shutdown", "th08-enemy-sensor", True, True),
            ],
        )

    def test_retirement_keeps_shared_service(self) -> None:
        events: list[object] = []
        resources = LiveServiceResources(
            local_only=True,
            postpublished_survival_shadow=False,
            pipeline_prewarm_shadow=False,
            candidate_verifier_shadow=False,
            viability_audit_enabled=False,
            candidate_horizon_frames=32,
            candidate_decision_frames=(4, 5, 6),
            candidate_timeout_ms=10,
            close_pipeline_prewarms=lambda solutions: events.append(
                ("retire", solutions)
            ),
            executor_factory=lambda **kwargs: _FakeExecutor(
                events,
                **kwargs,
            ),
        )
        shared = object()
        retained = _Solution(pipeline_prewarm_service=shared)
        duplicate = _Solution(pipeline_prewarm_service=shared)
        retired = _Solution(pipeline_prewarm_service=object())

        resources.retire_pipeline_solutions(
            (duplicate, retired),
            retained=(retained,),
        )

        self.assertEqual(events[1], ("retire", (retired,)))
        resources.close()


if __name__ == "__main__":
    unittest.main()
