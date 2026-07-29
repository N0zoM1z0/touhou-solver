from __future__ import annotations

import json
from pathlib import Path
import unittest

from th08_live.scale_schedule_authority import (
    FinalBScaleScheduleAuthority,
)
from th08_live.sensing_trace import _time_scale_schedule_hard_authority
from th08_live.controller import (
    _corridor_scale_schedule_supported,
    _finalb_scale_delivery_complete,
)
from th08_time_scale import (
    SCALE_COVERAGE_COMPLETE,
    TH08_UNIT_TIME_SCALE_BITS,
    Th08TimeScaleSchedule,
)


QUARTER_SCALE_BITS = 0x3E800000
PHYSICAL_C4_ARTIFACT = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "runtime_reports"
    / "finalb_scale_source_replay_20260729_215613.json"
)


class _TraceService:
    def __init__(
        self,
        schedule: Th08TimeScaleSchedule | None,
        *,
        due: bool = True,
        accepted: bool = True,
        captured_predeath: int = 0,
        captured_player_phase: int = 0,
    ) -> None:
        self._schedule = schedule
        self.due = due
        self.accepted = accepted
        self.captured_predeath = captured_predeath
        self.captured_player_phase = captured_player_phase
        self.calls = 0
        self.resets = 0

    @property
    def accepted_schedule(self) -> Th08TimeScaleSchedule | None:
        return self._schedule if self.accepted and self.calls else None

    def observe_if_due(
        self,
        *_args: object,
        **_kwargs: object,
    ) -> dict[str, object] | None:
        self.calls += 1
        if not self.due:
            return None
        return {
            "kind": "finalb_scale_source_trace",
            "status": (
                "accepted_complete_source_trace"
                if self.accepted
                else "unknown"
            ),
            "source_capture": {
                "phase_before": {
                    "player_predeath_counter": self.captured_predeath,
                    "player_phase": self.captured_player_phase,
                }
            },
        }

    def reset(self) -> None:
        self.calls = 0
        self.resets += 1


def _origin(*, source_frame: int = 100) -> Th08TimeScaleSchedule:
    return Th08TimeScaleSchedule.explicit(
        root_scale_bits=QUARTER_SCALE_BITS,
        player_scale_bits=(
            QUARTER_SCALE_BITS,
            QUARTER_SCALE_BITS,
            TH08_UNIT_TIME_SCALE_BITS,
            TH08_UNIT_TIME_SCALE_BITS,
        ),
        laser_scale_bits=(
            QUARTER_SCALE_BITS,
            TH08_UNIT_TIME_SCALE_BITS,
            TH08_UNIT_TIME_SCALE_BITS,
            TH08_UNIT_TIME_SCALE_BITS,
        ),
        complete=True,
        provenance="physical_complete_source_fixture",
        source_frame=source_frame,
    )


def _resolve(
    authority: FinalBScaleScheduleAuthority,
    *,
    source_frame: int = 100,
    scale_bits: int = QUARTER_SCALE_BITS,
    gameplay_epoch: int = 1,
    spell_id: int | None = 190,
    bomb_active: int = 0,
    player_phase: int = 0,
    predeath_counter: int = 0,
    hit_started: bool = False,
):
    return authority.resolve(
        object(),
        decision_frame=source_frame,
        source_frame=source_frame,
        gameplay_epoch=gameplay_epoch,
        route_id=2,
        difficulty_index=3,
        stage_route_index=7,
        spell_id=spell_id,
        observed_root_scale_bits=scale_bits,
        observed_player_bomb_active=bomb_active,
        player_phase=player_phase,
        player_predeath_counter=predeath_counter,
        hit_started=hit_started,
    )


class FinalBScaleScheduleAuthorityTests(unittest.TestCase):
    def test_not_due_remains_root_only(self) -> None:
        service = _TraceService(_origin(), due=False)
        resolution = _resolve(FinalBScaleScheduleAuthority(service))

        self.assertFalse(resolution.planner_scale_authority)
        self.assertEqual(
            resolution.status,
            "root_only_complete_source_not_due",
        )
        self.assertEqual(resolution.schedule.complete_horizon, 0)
        self.assertEqual(service.calls, 1)

    def test_accepted_source_is_delivered_at_the_exact_root(self) -> None:
        service = _TraceService(_origin())
        authority = FinalBScaleScheduleAuthority(service)
        resolution = _resolve(authority)

        self.assertTrue(resolution.planner_scale_authority)
        self.assertEqual(
            resolution.status,
            "complete_exact_source_schedule",
        )
        self.assertEqual(
            resolution.schedule.coverage,
            SCALE_COVERAGE_COMPLETE,
        )
        self.assertEqual(resolution.schedule.complete_horizon, 4)
        self.assertEqual(resolution.origin_source_frame, 100)
        self.assertEqual(resolution.frame_offset, 0)
        self.assertIsNotNone(resolution.trace_record)
        self.assertIs(authority.origin_schedule, service.accepted_schedule)

    def test_later_frame_rebases_the_same_immutable_schedule(self) -> None:
        service = _TraceService(_origin())
        authority = FinalBScaleScheduleAuthority(service)
        _resolve(authority)

        resolution = _resolve(
            authority,
            source_frame=102,
            scale_bits=TH08_UNIT_TIME_SCALE_BITS,
        )

        self.assertTrue(resolution.planner_scale_authority)
        self.assertEqual(resolution.frame_offset, 2)
        self.assertEqual(resolution.schedule.source_frame, 102)
        self.assertEqual(
            resolution.schedule.player_scale_bits,
            (
                TH08_UNIT_TIME_SCALE_BITS,
                TH08_UNIT_TIME_SCALE_BITS,
            ),
        )
        self.assertEqual(
            resolution.schedule.laser_scale_bits,
            (
                TH08_UNIT_TIME_SCALE_BITS,
                TH08_UNIT_TIME_SCALE_BITS,
            ),
        )
        self.assertEqual(service.calls, 1)

    def test_observed_root_mismatch_fails_closed(self) -> None:
        service = _TraceService(_origin())
        authority = FinalBScaleScheduleAuthority(service)
        _resolve(authority)

        resolution = _resolve(
            authority,
            source_frame=101,
            scale_bits=TH08_UNIT_TIME_SCALE_BITS,
        )

        self.assertFalse(resolution.planner_scale_authority)
        self.assertEqual(
            resolution.status,
            "root_only_observed_root_mismatch",
        )
        self.assertEqual(
            resolution.compact_record()["fallback"],
            "terminate_and_release_keys",
        )

    def test_capture_from_a_future_frame_cannot_backfill_the_root(self) -> None:
        service = _TraceService(_origin(source_frame=101))
        resolution = _resolve(FinalBScaleScheduleAuthority(service))

        self.assertFalse(resolution.planner_scale_authority)
        self.assertEqual(
            resolution.status,
            "root_only_source_frame_out_of_range",
        )
        self.assertEqual(resolution.frame_offset, -1)

    def test_capture_that_becomes_predeath_contaminated_fails_closed(
        self,
    ) -> None:
        service = _TraceService(_origin(), captured_predeath=7)
        resolution = _resolve(FinalBScaleScheduleAuthority(service))

        self.assertFalse(resolution.planner_scale_authority)
        self.assertEqual(
            resolution.status,
            "root_only_complete_source_unknown",
        )

    def test_hit_bomb_and_context_changes_never_reuse_authority(self) -> None:
        wrong_target_service = _TraceService(_origin())
        wrong_target = _resolve(
            FinalBScaleScheduleAuthority(wrong_target_service),
            spell_id=189,
            scale_bits=TH08_UNIT_TIME_SCALE_BITS,
        )
        self.assertFalse(wrong_target.planner_scale_authority)
        self.assertTrue(wrong_target.experimental_transport)
        self.assertFalse(
            _time_scale_schedule_hard_authority(wrong_target.schedule)
        )
        self.assertEqual(
            wrong_target.compact_record()["hard_action_authority"],
            False,
        )
        self.assertEqual(wrong_target_service.calls, 0)

        for keyword, expected_reason in (
            ({"hit_started": True}, "fresh_hit"),
            ({"bomb_active": 1}, "bomb_active"),
            ({"predeath_counter": 7}, "predeath_baseline_changed"),
        ):
            with self.subTest(expected_reason=expected_reason):
                service = _TraceService(_origin())
                authority = FinalBScaleScheduleAuthority(service)
                _resolve(authority)
                resolution = _resolve(
                    authority,
                    source_frame=101,
                    **keyword,
                )
                self.assertFalse(resolution.planner_scale_authority)
                self.assertEqual(resolution.reason, expected_reason)

        service = _TraceService(_origin())
        authority = FinalBScaleScheduleAuthority(service)
        _resolve(authority)
        changed = _resolve(
            authority,
            source_frame=101,
            gameplay_epoch=2,
        )
        self.assertFalse(changed.planner_scale_authority)
        self.assertEqual(changed.reason, "immutable_context_mismatch")

    def test_stable_predeath_residue_can_bind_but_change_cannot(self) -> None:
        service = _TraceService(_origin(), captured_predeath=7)
        authority = FinalBScaleScheduleAuthority(service)
        accepted = _resolve(authority, predeath_counter=7)

        self.assertTrue(accepted.planner_scale_authority)
        self.assertEqual(accepted.baseline_predeath_counter, 7)
        changed = _resolve(
            authority,
            source_frame=101,
            predeath_counter=8,
        )
        self.assertFalse(changed.planner_scale_authority)
        self.assertEqual(changed.reason, "predeath_baseline_changed")

    def test_contaminated_phase_three_can_bind_scale_delivery(self) -> None:
        service = _TraceService(
            _origin(),
            captured_predeath=7,
            captured_player_phase=3,
        )
        authority = FinalBScaleScheduleAuthority(service)

        accepted = _resolve(
            authority,
            player_phase=3,
            predeath_counter=7,
        )

        self.assertTrue(accepted.planner_scale_authority)
        self.assertEqual(accepted.baseline_predeath_counter, 7)
        self.assertEqual(accepted.source_player_phase, 3)
        self.assertEqual(
            accepted.compact_record()["source_player_phase"],
            3,
        )

    def test_explicit_reset_rearms_the_physical_service(self) -> None:
        service = _TraceService(_origin())
        authority = FinalBScaleScheduleAuthority(service)
        _resolve(authority)
        authority.reset()

        self.assertIsNone(authority.origin_schedule)
        self.assertEqual(service.resets, 1)
        again = _resolve(authority, gameplay_epoch=2)
        self.assertTrue(again.planner_scale_authority)

    def test_corridor_remains_disabled_for_nonunit_or_short_schedules(
        self,
    ) -> None:
        varying = _origin()
        self.assertFalse(
            _corridor_scale_schedule_supported(varying, horizon=4)
        )
        unit = Th08TimeScaleSchedule.constant(
            TH08_UNIT_TIME_SCALE_BITS,
            horizon=4,
            source_frame=100,
        )
        self.assertTrue(
            _corridor_scale_schedule_supported(unit, horizon=4)
        )
        self.assertFalse(
            _corridor_scale_schedule_supported(unit, horizon=5)
        )

    def test_retained_physical_schedule_rebases_across_the_restore(
        self,
    ) -> None:
        payload = json.loads(PHYSICAL_C4_ARTIFACT.read_text(encoding="utf-8"))
        record = payload["record"]
        schedule_record = record["schedule"]
        origin = Th08TimeScaleSchedule.explicit(
            root_scale_bits=schedule_record["root_scale_bits"],
            player_scale_bits=tuple(
                schedule_record["player_scale_bits"]
            ),
            laser_scale_bits=tuple(
                schedule_record["laser_scale_bits"]
            ),
            complete=True,
            provenance=schedule_record["provenance"],
            source_frame=schedule_record["source_frame"],
        )
        service = _TraceService(origin)
        authority = FinalBScaleScheduleAuthority(service)
        source = origin.source_frame
        assert source is not None
        first = _resolve(
            authority,
            source_frame=source,
            scale_bits=origin.root_scale_bits,
        )
        self.assertTrue(first.planner_scale_authority)

        transition = _resolve(
            authority,
            source_frame=source + 239,
            scale_bits=QUARTER_SCALE_BITS,
        )
        self.assertEqual(
            transition.schedule.player_scale_bits[0],
            QUARTER_SCALE_BITS,
        )
        self.assertEqual(
            transition.schedule.laser_scale_bits[0],
            TH08_UNIT_TIME_SCALE_BITS,
        )

        restored = _resolve(
            authority,
            source_frame=source + 240,
            scale_bits=TH08_UNIT_TIME_SCALE_BITS,
        )
        self.assertTrue(restored.planner_scale_authority)
        self.assertTrue(_finalb_scale_delivery_complete(restored))
        self.assertEqual(restored.schedule.complete_horizon, 60)
        self.assertTrue(
            all(
                bits == TH08_UNIT_TIME_SCALE_BITS
                for bits in (
                    *restored.schedule.player_scale_bits,
                    *restored.schedule.laser_scale_bits,
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
