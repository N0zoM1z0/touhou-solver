#!/usr/bin/env python3
"""Audit one H1 native snapshot at the first unsupported producer event.

This is a wind-tunnel differential, not a physical trial or a predictive
policy.  It consumes only the retained root plus the immutable decoded ECL
program when advancing the causal model.  Endpoint births are used afterward
for retrospective attribution and can never fill a missing root transition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_ecl_tool.core import parse_ecl  # noqa: E402
from th08_rng import Th08Rng  # noqa: E402
from th08_timeline_model import (  # noqa: E402
    IndexedEnemyView,
    StageTimelineState,
    TimelineClock,
    TimelineExternalState,
    step_stage_timelines,
)


SCHEMA = "th08-native-h1-ecl-source-differential-v2"
RAW_SCHEMAS = frozenset(
    {
        "th08-native-snapshot-rolling-trial-v3",
        "th08-native-snapshot-rolling-trial-v11",
        "th08-native-snapshot-rolling-trial-v12",
    }
)
PROJECTION_SCHEMAS = frozenset(
    {
        "th08-native-snapshot-collision-control-projection-v7",
        "th08-native-snapshot-collision-control-projection-v8",
        "th08-native-snapshot-collision-control-projection-v9",
        "th08-native-snapshot-collision-control-projection-v10",
        "th08-native-snapshot-collision-control-projection-v11",
        "th08-native-snapshot-collision-control-projection-v12",
    }
)
EXPECTED_RAW_SHA256 = (
    "a072073ab792de627d5e44b0392f8cc251d1eabbf15923a8c740e85bb1b2c5a8"
)
EXPECTED_MANAGER_FRAME = 2129
EXPECTED_ACTION = 0x94
EXPECTED_BIRTH_SLOTS = tuple(range(1220, 1227))
EXPECTED_REMOVAL_SLOTS = (87, 120, 545, 710)
DIRECT_FIRE_OPCODES = frozenset(range(0x60, 0x69))

REPO_ROOT = SCRIPTS_ROOT.parent
DEFAULT_RAW = (
    REPO_ROOT
    / "archive"
    / "raw"
    / "native_snapshot_rolling"
    / "raw"
    / "th08_h1_94_source_v8_accepted_20260731.json"
)
DEFAULT_ECL = REPO_ROOT / "artifacts" / "decoded" / "ecldata5.ecl"
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_native_h1_ecl_source_differential_root2129_20260731.json"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _float32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _float32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def _signed_u32(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def _payload(record: dict[str, object]) -> dict[str, object]:
    _require(
        record.get("schema") in PROJECTION_SCHEMAS,
        "projection schema drift",
    )
    payload = record.get("model_payload")
    _require(isinstance(payload, dict), "projection omits model payload")
    _require(
        payload.get("schema") in PROJECTION_SCHEMAS,
        "model payload schema drift",
    )
    return payload


def _bullet_map(payload: dict[str, object]) -> dict[int, list[object]]:
    bullets = payload.get("bullets")
    _require(isinstance(bullets, list), "projection omits bullet list")
    result: dict[int, list[object]] = {}
    for row in bullets:
        _require(isinstance(row, list) and row, "malformed bullet row")
        slot = int(row[0])
        _require(slot not in result, f"duplicate bullet slot {slot}")
        result[slot] = row
    return result


def _birth_and_removal_rows(
    root_payload: dict[str, object],
    endpoint_payload: dict[str, object],
) -> tuple[list[list[object]], list[int]]:
    root = _bullet_map(root_payload)
    endpoint = _bullet_map(endpoint_payload)
    births = [endpoint[slot] for slot in sorted(endpoint.keys() - root.keys())]
    removals = sorted(root.keys() - endpoint.keys())
    _require(
        tuple(int(row[0]) for row in births) == EXPECTED_BIRTH_SLOTS,
        "unexpected H1 birth slots",
    )
    _require(tuple(removals) == EXPECTED_REMOVAL_SLOTS, "unexpected H1 removals")
    return births, removals


def _rng_alignment(
    root_compact: dict[str, object],
    endpoint_compact: dict[str, object],
    births: list[list[object]],
) -> dict[str, object]:
    state = int(root_compact["rng_state"])
    calls = int(root_compact["rng_calls"])
    endpoint_calls = int(endpoint_compact["rng_calls"])
    rng = Th08Rng(state, calls)
    by_speed_bits = {
        _float32_bits(float(row[8][0])): int(row[0])
        for row in births
    }
    pairs: list[dict[str, object]] = []
    for pair_index in range(8):
        calls_before = rng.calls
        signed_unit = rng.next_signed_unit()
        unit = rng.next_unit()
        # ecl_eval_float stores the RNG value to float32 before the add; the
        # native rank adjustment then rounds both arithmetic steps to float32.
        speed = _float32(
            _float32(_float32(1.0) + _float32(unit))
            - _float32(0.0375)
        )
        speed_bits = _float32_bits(speed)
        pairs.append(
            {
                "pair_index": pair_index,
                "rng_calls_before": calls_before,
                "rng_calls_after": rng.calls,
                "signed_unit": signed_unit,
                "unit": unit,
                "rank_adjusted_speed": speed,
                "rank_adjusted_speed_bits": speed_bits,
                "matching_birth_slot": by_speed_bits.get(speed_bits),
            }
        )
    _require(rng.calls == endpoint_calls, "eight RNG pairs do not close H1 calls")
    _require(
        [row["matching_birth_slot"] for row in pairs]
        == [None, *EXPECTED_BIRTH_SLOTS],
        "retrospective RNG/birth alignment drift",
    )
    return {
        "root_state": state,
        "root_calls": calls,
        "endpoint_calls": endpoint_calls,
        "u16_calls_consumed": endpoint_calls - calls,
        "pairs": pairs,
        "authority": (
            "retrospective_endpoint_alignment_only_not_a_causal_root_input"
        ),
    }


def _timeline_result(
    ecl: Any,
    root_payload: dict[str, object],
    root_compact: dict[str, object],
) -> dict[str, object]:
    runtime = root_payload["stage_timeline_runtime"]
    rows = runtime["rows"]
    _require(len(rows) == len(ecl.timelines), "timeline program/count mismatch")
    clocks: list[TimelineClock] = []
    for timeline, row in zip(ecl.timelines, rows, strict=True):
        current_offset = int(row["current_instruction"]["static_offset"])
        instruction_index = next(
            (
                index
                for index, instruction in enumerate(timeline.instructions)
                if instruction.offset == current_offset
            ),
            None,
        )
        _require(
            instruction_index is not None,
            f"timeline {timeline.index} PC is not a static instruction",
        )
        clocks.append(
            TimelineClock(
                instruction_index=instruction_index,
                elapsed=int(row["elapsed"]),
                stopped=bool(row["current_instruction"]["terminal"]),
            )
        )

    external_record = runtime["external"]
    indexed: list[IndexedEnemyView | None] = []
    for row in external_record["indexed_enemies"]:
        if row is None:
            indexed.append(None)
            continue
        # The current retained root does not need field_2d30 because every
        # registry slot is null.  A future non-null registry must add that
        # field rather than silently substituting zero.
        _require(
            "field_2d30" in row,
            "non-null indexed enemy lacks field_2d30; timeline is UNKNOWN",
        )
        indexed.append(
            IndexedEnemyView(
                active=bool(row["active"]),
                field_2d30=int(row["field_2d30"]),
            )
        )
    state = StageTimelineState(
        clocks=tuple(clocks),
        markers=tuple(int(value) for value in external_record["markers"]),
        rng_state=int(root_compact["rng_state"]),
        rng_calls=int(root_compact["rng_calls"]),
        stage_flag_10=bool(runtime["stage_flag_10"]),
    )
    external = TimelineExternalState(
        stage_transition_busy=bool(external_record["stage_transition_busy"]),
        spawn_suppressed=bool(external_record["spawn_suppressed"]),
        conditional_gate_blocked=bool(
            external_record["conditional_gate_blocked"]
        ),
        indexed_enemies=tuple(indexed),
    )
    result = step_stage_timelines(
        ecl,
        state,
        active_difficulty_mask=int(runtime["difficulty_mask"]),
        external=external,
    )
    _require(not result.spawns, "root timeline unexpectedly spawns in H1")
    _require(not result.engine_events, "root timeline emits an engine event")
    _require(not result.field_writes, "root timeline writes indexed enemy state")
    _require(
        result.state.rng_calls == state.rng_calls,
        "root timeline unexpectedly consumes RNG",
    )
    return {
        "status": "exact_no_event",
        "timeline_count": len(rows),
        "root_clocks": [
            {
                "timeline_index": index,
                "elapsed": clock.elapsed,
                "instruction_index": clock.instruction_index,
                "current_static_offset": int(
                    rows[index]["current_instruction"]["static_offset"]
                ),
                "current_instruction_time": int(
                    rows[index]["current_instruction"]["time"]
                ),
            }
            for index, clock in enumerate(state.clocks)
        ],
        "rng_calls_before": state.rng_calls,
        "rng_calls_after": result.state.rng_calls,
        "spawn_count": 0,
        "engine_event_count": 0,
        "field_write_count": 0,
    }


def _instruction_index(ecl: Any) -> dict[int, Any]:
    return {
        instruction.offset: instruction
        for subroutine in ecl.subroutines
        for instruction in subroutine.instructions
    }


def _auxiliary_fire_suffix(
    ecl: Any,
    root_payload: dict[str, object],
) -> dict[str, object]:
    runtime = root_payload["stage_timeline_runtime"]
    ecl_base = int(runtime["ecl_file"]["file_base"])
    instructions = _instruction_index(ecl)
    manager_template = root_payload["enemy_manager_template_source"]
    source_ranges = (
        (
            str(manager_template["source_role"]),
            manager_template["auxiliary_ecl_contexts"]["rows"],
            manager_template["periodic_emission_state"]["rows"],
        ),
        (
            "ordinary_enemy_pool",
            root_payload["enemy_auxiliary_ecl_contexts"]["rows"],
            root_payload["enemy_periodic_emission_state"]["rows"],
        ),
    )
    rows: list[dict[str, object]] = []
    for source_role, contexts, periodic_rows in source_ranges:
        periodic_by_slot = {
            int(row["slot"]): row
            for row in periodic_rows
        }
        for context in contexts:
            _require(
                int(context["target_subroutine"]) == 30,
                "unexpected auxiliary target subroutine",
            )
            _require(
                not context["installed_callback"]["function_pointer"],
                "auxiliary callback requires address-specific lowering",
            )
            slot = int(context["slot"])
            owner = periodic_by_slot[slot]
            _require(int(owner["hitpoints"]) > 0, "auxiliary owner is not alive")
            state = context["state"]
            timer = int(state["timer_elapsed"])
            offset = int(state["instruction_pointer"]) - ecl_base
            direct_fires: list[int] = []
            visited: set[tuple[int, int]] = set()
            stop_reason = "instruction_time_ahead"
            for _ in range(32):
                key = (offset, timer)
                _require(
                    key not in visited,
                    "auxiliary control flow loops in one tick",
                )
                visited.add(key)
                instruction = instructions.get(offset)
                _require(
                    instruction is not None,
                    "auxiliary PC is not in static ECL",
                )
                if instruction.time != timer:
                    break
                opcode = int(instruction.opcode)
                if opcode == 0x04:
                    _require(
                        len(instruction.arguments) == 2,
                        "auxiliary jump argument drift",
                    )
                    timer = _signed_u32(int(instruction.arguments[0]))
                    offset += _signed_u32(int(instruction.arguments[1]))
                    continue
                if opcode == 0x02:
                    _require(
                        len(instruction.arguments) == 1,
                        "auxiliary timer-reset argument drift",
                    )
                    _require(
                        int(instruction.arguments[0]) == 10038,
                        "auxiliary wait variable drift",
                    )
                    scratch = state["local_projection"]["scratch_integers"]
                    _require(
                        int(scratch[2]) == 2,
                        "auxiliary wait is not two ticks",
                    )
                    stop_reason = "timer_reset_to_two"
                    break
                if opcode in DIRECT_FIRE_OPCODES:
                    direct_fires.append(instruction.offset)
                elif opcode not in (0x0F, 0x1B):
                    raise ValueError(
                        f"unsupported auxiliary opcode {opcode:#x} "
                        f"at {offset:#x}"
                    )
                offset += instruction.size
            else:
                raise ValueError(
                    "auxiliary H1 scan exceeded its instruction bound"
                )
            _require(
                len(direct_fires) == 1,
                "auxiliary does not fire exactly once",
            )
            rows.append(
                {
                    "source_role": source_role,
                    "enemy_pointer": int(context["enemy_pointer"]),
                    "slot": slot,
                    "auxiliary_index": int(context["auxiliary_index"]),
                    "root_static_offset": (
                        int(state["instruction_pointer"]) - ecl_base
                    ),
                    "direct_fire_static_offset": direct_fires[0],
                    "stop_reason": stop_reason,
                    "direct_fire_count": 1,
                }
            )
    _require(len(rows) == 7, "expected seven active auxiliary contexts")
    return {
        "status": "exact_control_flow_one_direct_fire_each",
        "rows": rows,
        "direct_fire_count": sum(int(row["direct_fire_count"]) for row in rows),
        "numeric_descriptor_authority": (
            "causal_root_vm_and_rng_state_present_descriptor_lowering_pending"
        ),
    }


def _due_main_paths(
    ecl: Any,
    root_payload: dict[str, object],
) -> dict[str, object]:
    ecl_base = int(root_payload["stage_timeline_runtime"]["ecl_file"]["file_base"])
    inventory = {
        int(row[0]): row
        for row in root_payload["enemy_main_ecl_vm_inventory"]["rows"]
    }
    current = {
        int(row["slot"]): row
        for row in root_payload["enemy_current_ecl_instructions"]["rows"]
    }
    instructions = _instruction_index(ecl)
    due: list[dict[str, object]] = []
    for slot, row in sorted(current.items()):
        timer_elapsed = int(inventory[slot][5])
        if timer_elapsed != int(row["time"]):
            continue
        offset = int(row["instruction_pointer"]) - ecl_base
        path: list[dict[str, int]] = []
        for _ in range(16):
            instruction = instructions.get(offset)
            _require(instruction is not None, "due main PC is not static ECL")
            if instruction.time != timer_elapsed:
                break
            path.append(
                {
                    "static_offset": instruction.offset,
                    "opcode": int(instruction.opcode),
                }
            )
            _require(
                int(instruction.opcode) not in DIRECT_FIRE_OPCODES,
                "due main path unexpectedly contains direct fire",
            )
            offset += instruction.size
        else:
            raise ValueError("due main path exceeded its instruction bound")
        due.append(
            {
                "slot": slot,
                "timer_elapsed": timer_elapsed,
                "instructions": path,
                "contains_direct_fire": False,
            }
        )
    _require([row["slot"] for row in due] == [8], "due main slot drift")
    _require(
        [item["opcode"] for item in due[0]["instructions"]]
        == [0x41, 0x07, 0x07, 0x5C],
        "slot-8 due main path drift",
    )
    return {
        "status": "exact_literal_due_prefix",
        "rows": due,
        "closure": (
            "stops_at_opcode_0x5c_child_spawn_boundary_no_direct_fire_in_prefix"
        ),
    }


def build_report(
    *,
    raw_path: Path,
    ecl_path: Path,
    expected_raw_sha256: str = EXPECTED_RAW_SHA256,
) -> dict[str, object]:
    raw_bytes = raw_path.read_bytes()
    raw_sha256 = _sha256_bytes(raw_bytes)
    _require(raw_sha256 == expected_raw_sha256, "raw H1 SHA-256 drift")
    raw = json.loads(raw_bytes)
    _require(raw.get("schema") in RAW_SCHEMAS, "raw trial schema drift")
    _require(int(raw["target_manager_frame"]) == EXPECTED_MANAGER_FRAME, "root drift")
    _require(int(raw["horizon"]) == 1, "report requires H1")
    _require(int(raw["result"]["branches"]["b"]["action_override"]) == EXPECTED_ACTION, "action drift")
    _require(not (EXPECTED_ACTION & 0x02), "Bomb action is forbidden")
    _require(
        raw["result"]["status"] == "rolling_native_projection_snapshot_passed",
        "native snapshot trial did not pass",
    )
    _require(raw["result"]["same_action_full_endpoint_exact"], "A1/A2 mismatch")
    _require(
        raw["result"]["same_action_collision_control_projection_exact"],
        "A1/A2 collision projection mismatch",
    )
    root_record = raw["result"]["root_collision_control_projection"]
    endpoint_tick = raw["result"]["branches"]["b"]["ticks"][0]
    endpoint_record = endpoint_tick["collision_control_projection"]
    root_payload = _payload(root_record)
    endpoint_payload = _payload(endpoint_record)
    root_compact = raw["result"]["root_compact_state"]
    endpoint_compact = endpoint_tick["compact_state"]
    births, removals = _birth_and_removal_rows(root_payload, endpoint_payload)
    endpoint_lifecycle = {
        int(row["slot"]): row
        for row in endpoint_payload["bullet_lifecycle"]
    }
    _require(
        all(
            int(endpoint_lifecycle[int(row[0])]["state"]) == 2
            for row in births
        ),
        "H1 births are not all native state 2",
    )

    ecl_bytes = ecl_path.read_bytes()
    ecl = parse_ecl(ecl_path)
    runtime_ecl = root_payload["stage_timeline_runtime"]["ecl_file"]
    _require(
        int(runtime_ecl["static_data_end_offset"]) == ecl.header.data_end_offset,
        "runtime/static ECL data-end mismatch",
    )
    timeline = _timeline_result(ecl, root_payload, root_compact)
    auxiliary = _auxiliary_fire_suffix(ecl, root_payload)
    main = _due_main_paths(ecl, root_payload)

    periodic_rows = root_payload["enemy_periodic_emission_state"]["rows"]
    manager_template = root_payload["enemy_manager_template_source"]
    manager_periodic_rows = manager_template["periodic_emission_state"]["rows"]
    enabled_periodic = [
        row
        for row in (*manager_periodic_rows, *periodic_rows)
        if row["enabled"]
    ]
    main_callbacks = [
        row
        for row in root_payload["enemy_main_ecl_installed_callbacks"]["rows"]
        if row["installed_callback"]["function_pointer"]
    ]
    auxiliary_callbacks = [
        row
        for row in (
            *manager_template["auxiliary_ecl_contexts"]["rows"],
            *root_payload["enemy_auxiliary_ecl_contexts"]["rows"],
        )
        if row["installed_callback"]["function_pointer"]
    ]
    manager_main_callbacks = [
        row
        for row in manager_template["main_ecl_installed_callbacks"]["rows"]
        if row["installed_callback"]["function_pointer"]
    ]
    _require(not enabled_periodic, "periodic emitter requires exact stepping")
    _require(
        not (*manager_main_callbacks, *main_callbacks),
        "main installed callback requires lowering",
    )
    _require(not auxiliary_callbacks, "aux installed callback requires lowering")

    rng = _rng_alignment(root_compact, endpoint_compact, births)
    return {
        "schema": SCHEMA,
        "authority": {
            "kind": "offline_native_snapshot_first_mismatch_differential",
            "physical_predictive_authority": False,
            "planner_action_authority": False,
            "uses_endpoint_as_model_input": False,
            "physical_trial_run": False,
        },
        "inputs": {
            "raw_path": str(raw_path.relative_to(REPO_ROOT)),
            "raw_sha256": raw_sha256,
            "decoded_ecl_path": str(ecl_path.relative_to(REPO_ROOT)),
            "decoded_ecl_sha256": _sha256_bytes(ecl_bytes),
            "runtime_ecl_file_base": int(runtime_ecl["file_base"]),
            "runtime_ecl_static_data_end_offset": int(
                runtime_ecl["static_data_end_offset"]
            ),
        },
        "native_acceptance": {
            "status": raw["result"]["status"],
            "manager_frame": int(root_compact["manager_frame"]),
            "action": EXPECTED_ACTION,
            "horizon": 1,
            "a1_a2_full_endpoint_exact": True,
            "a1_a2_collision_control_exact": True,
            "natural_reference_status": (
                raw["result"].get("natural_reference", {}).get(
                    "status",
                    "not_requested",
                )
            ),
        },
        "causal_root_layers": {
            "timeline": timeline,
            "periodic_emitter": {
                "status": "exact_no_enabled_emitter",
                "active_enemy_rows": (
                    len(manager_periodic_rows) + len(periodic_rows)
                ),
                "enabled_count": 0,
            },
            "installed_callbacks": {
                "status": "exact_no_installed_callback",
                "main_nonzero_count": 0,
                "auxiliary_nonzero_count": 0,
            },
            "due_main_vm": main,
            "auxiliary_vm": auxiliary,
        },
        "native_endpoint": {
            "birth_slots": [int(row[0]) for row in births],
            "births": [
                {
                    "slot": int(row[0]),
                    "x": float(row[1]),
                    "y": float(row[2]),
                    "velocity_x": float(row[3]),
                    "velocity_y": float(row[4]),
                    "speed": float(row[8][0]),
                    "speed_bits": _float32_bits(float(row[8][0])),
                    "angle": float(row[8][1]),
                    "state": int(endpoint_lifecycle[int(row[0])]["state"]),
                    "original_flags": int(row[8][2]),
                }
                for row in births
            ],
            "removal_slots": removals,
        },
        "retrospective_rng_alignment": rng,
        "closed_prior_mismatch": {
            "status": "SOURCE_INVENTORY_CLOSED",
            "rng_calls_before_unknown": int(root_compact["rng_calls"]),
            "non_emission_rng_pair_index": 0,
            "non_emission_rng_consumer": {
                "classification": (
                    "same_update_child_subroutine_35_initialization"
                ),
                "instruction_static_offset": 13220,
                "opcode": 0x49,
                "dynamic_float_operands": [10016.0, 10017.0],
                "endpoint_child_slot": 3,
            },
            "birth_rng_pair_indices": list(range(1, 8)),
            "birth_slots": list(range(1220, 1227)),
            "auxiliary_sources_in_native_order": [
                {
                    "source_role": row["source_role"],
                    "enemy_pointer": row["enemy_pointer"],
                    "slot": row["slot"],
                }
                for row in auxiliary["rows"]
            ],
            "reason": (
                "the manager-template/special-singleton record at 0x57D2F0 "
                "was active but omitted from the v7 source inventory; its "
                "auxiliary sub30 VM is the seventh direct-fire producer"
            ),
        },
        "promotion": {
            "integrated_h1_status": "SOURCE_COMPLETE_GEOMETRY_LOWERING_PENDING",
            "physical_gate_authorized": False,
            "next_minimum_closure": (
                "lower the seven root-causal direct-fire descriptors into "
                "future hazard geometry, then extend the same source-range "
                "closure across the publication horizon"
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--ecl", type=Path, default=DEFAULT_ECL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--expected-raw-sha256",
        default=EXPECTED_RAW_SHA256,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(
        raw_path=args.raw.resolve(),
        ecl_path=args.ecl.resolve(),
        expected_raw_sha256=args.expected_raw_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"native H1 ECL source differential: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
