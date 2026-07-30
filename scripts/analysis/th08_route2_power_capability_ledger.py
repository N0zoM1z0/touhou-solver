#!/usr/bin/env python3
"""Build the static Route-2 pickup-to-shot-capability ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from th08_item_model import (
    ITEM_FULL_POWER,
    ITEM_POWER_LARGE,
    ITEM_POWER_OVERFLOW,
    ITEM_POWER_SMALL,
    POWER_LEVEL_THRESHOLDS,
    ItemResources,
    ItemState,
    collect_item,
)
from th08_player_shot_model import select_player_shot_level
from th08_route2_shot_coverage import normal_level_cadence_summary
from th08_sht import ShtFile, ShtLevel, parse_sht


SCHEMA = "th08-route2-power-capability-ledger-v1"
EXPECTED_PRIMARY_SHA256 = (
    "4765744ab5bbf797746469d5a6afc6ec7d4b0371422b5aa5a2e54ae668c48885"
)
EXPECTED_SECONDARY_SHA256 = (
    "f7554b3a32e16da01de9432e22609482a1c98a33212eb904ad47789079abebd3"
)
PICKUP_KINDS = (
    ("small_power", ITEM_POWER_SMALL),
    ("large_power", ITEM_POWER_LARGE),
    ("full_power", ITEM_FULL_POWER),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _level_capability(level: ShtLevel) -> dict[str, int]:
    cadence = normal_level_cadence_summary(level)
    return {
        "level": level.index,
        "emissions_per_20_tick_cycle": cadence.emissions_per_cycle,
        "nominal_base_damage_per_20_tick_cycle": (
            cadence.base_damage_per_cycle
        ),
        "callback_rng_u16_calls_per_20_tick_cycle": (
            cadence.callback_rng_u16_calls_per_cycle
        ),
    }


def _selected_capability(
    primary: ShtFile,
    secondary: ShtFile,
    *,
    power: int,
) -> dict[str, dict[str, int]]:
    unfocused = select_player_shot_level(
        primary,
        secondary,
        focus_logic_value=0,
        power=float(power),
    )
    focused = select_player_shot_level(
        primary,
        secondary,
        focus_logic_value=1,
        power=float(power),
    )
    return {
        "unfocused_primary": _level_capability(unfocused.level),
        "focused_secondary": _level_capability(focused.level),
    }


def _delta(
    before: dict[str, dict[str, int]],
    after: dict[str, dict[str, int]],
) -> dict[str, dict[str, int]]:
    fields = (
        "level",
        "emissions_per_20_tick_cycle",
        "nominal_base_damage_per_20_tick_cycle",
        "callback_rng_u16_calls_per_20_tick_cycle",
    )
    return {
        profile: {
            field: after[profile][field] - before[profile][field]
            for field in fields
        }
        for profile in before
    }


def _effective_pickup_type(power: int, requested_type: int) -> int:
    if power >= 128 and requested_type in (
        ITEM_POWER_SMALL,
        ITEM_POWER_LARGE,
    ):
        return ITEM_POWER_OVERFLOW
    return requested_type


def _transition(
    primary: ShtFile,
    secondary: ShtFile,
    *,
    power: int,
    pickup_name: str,
    requested_type: int,
) -> dict[str, object]:
    effective_type = _effective_pickup_type(power, requested_type)
    collection = collect_item(
        ItemState(0.0, 0.0, 0.0, 0.0, item_type=effective_type),
        ItemResources(power=power),
        difficulty_index=3,
    )
    after_power = collection.resources.power
    before_capability = _selected_capability(
        primary,
        secondary,
        power=power,
    )
    after_capability = _selected_capability(
        primary,
        secondary,
        power=after_power,
    )
    thresholds_crossed = [
        threshold
        for threshold in POWER_LEVEL_THRESHOLDS
        if power < threshold <= after_power
    ]
    profile_changed = any(
        before_capability[profile]["level"]
        != after_capability[profile]["level"]
        for profile in before_capability
    )
    return {
        "power_before": power,
        "requested_pickup": pickup_name,
        "requested_item_type": requested_type,
        "effective_item_type": effective_type,
        "spawn_converted_to_overflow": effective_type
        == ITEM_POWER_OVERFLOW,
        "power_after": after_power,
        "power_delta": after_power - power,
        "thresholds_crossed": thresholds_crossed,
        "converted_other_active_power_items": (
            collection.converted_active_power_items
        ),
        "profile_changed": profile_changed,
        "capability_delta": (
            _delta(before_capability, after_capability)
            if profile_changed
            else None
        ),
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
    primary = parse_sht(primary_path)
    secondary = parse_sht(secondary_path)

    bands: list[dict[str, object]] = []
    lower = 0
    for upper in (*POWER_LEVEL_THRESHOLDS, 129):
        representative = lower
        bands.append(
            {
                "power_lower_inclusive": lower,
                "power_upper_inclusive": upper - 1,
                "capability": _selected_capability(
                    primary,
                    secondary,
                    power=representative,
                ),
            }
        )
        lower = upper

    transitions = [
        _transition(
            primary,
            secondary,
            power=power,
            pickup_name=pickup_name,
            requested_type=requested_type,
        )
        for power in range(129)
        for pickup_name, requested_type in PICKUP_KINDS
    ]
    threshold_marginals = [
        {
            "threshold": threshold,
            "small_pickup_transition": next(
                transition
                for transition in transitions
                if transition["power_before"] == threshold - 1
                and transition["requested_pickup"] == "small_power"
            ),
        }
        for threshold in POWER_LEVEL_THRESHOLDS
    ]

    return {
        "schema": SCHEMA,
        "authority": {
            "kind": "offline_native_semantics_plus_shipped_data_ledger",
            "pickup_power_arithmetic": "observed_native_semantics",
            "shot_capability": "static_empty_pool_sht_projection",
            "planner_action_authority": False,
            "causal_collection_authority": False,
            "physical_predictive_authority": False,
            "physical_trial_run": False,
        },
        "inputs": {
            "primary_sht": str(primary_path),
            "primary_sht_sha256": primary_sha256,
            "secondary_sht": str(secondary_path),
            "secondary_sht_sha256": secondary_sha256,
            "power_domain": [0, 128],
            "normal_power_thresholds": list(POWER_LEVEL_THRESHOLDS),
        },
        "revalidated_native_semantics": {
            "item_pool_spawn": "0x004400A0",
            "item_manager_update": "0x00440500",
            "collect_small_power_item": "0x00440CF0",
            "collect_large_power_item": "0x00441170",
            "convert_active_power_items_to_overflow": "0x00441450",
            "set_player_power": "0x00406FA0",
            "pool_size": 2096,
            "allocation": (
                "rotating cursor with cyclic free-slot scan"
            ),
            "update_order": "active linked-list allocation order",
            "full_power": (
                "clamp to 128, convert other active type 0/2 items to type 8, "
                "and clamp converted velocity to (0,-0.5) only when vy>-0.5"
            ),
        },
        "power_bands": bands,
        "pickup_transitions": transitions,
        "threshold_marginals": threshold_marginals,
        "summary": {
            "transition_count": len(transitions),
            "small_threshold_crossings": sum(
                bool(transition["thresholds_crossed"])
                for transition in transitions
                if transition["requested_pickup"] == "small_power"
            ),
            "large_threshold_crossings": sum(
                bool(transition["thresholds_crossed"])
                for transition in transitions
                if transition["requested_pickup"] == "large_power"
            ),
            "large_pickup_124": next(
                transition
                for transition in transitions
                if transition["power_before"] == 124
                and transition["requested_pickup"] == "large_power"
            ),
        },
        "interpretation": {
            "supported": (
                "every natural Power pickup maps to a capped resource state "
                "and an action-conditioned normal-shot capability band"
            ),
            "not_supported": (
                "the ledger does not prove that a physical pickup is reachable, "
                "safe, observed, or causally beneficial later in the route"
            ),
            "next_gate": (
                "retain same-update generation/pickup/resource identity on a "
                "natural first-hit-bounded root, then branch only exact viable "
                "actions and carry the immutable world through a threshold"
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
