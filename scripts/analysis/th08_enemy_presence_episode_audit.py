#!/usr/bin/env python3
"""Audit observation-bounded enemy presence episodes in a retained trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from analysis.enemy_combat_progress_audit.schema import (
    EnemyCombatProgressAuditError,
    OBSERVATION_SCHEMA,
    require_exact_int,
    validate_inventory,
)


SCHEMA = "th08-enemy-presence-episode-audit-v1"


def _sign(value: int) -> str:
    if value < 0:
        return "negative"
    if value == 0:
        return "zero"
    return "positive"


@dataclass
class _Episode:
    stage_route_index: int
    gameplay_epoch: int
    slot: int
    observation_ordinal: int
    left_censored: bool
    start_after_frame: int | None
    first_frame: int
    last_frame: int
    observation_count: int
    initial_hp: int
    minimum_hp: int
    last_hp: int
    positive_frame_damage_observations: int
    adjacent_hp_decrease_count: int
    maximum_observation_gap: int
    last_frame_damage: int
    last_damage_gate: bool
    last_defeat_mode: int
    last_flags: int
    last_flags2: int
    right_censored: bool = False
    end_at_or_before_frame: int | None = None

    @classmethod
    def begin(
        cls,
        *,
        stage_route_index: int,
        gameplay_epoch: int,
        slot: int,
        observation_ordinal: int,
        left_censored: bool,
        start_after_frame: int | None,
        frame: int,
        row: list[int | bool],
    ) -> _Episode:
        hp = int(row[4])
        return cls(
            stage_route_index=stage_route_index,
            gameplay_epoch=gameplay_epoch,
            slot=slot,
            observation_ordinal=observation_ordinal,
            left_censored=left_censored,
            start_after_frame=start_after_frame,
            first_frame=frame,
            last_frame=frame,
            observation_count=1,
            initial_hp=hp,
            minimum_hp=hp,
            last_hp=hp,
            positive_frame_damage_observations=int(int(row[7]) > 0),
            adjacent_hp_decrease_count=0,
            maximum_observation_gap=0,
            last_frame_damage=int(row[7]),
            last_damage_gate=bool(row[8]),
            last_defeat_mode=int(row[9]),
            last_flags=int(row[2]),
            last_flags2=int(row[3]),
        )

    def retain(self, *, frame: int, row: list[int | bool]) -> None:
        gap = frame - self.last_frame
        hp = int(row[4])
        if hp < self.last_hp:
            self.adjacent_hp_decrease_count += 1
        self.last_frame = frame
        self.observation_count += 1
        self.minimum_hp = min(self.minimum_hp, hp)
        self.last_hp = hp
        self.positive_frame_damage_observations += int(int(row[7]) > 0)
        self.maximum_observation_gap = max(self.maximum_observation_gap, gap)
        self.last_frame_damage = int(row[7])
        self.last_damage_gate = bool(row[8])
        self.last_defeat_mode = int(row[9])
        self.last_flags = int(row[2])
        self.last_flags2 = int(row[3])

    def record(self) -> dict[str, object]:
        return {
            "stage_route_index": self.stage_route_index,
            "gameplay_epoch": self.gameplay_epoch,
            "slot": self.slot,
            "observation_ordinal": self.observation_ordinal,
            "left_censored": self.left_censored,
            "start_window": {
                "after_frame": self.start_after_frame,
                "at_or_before_frame": self.first_frame,
            },
            "first_frame": self.first_frame,
            "last_active_frame": self.last_frame,
            "observation_count": self.observation_count,
            "initial_hp": self.initial_hp,
            "minimum_hp": self.minimum_hp,
            "last_hp": self.last_hp,
            "positive_frame_damage_observations": (
                self.positive_frame_damage_observations
            ),
            "adjacent_hp_decrease_count": self.adjacent_hp_decrease_count,
            "maximum_observation_gap": self.maximum_observation_gap,
            "last_frame_damage": self.last_frame_damage,
            "last_damage_gate": self.last_damage_gate,
            "last_defeat_mode": self.last_defeat_mode,
            "last_flags": self.last_flags,
            "last_flags2": self.last_flags2,
            "right_censored": self.right_censored,
            "end_window": (
                None
                if self.right_censored
                else {
                    "after_frame": self.last_frame,
                    "at_or_before_frame": self.end_at_or_before_frame,
                }
            ),
            "end_classification": (
                "right_censored"
                if self.right_censored
                else (
                    "damage_adjacent_disappearance_candidate"
                    if self.last_frame_damage > 0
                    else "unobserved_end_reason"
                )
            ),
        }


class _Accumulator:
    def __init__(self) -> None:
        self.observation_count = 0
        self.active_row_count = 0
        self.previous_frame: dict[tuple[int, int], int] = {}
        self.previous_rows: dict[
            tuple[int, int], dict[int, list[int | bool]]
        ] = {}
        self.open_episodes: dict[tuple[int, int, int], _Episode] = {}
        self.next_ordinal: Counter[tuple[int, int, int]] = Counter()
        self.episodes: list[_Episode] = []
        self.decision_gap_counts: Counter[int] = Counter()
        self.observations_by_epoch: Counter[str] = Counter()
        self.row_hp_sign_counts: Counter[str] = Counter()
        self.row_defeat_mode_counts: Counter[int] = Counter()

    def _begin(
        self,
        *,
        epoch_key: tuple[int, int],
        slot: int,
        left_censored: bool,
        start_after_frame: int | None,
        frame: int,
        row: list[int | bool],
    ) -> None:
        key = (*epoch_key, slot)
        ordinal = self.next_ordinal[key]
        self.next_ordinal[key] += 1
        self.open_episodes[key] = _Episode.begin(
            stage_route_index=epoch_key[0],
            gameplay_epoch=epoch_key[1],
            slot=slot,
            observation_ordinal=ordinal,
            left_censored=left_censored,
            start_after_frame=start_after_frame,
            frame=frame,
            row=row,
        )

    def retain(
        self,
        *,
        stage_route_index: int,
        gameplay_epoch: int,
        decision_frame: int,
        rows: list[list[int | bool]],
    ) -> None:
        epoch_key = (stage_route_index, gameplay_epoch)
        label = f"{stage_route_index}:{gameplay_epoch}"
        self.observation_count += 1
        self.observations_by_epoch[label] += 1
        self.active_row_count += len(rows)
        current = {int(row[0]): row for row in rows}
        previous = self.previous_rows.get(epoch_key)
        previous_frame = self.previous_frame.get(epoch_key)
        if previous_frame is not None:
            gap = decision_frame - previous_frame
            if gap <= 0:
                raise EnemyCombatProgressAuditError(
                    "decision frames do not strictly increase within an epoch"
                )
            self.decision_gap_counts[gap] += 1

        for row in rows:
            self.row_hp_sign_counts[_sign(int(row[4]))] += 1
            self.row_defeat_mode_counts[int(row[9])] += 1

        if previous is None:
            for slot, row in current.items():
                self._begin(
                    epoch_key=epoch_key,
                    slot=slot,
                    left_censored=True,
                    start_after_frame=None,
                    frame=decision_frame,
                    row=row,
                )
        else:
            assert previous_frame is not None
            for slot in previous.keys() - current.keys():
                key = (*epoch_key, slot)
                episode = self.open_episodes.pop(key)
                episode.end_at_or_before_frame = decision_frame
                self.episodes.append(episode)
            for slot, row in current.items():
                key = (*epoch_key, slot)
                if slot not in previous:
                    self._begin(
                        epoch_key=epoch_key,
                        slot=slot,
                        left_censored=False,
                        start_after_frame=previous_frame,
                        frame=decision_frame,
                        row=row,
                    )
                else:
                    self.open_episodes[key].retain(
                        frame=decision_frame,
                        row=row,
                    )

        self.previous_rows[epoch_key] = current
        self.previous_frame[epoch_key] = decision_frame

    def finish(self) -> list[dict[str, object]]:
        for episode in self.open_episodes.values():
            episode.right_censored = True
            self.episodes.append(episode)
        self.open_episodes.clear()
        return [
            episode.record()
            for episode in sorted(
                self.episodes,
                key=lambda value: (
                    value.stage_route_index,
                    value.gameplay_epoch,
                    value.slot,
                    value.observation_ordinal,
                ),
            )
        ]


def _validate_observation(
    record: dict[str, Any],
    *,
    line_number: int,
    expected_route_id: int,
    expected_difficulty_index: int,
    expected_stage_route_index: int,
) -> tuple[int, int, int, list[list[int | bool]]]:
    if record.get("schema") != OBSERVATION_SCHEMA:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: unexpected observation schema"
        )
    route_id = require_exact_int(
        record.get("route_id"),
        line_number=line_number,
        field="route_id",
    )
    difficulty_index = require_exact_int(
        record.get("difficulty_index"),
        line_number=line_number,
        field="difficulty_index",
    )
    stage_route_index = require_exact_int(
        record.get("stage_route_index"),
        line_number=line_number,
        field="stage_route_index",
    )
    if (
        route_id != expected_route_id
        or difficulty_index != expected_difficulty_index
        or stage_route_index != expected_stage_route_index
    ):
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: physical identity mismatch"
        )
    gameplay_epoch = require_exact_int(
        record.get("gameplay_epoch"),
        line_number=line_number,
        field="gameplay_epoch",
    )
    decision_frame = require_exact_int(
        record.get("decision_frame"),
        line_number=line_number,
        field="decision_frame",
    )
    frame_before = require_exact_int(
        record.get("frame_before"),
        line_number=line_number,
        field="frame_before",
    )
    frame_after = require_exact_int(
        record.get("frame_after"),
        line_number=line_number,
        field="frame_after",
    )
    if record.get("stable") is not True or frame_before != frame_after:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: observation bracket is not stable"
        )
    rows, _decode_ms, _record_ms = validate_inventory(
        record.get("inventory"),
        line_number=line_number,
    )
    return stage_route_index, gameplay_epoch, decision_frame, rows


def audit_enemy_presence_episodes(
    trace_path: Path,
    *,
    expected_route_id: int,
    expected_difficulty_index: int,
    expected_stage_route_index: int,
    expected_trace_sha256: str | None = None,
) -> dict[str, object]:
    digest = hashlib.sha256()
    line_count = 0
    accumulator = _Accumulator()
    schema_marker = OBSERVATION_SCHEMA.encode("ascii")
    with trace_path.open("rb") as source:
        for line_number, raw_line in enumerate(source, 1):
            digest.update(raw_line)
            line_count = line_number
            if schema_marker not in raw_line:
                continue
            try:
                record = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise EnemyCombatProgressAuditError(
                    f"line {line_number}: invalid observation JSON: {error}"
                ) from error
            if not isinstance(record, dict):
                raise EnemyCombatProgressAuditError(
                    f"line {line_number}: observation must be an object"
                )
            stage_route_index, gameplay_epoch, decision_frame, rows = (
                _validate_observation(
                    record,
                    line_number=line_number,
                    expected_route_id=expected_route_id,
                    expected_difficulty_index=expected_difficulty_index,
                    expected_stage_route_index=expected_stage_route_index,
                )
            )
            accumulator.retain(
                stage_route_index=stage_route_index,
                gameplay_epoch=gameplay_epoch,
                decision_frame=decision_frame,
                rows=rows,
            )

    trace_sha256 = digest.hexdigest()
    if (
        expected_trace_sha256 is not None
        and trace_sha256 != expected_trace_sha256
    ):
        raise EnemyCombatProgressAuditError(
            "trace SHA-256 does not match the immutable expected input"
        )
    episodes = accumulator.finish()
    ended = [episode for episode in episodes if not episode["right_censored"]]
    right_censored = [
        episode for episode in episodes if episode["right_censored"]
    ]
    damage_adjacent = [
        episode
        for episode in ended
        if episode["end_classification"]
        == "damage_adjacent_disappearance_candidate"
    ]
    episode_payload = json.dumps(
        episodes,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report: dict[str, object] = {
        "schema": SCHEMA,
        "trace_sha256": trace_sha256,
        "line_count": line_count,
        "expected_identity": {
            "route_id": expected_route_id,
            "difficulty_index": expected_difficulty_index,
            "stage_route_index": expected_stage_route_index,
        },
        "observation_count": accumulator.observation_count,
        "active_row_count": accumulator.active_row_count,
        "observations_by_stage_epoch": dict(
            sorted(accumulator.observations_by_epoch.items())
        ),
        "decision_gap_counts": {
            str(key): value
            for key, value in sorted(accumulator.decision_gap_counts.items())
        },
        "presence_episode_count": len(episodes),
        "ended_presence_episode_count": len(ended),
        "right_censored_presence_episode_count": len(right_censored),
        "left_censored_presence_episode_count": sum(
            bool(episode["left_censored"]) for episode in episodes
        ),
        "presence_episode_digest": hashlib.sha256(episode_payload).hexdigest(),
        "end_last_hp_sign_counts": dict(
            sorted(Counter(_sign(int(episode["last_hp"])) for episode in ended).items())
        ),
        "end_last_defeat_mode_counts": {
            str(key): value
            for key, value in sorted(
                Counter(int(episode["last_defeat_mode"]) for episode in ended).items()
            )
        },
        "end_window_width_counts": {
            str(key): value
            for key, value in sorted(
                Counter(
                    int(episode["end_window"]["at_or_before_frame"])
                    - int(episode["end_window"]["after_frame"])
                    for episode in ended
                ).items()
            )
        },
        "row_hp_sign_counts": dict(
            sorted(accumulator.row_hp_sign_counts.items())
        ),
        "row_defeat_mode_counts": {
            str(key): value
            for key, value in sorted(
                accumulator.row_defeat_mode_counts.items()
            )
        },
        "damage_adjacent_disappearance_candidates": damage_adjacent,
        "classification": {
            "generation_authority": "observation_presence_episode_only",
            "native_generation_authority": "none",
            "end_reason_authority": "none",
            "verified_kill_count": 0,
            "timeout_count": 0,
            "scripted_despawn_count": 0,
            "transition_count": 0,
            "unknown_ended_episode_count": len(ended),
            "damage_adjacent_candidate_count": len(damage_adjacent),
            "reason": (
                "the post-update active-only trace captures no same-update "
                "clear path; active-row HP and defeat-mode values cannot "
                "classify disappearance end reasons"
            ),
        },
        "authority": {
            "kind": "offline_observation_presence_episode_audit",
            "kill_policy_gate_passed": False,
            "planner_action_authority": False,
            "physical_predictive_authority": False,
            "physical_trial_run": False,
        },
        "next_capture": {
            "requires_same_update_end_event": True,
            "required_clear_path_classes": [
                "hp_defeat",
                "main_ecl_completion",
                "offscreen_cleanup",
                "health_transition",
                "timeout_transition",
                "other",
            ],
            "requires_generation_or_one_update_root_identity": True,
            "requires_drop_birth_rng_join": True,
        },
    }
    report_payload = json.dumps(
        report,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report["report_digest"] = hashlib.sha256(report_payload).hexdigest()
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--route-id", type=int, default=2)
    parser.add_argument("--difficulty-index", type=int, default=3)
    parser.add_argument("--stage-route-index", type=int, default=5)
    parser.add_argument("--expected-trace-sha256")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = audit_enemy_presence_episodes(
        args.trace,
        expected_route_id=args.route_id,
        expected_difficulty_index=args.difficulty_index,
        expected_stage_route_index=args.stage_route_index,
        expected_trace_sha256=args.expected_trace_sha256,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
