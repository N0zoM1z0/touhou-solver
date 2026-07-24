#!/usr/bin/env python3
"""Audit whether TH08 safe actions leave measurable boss damage on the table.

Horizontal alignment remains a coarse shot-coverage proxy.  New traces add
native boss HP deltas, damage gates, phase timers, and the action the guarded
damage objective would select inside the fresh survival set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


SHOT = 0x01
ALIGNMENT_THRESHOLDS = (16.0, 32.0, 48.0, 64.0)


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = fraction * (len(ordered) - 1)
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


@dataclass
class PhaseAudit:
    spell_id: int
    spell_name: str
    first_frame: int
    last_frame: int
    decision_count: int = 0
    hit_count: int = 0
    normal_player_phase_count: int = 0
    guard_count: int = 0
    normal_guard_count: int = 0
    output_shot_count: int = 0
    active_shot_count: int = 0
    horizontal_errors: list[float] = field(default_factory=list)
    normal_horizontal_errors: list[float] = field(default_factory=list)
    power_samples: list[float] = field(default_factory=list)
    boss_sample_count: int = 0
    stable_boss_sample_count: int = 0
    damageable_boss_sample_count: int = 0
    comparable_damage_sample_count: int = 0
    observed_health_delta: int = 0
    observed_damage_frames: int = 0
    native_frame_damage: list[int] = field(default_factory=list)
    boss_health_samples: list[int] = field(default_factory=list)
    boss_phase_end_samples: list[int] = field(default_factory=list)
    boss_timer_samples: list[float] = field(default_factory=list)
    boss_timeout_samples: list[int] = field(default_factory=list)
    damage_objective_available_count: int = 0
    damage_shadow_change_count: int = 0
    damage_live_change_count: int = 0
    alignment_cost_improvements: list[float] = field(default_factory=list)

    def add(self, row: dict[str, object]) -> None:
        frame = int(row["frame"])
        self.first_frame = min(self.first_frame, frame)
        self.last_frame = max(self.last_frame, frame)
        self.decision_count += 1
        self.hit_count += int(bool(row.get("hit_started")))
        normal_player_phase = (
            isinstance(row.get("player"), dict)
            and int(row["player"].get("phase", -1)) == 3
        )
        self.normal_player_phase_count += int(normal_player_phase)
        self.output_shot_count += int(int(row.get("mask", 0)) & SHOT != 0)
        input_snapshot = row.get("input_snapshot")
        if isinstance(input_snapshot, dict):
            self.active_shot_count += int(
                int(input_snapshot.get("current", 0)) & SHOT != 0
            )
        resources = row.get("resources")
        if isinstance(resources, dict) and resources.get("power") is not None:
            self.power_samples.append(float(resources["power"]))
        boss = row.get("boss_phase")
        if isinstance(boss, dict) and boss.get("pointer") is not None:
            self.boss_sample_count += 1
            self.stable_boss_sample_count += int(bool(boss.get("stable")))
            self.native_frame_damage.append(int(boss.get("frame_damage", 0)))
            if boss.get("current_health") is not None:
                self.boss_health_samples.append(
                    int(boss["current_health"])
                )
            if boss.get("phase_end_health") is not None:
                self.boss_phase_end_samples.append(
                    int(boss["phase_end_health"])
                )
            if boss.get("elapsed_frames") is not None:
                self.boss_timer_samples.append(
                    float(boss["elapsed_frames"])
                )
            if boss.get("timeout_frame") is not None:
                self.boss_timeout_samples.append(
                    int(boss["timeout_frame"])
                )
        progress = row.get("boss_phase_progress")
        if isinstance(progress, dict):
            self.damageable_boss_sample_count += int(
                bool(progress.get("damageable"))
            )
            if (
                progress.get("status") == "comparable"
                and progress.get("health_delta") is not None
                and progress.get("frame_delta") is not None
            ):
                self.comparable_damage_sample_count += 1
                self.observed_health_delta += int(progress["health_delta"])
                self.observed_damage_frames += int(progress["frame_delta"])
        objective = row.get("damage_objective")
        if isinstance(objective, dict) and bool(objective.get("available")):
            self.damage_objective_available_count += 1
            baseline = objective.get("baseline_action")
            shadow = objective.get("shadow_action")
            self.damage_shadow_change_count += int(
                baseline is not None and shadow != baseline
            )
            self.damage_live_change_count += int(
                bool(objective.get("live_selected"))
            )
            current_cost = objective.get("current_alignment_cost")
            shadow_cost = objective.get("shadow_alignment_cost")
            if current_cost is not None and shadow_cost is not None:
                self.alignment_cost_improvements.append(
                    float(current_cost) - float(shadow_cost)
                )
        guard = row.get("spell_enemy_body_guard")
        if not isinstance(guard, dict):
            return
        body = guard.get("body")
        player = row.get("player")
        if (
            not isinstance(body, list)
            or len(body) < 2
            or not isinstance(player, dict)
            or player.get("x") is None
        ):
            return
        error = abs(float(player["x"]) - float(body[1]))
        self.guard_count += 1
        self.horizontal_errors.append(error)
        if normal_player_phase:
            self.normal_guard_count += 1
            self.normal_horizontal_errors.append(error)

    def report(self) -> dict[str, object]:
        normal = self.normal_horizontal_errors
        return {
            "spell_id": self.spell_id,
            "spell_name": self.spell_name,
            "first_frame": self.first_frame,
            "last_frame": self.last_frame,
            "observed_frame_span": self.last_frame - self.first_frame,
            "decision_count": self.decision_count,
            "hit_count": self.hit_count,
            "normal_player_phase_count": self.normal_player_phase_count,
            "spell_owner_guard_count": self.guard_count,
            "normal_spell_owner_guard_count": self.normal_guard_count,
            "output_shot_fraction": (
                self.output_shot_count / self.decision_count
                if self.decision_count
                else None
            ),
            "active_shot_fraction": (
                self.active_shot_count / self.decision_count
                if self.decision_count
                else None
            ),
            "normal_horizontal_alignment_error": {
                "median": _percentile(normal, 0.5),
                "p95": _percentile(normal, 0.95),
                "maximum": max(normal) if normal else None,
            },
            "normal_alignment_fraction": {
                str(int(threshold)): (
                    sum(error <= threshold for error in normal) / len(normal)
                    if normal
                    else None
                )
                for threshold in ALIGNMENT_THRESHOLDS
            },
            "power": {
                "first": (
                    self.power_samples[0] if self.power_samples else None
                ),
                "last": (
                    self.power_samples[-1] if self.power_samples else None
                ),
                "median": (
                    statistics.median(self.power_samples)
                    if self.power_samples
                    else None
                ),
            },
            "native_boss_telemetry": {
                "sample_count": self.boss_sample_count,
                "stable_fraction": (
                    self.stable_boss_sample_count / self.boss_sample_count
                    if self.boss_sample_count
                    else None
                ),
                "damageable_fraction": (
                    self.damageable_boss_sample_count / self.boss_sample_count
                    if self.boss_sample_count
                    else None
                ),
                "comparable_damage_sample_count": (
                    self.comparable_damage_sample_count
                ),
                "observed_health_delta": self.observed_health_delta,
                "observed_damage_frames": self.observed_damage_frames,
                "observed_damage_per_frame": (
                    self.observed_health_delta / self.observed_damage_frames
                    if self.observed_damage_frames
                    else None
                ),
                "sampled_native_frame_damage_sum": sum(
                    self.native_frame_damage
                ),
                "current_health": {
                    "first": (
                        self.boss_health_samples[0]
                        if self.boss_health_samples
                        else None
                    ),
                    "last": (
                        self.boss_health_samples[-1]
                        if self.boss_health_samples
                        else None
                    ),
                    "minimum": (
                        min(self.boss_health_samples)
                        if self.boss_health_samples
                        else None
                    ),
                },
                "phase_end_health": (
                    self.boss_phase_end_samples[-1]
                    if self.boss_phase_end_samples
                    else None
                ),
                "timer": {
                    "first": (
                        self.boss_timer_samples[0]
                        if self.boss_timer_samples
                        else None
                    ),
                    "last": (
                        self.boss_timer_samples[-1]
                        if self.boss_timer_samples
                        else None
                    ),
                    "timeout": (
                        self.boss_timeout_samples[-1]
                        if self.boss_timeout_samples
                        else None
                    ),
                },
            },
            "safe_damage_objective": {
                "available_count": self.damage_objective_available_count,
                "shadow_action_change_count": (
                    self.damage_shadow_change_count
                ),
                "live_action_change_count": self.damage_live_change_count,
                "alignment_cost_improvement": {
                    "median": _percentile(
                        self.alignment_cost_improvements,
                        0.5,
                    ),
                    "p95": _percentile(
                        self.alignment_cost_improvements,
                        0.95,
                    ),
                    "maximum": (
                        max(self.alignment_cost_improvements)
                        if self.alignment_cost_improvements
                        else None
                    ),
                },
            },
        }


def audit_trace(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    decision_count = 0
    output_shot_count = 0
    active_shot_count = 0
    phases: dict[int, PhaseAudit] = {}
    with path.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if not isinstance(row, dict) or row.get("kind") != "decision":
                continue
            decision_count += 1
            output_shot_count += int(int(row.get("mask", 0)) & SHOT != 0)
            input_snapshot = row.get("input_snapshot")
            if isinstance(input_snapshot, dict):
                active_shot_count += int(
                    int(input_snapshot.get("current", 0)) & SHOT != 0
                )
            spell = row.get("spell")
            if not isinstance(spell, dict) or not bool(spell.get("active")):
                continue
            spell_id = int(spell["spell_id"])
            phase = phases.get(spell_id)
            if phase is None:
                phase = PhaseAudit(
                    spell_id=spell_id,
                    spell_name=str(spell.get("name", "")),
                    first_frame=int(row["frame"]),
                    last_frame=int(row["frame"]),
                )
                phases[spell_id] = phase
            phase.add(row)
    return {
        "trace": str(path),
        "sha256": digest.hexdigest(),
        "decision_count": decision_count,
        "output_shot_fraction": (
            output_shot_count / decision_count if decision_count else None
        ),
        "active_shot_fraction": (
            active_shot_count / decision_count if decision_count else None
        ),
        "phases": [
            phases[spell_id].report() for spell_id in sorted(phases)
        ],
    }


def build_report(paths: Iterable[Path]) -> dict[str, object]:
    return {
        "schema": "th08-attack-alignment-audit-v2",
        "role": "shadow_with_retained_rejected_live_experiment",
        "proxy": (
            "absolute player-x minus spell-owner-x during native player phase 3"
        ),
        "warning": (
            "native HP delta is observed damage, but horizontal alignment is "
            "still only a coverage proxy; shot/option geometry is not modeled"
        ),
        "alignment_thresholds": list(ALIGNMENT_THRESHOLDS),
        "traces": [audit_trace(path) for path in paths],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.traces)
    encoded = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.output is None:
        print(encoded, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
