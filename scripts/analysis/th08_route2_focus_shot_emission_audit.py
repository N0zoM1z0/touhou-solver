#!/usr/bin/env python3
"""Build the offline route-2 Focus/Shot emission audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from th08_player_shot_model import (
    PLAYER_SHOT_POOL_SIZE,
    emit_player_shot_level,
    select_player_shot_level,
)
from th08_player_shot_runtime import PLAYER_SHOT_EMISSION_STATE_SCHEMA
from th08_rng import Th08Rng
from th08_sht import ShtFile, ShtLevel, parse_sht


SCHEMA = "th08-route2-focus-shot-emission-audit-v1"
EXPECTED_H1_SCHEMA = "th08-native-h1-ecl-source-differential-v1"
EXPECTED_PRIMARY_SHA256 = (
    "4765744ab5bbf797746469d5a6afc6ec7d4b0371422b5aa5a2e54ae668c48885"
)
EXPECTED_SECONDARY_SHA256 = (
    "f7554b3a32e16da01de9432e22609482a1c98a33212eb904ad47789079abebd3"
)
ROOT_MANAGER_FRAME = 2129
ROOT_POWER = 128.0
ROOT_FOCUS_LOGIC = 1
HOSTILE_BIRTH_U16_CALLS = 4


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _ranges(values: Iterable[int]) -> list[list[int]]:
    ordered = sorted(set(values))
    if not ordered:
        return []
    result: list[list[int]] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value != previous + 1:
            result.append([start, previous])
            start = value
        previous = value
    result.append([start, previous])
    return result


def _emit(
    level: ShtLevel,
    *,
    cadence: int,
    free_slots: int,
    rng_state: int,
    rng_calls: int,
) -> dict[str, object]:
    rng = Th08Rng(rng_state, rng_calls)
    result = emit_player_shot_level(
        level,
        cadence_frame=cadence,
        player_position=(192.0, 432.0),
        option_positions=((160.0, 416.0),) * 4,
        free_slots=free_slots,
        rng=rng,
    )
    return {
        "cadence": cadence,
        "free_slots": free_slots,
        "record_offsets": [shot.record_offset for shot in result.shots],
        "source_indices": [shot.source_index for shot in result.shots],
        "emitted_shot_count": result.pool_slots_used,
        "base_damage_sum": sum(shot.damage for shot in result.shots),
        "rng_u16_calls": result.rng_calls_consumed,
        "rng_state_after": rng.state,
        "records_evaluated": result.records_evaluated,
        "stopped_for_pool_capacity": result.stopped_for_pool_capacity,
    }


def _normal_profile(sht: ShtFile) -> dict[str, object]:
    levels: list[dict[str, object]] = []
    for level in sht.levels:
        if level.power_upper_bound >= 999:
            levels.append(
                {
                    "level": level.index,
                    "power_upper_bound": level.power_upper_bound,
                    "record_count": len(level.shots),
                    "callback_0_counts": dict(
                        sorted(
                            Counter(
                                record.callback_0_index for record in level.shots
                            ).items()
                        )
                    ),
                }
            )
            break
        levels.append(
            {
                "level": level.index,
                "power_upper_bound": level.power_upper_bound,
                "record_count": len(level.shots),
                "callback_0_counts": dict(
                    sorted(
                        Counter(
                            record.callback_0_index for record in level.shots
                        ).items()
                    )
                ),
            }
        )
    return {
        "path": str(sht.path),
        "sha256": sht.sha256,
        "normal_levels": levels,
    }


def build_report(
    *,
    primary_path: Path,
    secondary_path: Path,
    h1_report_path: Path,
) -> dict[str, object]:
    primary = parse_sht(primary_path)
    secondary = parse_sht(secondary_path)
    if primary.sha256 != EXPECTED_PRIMARY_SHA256:
        raise ValueError("unexpected route-2 primary SHT identity")
    if secondary.sha256 != EXPECTED_SECONDARY_SHA256:
        raise ValueError("unexpected route-2 secondary SHT identity")

    h1_bytes = h1_report_path.read_bytes()
    h1 = json.loads(h1_bytes)
    if h1.get("schema") != EXPECTED_H1_SCHEMA:
        raise ValueError("unexpected H1 differential schema")
    acceptance = h1.get("native_acceptance")
    alignment = h1.get("retrospective_rng_alignment")
    endpoint = h1.get("native_endpoint")
    if not isinstance(acceptance, dict):
        raise ValueError("H1 report omits native acceptance")
    if not isinstance(alignment, dict):
        raise ValueError("H1 report omits RNG alignment")
    if not isinstance(endpoint, dict):
        raise ValueError("H1 report omits endpoint")
    if _integer(acceptance.get("manager_frame"), "H1 manager frame") != (
        ROOT_MANAGER_FRAME
    ):
        raise ValueError("H1 report has the wrong root")
    births = endpoint.get("births")
    if not isinstance(births, list):
        raise ValueError("H1 endpoint omits births")
    total_u16_calls = _integer(
        alignment.get("u16_calls_consumed"),
        "H1 consumed u16 calls",
    )
    attributed_hostile_u16_calls = len(births) * HOSTILE_BIRTH_U16_CALLS
    prefix_u16_calls = total_u16_calls - attributed_hostile_u16_calls
    if prefix_u16_calls < 0:
        raise ValueError("H1 hostile attribution exceeds total RNG consumption")

    selection = select_player_shot_level(
        primary,
        secondary,
        focus_logic_value=ROOT_FOCUS_LOGIC,
        power=ROOT_POWER,
    )
    root_rng_state = _integer(alignment.get("root_state"), "H1 root RNG state")
    root_rng_calls = _integer(alignment.get("root_calls"), "H1 root RNG calls")

    full_capacity = [
        _emit(
            selection.level,
            cadence=cadence,
            free_slots=PLAYER_SHOT_POOL_SIZE,
            rng_state=root_rng_state,
            rng_calls=root_rng_calls,
        )
        for cadence in range(20)
    ]
    compatibility: list[dict[str, object]] = []
    for cadence in range(20):
        matching_capacities = [
            free_slots
            for free_slots in range(PLAYER_SHOT_POOL_SIZE + 1)
            if _emit(
                selection.level,
                cadence=cadence,
                free_slots=free_slots,
                rng_state=root_rng_state,
                rng_calls=root_rng_calls,
            )["rng_u16_calls"]
            == prefix_u16_calls
        ]
        if matching_capacities:
            compatibility.append(
                {
                    "cadence": cadence,
                    "free_slot_ranges": _ranges(matching_capacities),
                    "full_capacity": full_capacity[cadence],
                }
            )

    unfocused_selection = select_player_shot_level(
        primary,
        secondary,
        focus_logic_value=0,
        power=ROOT_POWER,
    )
    unfocused_full_capacity = [
        _emit(
            unfocused_selection.level,
            cadence=cadence,
            free_slots=PLAYER_SHOT_POOL_SIZE,
            rng_state=root_rng_state,
            rng_calls=root_rng_calls,
        )
        for cadence in range(20)
    ]

    return {
        "schema": SCHEMA,
        "authority": {
            "kind": "offline_static_data_plus_retained_native_compatibility_audit",
            "planner_action_authority": False,
            "physical_predictive_authority": False,
            "physical_trial_run": False,
            "random_spread_geometry_authority": "unknown_direction",
        },
        "inputs": {
            "primary_sht": _normal_profile(primary),
            "secondary_sht": _normal_profile(secondary),
            "h1_report_path": str(h1_report_path),
            "h1_report_sha256": hashlib.sha256(h1_bytes).hexdigest(),
        },
        "revalidated_native_semantics": {
            "player_emit_shot_level": "0x00450F60",
            "player_update_shot_cadence": "0x00451500",
            "random_spread_callback": "0x004501B0",
            "rng_next_signed_unit": "0x0043ED80",
            "shot_pool_slots": PLAYER_SHOT_POOL_SIZE,
            "supported_callback_0_indices": [0, 7],
            "capture_schema_for_future_roots": (
                PLAYER_SHOT_EMISSION_STATE_SCHEMA
            ),
        },
        "root2129": {
            "observed": {
                "manager_frame": ROOT_MANAGER_FRAME,
                "input_current": 0x05,
                "focus_logic": ROOT_FOCUS_LOGIC,
                "power": ROOT_POWER,
                "rng_state": root_rng_state,
                "rng_calls": root_rng_calls,
                "endpoint_total_u16_calls": total_u16_calls,
                "hostile_birth_count": len(births),
                "already_attributed_hostile_u16_calls": (
                    attributed_hostile_u16_calls
                ),
                "pre_hostile_prefix_u16_calls": prefix_u16_calls,
                "shot_timer_captured": False,
                "shot_pool_captured": False,
            },
            "selected_profile": {
                "profile": selection.profile,
                "sht_sha256": selection.sht_sha256,
                "native_power": selection.native_power,
                "level": selection.level.index,
            },
            "compatible_player_shot_states": compatibility,
            "classification": (
                "compatible_player_shot_prefix_not_unique_causal_proof"
            ),
            "inference": (
                "a due focused level-5 callback-7 option pair consumes the "
                "observed four-u16 prefix before priority-11 enemy work"
            ),
            "remaining_unknown": (
                "hostile birth slot 1220 still lacks an identified producer"
            ),
        },
        "focus_profile_comparison_at_power128": {
            "unfocused_primary": {
                "level": unfocused_selection.level.index,
                "cadence_rows": unfocused_full_capacity,
            },
            "focused_secondary": {
                "level": selection.level.index,
                "cadence_rows": full_capacity,
            },
            "conclusion": (
                "Focus changes same-frame shot geometry and may change the "
                "gameplay RNG inherited by later enemy/ECL work"
            ),
        },
        "promotion": {
            "combat_fast_01_status": "semantic_foundation_only",
            "next_gate": (
                "capture a v4 identical-root ordinary-enemy corpus with shot "
                "timer/pool state, then compare focused, unfocused, and causal "
                "refocus schedules inside the unchanged survival-feasible set"
            ),
            "live_focus_ranking_enabled": False,
            "live_shot_ranking_enabled": False,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--primary-sht",
        type=Path,
        default=Path("artifacts/decoded/ply02a.sht"),
    )
    parser.add_argument(
        "--secondary-sht",
        type=Path,
        default=Path("artifacts/decoded/ply02as.sht"),
    )
    parser.add_argument(
        "--h1-report",
        type=Path,
        default=Path(
            "artifacts/runtime_reports/"
            "th08_native_h1_ecl_source_differential_root2129_20260730.json"
        ),
    )
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(
        primary_path=args.primary_sht,
        secondary_path=args.secondary_sht,
        h1_report_path=args.h1_report,
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
