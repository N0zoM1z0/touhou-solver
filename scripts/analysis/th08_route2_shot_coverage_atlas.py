#!/usr/bin/env python3
"""Build a deterministic Route-2 normal-shot static coverage atlas."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from th08_route2_shot_coverage import (
    HorizontalInterval,
    Route2ShotProfile,
    normal_level_cadence_summary,
    normal_level_horizontal_coverage,
)
from th08_sht import ShtFile, ShtLevel, parse_sht


SCHEMA = "th08-route2-normal-shot-coverage-atlas-v1"
EXPECTED_PRIMARY_SHA256 = (
    "4765744ab5bbf797746469d5a6afc6ec7d4b0371422b5aa5a2e54ae668c48885"
)
EXPECTED_SECONDARY_SHA256 = (
    "f7554b3a32e16da01de9432e22609482a1c98a33212eb904ad47789079abebd3"
)
TARGET_RISES = (64.0, 128.0, 192.0)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normal_levels(sht: ShtFile) -> tuple[ShtLevel, ...]:
    levels: list[ShtLevel] = []
    for level in sht.levels:
        levels.append(level)
        if level.power_upper_bound >= 999:
            break
    return tuple(levels)


def _interval_payload(interval: HorizontalInterval) -> list[float]:
    return [interval.lower, interval.upper]


def _coverage_payload(
    level: ShtLevel,
    *,
    profile: Route2ShotProfile,
    target_rise: float,
) -> dict[str, object]:
    intervals = normal_level_horizontal_coverage(
        level,
        profile=profile,
        target_rise=target_rise,
    )
    union_width = sum(interval.width for interval in intervals)
    return {
        "target_rise": target_rise,
        "merged_enemy_point_center_x_intervals": [
            _interval_payload(interval) for interval in intervals
        ],
        "interval_count": len(intervals),
        "union_width": union_width,
        "span_width": (
            intervals[-1].upper - intervals[0].lower if intervals else 0.0
        ),
    }


def _profile_payload(
    level: ShtLevel,
    *,
    profile: Route2ShotProfile,
) -> dict[str, object]:
    cadence = normal_level_cadence_summary(level)
    return {
        "level": level.index,
        "record_count": len(level.shots),
        "empty_pool_timer_cycle": {
            "emissions": cadence.emissions_per_cycle,
            "nominal_base_damage": cadence.base_damage_per_cycle,
            "callback_rng_u16_calls": (
                cadence.callback_rng_u16_calls_per_cycle
            ),
            "emissions_by_cadence": list(cadence.emissions_by_cadence),
            "nominal_base_damage_by_cadence": list(
                cadence.base_damage_by_cadence
            ),
        },
        "coverage": [
            _coverage_payload(
                level,
                profile=profile,
                target_rise=target_rise,
            )
            for target_rise in TARGET_RISES
        ],
    }


def build_report(
    *,
    primary_path: Path,
    secondary_path: Path,
) -> dict[str, object]:
    primary_sha256 = _sha256(primary_path)
    secondary_sha256 = _sha256(secondary_path)
    if primary_sha256 != EXPECTED_PRIMARY_SHA256:
        raise ValueError(f"unexpected primary SHT SHA-256 {primary_sha256}")
    if secondary_sha256 != EXPECTED_SECONDARY_SHA256:
        raise ValueError(f"unexpected secondary SHT SHA-256 {secondary_sha256}")

    primary_levels = _normal_levels(parse_sht(primary_path))
    secondary_levels = _normal_levels(parse_sht(secondary_path))
    primary_bounds = tuple(level.power_upper_bound for level in primary_levels)
    secondary_bounds = tuple(
        level.power_upper_bound for level in secondary_levels
    )
    if primary_bounds != secondary_bounds:
        raise ValueError("primary and secondary normal Power partitions differ")

    rows: list[dict[str, object]] = []
    lower_bound = 0
    wider_primary = 0
    wider_secondary = 0
    equal_width = 0
    for primary, secondary in zip(
        primary_levels,
        secondary_levels,
        strict=True,
    ):
        primary_payload = _profile_payload(
            primary,
            profile="unfocused_primary",
        )
        secondary_payload = _profile_payload(
            secondary,
            profile="focused_secondary",
        )
        comparisons: list[dict[str, object]] = []
        for primary_coverage, secondary_coverage in zip(
            primary_payload["coverage"],
            secondary_payload["coverage"],
            strict=True,
        ):
            primary_width = float(primary_coverage["union_width"])
            secondary_width = float(secondary_coverage["union_width"])
            if primary_width > secondary_width:
                relation = "unfocused_primary_wider"
                wider_primary += 1
            elif secondary_width > primary_width:
                relation = "focused_outer_envelope_wider"
                wider_secondary += 1
            else:
                relation = "equal"
                equal_width += 1
            comparisons.append(
                {
                    "target_rise": primary_coverage["target_rise"],
                    "union_width_relation": relation,
                    "unfocused_minus_focused_outer_envelope": (
                        primary_width - secondary_width
                    ),
                }
            )
        rows.append(
            {
                "power_interval": {
                    "lower_inclusive": lower_bound,
                    "upper_exclusive": primary.power_upper_bound,
                },
                "unfocused_primary": primary_payload,
                "focused_secondary": secondary_payload,
                "comparison": comparisons,
            }
        )
        lower_bound = primary.power_upper_bound

    return {
        "schema": SCHEMA,
        "authority": {
            "kind": "offline_shipped_data_static_geometry_audit",
            "unfocused_callback0_geometry": (
                "revalidated_scalar_projection_no_native_bit_differential"
            ),
            "focused_callback7_geometry": (
                "continuous_conservative_outer_envelope_unknown_direction"
            ),
            "focused_envelope_damage_direction": "optimistic",
            "planner_action_authority": False,
            "physical_predictive_authority": False,
            "physical_trial_run": False,
        },
        "inputs": {
            "primary_sht": str(primary_path),
            "primary_sht_sha256": primary_sha256,
            "secondary_sht": str(secondary_path),
            "secondary_sht_sha256": secondary_sha256,
            "target_rises_from_player": list(TARGET_RISES),
            "target_enemy_size": [0.0, 0.0],
            "player_shot_pool_assumption": "empty_at_each_cadence_row",
            "focused_option_assumption": "steady_active_orbit",
        },
        "native_semantics": {
            "player_shot_initialize": "0x0044FB70",
            "player_emit_shot_level": "0x00450F60",
            "random_spread_callback": "0x004501B0",
            "player_compute_damage_to_enemy": "0x00451670",
            "inclusive_center_size_aabb": "0x00451740",
            "ordinary_shot_frame_damage_cap": 50,
        },
        "power_profiles": rows,
        "aggregate_static_width_relations": {
            "unfocused_primary_wider": wider_primary,
            "focused_outer_envelope_wider": wider_secondary,
            "equal": equal_width,
            "comparison_count": wider_primary + wider_secondary + equal_width,
        },
        "interpretation": {
            "supported": (
                "Focus changes cadence, nominal base-damage opportunity, "
                "horizontal support, and shared RNG consumption at every "
                "normal Power partition."
            ),
            "falsified_coarse_rule": (
                "releasing Focus is not uniformly wider across Power and "
                "target height, even before survival and target motion."
            ),
            "not_supported": (
                "no static width or nominal-damage row proves a kill, "
                "prevented emission, phase shortening, or safe Focus switch"
            ),
        },
        "promotion": {
            "combat_fast_01_status": "static_action_conditioned_foundation",
            "live_focus_ranking_enabled": False,
            "next_gate": (
                "join immutable native roots to enemy generation, HP delta, "
                "shot timer/pool, target motion, and exact viable actions"
            ),
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
