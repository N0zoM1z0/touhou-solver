#!/usr/bin/env python3
"""Audit Route-2 normal SHT reachability and damage-path callbacks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from th08_sht import ShtFile, ShtLevel, ShtShotRecord, parse_sht


SCHEMA = "th08-route2-normal-shot-content-audit-v1"
EXPECTED_PRIMARY_SHA256 = (
    "4765744ab5bbf797746469d5a6afc6ec7d4b0371422b5aa5a2e54ae668c48885"
)
EXPECTED_SECONDARY_SHA256 = (
    "f7554b3a32e16da01de9432e22609482a1c98a33212eb904ad47789079abebd3"
)
EXPECTED_NORMAL_POWER_BOUNDS = (8, 24, 48, 80, 128, 999)
SUPPORTED_EMISSION_CALLBACKS = frozenset((0, 7))


def _split_normal_and_special_levels(
    sht: ShtFile,
) -> tuple[tuple[ShtLevel, ...], tuple[ShtLevel, ...]]:
    normal: list[ShtLevel] = []
    terminal_index = None
    for level in sht.levels:
        normal.append(level)
        if level.power_upper_bound >= 999:
            terminal_index = level.index
            break
    if terminal_index is None:
        raise ValueError(f"{sht.path.name} has no terminal normal SHT level")
    return tuple(normal), tuple(sht.levels[terminal_index + 1 :])


def _record_payload(
    record: ShtShotRecord,
    *,
    profile: str,
    level: int,
) -> dict[str, object]:
    return {
        "profile": profile,
        "level": level,
        "offset": record.offset,
        "shot_type": record.shot_type,
        "callback_0_index": record.callback_0_index,
        "callback_1_index": record.callback_1_index,
        "callback_2_index": record.callback_2_index,
        "callback_3_index": record.callback_3_index,
    }


def _profile_payload(
    sht: ShtFile,
    *,
    profile: str,
) -> dict[str, object]:
    normal_levels, special_levels = _split_normal_and_special_levels(sht)
    normal_records = [
        _record_payload(record, profile=profile, level=level.index)
        for level in normal_levels
        for record in level.shots
    ]
    damage_path_incompatible = [
        record
        for record in normal_records
        if (
            record["shot_type"] != 0
            or record["callback_1_index"] != 0
            or record["callback_3_index"] != 0
        )
    ]
    unsupported_emission = [
        record
        for record in normal_records
        if record["callback_0_index"] not in SUPPORTED_EMISSION_CALLBACKS
    ]
    special_records = [
        _record_payload(record, profile=profile, level=level.index)
        for level in special_levels
        for record in level.shots
    ]
    return {
        "profile": profile,
        "path": str(sht.path),
        "sha256": sht.sha256,
        "normal_level_indices": [level.index for level in normal_levels],
        "normal_power_upper_bounds": [
            level.power_upper_bound for level in normal_levels
        ],
        "normal_record_count": len(normal_records),
        "normal_shot_types": sorted(
            {int(record["shot_type"]) for record in normal_records}
        ),
        "normal_callback_indices": {
            f"callback_{index}": sorted(
                {
                    int(record[f"callback_{index}_index"])
                    for record in normal_records
                }
            )
            for index in range(4)
        },
        "damage_path_incompatible_normal_records": damage_path_incompatible,
        "unsupported_emission_normal_records": unsupported_emission,
        "special_level_indices": [level.index for level in special_levels],
        "special_record_count": len(special_records),
        "special_records": special_records,
        "normal_records": normal_records,
    }


def audit_route2_normal_shot_content(
    primary: ShtFile,
    secondary: ShtFile,
) -> dict[str, object]:
    if primary.sha256 != EXPECTED_PRIMARY_SHA256:
        raise ValueError(f"unexpected primary SHT SHA-256 {primary.sha256}")
    if secondary.sha256 != EXPECTED_SECONDARY_SHA256:
        raise ValueError(f"unexpected secondary SHT SHA-256 {secondary.sha256}")

    primary_payload = _profile_payload(
        primary,
        profile="unfocused_primary",
    )
    secondary_payload = _profile_payload(
        secondary,
        profile="focused_secondary",
    )
    primary_bounds = tuple(primary_payload["normal_power_upper_bounds"])
    secondary_bounds = tuple(secondary_payload["normal_power_upper_bounds"])
    if primary_bounds != EXPECTED_NORMAL_POWER_BOUNDS:
        raise ValueError(
            f"unexpected primary normal Power bounds {primary_bounds!r}"
        )
    if secondary_bounds != EXPECTED_NORMAL_POWER_BOUNDS:
        raise ValueError(
            f"unexpected secondary normal Power bounds {secondary_bounds!r}"
        )

    profiles = (primary_payload, secondary_payload)
    normal_record_count = sum(
        int(profile["normal_record_count"]) for profile in profiles
    )
    incompatible = [
        record
        for profile in profiles
        for record in profile["damage_path_incompatible_normal_records"]
    ]
    unsupported_emission = [
        record
        for profile in profiles
        for record in profile["unsupported_emission_normal_records"]
    ]
    content_closed = not incompatible and not unsupported_emission
    return {
        "schema": SCHEMA,
        "taskbook_card": "COMBAT-FAST-01",
        "inputs": {
            "primary_sht": {
                "path": str(primary.path),
                "sha256": primary.sha256,
            },
            "secondary_sht": {
                "path": str(secondary.path),
                "sha256": secondary.sha256,
            },
        },
        "native_selector": {
            "function": "player_emit_shot_level",
            "address": "0x00450F60",
            "focus_profile_selector": "player_focus_logic_byte_plus_0x03",
            "normal_selection": (
                "first level whose signed Power threshold exceeds "
                "truncated current Power"
            ),
            "normal_power_domain": [0, 128],
            "normal_power_upper_bounds": list(
                EXPECTED_NORMAL_POWER_BOUNDS
            ),
            "route2_special_override": (
                "secondary level 6 or 7 only while Bomb callback is active, "
                "callback index is odd, and Bomb timer is at least 60"
            ),
        },
        "profiles": list(profiles),
        "aggregate": {
            "normal_record_count": normal_record_count,
            "damage_path_incompatible_normal_record_count": len(incompatible),
            "unsupported_emission_normal_record_count": len(
                unsupported_emission
            ),
            "normal_damage_path_content_closed": content_closed,
            "runtime_slot_compatibility_criteria": {
                "shot_type": 0,
                "update_callback_pointer": 0,
                "hit_callback_pointer": 0,
            },
        },
        "result": {
            "status": (
                "route2_normal_damage_path_content_closed"
                if content_closed
                else "route2_normal_damage_path_content_open"
            ),
            "type45_reachable_from_normal_selector": bool(
                any(
                    int(record["shot_type"]) in (4, 5)
                    for record in incompatible
                )
            ),
            "nonzero_update_callback_reachable_from_normal_selector": bool(
                any(
                    int(record["callback_1_index"]) != 0
                    for record in incompatible
                )
            ),
            "nonzero_hit_callback_reachable_from_normal_selector": bool(
                any(
                    int(record["callback_3_index"]) != 0
                    for record in incompatible
                )
            ),
        },
        "authority": {
            "kind": "pinned_shipped_sht_and_revalidated_native_selector",
            "runtime_closure_requires": [
                "route_id_2",
                "zero_bomb_history_and_branch_actions",
                "root_active_slots_match_runtime_compatibility_criteria",
                "no_player_phase_2_in_root_or_branch",
            ],
            "generation_safe_damage_authority": False,
            "combat_benefit_authority": False,
            "live_action_authority": False,
            "physical_trial_run": False,
        },
    }


def build_report(
    *,
    primary_path: Path,
    secondary_path: Path,
) -> dict[str, object]:
    return audit_route2_normal_shot_content(
        parse_sht(primary_path),
        parse_sht(secondary_path),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(
        primary_path=args.primary_sht,
        secondary_path=args.secondary_sht,
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
