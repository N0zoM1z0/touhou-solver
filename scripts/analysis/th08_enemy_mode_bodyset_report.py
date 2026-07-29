#!/usr/bin/env python3
"""Audit action-conditioned TH08 mode/body-set endpoints in a physical trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from th08_enemy_mode import (
    BOMB_INPUT_BIT,
    ENEMY_ACTIVE_FLAG,
    ENEMY_CONTACT_ENABLED_FLAG,
    ENEMY_MANAGER_BLOCKING_FLAGS,
    ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG,
    ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG,
    Route2EnemyModeBody,
    project_route2_mode_decision_branches,
)
from th08_pipeline_actions import th08_complete_mask_token
from touhou_control.local_pipeline_oracle import LocalPipelineRoot


REPORT_SCHEMA = "th08-enemy-mode-bodyset-report-v1"
_MAX_RETAINED_INTERVALS = 32
_MAX_RETAINED_BRANCH_SUMMARIES = 8
_MAX_AUDITED_MANAGER_DELTA = 64


def _records(path: Path) -> Iterable[tuple[int, dict[str, object]]]:
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"line {line_number}: trace row is not an object")
            yield line_number, record


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _integer(value: object, *, line_number: int, field: str) -> int:
    if type(value) is not int:
        raise ValueError(f"line {line_number}: {field} must be an integer")
    return value


def _boolean(value: object, *, line_number: int, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"line {line_number}: {field} must be a Boolean")
    return value


def _mode_state(
    player: dict[str, object],
    *,
    line_number: int,
) -> tuple[int, bool, int]:
    state = (
        _integer(
            player.get("focus_logic"),
            line_number=line_number,
            field="player_after.focus_logic",
        ),
        _boolean(
            player.get("secondary_character_active"),
            line_number=line_number,
            field="player_after.secondary_character_active",
        ),
        _integer(
            player.get("focus_transition_counter"),
            line_number=line_number,
            field="player_after.focus_transition_counter",
        ),
    )
    if not 0 <= state[0] <= 0xFF or state[2] < 0:
        raise ValueError(f"line {line_number}: invalid native mode state")
    return state


def _mode_sensitive_bodies(
    capture: dict[str, object],
    *,
    line_number: int,
) -> tuple[Route2EnemyModeBody, ...]:
    rows = capture.get("mode_sensitive_bodies")
    if not isinstance(rows, list):
        raise ValueError(f"line {line_number}: mode_sensitive_bodies must be an array")
    bodies: list[Route2EnemyModeBody] = []
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError(
                f"line {line_number}: mode_sensitive_bodies[{index}] is malformed"
            )
        bodies.append(
            Route2EnemyModeBody(
                identity=_integer(
                    row[0],
                    line_number=line_number,
                    field=f"mode_sensitive_bodies[{index}].pointer",
                ),
                raw_flags=_integer(
                    row[1],
                    line_number=line_number,
                    field=f"mode_sensitive_bodies[{index}].raw_flags",
                ),
            )
        )
    identities = tuple(body.identity for body in bodies)
    if len(set(identities)) != len(identities):
        raise ValueError(f"line {line_number}: duplicate mode-sensitive body pointer")
    return tuple(bodies)


def _pipeline_root(
    record: dict[str, object],
    *,
    line_number: int,
) -> tuple[LocalPipelineRoot, dict[str, int]] | None:
    raw = record.get("local_pipeline_root")
    if (
        not isinstance(raw, dict)
        or raw.get("canonical_status") != "available"
        or raw.get("estimator_consistent") is not True
    ):
        return None

    actions_and_masks: tuple[tuple[str, str], ...] = (
        ("active_action", "active_mask"),
        ("held_desired_action", "held_desired_mask"),
    )
    tokens: dict[str, str] = {}
    masks: dict[str, int] = {}
    for action_field, mask_field in actions_and_masks:
        movement_label = raw.get(action_field)
        if not isinstance(movement_label, str) or not movement_label:
            raise ValueError(f"line {line_number}: {action_field} is malformed")
        mask = _integer(
            raw.get(mask_field),
            line_number=line_number,
            field=f"local_pipeline_root.{mask_field}",
        )
        if not 0 <= mask <= 0xFFFFFFFF or mask & BOMB_INPUT_BIT:
            raise ValueError(f"line {line_number}: invalid hard-no-Bomb root mask")
        token = th08_complete_mask_token(mask)
        tokens[action_field] = token
        masks[token] = mask

    pending_action = raw.get("pending_action")
    pending_mask = raw.get("pending_mask")
    remaining = raw.get("remaining_delay_support")
    if not isinstance(remaining, list):
        raise ValueError(
            f"line {line_number}: remaining_delay_support must be an array"
        )
    remaining_support = tuple(
        _integer(
            value,
            line_number=line_number,
            field="local_pipeline_root.remaining_delay_support",
        )
        for value in remaining
    )
    if pending_action is None:
        if pending_mask is not None or remaining_support:
            raise ValueError(
                f"line {line_number}: absent pending action has pending state"
            )
    else:
        if not isinstance(pending_action, str) or not pending_action:
            raise ValueError(f"line {line_number}: pending_action is malformed")
        mask = _integer(
            pending_mask,
            line_number=line_number,
            field="local_pipeline_root.pending_mask",
        )
        if not 0 <= mask <= 0xFFFFFFFF or mask & BOMB_INPUT_BIT:
            raise ValueError(f"line {line_number}: invalid pending mask")
        pending_token = th08_complete_mask_token(mask)
        masks[pending_token] = mask
    if pending_action is None:
        pending_token = None

    return (
        LocalPipelineRoot(
            active_action=tokens["active_action"],
            held_desired_action=tokens["held_desired_action"],
            pending_action=pending_token,
            remaining_delay_support=remaining_support,
        ),
        masks,
    )


def _capture(
    record: dict[str, object],
    *,
    line_number: int,
) -> dict[str, object] | None:
    capture = record.get("player_enemy_mode_capture")
    if capture is None:
        return None
    if not isinstance(capture, dict):
        raise ValueError(
            f"line {line_number}: player_enemy_mode_capture is not an object"
        )
    player = capture.get("player_after")
    if not isinstance(player, dict):
        raise ValueError(f"line {line_number}: capture lacks player_after")
    return {
        "coherent": capture.get("coherent") is True,
        "role": capture.get("role"),
        "action_authority": capture.get("action_authority"),
        "enemy_frame": _integer(
            capture.get("enemy_frame_after"),
            line_number=line_number,
            field="player_enemy_mode_capture.enemy_frame_after",
        ),
        "mode_state": _mode_state(player, line_number=line_number),
        "input_current": _integer(
            player.get("input_current"),
            line_number=line_number,
            field="player_after.input_current",
        ),
        "phase": _integer(
            player.get("phase"),
            line_number=line_number,
            field="player_after.phase",
        ),
        "bomb_active": _integer(
            player.get("bomb_active"),
            line_number=line_number,
            field="player_after.bomb_active",
        ),
        "bodies": _mode_sensitive_bodies(
            capture,
            line_number=line_number,
        ),
    }


def _delay_support(
    record: dict[str, object],
    *,
    line_number: int,
) -> tuple[int, ...] | None:
    raw = record.get("control_delay_candidates")
    if not isinstance(raw, list):
        return None
    support = tuple(
        _integer(
            value,
            line_number=line_number,
            field="control_delay_candidates",
        )
        for value in raw
    )
    if not support or tuple(sorted(set(support))) != support or support[0] < 0:
        return None
    return support


def _dispatch(
    record: dict[str, object],
    *,
    line_number: int,
) -> tuple[int, int, tuple[int, ...]] | None:
    raw = record.get("input_dispatch")
    if not isinstance(raw, dict):
        return None
    previous_mask = _integer(
        raw.get("previous_mask"),
        line_number=line_number,
        field="input_dispatch.previous_mask",
    )
    target_mask = _integer(
        raw.get("target_mask"),
        line_number=line_number,
        field="input_dispatch.target_mask",
    )
    if (
        not 0 <= previous_mask <= 0xFFFFFFFF
        or not 0 <= target_mask <= 0xFFFFFFFF
        or previous_mask & BOMB_INPUT_BIT
        or target_mask & BOMB_INPUT_BIT
    ):
        raise ValueError(f"line {line_number}: invalid hard-no-Bomb dispatch mask")
    transitions = raw.get("transitions")
    if not isinstance(transitions, list):
        raise ValueError(f"line {line_number}: input_dispatch.transitions is malformed")
    transition_count = _integer(
        raw.get("transition_count"),
        line_number=line_number,
        field="input_dispatch.transition_count",
    )
    if transition_count != len(transitions):
        raise ValueError(f"line {line_number}: dispatch transition count disagrees")

    mask = previous_mask
    intermediate_masks: list[int] = []
    for index, transition in enumerate(transitions):
        if not isinstance(transition, list) or len(transition) != 2:
            raise ValueError(
                f"line {line_number}: input_dispatch.transitions[{index}] is malformed"
            )
        bit = _integer(
            transition[0],
            line_number=line_number,
            field=f"input_dispatch.transitions[{index}].bit",
        )
        pressed = _boolean(
            transition[1],
            line_number=line_number,
            field=f"input_dispatch.transitions[{index}].pressed",
        )
        if bit <= 0 or bit > 0x80000000 or bit & (bit - 1):
            raise ValueError(
                f"line {line_number}: dispatch transition bit is not one-hot"
            )
        if bit == BOMB_INPUT_BIT:
            raise ValueError(f"line {line_number}: dispatch transition contains Bomb")
        next_mask = (mask | bit) if pressed else (mask & ~bit)
        if next_mask == mask:
            raise ValueError(
                f"line {line_number}: dispatch transition does not change the mask"
            )
        mask = next_mask
        intermediate_masks.append(mask)
    if mask != target_mask:
        raise ValueError(f"line {line_number}: ordered dispatch does not reach target")
    write_required = _boolean(
        raw.get("write_required"),
        line_number=line_number,
        field="input_dispatch.write_required",
    )
    if write_required != bool(transitions):
        raise ValueError(f"line {line_number}: dispatch write_required disagrees")
    return previous_mask, target_mask, tuple(intermediate_masks)


def _scalar_body_sets(
    bodies: tuple[Route2EnemyModeBody, ...],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    contact: list[int] = []
    damage: list[int] = []
    for body in bodies:
        flags = body.raw_flags
        gate_open = not bool(flags & ENEMY_MANAGER_BLOCKING_FLAGS)
        if (
            flags & ENEMY_ACTIVE_FLAG
            and flags & ENEMY_CONTACT_ENABLED_FLAG
            and gate_open
        ):
            contact.append(body.identity)
        if (
            flags & ENEMY_ACTIVE_FLAG
            and flags & ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG
            and gate_open
        ):
            damage.append(body.identity)
    return tuple(contact), tuple(damage)


def _mode_bit_transition(
    previous: tuple[Route2EnemyModeBody, ...],
    current: tuple[Route2EnemyModeBody, ...],
) -> tuple[int, int]:
    previous_flags = {body.identity: body.raw_flags for body in previous}
    set_count = 0
    clear_count = 0
    for body in current:
        old = previous_flags.get(body.identity)
        if old is None:
            continue
        non_mode_mask = 0xFFFFFFFF ^ ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG
        if (old & non_mode_mask) != (body.raw_flags & non_mode_mask):
            continue
        old_blocked = bool(old & ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG)
        new_blocked = bool(body.raw_flags & ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG)
        set_count += int(not old_blocked and new_blocked)
        clear_count += int(old_blocked and not new_blocked)
    return set_count, clear_count


def _exact_root_is_member_of_observed_belief(
    exact_root: LocalPipelineRoot,
    observed_root: LocalPipelineRoot,
) -> bool:
    if (
        exact_root.active_action != observed_root.active_action
        or exact_root.held_desired_action != observed_root.held_desired_action
        or exact_root.pending_action != observed_root.pending_action
    ):
        return False
    if exact_root.pending_action is None:
        return not observed_root.remaining_delay_support
    return (
        len(exact_root.remaining_delay_support) == 1
        and exact_root.remaining_delay_support[0]
        in observed_root.remaining_delay_support
    )


def _eligible(
    previous: dict[str, object],
    current: dict[str, object],
) -> tuple[str | None, int | None]:
    if (
        previous["gameplay_epoch"] != current["gameplay_epoch"]
        or previous["stage_route_index"] != current["stage_route_index"]
    ):
        return "epoch_or_stage_changed", None
    manager_delta = int(current["enemy_frame"]) - int(previous["enemy_frame"])
    if manager_delta <= 0:
        return "nonpositive_manager_delta", None
    if manager_delta > _MAX_AUDITED_MANAGER_DELTA:
        return "manager_delta_outside_bounded_audit", None
    action_lag = previous["action_lag"]
    if type(action_lag) is not int or action_lag < 0:
        return "action_lag_unavailable_or_invalid", None
    if previous["frame"] - previous["enemy_frame"] != action_lag:
        return "action_lag_disagrees_with_capture_to_issue_gap", None
    if current["enemy_frame"] - previous["frame"] <= 0:
        return "no_post_issue_physical_update", None
    if previous["phase"] != current["phase"]:
        return "player_phase_changed", None
    if previous["phase"] in (1, 2):
        return "mode_update_suppressed_player_phase", None
    if previous["bomb_active"] or current["bomb_active"]:
        return "bomb_active", None
    if not current["bodies"]:
        return "no_mode_sensitive_endpoint_bodies", None
    if previous["pipeline"] is None:
        return "previous_pipeline_root_unavailable_or_inconsistent", None
    if current["pipeline"] is None:
        return "current_pipeline_root_unavailable_or_inconsistent", None
    return None, manager_delta


def _interval_result(
    previous: dict[str, object],
    current: dict[str, object],
    *,
    manager_delta: int,
) -> dict[str, object]:
    previous_pipeline = previous["pipeline"]
    current_pipeline = current["pipeline"]
    assert isinstance(previous_pipeline, tuple)
    assert isinstance(current_pipeline, tuple)
    previous_root, action_masks = previous_pipeline
    current_root, current_action_masks = current_pipeline
    assert isinstance(previous_root, LocalPipelineRoot)
    assert isinstance(current_root, LocalPipelineRoot)

    if action_masks[previous_root.active_action] != previous["input_current"]:
        return {"error": "previous_root_active_mask_disagrees_with_capture"}
    if current_action_masks[current_root.active_action] != current["input_current"]:
        return {"error": "current_root_active_mask_disagrees_with_capture"}

    action = previous["action"]
    dispatch = previous["dispatch"]
    if not isinstance(action, str) or not action:
        return {"error": "selected_action_missing"}
    if not isinstance(dispatch, tuple):
        return {"error": "dispatch_unavailable"}
    dispatch_previous_mask, target_mask, transition_masks = dispatch
    if dispatch_previous_mask != previous["held_mask"]:
        return {"error": "dispatch_previous_mask_disagrees_with_held_desired"}
    if previous["selected_mask"] != target_mask:
        return {"error": "selected_mask_disagrees_with_dispatch"}
    selected_token = th08_complete_mask_token(target_mask)
    action_masks[selected_token] = target_mask

    delay_support = previous["delay_support"]
    if not isinstance(delay_support, tuple):
        return {"error": "delay_support_unavailable"}
    current_bodies = current["bodies"]
    assert isinstance(current_bodies, tuple)
    action_lag = int(previous["action_lag"])
    post_issue_steps = int(current["enemy_frame"]) - int(previous["frame"])
    if action_lag + post_issue_steps != manager_delta:
        return {"error": "manager_interval_decomposition_disagrees"}
    if action_lag:
        prefix_branches = project_route2_mode_decision_branches(
            pipeline_root=previous_root,
            selected_action=previous_root.held_desired_action,
            action_masks=action_masks,
            delay_frames=(0,),
            decision_frame_support=(action_lag,),
            initial_mode_state=previous["mode_state"],
            enemy_flag_frames=((),) * action_lag,
        )
        prefix_states = tuple(
            (
                branch.successor_pipeline_root,
                branch.successor_mode_state,
                branch.hazard_branch.pipeline_branch.older_remaining,
            )
            for branch in prefix_branches
        )
    else:
        prefix_states = ((previous_root, previous["mode_state"], None),)

    branches = []
    for prefix_root, prefix_mode_state, prefix_older_remaining in prefix_states:
        suffix = project_route2_mode_decision_branches(
            pipeline_root=prefix_root,
            selected_action=selected_token,
            action_masks=action_masks,
            delay_frames=delay_support,
            decision_frame_support=(post_issue_steps,),
            initial_mode_state=prefix_mode_state,
            enemy_flag_frames=((),) * (post_issue_steps - 1) + (current_bodies,),
        )
        branches.extend((prefix_older_remaining, branch) for branch in suffix)
    scalar_contact, scalar_damage = _scalar_body_sets(current_bodies)
    observed_flags = tuple((body.identity, body.raw_flags) for body in current_bodies)
    compatible = []
    mode_body_compatible_count = 0
    successor_root_compatible_count = 0
    successor_root_exact_compatible_count = 0
    endpoint_summaries = []
    for prefix_older_remaining, branch in branches:
        endpoint = branch.hazard_branch.frames[-1]
        projected_flags = tuple(
            (
                body.identity,
                body.projection.projected_flags,
            )
            for body in endpoint.body_projections
        )
        mode_body_compatible = (
            branch.successor_mode_state == current["mode_state"]
            and projected_flags == observed_flags
            and endpoint.contact_body_ids == scalar_contact
            and endpoint.player_shot_damage_body_ids == scalar_damage
        )
        successor_root_compatible = _exact_root_is_member_of_observed_belief(
            branch.successor_pipeline_root,
            current_root,
        )
        successor_root_exact_compatible = branch.successor_pipeline_root == current_root
        mode_body_compatible_count += int(mode_body_compatible)
        successor_root_compatible_count += int(successor_root_compatible)
        successor_root_exact_compatible_count += int(successor_root_exact_compatible)
        if len(endpoint_summaries) < _MAX_RETAINED_BRANCH_SUMMARIES:
            endpoint_summaries.append(
                {
                    "capture_to_issue_steps": action_lag,
                    "post_issue_steps": post_issue_steps,
                    "prefix_older_remaining": prefix_older_remaining,
                    "new_delay": branch.hazard_branch.pipeline_branch.new_delay,
                    "older_remaining": (
                        branch.hazard_branch.pipeline_branch.older_remaining
                    ),
                    "active_mask": endpoint.active_mask,
                    "mode_state": list(endpoint.mode_state_after),
                    "successor_root": {
                        "active_action": branch.successor_pipeline_root.active_action,
                        "held_desired_action": (
                            branch.successor_pipeline_root.held_desired_action
                        ),
                        "pending_action": (
                            branch.successor_pipeline_root.pending_action
                        ),
                        "remaining_delay_support": list(
                            branch.successor_pipeline_root.remaining_delay_support
                        ),
                    },
                    "mode_body_compatible": mode_body_compatible,
                    "successor_root_compatible": successor_root_compatible,
                    "successor_root_exact_compatible": (
                        successor_root_exact_compatible
                    ),
                }
            )
        if mode_body_compatible and successor_root_compatible:
            compatible.append((prefix_older_remaining, branch))

    observed_current_active_mask = current_action_masks[current_root.active_action]
    if compatible:
        mismatch_code = None
    elif observed_current_active_mask in transition_masks[:-1]:
        mismatch_code = "observed_ordered_partial_transition_mask"
    elif not mode_body_compatible_count:
        mismatch_code = "mode_or_body_endpoint_outside_manager_frame_decomposition"
    elif not successor_root_compatible_count:
        mismatch_code = "pipeline_endpoint_outside_manager_frame_decomposition"
    else:
        mismatch_code = "joint_mode_pipeline_branch_incompatible"

    mode_bit_set, mode_bit_cleared = _mode_bit_transition(
        previous["bodies"],
        current_bodies,
    )
    return {
        "error": None if compatible else "no_compatible_causal_branch",
        "branch_count": len(branches),
        "compatible_branch_count": len(compatible),
        "mode_body_compatible_branch_count": mode_body_compatible_count,
        "successor_root_compatible_branch_count": successor_root_compatible_count,
        "successor_root_exact_compatible_branch_count": (
            successor_root_exact_compatible_count
        ),
        "mismatch_code": mismatch_code,
        "endpoint_body_count": len(current_bodies),
        "scalar_contact_body_ids": scalar_contact,
        "scalar_damage_body_ids": scalar_damage,
        "mode_bit_set": mode_bit_set,
        "mode_bit_cleared": mode_bit_cleared,
        "selected_token": selected_token,
        "dispatch_previous_mask": dispatch_previous_mask,
        "dispatch_transition_masks": transition_masks,
        "observed_current_active_mask": observed_current_active_mask,
        "endpoint_summaries": endpoint_summaries,
    }


def build_report(path: Path) -> dict[str, object]:
    """Build a source-hashed action-conditioned endpoint body-set audit."""

    total_rows = 0
    decision_rows = 0
    capture_rows = 0
    coherent_rows = 0
    adjacent_coherent = 0
    eligible = 0
    matched = 0
    mismatched = 0
    endpoint_bodies_checked = 0
    compatible_branches = 0
    mode_bit_set = 0
    mode_bit_cleared = 0
    mode_bit_set_intervals = 0
    mode_bit_cleared_intervals = 0
    exclusion_counts: Counter[str] = Counter()
    manager_delta_counts: Counter[str] = Counter()
    compatible_branch_counts: Counter[str] = Counter()
    mismatch_counts: Counter[str] = Counter()
    ordered_partial_edge_position_counts: Counter[str] = Counter()
    ordered_partial_focus_path_counts: Counter[str] = Counter()
    ordered_partial_shot_path_counts: Counter[str] = Counter()
    ordered_partial_direction_path_counts: Counter[str] = Counter()
    ordered_partial_signature_counts: Counter[str] = Counter()
    intervening_kind_counts: Counter[str] = Counter()
    retained_matches: list[dict[str, object]] = []
    retained_mismatches: list[dict[str, object]] = []
    retained_mismatch_counts: Counter[str] = Counter()
    authority_violations: list[int] = []
    role_violations: list[int] = []
    previous: dict[str, object] | None = None
    intervening: Counter[str] = Counter()

    for line_number, record in _records(path):
        total_rows += 1
        if record.get("kind") != "decision":
            if previous is not None:
                label = str(record.get("kind"))
                intervening[label] += 1
                intervening_kind_counts[label] += 1
            continue
        decision_rows += 1
        capture = _capture(record, line_number=line_number)
        if capture is None:
            previous = None
            intervening.clear()
            continue
        capture_rows += 1
        if capture["action_authority"] is not False:
            authority_violations.append(line_number)
        if capture["role"] != "diagnostic_shadow":
            role_violations.append(line_number)
        if capture["coherent"] is not True:
            previous = None
            intervening.clear()
            continue
        coherent_rows += 1

        pipeline = _pipeline_root(record, line_number=line_number)
        held_mask = None
        if pipeline is not None:
            pipeline_root, pipeline_masks = pipeline
            held_mask = pipeline_masks[pipeline_root.held_desired_action]
        current = {
            "line": line_number,
            "frame": _integer(
                record.get("frame"),
                line_number=line_number,
                field="frame",
            ),
            "gameplay_epoch": record.get("gameplay_epoch"),
            "stage_route_index": record.get("stage_route_index"),
            "enemy_frame": capture["enemy_frame"],
            "mode_state": capture["mode_state"],
            "input_current": capture["input_current"],
            "phase": capture["phase"],
            "bomb_active": capture["bomb_active"],
            "bodies": capture["bodies"],
            "pipeline": pipeline,
            "held_mask": held_mask,
            "action": record.get("action"),
            "action_lag": record.get("action_lag"),
            "selected_mask": record.get("mask"),
            "dispatch": _dispatch(record, line_number=line_number),
            "delay_support": _delay_support(
                record,
                line_number=line_number,
            ),
        }

        if previous is not None:
            adjacent_coherent += 1
            if intervening:
                exclusion = "intervening_nondecision_trace_record"
                manager_delta = None
            else:
                exclusion, manager_delta = _eligible(previous, current)
            if exclusion is not None:
                exclusion_counts[exclusion] += 1
            else:
                assert manager_delta is not None
                outcome = _interval_result(
                    previous,
                    current,
                    manager_delta=manager_delta,
                )
                error = outcome["error"]
                if error is not None and error != "no_compatible_causal_branch":
                    exclusion_counts[str(error)] += 1
                else:
                    eligible += 1
                    manager_delta_counts[str(manager_delta)] += 1
                    endpoint_bodies_checked += int(outcome["endpoint_body_count"])
                    branch_count = int(outcome["compatible_branch_count"])
                    compatible_branches += branch_count
                    compatible_branch_counts[str(branch_count)] += 1
                    interval = {
                        "previous_line": previous["line"],
                        "line": line_number,
                        "previous_frame": previous["frame"],
                        "frame": current["frame"],
                        "previous_enemy_frame": previous["enemy_frame"],
                        "enemy_frame": current["enemy_frame"],
                        "manager_delta": manager_delta,
                        "capture_to_issue_steps": previous["action_lag"],
                        "post_issue_steps": (
                            int(current["enemy_frame"]) - int(previous["frame"])
                        ),
                        "initial_mode_state": list(previous["mode_state"]),
                        "observed_mode_state": list(current["mode_state"]),
                        "selected_action": previous["action"],
                        "selected_token": outcome["selected_token"],
                        "selected_mask": previous["selected_mask"],
                        "delay_support": list(previous["delay_support"]),
                        "branch_count": outcome["branch_count"],
                        "compatible_branch_count": branch_count,
                        "mode_body_compatible_branch_count": outcome[
                            "mode_body_compatible_branch_count"
                        ],
                        "successor_root_compatible_branch_count": outcome[
                            "successor_root_compatible_branch_count"
                        ],
                        "successor_root_exact_compatible_branch_count": outcome[
                            "successor_root_exact_compatible_branch_count"
                        ],
                        "mismatch_code": outcome["mismatch_code"],
                        "dispatch_previous_mask": outcome["dispatch_previous_mask"],
                        "dispatch_transition_masks": list(
                            outcome["dispatch_transition_masks"]
                        ),
                        "observed_current_active_mask": outcome[
                            "observed_current_active_mask"
                        ],
                        "endpoint_body_count": outcome["endpoint_body_count"],
                        "scalar_contact_body_ids": list(
                            outcome["scalar_contact_body_ids"]
                        ),
                        "scalar_damage_body_ids": list(
                            outcome["scalar_damage_body_ids"]
                        ),
                        "mode_bit_set": outcome["mode_bit_set"],
                        "mode_bit_cleared": outcome["mode_bit_cleared"],
                    }
                    if error is None:
                        matched += 1
                        set_count = int(outcome["mode_bit_set"])
                        clear_count = int(outcome["mode_bit_cleared"])
                        mode_bit_set += set_count
                        mode_bit_cleared += clear_count
                        mode_bit_set_intervals += int(set_count > 0)
                        mode_bit_cleared_intervals += int(clear_count > 0)
                        if len(retained_matches) < _MAX_RETAINED_INTERVALS and (
                            previous["mode_state"] != current["mode_state"]
                            or set_count
                            or clear_count
                        ):
                            retained_matches.append(interval)
                    else:
                        mismatched += 1
                        mismatch_code = str(outcome["mismatch_code"])
                        mismatch_counts[mismatch_code] += 1
                        if mismatch_code == "observed_ordered_partial_transition_mask":
                            dispatch_previous = int(outcome["dispatch_previous_mask"])
                            transition_masks = tuple(
                                int(mask)
                                for mask in outcome["dispatch_transition_masks"]
                            )
                            observed_active = int(
                                outcome["observed_current_active_mask"]
                            )
                            edge_index = transition_masks.index(observed_active)
                            ordered_partial_edge_position_counts[
                                f"{edge_index + 1}/{len(transition_masks)}"
                            ] += 1
                            target = transition_masks[-1]
                            ordered_partial_focus_path_counts[
                                (
                                    f"{int(bool(dispatch_previous & 0x04))}->"
                                    f"{int(bool(observed_active & 0x04))}->"
                                    f"{int(bool(target & 0x04))}"
                                )
                            ] += 1
                            ordered_partial_shot_path_counts[
                                (
                                    f"{int(bool(dispatch_previous & 0x01))}->"
                                    f"{int(bool(observed_active & 0x01))}->"
                                    f"{int(bool(target & 0x01))}"
                                )
                            ] += 1
                            ordered_partial_direction_path_counts[
                                (
                                    f"0x{dispatch_previous & 0xF0:02x}->"
                                    f"0x{observed_active & 0xF0:02x}->"
                                    f"0x{target & 0xF0:02x}"
                                )
                            ] += 1
                            signature = (
                                f"0x{dispatch_previous:02x}->"
                                + "->".join(
                                    f"0x{mask:02x}" for mask in transition_masks
                                )
                                + f"|observed=0x{observed_active:02x}"
                            )
                            ordered_partial_signature_counts[signature] += 1
                        interval["endpoint_summaries"] = outcome["endpoint_summaries"]
                        if (
                            retained_mismatch_counts[mismatch_code]
                            < _MAX_RETAINED_INTERVALS // 4
                        ):
                            retained_mismatches.append(interval)
                            retained_mismatch_counts[mismatch_code] += 1

        previous = current
        intervening.clear()

    integrity_errors = {
        "capture_action_authority_true_or_missing_lines": (authority_violations),
        "capture_non_diagnostic_role_lines": role_violations,
        "causal_endpoint_mismatch_count": mismatched,
        "eligible_interval_count_zero": int(eligible == 0),
    }
    return {
        "schema": REPORT_SCHEMA,
        "source": {
            "path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        },
        "scope": {
            "classification": (
                "observed_physical_posthoc_action_conditioned_endpoint_bodyset"
            ),
            "endpoint_contract": (
                "adjacent coherent captures with no intervening non-decision "
                "record, stable stage/epoch/non-suppressed player phase, no "
                "Bomb, an available exact local pipeline root on both ends, "
                "an exact capture-to-issue action_lag plus at least one "
                "post-issue update, and at least one native mode-sensitive "
                "endpoint body"
            ),
            "causal_interval_decomposition": (
                "diagnostic hypothesis only: first advance the observed root "
                "without a new write through capture-to-issue action_lag, "
                "then apply the recorded issue over the remaining manager "
                "updates to the next coherent capture"
            ),
            "body_schedule_contract": (
                "only the observed endpoint body/flag set is supplied; "
                "intermediate body frames are empty because body state does "
                "not affect the player-mode recurrence"
            ),
            "pipeline_action_equivalence": (
                "the injective 36-token TH08 no-Bomb complete-mask alphabet "
                "is preserved through active, held, pending, and selected "
                "pipeline identities even when movement or focus agrees"
            ),
            "successor_belief_compatibility": (
                "an exact hidden successor branch is compatible when its "
                "active/held/pending identity agrees and its singleton "
                "remaining delay is a member of the next observed estimator "
                "support; exact whole-root equality is reported separately "
                "because later observations may causally narrow the belief"
            ),
            "future_body_flag_geometry_coverage": "unknown",
            "manager_frame_decomposition_authority": (
                "unknown-direction diagnostic; failures other than a directly "
                "observed ordered partial transition can reflect issue/player/"
                "manager phase alignment rather than a standalone recurrence "
                "error"
            ),
            "manager_frame_universal_physical_clock_authority": False,
            "action_authority": False,
            "hard_survival_authority": False,
            "physical_survival_authority": False,
        },
        "rows": {
            "total": total_rows,
            "decision": decision_rows,
            "capture": capture_rows,
            "coherent": coherent_rows,
        },
        "intervals": {
            "adjacent_coherent": adjacent_coherent,
            "eligible": eligible,
            "matched": matched,
            "mismatched": mismatched,
            "excluded": adjacent_coherent - eligible,
            "exclusion_counts": dict(sorted(exclusion_counts.items())),
            "manager_delta_counts": dict(
                sorted(
                    manager_delta_counts.items(),
                    key=lambda item: int(item[0]),
                )
            ),
            "compatible_branch_counts": dict(
                sorted(
                    compatible_branch_counts.items(),
                    key=lambda item: int(item[0]),
                )
            ),
            "mismatch_counts": dict(sorted(mismatch_counts.items())),
            "intervening_nondecision_kind_counts": dict(
                sorted(intervening_kind_counts.items())
            ),
        },
        "body_sets": {
            "endpoint_bodies_checked": endpoint_bodies_checked,
            "compatible_branches": compatible_branches,
            "mode_bit_set_pointers": mode_bit_set,
            "mode_bit_cleared_pointers": mode_bit_cleared,
            "mode_bit_set_intervals": mode_bit_set_intervals,
            "mode_bit_cleared_intervals": mode_bit_cleared_intervals,
        },
        "interpretation": {
            "strict_manager_frame_gate_passed": bool(not mismatched),
            "ordered_partial_transition_physical_counterexample_count": (
                mismatch_counts["observed_ordered_partial_transition_mask"]
            ),
            "other_manager_frame_decomposition_mismatch_count": (
                mismatched - mismatch_counts["observed_ordered_partial_transition_mask"]
            ),
        },
        "ordered_partial_transactions": {
            "observed_count": mismatch_counts[
                "observed_ordered_partial_transition_mask"
            ],
            "unique_signature_count": len(ordered_partial_signature_counts),
            "edge_position_counts": dict(
                sorted(ordered_partial_edge_position_counts.items())
            ),
            "focus_path_counts": dict(
                sorted(ordered_partial_focus_path_counts.items())
            ),
            "shot_path_counts": dict(sorted(ordered_partial_shot_path_counts.items())),
            "direction_path_counts": dict(
                sorted(ordered_partial_direction_path_counts.items())
            ),
            "top_signatures": [
                {"signature": signature, "count": count}
                for signature, count in sorted(
                    ordered_partial_signature_counts.items(),
                    key=lambda item: (-item[1], item[0]),
                )[:32]
            ],
        },
        "retained_transition_matches": retained_matches,
        "retained_mismatches": retained_mismatches,
        "integrity": {
            "passed": bool(not any(integrity_errors.values())),
            "errors": integrity_errors,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    report = build_report(args.trace)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if report["integrity"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
