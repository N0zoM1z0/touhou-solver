#!/usr/bin/env python3
"""Audit TH08's read-only semantic input-clock shadow trace.

The manager frame is not a physical input clock while a message script is
active.  This audit compares semantic shadow episodes with the existing
wall-time auto-confirm pulse groups without granting either signal input
authority.  Legacy traces remain useful for pulse counts, but absence of the
new message-state schema is reported as unobservable rather than as zero
false positives.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


SCHEMA = "th08-input-clock-audit-v1"
SEMANTIC_KINDS = {
    "input_clock_shadow_observation",
    "input_clock_shadow_episode",
}
TERMINAL_STATUSES = {"terminal_unload", "route_complete"}


def _episode_key(value: object) -> str:
    """Return a stable hashable key while retaining the raw ID for output."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _integer(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _number(value: object) -> int | float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


def _native_input_current(value: object) -> int | None:
    """Read native active-input evidence without falling back to desired input."""

    if not isinstance(value, dict):
        return None
    for name in ("native_input_current", "input_current"):
        current = _integer(value.get(name))
        if current is not None:
            return current
    snapshot = value.get("input_snapshot")
    if isinstance(snapshot, dict):
        current = _integer(snapshot.get("current"))
        if current is not None:
            return current
    input_after = value.get("input_after")
    if isinstance(input_after, dict):
        current = _integer(input_after.get("current"))
        if current is not None:
            return current
    active_input = _integer(value.get("active_input"))
    if active_input is not None:
        return active_input
    sample = value.get("sample")
    if isinstance(sample, dict) and sample is not value:
        return _native_input_current(sample)
    return None


def _held_desired_mask(value: object) -> int | None:
    """Read held desired input without inferring it from native active input."""

    if not isinstance(value, dict):
        return None
    desired = _integer(value.get("held_desired_mask"))
    if desired is not None:
        return desired
    sample = value.get("sample")
    if isinstance(sample, dict) and sample is not value:
        return _integer(sample.get("held_desired_mask"))
    return None


def _observation_summary(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    sample = value.get("sample")
    frame = _integer(value.get("frame"))
    if frame is None:
        frame = _integer(value.get("physical_frame"))
    return {
        "frame": frame,
        "triggers": (
            list(value["triggers"])
            if isinstance(value.get("triggers"), list)
            else []
        ),
        "frozen_seconds": _number(value.get("frozen_seconds")),
        "repeat_poll_count": _integer(value.get("repeat_poll_count")),
        "gameplay_epoch": _integer(value.get("gameplay_epoch")),
        # These are deliberately separate fields.  Neither is a proxy for the
        # other under pending command pickup.
        "held_desired_mask": _held_desired_mask(value),
        "native_input_current": _native_input_current(value),
        "delay_support": (
            list(value["delay_support"])
            if isinstance(value.get("delay_support"), list)
            else None
        ),
        "role": value.get("role") if isinstance(value.get("role"), str) else None,
        "sample": dict(sample) if isinstance(sample, dict) else None,
    }


def _nested_observation(
    row: dict[str, object],
    *names: str,
) -> dict[str, object] | None:
    for name in names:
        value = row.get(name)
        if isinstance(value, dict):
            return _observation_summary(value)
    return None


def _sample_gate_active(value: object) -> bool | None:
    if not isinstance(value, dict):
        return None
    for name in (
        "native_manager_clock_blocked",
        "message_clock_gate_active",
        "semantic_active",
    ):
        gate = value.get(name)
        if isinstance(gate, bool):
            return gate
    observation = value.get("observation")
    if isinstance(observation, dict):
        gate = _sample_gate_active(observation)
        if gate is not None:
            return gate
    sample = value.get("sample")
    if isinstance(sample, dict) and sample is not value:
        return _sample_gate_active(sample)
    return None


def _semantic_config_enabled(row: dict[str, object]) -> bool:
    if row.get("input_clock_boundary_shadow") is True:
        return True
    if row.get("input_clock_shadow_enabled") is True:
        return True
    shadow = row.get("input_clock_shadow")
    if shadow is True:
        return True
    return isinstance(shadow, dict) and shadow.get("enabled") is True


@dataclass
class PulseGroup:
    stage_route_index: int | None
    frame: int
    first_line: int
    last_line: int
    pulse_count: int = 0
    episode_ids: dict[str, object] = field(default_factory=dict)
    held_desired_masks: set[int] = field(default_factory=set)
    native_input_current_masks: set[int] = field(default_factory=set)

    def add(self, row: dict[str, object], line_number: int) -> None:
        self.last_line = line_number
        self.pulse_count += 1
        top_level_episode_id = row.get("input_clock_shadow_episode_id")
        if top_level_episode_id is not None:
            self.episode_ids.setdefault(
                _episode_key(top_level_episode_id),
                top_level_episode_id,
            )
        desired = _held_desired_mask(row)
        if desired is not None:
            self.held_desired_masks.add(desired)
        shadow = row.get("input_clock_shadow")
        if not isinstance(shadow, dict):
            return
        if shadow.get("episode_id") is not None:
            raw_id = shadow["episode_id"]
            self.episode_ids.setdefault(_episode_key(raw_id), raw_id)
        shadow_desired = _held_desired_mask(shadow)
        if shadow_desired is not None:
            self.held_desired_masks.add(shadow_desired)
        current = _native_input_current(shadow)
        if current is not None:
            self.native_input_current_masks.add(current)


@dataclass
class Episode:
    episode_id: object
    first_line: int
    last_line: int
    statuses: list[str] = field(default_factory=list)
    stage_route_index: int | None = None
    start_frame: int | None = None
    current_frame: int | None = None
    reason: str | None = None
    declared_pulse_count: int | None = None
    duration_ns: int | None = None
    displacement: int | float | None = None
    start_update_serial: int | None = None
    current_update_serial: int | None = None
    start_msg_state: int | None = None
    current_msg_state: int | None = None
    start_observation: dict[str, object] | None = None
    current_observation: dict[str, object] | None = None
    attached_from_pulse: bool = False

    def add_event(
        self,
        row: dict[str, object],
        line_number: int,
    ) -> None:
        self.last_line = line_number
        status = row.get("status")
        if isinstance(status, str):
            self.statuses.append(status)
        stage = _integer(row.get("stage_route_index"))
        if self.stage_route_index is None and stage is not None:
            self.stage_route_index = stage
        frame = _integer(row.get("frame"))
        if frame is not None:
            if self.start_frame is None:
                self.start_frame = frame
            self.current_frame = frame
        reason = row.get("reason")
        if isinstance(reason, str):
            self.reason = reason
        pulse_count = _integer(row.get("pulse_count"))
        if pulse_count is not None:
            self.declared_pulse_count = pulse_count
        duration_ns = _integer(row.get("duration_ns"))
        if duration_ns is not None:
            self.duration_ns = duration_ns
        displacement = _number(row.get("displacement"))
        if displacement is not None:
            self.displacement = displacement

        start = _nested_observation(
            row,
            "start",
            "start_observation",
            "start_observation_summary",
        )
        current = _nested_observation(
            row,
            "current",
            "observation",
            "current_observation",
            "current_observation_summary",
        )
        if start is not None and self.start_observation is None:
            self.start_observation = start
            start_frame = _integer(start.get("frame"))
            if start_frame is not None:
                self.start_frame = start_frame
        if current is not None:
            self.current_observation = current
            current_frame = _integer(current.get("frame"))
            if current_frame is not None:
                self.current_frame = current_frame

        # Episode rows may carry a direct sample instead of repeating an
        # observation summary.  Preserve it as evidence, still with separate
        # desired and native active masks.
        if row.get("sample") is not None:
            direct = _observation_summary(row)
            sample = row.get("sample")
            assert isinstance(sample, dict)
            update_serial = _integer(
                sample.get("frscreen_update_serial_after")
            )
            msg_state = _integer(sample.get("msg_state_after"))
            if status == "begin":
                self.start_update_serial = update_serial
                self.start_msg_state = msg_state
            else:
                self.current_update_serial = update_serial
                self.current_msg_state = msg_state
            if status == "begin" and self.start_observation is None:
                self.start_observation = direct
            elif status == "begin" and self.start_observation is not None:
                for name in (
                    "held_desired_mask",
                    "native_input_current",
                    "delay_support",
                    "role",
                    "sample",
                ):
                    if self.start_observation.get(name) is None:
                        self.start_observation[name] = direct.get(name)
            if status != "begin" or self.current_observation is None:
                self.current_observation = direct

    @property
    def final_status(self) -> str:
        if "censored" in self.statuses:
            return "censored"
        if "end" in self.statuses:
            return "ended"
        if "begin" in self.statuses:
            return "open"
        if self.attached_from_pulse:
            return "pulse_only"
        return "incomplete"


def _terminal_marker(
    row: dict[str, object],
    line_number: int,
) -> tuple[int, int | None, int, str] | None:
    kind = row.get("kind")
    status: str | None = None
    frame = _integer(row.get("frame"))
    if kind == "scene_inactive" and row.get("status") in TERMINAL_STATUSES:
        status = str(row["status"])
    elif kind in TERMINAL_STATUSES:
        status = str(kind)
    elif kind == "summary" and row.get("termination_reason") in TERMINAL_STATUSES:
        status = str(row["termination_reason"])
        frame = _integer(row.get("last_frame"))
    if status is None or frame is None:
        return None
    return (
        line_number,
        _integer(row.get("stage_route_index")),
        frame,
        status,
    )


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "minimum": None,
            "median": None,
            "p95": None,
            "maximum": None,
            "mean": None,
        }
    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2
    median = (
        ordered[middle]
        if count % 2
        else (ordered[middle - 1] + ordered[middle]) / 2.0
    )
    return {
        "count": count,
        "minimum": ordered[0],
        "median": median,
        "p95": ordered[max(0, math.ceil(count * 0.95) - 1)],
        "maximum": ordered[-1],
        "mean": sum(ordered) / count,
    }


def audit(trace: Path) -> dict[str, object]:
    """Stream one trace and return a deterministic semantic-clock audit."""

    row_counts: Counter[str] = Counter()
    trigger_counts: Counter[str] = Counter()
    trigger_gate_counts: dict[str, Counter[str]] = {}
    trigger_frozen_seconds: dict[
        str,
        dict[str, list[float]],
    ] = {}
    role_counts: Counter[str] = Counter()
    gate_counts: Counter[str] = Counter()
    input_pairs: Counter[tuple[int, int]] = Counter()
    observation_count = 0
    desired_present_count = 0
    native_present_count = 0
    both_present_count = 0
    differing_count = 0
    capture_us_values: list[float] = []
    read_valid_counts: Counter[str] = Counter()
    message_stability_counts: Counter[str] = Counter()
    special_pause_counts: Counter[str] = Counter()
    msg_state_counts: Counter[str] = Counter()
    first_observation: dict[str, object] | None = None
    last_observation: dict[str, object] | None = None
    semantic_schema_seen = False
    pulse_groups_by_key: dict[tuple[int | None, int], PulseGroup] = {}
    episodes: dict[str, Episode] = {}
    terminal_markers: list[tuple[int, int | None, int, str]] = []
    integrity_errors: list[str] = []

    with trace.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSON at {trace}:{line_number}: {error}"
                ) from error
            if not isinstance(raw, dict):
                raise ValueError(
                    f"expected JSON object at {trace}:{line_number}"
                )
            row: dict[str, object] = raw
            kind = row.get("kind")
            kind_name = str(kind) if isinstance(kind, str) else "missing"
            row_counts[kind_name] += 1
            if kind in SEMANTIC_KINDS or _semantic_config_enabled(row):
                semantic_schema_seen = True

            marker = _terminal_marker(row, line_number)
            if marker is not None:
                terminal_markers.append(marker)

            if kind == "input_clock_shadow_observation":
                observation_count += 1
                summary = _observation_summary(row)
                assert summary is not None
                if first_observation is None:
                    first_observation = summary
                last_observation = summary
                triggers = row.get("triggers")
                trigger_names: list[str] = []
                if isinstance(triggers, list):
                    for trigger in triggers:
                        if isinstance(trigger, str):
                            trigger_counts[trigger] += 1
                            trigger_names.append(trigger)
                role = row.get("role")
                if isinstance(role, str):
                    role_counts[role] += 1
                gate = _sample_gate_active(row)
                gate_counts[
                    "true" if gate is True else "false" if gate is False else "unknown"
                ] += 1
                gate_label = (
                    "true"
                    if gate is True
                    else "false"
                    if gate is False
                    else "unknown"
                )
                for trigger in trigger_names:
                    trigger_gate_counts.setdefault(
                        trigger,
                        Counter(),
                    )[gate_label] += 1
                    frozen_seconds = _number(row.get("frozen_seconds"))
                    if frozen_seconds is not None:
                        trigger_frozen_seconds.setdefault(
                            trigger,
                            {},
                        ).setdefault(gate_label, []).append(
                            float(frozen_seconds)
                        )
                sample = row.get("sample")
                if isinstance(sample, dict):
                    capture_us = _number(sample.get("capture_us"))
                    if capture_us is not None:
                        capture_us_values.append(float(capture_us))
                    read_valid = sample.get("read_valid")
                    read_valid_counts[
                        (
                            "true"
                            if read_valid is True
                            else "false"
                            if read_valid is False
                            else "unknown"
                        )
                    ] += 1
                    stable = sample.get("message_snapshot_stable")
                    message_stability_counts[
                        (
                            "true"
                            if stable is True
                            else "false"
                            if stable is False
                            else "unknown"
                        )
                    ] += 1
                    special = sample.get("frscreen_special_pause")
                    special_pause_counts[
                        (
                            "true"
                            if special is True
                            else "false"
                            if special is False
                            else "unknown"
                        )
                    ] += 1
                    msg_state = _integer(sample.get("msg_state_after"))
                    msg_state_counts[
                        str(msg_state) if msg_state is not None else "unknown"
                    ] += 1
                desired = _held_desired_mask(row)
                current = _native_input_current(row)
                desired_present_count += int(desired is not None)
                native_present_count += int(current is not None)
                if desired is not None and current is not None:
                    both_present_count += 1
                    differing_count += int(desired != current)
                    input_pairs[(desired, current)] += 1
                continue

            if kind == "input_clock_shadow_episode":
                raw_id = row.get("episode_id")
                if raw_id is None:
                    integrity_errors.append(
                        f"line {line_number}: episode event missing episode_id"
                    )
                    continue
                key = _episode_key(raw_id)
                episode = episodes.get(key)
                if episode is None:
                    episode = Episode(raw_id, line_number, line_number)
                    episodes[key] = episode
                elif row.get("status") == "begin" and "begin" in episode.statuses:
                    integrity_errors.append(
                        f"line {line_number}: duplicate begin for episode {key}"
                    )
                episode.add_event(row, line_number)
                continue

            if kind != "auto_confirm_wall_pulse":
                continue
            frame = _integer(row.get("frame"))
            if frame is None:
                integrity_errors.append(
                    f"line {line_number}: wall pulse missing integer frame"
                )
                continue
            stage = _integer(row.get("stage_route_index"))
            group_key = (stage, frame)
            group = pulse_groups_by_key.get(group_key)
            if group is None:
                group = PulseGroup(
                    stage_route_index=stage,
                    frame=frame,
                    first_line=line_number,
                    last_line=line_number,
                )
                pulse_groups_by_key[group_key] = group
            group.add(row, line_number)

    pulse_groups = list(pulse_groups_by_key.values())
    terminal_by_group: dict[int, list[str]] = {}
    if pulse_groups:
        final_index = len(pulse_groups) - 1
        final_group = pulse_groups[final_index]
        for line_number, stage, frame, status in terminal_markers:
            if (
                line_number > final_group.last_line
                and frame == final_group.frame
                and (
                    stage is None
                    or final_group.stage_route_index is None
                    or stage == final_group.stage_route_index
                )
            ):
                terminal_by_group.setdefault(final_index, []).append(status)

    # A pulse-attached episode ID is the strongest match.  Create a visible
    # placeholder if an otherwise-new trace omitted its episode event so the
    # omission is auditable rather than silently becoming a false negative.
    for group in pulse_groups:
        for key, raw_id in group.episode_ids.items():
            if key not in episodes:
                episode = Episode(
                    raw_id,
                    group.first_line,
                    group.last_line,
                    stage_route_index=group.stage_route_index,
                    start_frame=group.frame,
                    current_frame=group.frame,
                    attached_from_pulse=True,
                )
                episodes[key] = episode
                integrity_errors.append(
                    f"pulse at frame {group.frame}: attached episode {key} "
                    "has no episode event"
                )

    ordered_episodes = sorted(
        episodes.items(),
        key=lambda item: (item[1].first_line, item[0]),
    )
    matched_episode_keys: set[str] = set()
    matched_group_indexes: set[int] = set()
    matches: list[dict[str, object]] = []
    match_for_episode: dict[str, int] = {}

    for group_index, group in enumerate(pulse_groups):
        explicit = [
            key
            for key in group.episode_ids
            if key in episodes and key not in matched_episode_keys
        ]
        candidates = explicit
        method = "episode_id"
        if not candidates:
            method = "same_frame"
            candidates = [
                key
                for key, episode in ordered_episodes
                if (
                    key not in matched_episode_keys
                    and episode.start_frame == group.frame
                    and episode.first_line <= group.last_line
                    and (
                        episode.final_status not in {"ended", "censored"}
                        or episode.last_line >= group.first_line
                    )
                    and (
                        episode.stage_route_index is None
                        or group.stage_route_index is None
                        or episode.stage_route_index == group.stage_route_index
                    )
                )
            ]
        if not candidates:
            continue
        key = candidates[0]
        matched_episode_keys.add(key)
        matched_group_indexes.add(group_index)
        match_for_episode[key] = group_index
        matches.append(
            {
                "episode_id": episodes[key].episode_id,
                "pulse_group_index": group_index,
                "frame": group.frame,
                "method": method,
                "right_censored": group_index in terminal_by_group,
            }
        )

    group_reports: list[dict[str, object]] = []
    for index, group in enumerate(pulse_groups):
        terminal_statuses = sorted(set(terminal_by_group.get(index, [])))
        group_reports.append(
            {
                "group_index": index,
                "frame": group.frame,
                "stage_route_index": group.stage_route_index,
                "pulse_count": group.pulse_count,
                "status": (
                    "positive_right_censored"
                    if terminal_statuses
                    else "positive"
                ),
                "terminal_statuses": terminal_statuses,
                "episode_ids": list(group.episode_ids.values()),
                # Preserve desired/native evidence as different collections.
                "held_desired_masks": sorted(group.held_desired_masks),
                "native_input_current_masks": sorted(
                    group.native_input_current_masks
                ),
                "matched": index in matched_group_indexes,
            }
        )

    episode_reports: list[dict[str, object]] = []
    for key, episode in ordered_episodes:
        group_index = match_for_episode.get(key)
        status = episode.final_status
        if (
            status == "open"
            and group_index is not None
            and group_index in terminal_by_group
        ):
            status = "inferred_censored"
        episode_reports.append(
            {
                "episode_id": episode.episode_id,
                "status": status,
                "event_statuses": list(episode.statuses),
                "reason": episode.reason,
                "stage_route_index": episode.stage_route_index,
                "start_frame": episode.start_frame,
                "current_frame": episode.current_frame,
                "declared_pulse_count": episode.declared_pulse_count,
                "duration_ns": episode.duration_ns,
                "displacement": episode.displacement,
                "frscreen_update_serial_start": (
                    episode.start_update_serial
                ),
                "frscreen_update_serial_current": (
                    episode.current_update_serial
                ),
                "frscreen_update_serial_delta": (
                    (
                        episode.current_update_serial
                        - episode.start_update_serial
                    )
                    & 0xFFFFFFFF
                    if (
                        episode.start_update_serial is not None
                        and episode.current_update_serial is not None
                    )
                    else None
                ),
                "msg_state_start": episode.start_msg_state,
                "msg_state_current": episode.current_msg_state,
                "matched_pulse_group_index": group_index,
                "start_observation": episode.start_observation,
                "current_observation": episode.current_observation,
            }
        )

    semantic_status = (
        "observable" if semantic_schema_seen else "not_observable"
    )
    if semantic_status == "observable":
        true_positives = len(matches)
        false_positives = len(episodes) - true_positives
        false_negatives = len(pulse_groups) - true_positives
        precision = _ratio(
            true_positives,
            true_positives + false_positives,
        )
        recall = _ratio(
            true_positives,
            true_positives + false_negatives,
        )
        right_censored_true_positives = sum(
            bool(match["right_censored"]) for match in matches
        )
    else:
        true_positives = None
        false_positives = None
        false_negatives = None
        precision = None
        recall = None
        right_censored_true_positives = None

    return {
        "schema": SCHEMA,
        "trace": str(trace),
        "semantic_status": semantic_status,
        "row_counts": dict(sorted(row_counts.items())),
        "wall_pulses": {
            "pulse_count": sum(group.pulse_count for group in pulse_groups),
            "group_count": len(pulse_groups),
            "positive_group_count": len(pulse_groups),
            "right_censored_positive_count": len(terminal_by_group),
            "groups": group_reports,
        },
        "semantic_observations": {
            "observation_count": observation_count,
            "trigger_counts": dict(sorted(trigger_counts.items())),
            "trigger_gate_counts": {
                trigger: dict(sorted(counts.items()))
                for trigger, counts in sorted(trigger_gate_counts.items())
            },
            "trigger_frozen_seconds": {
                trigger: {
                    gate: _numeric_summary(values)
                    for gate, values in sorted(by_gate.items())
                }
                for trigger, by_gate in sorted(
                    trigger_frozen_seconds.items()
                )
            },
            "role_counts": dict(sorted(role_counts.items())),
            "message_clock_gate_active_counts": dict(
                sorted(gate_counts.items())
            ),
            "native_manager_clock_blocked_counts": dict(
                sorted(gate_counts.items())
            ),
            "capture_us": _numeric_summary(capture_us_values),
            "read_valid_counts": dict(sorted(read_valid_counts.items())),
            "message_snapshot_stable_counts": dict(
                sorted(message_stability_counts.items())
            ),
            "frscreen_special_pause_counts": dict(
                sorted(special_pause_counts.items())
            ),
            "msg_state_counts": dict(sorted(msg_state_counts.items())),
            "first": first_observation,
            "last": last_observation,
            "input_evidence": {
                "source": "input_clock_shadow_observation_rows",
                "held_desired_present_count": desired_present_count,
                "native_input_current_present_count": native_present_count,
                "both_present_count": both_present_count,
                "differing_count": differing_count,
                "pairs": [
                    {
                        "held_desired_mask": desired,
                        "native_input_current": current,
                        "count": count,
                    }
                    for (desired, current), count in sorted(
                        input_pairs.items()
                    )
                ],
            },
        },
        "semantic_episodes": {
            "episode_count": len(episodes),
            "episodes": episode_reports,
        },
        "classification": {
            "reference": "same-frame auto_confirm_wall_pulse groups",
            "reference_role": "delayed_proxy_not_live_or_ground_truth",
            "true_positive_episode_count": true_positives,
            "false_positive_episode_count": false_positives,
            "false_negative_pulse_group_count": false_negatives,
            "right_censored_true_positive_count": (
                right_censored_true_positives
            ),
            "precision": precision,
            "recall": recall,
            "matches": matches if semantic_schema_seen else None,
        },
        "integrity": {
            "error_count": len(integrity_errors),
            "errors": integrity_errors,
        },
        "authority": "shadow_no_input_or_epoch_authority",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare TH08 semantic input-clock shadow episodes with "
            "same-frame wall-pulse groups."
        )
    )
    parser.add_argument("trace", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    arguments = parser.parse_args(argv)

    report = audit(arguments.trace)
    rendered = json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"
    if arguments.output is not None:
        arguments.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
