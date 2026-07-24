#!/usr/bin/env python3
"""Audit whether an always-firing TH08 trace actually tracks the spell owner.

This is deliberately a shadow diagnostic.  Horizontal player/boss alignment
is only a coarse shot-coverage proxy; it is not a damage model and must not be
used as live steering authority without native HP-delta parity.
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
        "schema": "th08-attack-alignment-audit-v1",
        "role": "shadow_only",
        "proxy": (
            "absolute player-x minus spell-owner-x during native player phase 3"
        ),
        "warning": (
            "alignment is not observed damage; HP delta, damageability, shot "
            "cadence, option geometry, and phase timeout are not traced"
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
