"""Exact-version live delivery for one accepted Final-B scale source.

The complete-source observer remains the shipped-runtime evidence producer.
This module adds only the narrow stateful delivery boundary needed by the
live controller: bind one accepted schedule to its physical context, rebase
it causally as manager frames advance, and fail closed on every mismatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from th08_live.scale_source_trace import (
    FINAL_B_QUARTER_SCALE_BITS,
    FINAL_B_SCALE_SPELL_ID,
    FINAL_B_STAGE_ROUTE_INDEX,
    FinalBScaleSourceTraceService,
)
from th08_time_scale import (
    SCALE_COVERAGE_COMPLETE,
    TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
    TH08_UNIT_TIME_SCALE_BITS,
    Th08TimeScaleSchedule,
)


FINAL_B_LIVE_SCALE_AUTHORITY_SCHEMA = (
    "th08-finalb-live-scale-schedule-authority-v1"
)
PRETARGET_UNIT_TRANSPORT_HORIZON = 256


class _ScaleSourceService(Protocol):
    @property
    def accepted_schedule(self) -> Th08TimeScaleSchedule | None: ...

    def observe_if_due(self, *args: object, **kwargs: object) -> dict[str, object] | None:
        ...

    def reset(self) -> None: ...


@dataclass(frozen=True)
class FinalBScaleScheduleResolution:
    schedule: Th08TimeScaleSchedule
    status: str
    reason: str | None
    trace_record: dict[str, object] | None
    origin_source_frame: int | None
    frame_offset: int | None
    baseline_predeath_counter: int | None

    @property
    def planner_scale_authority(self) -> bool:
        return (
            self.status == "complete_exact_source_schedule"
            and self.schedule.coverage == SCALE_COVERAGE_COMPLETE
        )

    @property
    def experimental_transport(self) -> bool:
        return (
            self.status == "complete_experimental_pretarget_unit_transport"
            and self.schedule.coverage == SCALE_COVERAGE_COMPLETE
        )

    def compact_record(self) -> dict[str, object]:
        return {
            "kind": "finalb_live_scale_schedule_authority",
            "schema": FINAL_B_LIVE_SCALE_AUTHORITY_SCHEMA,
            "status": self.status,
            "reason": self.reason,
            "planner_scale_schedule_authority": (
                self.planner_scale_authority
            ),
            "experimental_pretarget_transport": (
                self.experimental_transport
            ),
            "hard_action_authority": False,
            "semantics_version": TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
            "origin_source_frame": self.origin_source_frame,
            "current_source_frame": self.schedule.source_frame,
            "frame_offset": self.frame_offset,
            "baseline_predeath_counter": self.baseline_predeath_counter,
            "root_scale_bits": self.schedule.root_scale_bits,
            "coverage": self.schedule.coverage,
            "complete_horizon": self.schedule.complete_horizon,
            "provenance": self.schedule.provenance,
            "fallback": (
                None
                if (
                    self.planner_scale_authority
                    or self.experimental_transport
                )
                else "terminate_and_release_keys"
            ),
        }


class FinalBScaleScheduleAuthority:
    """Bind and causally rebase one exact physical scale-source schedule."""

    def __init__(
        self,
        trace_service: _ScaleSourceService | FinalBScaleSourceTraceService,
    ) -> None:
        self._trace_service = trace_service
        self._origin_schedule: Th08TimeScaleSchedule | None = None
        self._binding: tuple[int, int, int, int, int | None] | None = None
        self._baseline_predeath_counter: int | None = None

    @property
    def origin_schedule(self) -> Th08TimeScaleSchedule | None:
        return self._origin_schedule

    def reset(self) -> None:
        self._origin_schedule = None
        self._binding = None
        self._baseline_predeath_counter = None
        self._trace_service.reset()

    @staticmethod
    def _root_only(
        *,
        scale_bits: int,
        source_frame: int,
        provenance: str,
        status: str,
        reason: str | None,
        trace_record: dict[str, object] | None = None,
        origin_source_frame: int | None = None,
        frame_offset: int | None = None,
        baseline_predeath_counter: int | None = None,
    ) -> FinalBScaleScheduleResolution:
        return FinalBScaleScheduleResolution(
            schedule=Th08TimeScaleSchedule.root_observation(
                scale_bits,
                source_frame=source_frame,
                provenance=provenance,
            ),
            status=status,
            reason=reason,
            trace_record=trace_record,
            origin_source_frame=origin_source_frame,
            frame_offset=frame_offset,
            baseline_predeath_counter=baseline_predeath_counter,
        )

    @staticmethod
    def _experimental_unit_transport(
        *,
        source_frame: int,
    ) -> FinalBScaleScheduleResolution:
        return FinalBScaleScheduleResolution(
            schedule=Th08TimeScaleSchedule.constant(
                TH08_UNIT_TIME_SCALE_BITS,
                horizon=PRETARGET_UNIT_TRANSPORT_HORIZON,
                provenance=(
                    "experimental_pretarget_unit_transport_unknown_direction"
                ),
                source_frame=source_frame,
            ),
            status="complete_experimental_pretarget_unit_transport",
            reason="complete_finalb_source_not_yet_due",
            trace_record=None,
            origin_source_frame=None,
            frame_offset=None,
            baseline_predeath_counter=None,
        )

    def _rebase(
        self,
        *,
        source_frame: int,
        observed_root_scale_bits: int,
        trace_record: dict[str, object] | None,
    ) -> FinalBScaleScheduleResolution:
        origin = self._origin_schedule
        assert origin is not None
        assert origin.source_frame is not None
        frame_offset = source_frame - origin.source_frame
        if frame_offset < 0 or frame_offset >= origin.complete_horizon:
            return self._root_only(
                scale_bits=observed_root_scale_bits,
                source_frame=source_frame,
                provenance="live_scale_source_frame_out_of_range",
                status="root_only_source_frame_out_of_range",
                reason="source_frame_out_of_range",
                trace_record=trace_record,
                origin_source_frame=origin.source_frame,
                frame_offset=frame_offset,
                baseline_predeath_counter=(
                    self._baseline_predeath_counter
                ),
            )
        expected_root = (
            origin.root_scale_bits
            if frame_offset == 0
            else origin.laser_scale_bits[frame_offset - 1]
        )
        if observed_root_scale_bits != expected_root:
            return self._root_only(
                scale_bits=observed_root_scale_bits,
                source_frame=source_frame,
                provenance="live_scale_source_root_mismatch",
                status="root_only_observed_root_mismatch",
                reason="observed_root_mismatch",
                trace_record=trace_record,
                origin_source_frame=origin.source_frame,
                frame_offset=frame_offset,
                baseline_predeath_counter=(
                    self._baseline_predeath_counter
                ),
            )
        return FinalBScaleScheduleResolution(
            schedule=Th08TimeScaleSchedule.explicit(
                root_scale_bits=observed_root_scale_bits,
                player_scale_bits=origin.player_scale_bits[frame_offset:],
                laser_scale_bits=origin.laser_scale_bits[frame_offset:],
                complete=True,
                provenance=(
                    f"{origin.provenance}:live_exact_rebase:"
                    f"origin={origin.source_frame}"
                ),
                source_frame=source_frame,
            ),
            status="complete_exact_source_schedule",
            reason=None,
            trace_record=trace_record,
            origin_source_frame=origin.source_frame,
            frame_offset=frame_offset,
            baseline_predeath_counter=self._baseline_predeath_counter,
        )

    def resolve(
        self,
        reader: object,
        *,
        decision_frame: int,
        source_frame: int,
        gameplay_epoch: int,
        route_id: int,
        difficulty_index: int,
        stage_route_index: int,
        spell_id: int | None,
        observed_root_scale_bits: int,
        observed_player_bomb_active: int,
        player_phase: int,
        player_predeath_counter: int,
        hit_started: bool,
    ) -> FinalBScaleScheduleResolution:
        binding = (
            gameplay_epoch,
            route_id,
            difficulty_index,
            stage_route_index,
            spell_id,
        )
        target_context = (
            route_id == 2
            and difficulty_index == 3
            and stage_route_index == FINAL_B_STAGE_ROUTE_INDEX
            and spell_id == FINAL_B_SCALE_SPELL_ID
        )
        if self._origin_schedule is None and (
            not target_context
            or observed_root_scale_bits != FINAL_B_QUARTER_SCALE_BITS
            or player_phase != 0
            or hit_started
            or observed_player_bomb_active != 0
        ):
            if observed_root_scale_bits == TH08_UNIT_TIME_SCALE_BITS:
                return self._experimental_unit_transport(
                    source_frame=source_frame,
                )
            return self._root_only(
                scale_bits=observed_root_scale_bits,
                source_frame=source_frame,
                provenance="live_scale_complete_source_not_due",
                status="root_only_complete_source_not_due",
                reason="complete_source_not_due",
            )
        if self._origin_schedule is not None and (
            hit_started
            or observed_player_bomb_active != 0
            or player_predeath_counter
            != self._baseline_predeath_counter
        ):
            return self._root_only(
                scale_bits=observed_root_scale_bits,
                source_frame=source_frame,
                provenance="live_scale_continuation_invalid",
                status="root_only_continuation_invalid",
                reason=(
                    "fresh_hit"
                    if hit_started
                    else (
                        "bomb_active"
                        if observed_player_bomb_active != 0
                        else "predeath_baseline_changed"
                    )
                ),
                origin_source_frame=(
                    self._origin_schedule.source_frame
                    if self._origin_schedule is not None
                    else None
                ),
                baseline_predeath_counter=(
                    self._baseline_predeath_counter
                ),
            )
        if self._binding is not None and binding != self._binding:
            return self._root_only(
                scale_bits=observed_root_scale_bits,
                source_frame=source_frame,
                provenance="live_scale_context_mismatch",
                status="root_only_context_mismatch",
                reason="immutable_context_mismatch",
                origin_source_frame=(
                    self._origin_schedule.source_frame
                    if self._origin_schedule is not None
                    else None
                ),
                baseline_predeath_counter=(
                    self._baseline_predeath_counter
                ),
            )

        trace_record: dict[str, object] | None = None
        if self._origin_schedule is None:
            trace_record = self._trace_service.observe_if_due(
                reader,
                decision_frame=decision_frame,
                expected_manager_frame=source_frame,
                gameplay_epoch=gameplay_epoch,
                route_id=route_id,
                difficulty_index=difficulty_index,
                stage_route_index=stage_route_index,
                spell_id=spell_id,
                observed_root_scale_bits=observed_root_scale_bits,
                observed_player_bomb_active=observed_player_bomb_active,
            )
            if trace_record is None:
                return self._root_only(
                    scale_bits=observed_root_scale_bits,
                    source_frame=source_frame,
                    provenance="live_scale_complete_source_not_due",
                    status="root_only_complete_source_not_due",
                    reason="complete_source_not_due",
                )
            accepted = self._trace_service.accepted_schedule
            source_capture = trace_record.get("source_capture")
            phase_before = (
                source_capture.get("phase_before")
                if isinstance(source_capture, dict)
                else None
            )
            if (
                trace_record.get("status")
                != "accepted_complete_source_trace"
                or accepted is None
                or accepted.coverage != SCALE_COVERAGE_COMPLETE
                or not isinstance(phase_before, dict)
                or type(phase_before.get("player_predeath_counter")) is not int
                or phase_before.get("player_predeath_counter")
                != player_predeath_counter
            ):
                return self._root_only(
                    scale_bits=observed_root_scale_bits,
                    source_frame=source_frame,
                    provenance="live_scale_complete_source_unknown",
                    status="root_only_complete_source_unknown",
                    reason="complete_source_capture_unknown",
                    trace_record=trace_record,
                )
            self._origin_schedule = accepted
            self._binding = binding
            self._baseline_predeath_counter = player_predeath_counter

        return self._rebase(
            source_frame=source_frame,
            observed_root_scale_bits=observed_root_scale_bits,
            trace_record=trace_record,
        )


__all__ = [
    "FINAL_B_LIVE_SCALE_AUTHORITY_SCHEMA",
    "FinalBScaleScheduleAuthority",
    "FinalBScaleScheduleResolution",
]
