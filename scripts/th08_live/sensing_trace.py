#!/usr/bin/env python3
"""Pure sensing and hazard-alignment fields for live decision traces."""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from th08_live.iteration import FreshIssueResult


@dataclass(frozen=True)
class SensingTraceInput:
    """Already-captured sensing values for one post-issue trace record."""

    resources: Mapping[str, object]
    stage_route_index: int
    spell: object
    boss_phase_snapshot: Any
    boss_phase_error: str | None
    boss_phase_progress: Any
    ecl_vm_snapshot: Any
    ecl_lookahead: Any
    tagged_velocity_toggles: Sequence[Any]
    bullets: Sequence[Any]
    ecl_event_frame_offset: int
    ecl_event_frame_uncertainty: Sequence[int]
    ecl_lookahead_error: str | None
    lasers: Sequence[Any]
    items: Sequence[Any]
    enemy_bodies: Sequence[Any]
    dormant_enemy_body_pointers: Collection[int]
    bullet_frame_before: int
    bullet_frame_after: int
    enemy_prefix_snapshot: Any
    enemy_prefix_bodies: Sequence[Any]
    bullet_capture_span: int
    hazard_snapshot_age: int
    player_to_hazard_lag: int
    ecl_frame_before: int | None
    ecl_frame_after: int | None
    boss_guard_frame_before: int | None
    boss_guard_frame_after: int | None
    enemy_body_snapshot_frame: int | None
    query_frame: int
    issue_enemy_prefix_snapshot: Any
    issue_enemy_prefix_bodies: Sequence[Any]
    issue_dormant_enemy_body_pointers: Collection[int]
    issue_enemy_changes: Sequence[object]
    issue_enemy_read_ms: float
    issue_enemy_recertificate_ms: float
    issue: FreshIssueResult
    spell_enemy_body_guard: Any
    spell_enemy_body_guard_error: str | None


def build_sensing_trace_fields(
    trace_input: SensingTraceInput,
    *,
    serialize_boss_phase_snapshot: Callable[[Any], dict[str, object] | None],
    serialize_enemy_bodies: Callable[[Sequence[Any]], list[object]],
    enemy_body_contact_enabled: Callable[[Any], bool],
    enemy_pointer_in_scanned_pool: Callable[[int], bool],
    issue_recertification_record: Callable[[Any], dict[str, object] | None],
) -> dict[str, object]:
    """Serialize observed sensing state without reads or model expansion."""

    boss_snapshot = trace_input.boss_phase_snapshot
    boss_error = trace_input.boss_phase_error
    progress = trace_input.boss_phase_progress
    ecl_snapshot = trace_input.ecl_vm_snapshot
    ecl_lookahead = trace_input.ecl_lookahead
    bullets = trace_input.bullets
    dormant = trace_input.dormant_enemy_body_pointers
    enemy_bodies = trace_input.enemy_bodies
    enemy_prefix = trace_input.enemy_prefix_snapshot
    issue_prefix = trace_input.issue_enemy_prefix_snapshot
    issue = trace_input.issue

    ecl_tagged_bullets = (
        tuple(
            bullet
            for bullet in bullets
            if (
                (
                    bullet.original_transform_flags
                    or (
                        bullet.transform_runtime.original_flags
                        if bullet.transform_runtime is not None
                        else 0
                    )
                )
                & ecl_snapshot.tag_mask
            )
        )
        if ecl_snapshot is not None
        else ()
    )

    return {
        "resources": trace_input.resources,
        "stage_route_index": trace_input.stage_route_index,
        "spell": trace_input.spell,
        "boss_phase": (
            {
                **(serialize_boss_phase_snapshot(boss_snapshot) or {}),
                "error": boss_error,
            }
            if boss_snapshot is not None or boss_error is not None
            else None
        ),
        "boss_phase_progress": (
            {
                "status": progress.status,
                "frame_delta": progress.frame_delta,
                "health_delta": progress.health_delta,
                "damage_per_frame": progress.damage_per_frame,
                "damage_per_second_60hz": (
                    progress.damage_per_frame * 60.0
                    if progress.damage_per_frame is not None
                    else None
                ),
                "damageable": progress.state.damageable,
            }
            if progress is not None
            else None
        ),
        "bullet_velocity_lookahead": (
            {
                "instruction_pointer": ecl_snapshot.instruction_pointer,
                "timer_fraction": ecl_snapshot.timer_fraction,
                "timer_elapsed": ecl_snapshot.timer_elapsed,
                "time_scale": ecl_snapshot.time_scale,
                "tag_mask": ecl_snapshot.tag_mask,
                "instructions_scanned": (
                    ecl_lookahead.instructions_scanned
                    if ecl_lookahead is not None
                    else 0
                ),
                "stop_reason": (
                    ecl_lookahead.stop_reason
                    if ecl_lookahead is not None
                    else None
                ),
                "horizon_covered": (
                    ecl_lookahead.horizon_covered
                    if ecl_lookahead is not None
                    else False
                ),
                "coverage_status": (
                    ecl_lookahead.coverage_status
                    if ecl_lookahead is not None
                    else "unknown"
                ),
                "requested_horizon_frames": (
                    ecl_lookahead.requested_horizon_frames
                    if ecl_lookahead is not None
                    else None
                ),
                "stop_frame": (
                    ecl_lookahead.stop_frame
                    if ecl_lookahead is not None
                    else None
                ),
                "covered_through_frame": (
                    ecl_lookahead.covered_through_frame
                    if ecl_lookahead is not None
                    else 0
                ),
                "unknown_from_frame": (
                    ecl_lookahead.unknown_from_frame
                    if ecl_lookahead is not None
                    else 1
                ),
                "result_kind": (
                    (
                        "complete_schedule"
                        if ecl_lookahead.horizon_covered
                        else "prefix_only"
                    )
                    if ecl_lookahead is not None
                    else "unavailable"
                ),
                "prefix_events": [
                    [
                        event.frame,
                        event.callback_index,
                        event.tag_mask,
                        event.alternate_velocity_x,
                        event.alternate_velocity_y,
                    ]
                    for event in (
                        ecl_lookahead.events
                        if ecl_lookahead is not None
                        else ()
                    )
                ],
                "events": [
                    [
                        event.frame,
                        event.callback_index,
                        event.tag_mask,
                        event.alternate_velocity_x,
                        event.alternate_velocity_y,
                    ]
                    for event in trace_input.tagged_velocity_toggles
                ],
                "lowering_status": (
                    "complete_schedule_lowered"
                    if (
                        ecl_lookahead is not None
                        and ecl_lookahead.horizon_covered
                    )
                    else "incomplete_prefix_not_lowered"
                ),
                "attached_bullets": sum(
                    bool(bullet.velocity_changes) for bullet in bullets
                ),
                "tagged_bullets": len(ecl_tagged_bullets),
                "stopped_tagged_bullets": sum(
                    bullet.callback_phase_state == 0
                    and bullet.callback_aux_state == 1
                    for bullet in ecl_tagged_bullets
                ),
                "event_frame_offset": trace_input.ecl_event_frame_offset,
                "event_frame_uncertainty": (
                    trace_input.ecl_event_frame_uncertainty
                ),
                "error": trace_input.ecl_lookahead_error,
            }
            if ecl_snapshot is not None
            else (
                {"error": trace_input.ecl_lookahead_error}
                if trace_input.ecl_lookahead_error is not None
                else None
            )
        ),
        "active_bullets": len(bullets),
        "active_lasers": len(trace_input.lasers),
        "active_items": len(trace_input.items),
        "active_enemy_bodies": len(enemy_bodies),
        "enemy_body_contact_enabled_count": sum(
            body.pointer not in dormant
            and enemy_body_contact_enabled(body)
            for body in enemy_bodies
        ),
        "enemy_body_anticipatory_count": sum(
            body.pointer not in dormant
            and not enemy_body_contact_enabled(body)
            for body in enemy_bodies
        ),
        "enemy_body_dormant_count": sum(
            body.pointer in dormant for body in enemy_bodies
        ),
        "hazard_alignment": {
            "bullet_frame_before": trace_input.bullet_frame_before,
            "bullet_frame_after": trace_input.bullet_frame_after,
            "enemy_prefix_frame_before": enemy_prefix.frame_before,
            "enemy_prefix_frame_after": enemy_prefix.frame_after,
            "enemy_prefix_body_count": len(trace_input.enemy_prefix_bodies),
            "enemy_prefix_observed_body_count": len(enemy_prefix.bodies),
            "enemy_prefix_contact_enabled_count": sum(
                body.pointer not in dormant
                and enemy_body_contact_enabled(body)
                for body in trace_input.enemy_prefix_bodies
            ),
            "enemy_prefix_anticipatory_count": sum(
                body.pointer not in dormant
                and not enemy_body_contact_enabled(body)
                for body in trace_input.enemy_prefix_bodies
            ),
            "enemy_prefix_dormant_count": len(dormant),
            "enemy_prefix_attempts": enemy_prefix.attempts,
            "bullet_capture_span": trace_input.bullet_capture_span,
            "hazard_snapshot_age": trace_input.hazard_snapshot_age,
            "player_to_hazard_lag": trace_input.player_to_hazard_lag,
            "ecl_frame_before": trace_input.ecl_frame_before,
            "ecl_frame_after": trace_input.ecl_frame_after,
            "boss_guard_frame_before": trace_input.boss_guard_frame_before,
            "boss_guard_frame_after": trace_input.boss_guard_frame_after,
        },
        "enemy_body_snapshot_frame": trace_input.enemy_body_snapshot_frame,
        "enemy_body_snapshot_age": (
            trace_input.query_frame - trace_input.enemy_body_snapshot_frame
            if trace_input.enemy_body_snapshot_frame is not None
            else None
        ),
        "issue_time_enemy_guard": {
            "frame_before": issue_prefix.frame_before,
            "frame_after": issue_prefix.frame_after,
            "body_count": len(trace_input.issue_enemy_prefix_bodies),
            "observed_body_count": len(issue_prefix.bodies),
            "contact_enabled_count": sum(
                enemy_body_contact_enabled(body) for body in issue_prefix.bodies
            ),
            "anticipatory_count": sum(
                not enemy_body_contact_enabled(body)
                for body in issue_prefix.bodies
            ),
            "dormant_count": len(
                trace_input.issue_dormant_enemy_body_pointers
            ),
            "attempts": issue_prefix.attempts,
            "stable": issue_prefix.stable,
            "changes": list(trace_input.issue_enemy_changes),
            "recertified": bool(trace_input.issue_enemy_changes),
            "planned_action_before_guard": issue.pre_issue_action,
            "planned_mask_before_guard": issue.pre_issue_mask,
            "action_after_guard": issue.post_guard_action,
            "mask_after_guard": issue.post_guard_mask,
            "read_ms": trace_input.issue_enemy_read_ms,
            "recertificate_ms": trace_input.issue_enemy_recertificate_ms,
            "transaction": issue_recertification_record(
                issue.decision.issue_recertification
            ),
        },
        "spell_enemy_body_guard": (
            {
                "source": "boss_registry_or_spell_owner",
                "body": serialize_enemy_bodies(
                    (trace_input.spell_enemy_body_guard.body,)
                )[0],
                "contact_enabled": (
                    trace_input.spell_enemy_body_guard.contact_enabled
                ),
                "anticipatory": (
                    not trace_input.spell_enemy_body_guard.contact_enabled
                ),
                "covered_by_async_pool": enemy_pointer_in_scanned_pool(
                    trace_input.spell_enemy_body_guard.body.pointer
                ),
                "error": None,
            }
            if trace_input.spell_enemy_body_guard is not None
            else (
                {"error": trace_input.spell_enemy_body_guard_error}
                if trace_input.spell_enemy_body_guard_error is not None
                else None
            )
        ),
    }


__all__ = ["SensingTraceInput", "build_sensing_trace_fields"]
