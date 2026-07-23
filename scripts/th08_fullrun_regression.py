#!/usr/bin/env python3
"""Validate retained TH08 live failure witnesses as executable regressions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


EXPECTED_SCHEMAS = {
    "th08-live-death-regressions-v1",
    "th08-practice-death-regressions-v1",
}
PRIMARY_CAUSES = {
    "observed_enemy_body_overlap",
    "observed_multiple_hazard_overlap",
    "observed_bullet_overlap",
    "observed_laser_overlap",
    "active_laser_without_observed_overlap",
    "modeled_committed_prefix_collision",
    "sensor_gap_or_unmodeled_hazard",
    "enemy_body_contact_candidate",
}


class CorpusError(ValueError):
    pass


@dataclass(frozen=True)
class CorpusSummary:
    run_id: str
    case_count: int
    stage_counts: dict[str, int]
    cause_counts: dict[str, int]
    factor_counts: dict[str, int]
    deathbomb_count: int
    exact_bullet_witnesses: int
    exact_laser_witnesses: int
    exact_enemy_body_witnesses: int


def _require(
    condition: bool,
    *,
    case_id: str,
    message: str,
) -> None:
    if not condition:
        raise CorpusError(f"{case_id}: {message}")


def validate_case(case: dict[str, object]) -> None:
    case_id = str(case.get("case_id", "<missing-case-id>"))
    cause = str(case.get("primary_cause_class"))
    _require(cause in PRIMARY_CAUSES, case_id=case_id, message=f"unknown cause {cause}")
    _require(
        int(case["frame"]) >= 0,
        case_id=case_id,
        message="negative frame",
    )
    _require(
        case.get("stage_label") is not None,
        case_id=case_id,
        message="missing stage label",
    )
    player = case["player"]
    _require(
        int(player["phase_at_action"]) == 2,
        case_id=case_id,
        message="retained witness is not a native phase-2 edge",
    )

    bullet = case.get("observed_bullet_contact_candidate")
    laser = case.get("observed_laser_contact_candidate")
    enemy = case.get("observed_enemy_body_contact_candidate")
    overlap_count = sum(
        isinstance(witness, dict) for witness in (bullet, laser, enemy)
    )
    if cause == "observed_multiple_hazard_overlap":
        _require(
            overlap_count >= 2,
            case_id=case_id,
            message="multiple-overlap cause has fewer than two witnesses",
        )
    elif cause == "observed_enemy_body_overlap":
        _require(
            isinstance(enemy, dict)
            and float(enemy["aabb_clearance"]) <= 0.0,
            case_id=case_id,
            message="enemy-body cause lacks an overlapping AABB witness",
        )
    elif cause == "observed_bullet_overlap":
        _require(
            isinstance(bullet, dict)
            and float(bullet["aabb_clearance"]) <= 0.0,
            case_id=case_id,
            message="bullet-overlap cause lacks an overlapping AABB witness",
        )
        _require(
            laser is None and enemy is None,
            case_id=case_id,
            message="another exact witness must not be hidden by bullet cause",
        )
    elif cause == "observed_laser_overlap":
        _require(
            isinstance(laser, dict) and float(laser["clearance"]) <= 0.0,
            case_id=case_id,
            message="laser-overlap cause lacks a finite-segment witness",
        )
    elif cause == "active_laser_without_observed_overlap":
        _require(
            int(case["active_lasers"]) > 0
            and laser is None
            and float(case["pipeline_clearance_at_hit"]) > 0.0,
            case_id=case_id,
            message=(
                "active-laser gap must have no overlapping segment or "
                "committed-prefix collision"
            ),
        )
    elif cause == "modeled_committed_prefix_collision":
        _require(
            float(case["pipeline_clearance_at_hit"]) <= 0.0,
            case_id=case_id,
            message="committed-prefix cause has positive pipeline clearance",
        )
        _require(
            bullet is None and laser is None and enemy is None,
            case_id=case_id,
            message="observed contact must outrank modeled prefix collision",
        )
    elif cause == "enemy_body_contact_candidate":
        _require(
            isinstance(case.get("enemy_body_evidence"), dict),
            case_id=case_id,
            message="enemy-body candidate lacks static evidence",
        )
        _require(
            int(case["active_bullets"]) == 0
            and int(case["active_lasers"]) == 0
            and float(case["pipeline_clearance_at_hit"]) > 0.0
            and overlap_count == 0,
            case_id=case_id,
            message="enemy-body candidate contains a higher-priority witness",
        )
    else:
        _require(
            float(case["pipeline_clearance_at_hit"]) > 0.0,
            case_id=case_id,
            message="sensor-gap cause has nonpositive modeled clearance",
        )
        _require(
            bullet is None
            and laser is None
            and enemy is None
            and int(case["active_lasers"]) == 0,
            case_id=case_id,
            message="sensor-gap cause contains an observed higher-priority witness",
        )

    factors = set(str(value) for value in case["contributing_factors"])
    slack = case.get("minimum_corridor_slack_240f")
    _require(
        ("corridor_deadline_miss" in factors)
        == (slack is not None and float(slack) < 0.0),
        case_id=case_id,
        message="corridor factor disagrees with retained slack",
    )
    _require(
        ("action_lag_over_model" in factors) == (int(case["action_lag"]) > 3),
        case_id=case_id,
        message="action-lag factor disagrees with retained lag",
    )
    _require(
        ("pool_density_over_1000" in factors)
        == (int(case["active_bullets"]) >= 1000),
        case_id=case_id,
        message="density factor disagrees with active bullet count",
    )
    _require(
        ("fast_mode" in factors) == ("_fast" in str(case["action"])),
        case_id=case_id,
        message="fast-mode factor disagrees with action",
    )
    player_x = float(player["x"])
    player_y = float(player["y"])
    _require(
        ("playfield_boundary" in factors)
        == (
            player_y >= 428.0
            or player_x <= 12.0
            or player_x >= 372.0
        ),
        case_id=case_id,
        message="boundary factor disagrees with player position",
    )
    _require(
        bool(case["deathbomb_requested"])
        == ("+deathbomb" in str(case["action"])),
        case_id=case_id,
        message="deathbomb flag disagrees with action",
    )
    _require(
        float(case["observed_bomb_cost"]) >= 0.0,
        case_id=case_id,
        message="negative observed Bomb cost",
    )
    _require(
        isinstance(case.get("spell_attribution"), dict)
        and bool(case["spell_attribution"].get("status")),
        case_id=case_id,
        message="spell attribution status is not explicit",
    )


def load_and_validate(path: Path) -> CorpusSummary:
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = payload.get("schema")
    if schema not in EXPECTED_SCHEMAS:
        raise CorpusError(f"{path}: unexpected schema {payload.get('schema')!r}")
    if schema == "th08-practice-death-regressions-v1":
        verification = payload.get("no_bomb_verification")
        if not isinstance(verification, dict) or not verification.get("passed"):
            raise CorpusError(f"{path}: practice corpus did not pass no-Bomb gate")
        for key in (
            "mask_violation_frames",
            "bomb_flag_violation_frames",
            "bomb_action_violation_frames",
        ):
            if verification.get(key) != []:
                raise CorpusError(f"{path}: nonempty no-Bomb violation {key}")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise CorpusError(f"{path}: cases must be a list")
    if int(payload.get("case_count", -1)) != len(cases):
        raise CorpusError(f"{path}: case_count disagrees with cases")

    seen = set()
    stage_counts: Counter[str] = Counter()
    cause_counts: Counter[str] = Counter()
    factor_counts: Counter[str] = Counter()
    deathbomb_count = 0
    bullet_witnesses = 0
    laser_witnesses = 0
    enemy_body_witnesses = 0
    for case in cases:
        if not isinstance(case, dict):
            raise CorpusError(f"{path}: non-object case")
        case_id = str(case.get("case_id"))
        if case_id in seen:
            raise CorpusError(f"{path}: duplicate case ID {case_id}")
        seen.add(case_id)
        validate_case(case)
        if schema == "th08-practice-death-regressions-v1":
            _require(
                bool(case.get("bomb_input_verified_absent"))
                and not int(case["mask"]) & 0x02
                and not bool(case["deathbomb_requested"]),
                case_id=case_id,
                message="practice case violates hard no-Bomb policy",
            )
        stage_counts[str(case["stage_label"])] += 1
        cause_counts[str(case["primary_cause_class"])] += 1
        factor_counts.update(
            str(value) for value in case["contributing_factors"]
        )
        deathbomb_count += bool(case["deathbomb_requested"])
        bullet_witnesses += case["observed_bullet_contact_candidate"] is not None
        laser_witnesses += case["observed_laser_contact_candidate"] is not None
        enemy_body_witnesses += (
            case.get("observed_enemy_body_contact_candidate") is not None
        )

    return CorpusSummary(
        run_id=str(payload["run_id"]),
        case_count=len(cases),
        stage_counts=dict(stage_counts),
        cause_counts=dict(cause_counts),
        factor_counts=dict(factor_counts),
        deathbomb_count=deathbomb_count,
        exact_bullet_witnesses=bullet_witnesses,
        exact_laser_witnesses=laser_witnesses,
        exact_enemy_body_witnesses=enemy_body_witnesses,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args(argv)
    summary = load_and_validate(args.input)
    print(json.dumps(summary.__dict__, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
