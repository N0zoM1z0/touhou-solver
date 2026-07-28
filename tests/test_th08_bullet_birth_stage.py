#!/usr/bin/env python3
"""Tests for post-issue bullet-birth stage orchestration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import SimpleNamespace
import unittest

from th08_live.birth_contention import (
    FUTURE_ABSENT,
    BirthObserverFutureStates,
)
from th08_live.bullet_birth_stage import (
    BulletBirthStageDependencies,
    BulletBirthStageRequest,
    run_bullet_birth_stage,
)


class _Tracker:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[object, int, int]] = []
        self.reset_count = 0

    def observe(
        self,
        blob: object,
        *,
        frame_before: int,
        frame_after: int,
    ) -> object:
        self.calls.append((blob, frame_before, frame_after))
        if self.error is not None:
            raise self.error
        return SimpleNamespace(name="observation")

    def reset(self) -> None:
        self.reset_count += 1


class _Diagnostics:
    def __init__(self, label: str, events: list[object]) -> None:
        self.label = label
        self.events = events

    def record(self, *, observation_ms: float) -> dict[str, object]:
        self.events.append((f"{self.label}_record", observation_ms))
        return {
            "label": self.label,
            "observation_ms": observation_ms,
        }


class _NativeTracker(_Tracker):
    def __init__(self, events: list[object]) -> None:
        super().__init__()
        self.events = events

    def diagnostics(self) -> _Diagnostics:
        self.events.append("native_diagnostics")
        return _Diagnostics("native", self.events)


class _DerivedObserver:
    def __init__(self, events: list[object]) -> None:
        self.events = events

    def observe(
        self,
        blob: object,
        *,
        frame_before: int,
        frame_after: int,
    ) -> object:
        self.events.append(
            ("derived_observe", blob, frame_before, frame_after)
        )
        return SimpleNamespace(name="derived")

    def diagnostics(self) -> _Diagnostics:
        self.events.append("derived_diagnostics")
        return _Diagnostics("derived", self.events)


class _TraceSink:
    def __init__(self, events: list[object]) -> None:
        self.events = events

    def emit(
        self,
        record: dict[str, object],
        *,
        flush: bool,
        measure: bool,
    ) -> float:
        self.events.append(("emit", record, flush, measure))
        return 0.75


@dataclass(frozen=True)
class _Deferred:
    active: bool


class BulletBirthStageTests(unittest.TestCase):
    @staticmethod
    def _request(
        events: list[object],
        *,
        tracker: _Tracker | None,
        trace_derived_sources: bool = True,
        ecl_vm_snapshot: object | None = None,
    ) -> BulletBirthStageRequest:
        return BulletBirthStageRequest(
            trace_sink=_TraceSink(events),  # type: ignore[arg-type]
            tracker=tracker,  # type: ignore[arg-type]
            derived_source_observer=None,
            trace_derived_sources=trace_derived_sources,
            bullet_blob=b"blob",
            bullet_frame_before=117,
            bullet_frame_after=118,
            corridor_future=None,
            survival_future=None,
            enemy_future=None,
            ecl_vm_snapshot=ecl_vm_snapshot,  # type: ignore[arg-type]
            instruction_at=lambda address: address,
            intent_horizon_frames=80,
            difficulty_index=3,
            spell_enemy_pointer=0x4B5A30,
            observed_enemy_pointer=0x4B5A30,
            observed_enemy_flags=0,
            boss_guard_frame_before=118,
            boss_guard_frame_after=118,
            ecl_frame_before=118,
            ecl_frame_after=118,
            ecl_event_frame_offset=2,
            ecl_event_frame_uncertainty=0,
            issue_frame=120,
            snapshot_frame=117,
            gameplay_epoch=4,
            stage_route_index=3,
            observation_backend="native",
            native_call_mode="gil-held",
            previous_emit_ms=0.125,
            nonspell_main_vm_inventory=None,
            enemy_prefix_frame_before=117,
            enemy_prefix_frame_after=117,
            enemy_prefix_capture_ms=0.25,
        )

    def test_success_preserves_stage_order_and_trace_fields(self) -> None:
        events: list[object] = []
        tracker = _Tracker()
        wall_ticks = iter((1.0, 1.002, 2.0, 2.003, 3.0, 3.004, 4.0, 4.005))
        cpu_ticks = iter((10.0, 10.001))
        future = BirthObserverFutureStates(
            FUTURE_ABSENT,
            FUTURE_ABSENT,
            FUTURE_ABSENT,
        )

        def deferred(**arguments: object) -> _Deferred:
            events.append(("deferred", arguments))
            return _Deferred(active=True)

        def capture(**arguments: object) -> BirthObserverFutureStates:
            events.append(("future", arguments))
            return future

        def derived(*args: object, **kwargs: object) -> object:
            events.append(("derived", args, kwargs))
            return SimpleNamespace(name="derived")

        def analyze(*args: object, **kwargs: object) -> object:
            events.append(("intent", args, kwargs))
            return SimpleNamespace(name="intent")

        captured_input: list[object] = []

        def build(trace_input: object) -> dict[str, object]:
            events.append("build")
            captured_input.append(trace_input)
            return {"timing_ms": {}}

        result = run_bullet_birth_stage(
            self._request(
                events,
                tracker=tracker,
                ecl_vm_snapshot=SimpleNamespace(),
            ),
            dependencies=BulletBirthStageDependencies(
                observe_deferred_fire=deferred,  # type: ignore[arg-type]
                capture_future_states=capture,
                observe_derived_sources=derived,  # type: ignore[arg-type]
                analyze_intents=analyze,  # type: ignore[arg-type]
                build_record=build,  # type: ignore[arg-type]
                requires_immediate_flush=lambda **_kwargs: False,
                native_tracker_type=type(None),
                wall_clock=lambda: next(wall_ticks),
                cpu_clock=lambda: next(cpu_ticks),
            ),
        )

        self.assertEqual(
            [event[0] if isinstance(event, tuple) else event for event in events],
            [
                "deferred",
                "future",
                "future",
                "derived",
                "intent",
                "build",
                "emit",
            ],
        )
        self.assertEqual(tracker.calls, [(b"blob", 117, 118)])
        trace_input = captured_input[0]
        self.assertEqual(trace_input.frame, 120)
        self.assertEqual(trace_input.snapshot_frame, 117)
        self.assertEqual(trace_input.previous_emit_ms, 0.125)
        intent_event = next(
            event
            for event in events
            if isinstance(event, tuple) and event[0] == "intent"
        )
        self.assertEqual(intent_event[2]["horizon_frames"], 80)
        self.assertAlmostEqual(trace_input.observation_ms, 2.0)
        self.assertAlmostEqual(trace_input.observation_cpu_ms, 1.0)
        self.assertAlmostEqual(trace_input.derived_source_ms, 3.0)
        self.assertAlmostEqual(trace_input.intent_ms, 4.0)
        timing = result.record["timing_ms"]
        assert isinstance(timing, dict)
        self.assertAlmostEqual(timing["build"], 5.0)
        self.assertAlmostEqual(timing["pre_emit_total"], 14.0)
        self.assertEqual(result.emit_ms, 0.75)
        self.assertIsNone(result.observation_error)

    def test_observer_failure_resets_and_flushes_failed_row(self) -> None:
        events: list[object] = []
        tracker = _Tracker(error=ValueError("bad birth"))
        wall_ticks = iter((1.0, 1.002, 2.0, 2.003))
        cpu_ticks = iter((10.0, 10.001))
        future = BirthObserverFutureStates(
            FUTURE_ABSENT,
            FUTURE_ABSENT,
            FUTURE_ABSENT,
        )
        flush_arguments: list[dict[str, object]] = []

        def flush(**arguments: object) -> bool:
            flush_arguments.append(arguments)
            return bool(arguments["observation_error"])

        result = run_bullet_birth_stage(
            self._request(
                events,
                tracker=tracker,
                trace_derived_sources=False,
            ),
            dependencies=BulletBirthStageDependencies(
                observe_deferred_fire=lambda **_kwargs: _Deferred(False),
                capture_future_states=lambda **_kwargs: future,
                build_record=lambda _input: {"timing_ms": {}},
                requires_immediate_flush=flush,
                native_tracker_type=type(None),
                wall_clock=lambda: next(wall_ticks),
                cpu_clock=lambda: next(cpu_ticks),
            ),
        )
        self.assertEqual(tracker.reset_count, 1)
        self.assertEqual(result.observation_error, "ValueError: bad birth")
        self.assertTrue(flush_arguments[0]["observation_error"])
        emit = events[-1]
        assert isinstance(emit, tuple)
        self.assertTrue(emit[2])

    def test_native_and_derived_diagnostics_reach_trace_input(self) -> None:
        events: list[object] = []
        tracker = _NativeTracker(events)
        derived_observer = _DerivedObserver(events)
        request = replace(
            self._request(events, tracker=tracker),
            derived_source_observer=derived_observer,  # type: ignore[arg-type]
        )
        future = BirthObserverFutureStates(
            FUTURE_ABSENT,
            FUTURE_ABSENT,
            FUTURE_ABSENT,
        )
        wall_ticks = iter((1.0, 1.002, 2.0, 2.003, 3.0, 3.004))
        cpu_ticks = iter((10.0, 10.001))
        captured_input: list[object] = []

        def build(trace_input: object) -> dict[str, object]:
            captured_input.append(trace_input)
            return {"timing_ms": {}}

        run_bullet_birth_stage(
            request,
            dependencies=BulletBirthStageDependencies(
                observe_deferred_fire=lambda **_kwargs: _Deferred(False),
                capture_future_states=lambda **_kwargs: future,
                build_record=build,  # type: ignore[arg-type]
                requires_immediate_flush=lambda **_kwargs: False,
                native_tracker_type=_NativeTracker,
                wall_clock=lambda: next(wall_ticks),
                cpu_clock=lambda: next(cpu_ticks),
            ),
        )

        trace_input = captured_input[0]
        native_diagnostics = trace_input.observation_diagnostics
        derived_diagnostics = trace_input.derived_source_diagnostics
        assert native_diagnostics is not None
        assert derived_diagnostics is not None
        self.assertEqual(native_diagnostics["label"], "native")
        self.assertAlmostEqual(native_diagnostics["observation_ms"], 2.0)
        self.assertEqual(derived_diagnostics["label"], "derived")
        self.assertAlmostEqual(
            derived_diagnostics["observation_ms"],
            3.0,
        )
        self.assertLess(
            events.index("native_diagnostics"),
            events.index(("derived_observe", b"blob", 117, 118)),
        )
        derived_record_index = next(
            index
            for index, event in enumerate(events)
            if isinstance(event, tuple) and event[0] == "derived_record"
        )
        self.assertLess(
            events.index("derived_diagnostics"),
            derived_record_index,
        )

    def test_absent_tracker_still_brackets_contention_without_clocks(
        self,
    ) -> None:
        events: list[object] = []
        future = BirthObserverFutureStates(
            FUTURE_ABSENT,
            FUTURE_ABSENT,
            FUTURE_ABSENT,
        )
        captures = 0

        def capture(**_arguments: object) -> BirthObserverFutureStates:
            nonlocal captures
            captures += 1
            return future

        wall_ticks = iter((3.0, 3.001))
        result = run_bullet_birth_stage(
            self._request(
                events,
                tracker=None,
                trace_derived_sources=False,
            ),
            dependencies=BulletBirthStageDependencies(
                observe_deferred_fire=lambda **_kwargs: _Deferred(False),
                capture_future_states=capture,
                build_record=lambda _input: {"timing_ms": {}},
                requires_immediate_flush=lambda **_kwargs: False,
                wall_clock=lambda: next(wall_ticks),
                cpu_clock=lambda: self.fail("CPU clock must not be sampled"),
            ),
        )
        self.assertEqual(captures, 2)
        timing = result.record["timing_ms"]
        assert isinstance(timing, dict)
        self.assertAlmostEqual(timing["pre_emit_total"], 1.0)


if __name__ == "__main__":
    unittest.main()
