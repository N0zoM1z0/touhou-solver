#!/usr/bin/env python3
"""Run rolling same-root native snapshot and natural-frame differential trials."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_automation.finalb_replay_observer import (  # noqa: E402
    drive_native_stage_replay_menu,
    validate_native_stage_replay,
    wait_for_bound_replay_gameplay,
)
from th08_automation.practice_supervisor import (  # noqa: E402
    DEFAULT_LAUNCH_BAT,
    _stop_batch_process,
)
from th08_automation.practice_windows import (  # noqa: E402
    focus_target_window,
    launch_patch_batch,
    matching_targets,
    terminate_exact_target,
    wait_for_patched_target,
)
from th08_native_future_body_root import (  # noqa: E402
    Route2NativeFutureBodyRootSlice,
    capture_route2_native_future_body_root_slice,
    decode_route2_ordinary_pool_active_slots,
    route2_revalidated_native_root_component_specs,
)
from th08_runtime.native_snapshot import (  # noqa: E402
    NativeBarrierHeader,
    NativeCalculationBarrier,
    NativeDirtyPage,
    NativeSnapshot,
    NativeSnapshotUnknownError,
    STATUS_ROOT_WAIT,
    changed_byte_addresses,
    capture_native_snapshot,
    committed_map_identity,
    enumerate_target_thread_ids,
    query_native_virtual_regions,
    recapture_native_snapshot,
    release_frozen_threads,
    resolve_native_replay_action_carrier,
    restore_native_dirty_pages,
    snapshot_dirty_pages,
    snapshot_excluded_allocation_bases,
    suspend_non_owner_threads,
    verify_native_dirty_pages,
    write_native_replay_action,
)
from th08_runtime.native_snapshot_projection import (  # noqa: E402
    CollisionControlProjection,
    capture_collision_control_projection,
    collision_control_projection_changes,
)
from th08_runtime_agent import (  # noqa: E402
    SUPPORTED_INPUT_MASK,
    TARGET_EXE,
    Win32,
    observe_state,
    release_injected_keys,
    send_scan_key,
    verify_target,
)
from touhou_control.pipeline_identity import VersionIdentity  # noqa: E402


SCHEMA = "th08-native-snapshot-rolling-trial-v2"
DEFAULT_GAME_DIR = Path(
    "D:/Entertainment/Game/Touhou/[th08] 东方永夜抄 (日文版)__codex_wind_tunnel"
)
DEFAULT_STAGE5_SLOT = 15
DEFAULT_STAGE5_SHA256 = (
    "de1e4e941adc8c2899eb3ae1bedd2b4faaf14362d4ce2af984d1c9e5a32da613"
)
DEFAULT_TARGET_MANAGER_FRAME = 2129
DEFAULT_ACTION_B = 0x15
DEFAULT_HORIZON = 2
DEFAULT_HOLD_FRAMES = 3
DEFAULT_COMPACT_CORPUS_TICKS = 2
DEFAULT_COMPACT_CORPUS = (
    SCRIPTS_ROOT.parent
    / "artifacts"
    / "native_replay_wind_tunnel"
    / "raw"
    / "accepted"
    / "th08_native_branch_trials_latest_root2129_fence2137_20260730"
    / "th08_mask_05.json"
)
DEFAULT_PORTFOLIO_CORPUS = (
    SCRIPTS_ROOT.parent
    / "artifacts"
    / "runtime_reports"
    / "th08_native_branch_trials_latest_root2129_fence2137_all36_20260730.json"
)
PORTFOLIO_NO_BOMB_MASKS = tuple(
    direction | modifier
    for direction in (
        0x00,
        0x10,
        0x20,
        0x40,
        0x50,
        0x60,
        0x80,
        0x90,
        0xA0,
    )
    for modifier in (0x00, 0x01, 0x04, 0x05)
)


def _duration_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


def _compact_addresses(
    addresses: tuple[int, ...],
    *,
    limit: int = 256,
) -> dict[str, object]:
    return {
        "count": len(addresses),
        "first": list(addresses[:limit]),
        "truncated": len(addresses) > limit,
    }


def _compact_dirty_pages(pages: tuple[object, ...]) -> dict[str, object]:
    records = [page.record() for page in pages[:256]]
    return {
        "count": len(pages),
        "pages": records,
        "truncated": len(pages) > len(records),
    }


def _snapshot_byte(snapshot: NativeSnapshot, address: int) -> int:
    for capture in snapshot.regions:
        if capture.region.base <= address < capture.region.end:
            return capture.data[address - capture.region.base]
    raise ValueError(f"snapshot does not contain address 0x{address:08x}")


def _group_changes_by_region(
    root: NativeSnapshot,
    left: NativeSnapshot,
    right: NativeSnapshot,
    addresses: tuple[int, ...],
) -> dict[str, object]:
    groups: list[dict[str, object]] = []
    address_index = 0
    for capture in root.regions:
        region_addresses: list[int] = []
        while (
            address_index < len(addresses)
            and addresses[address_index] < capture.region.base
        ):
            address_index += 1
        while (
            address_index < len(addresses)
            and addresses[address_index] < capture.region.end
        ):
            region_addresses.append(addresses[address_index])
            address_index += 1
        if region_addresses:
            groups.append(
                {
                    **capture.region.record(),
                    "changed_byte_count": len(region_addresses),
                    "first_addresses": region_addresses[:64],
                }
            )
    samples = [
        {
            "address": address,
            "left": _snapshot_byte(left, address),
            "right": _snapshot_byte(right, address),
        }
        for address in addresses[:256]
    ]
    return {
        "changed_bytes": _compact_addresses(addresses),
        "region_count": len(groups),
        "regions": groups[:128],
        "regions_truncated": len(groups) > 128,
        "byte_samples": samples,
    }


def _assert_thread_epoch(
    api: object,
    pid: int,
    expected_thread_ids: tuple[int, ...],
) -> None:
    actual = enumerate_target_thread_ids(api, pid)
    if actual != expected_thread_ids:
        raise NativeSnapshotUnknownError(
            "target thread set changed inside the native snapshot epoch: "
            f"{expected_thread_ids!r} -> {actual!r}"
        )


def _assert_endpoint_stack_and_clock(
    root_header: NativeBarrierHeader,
    endpoint_header: NativeBarrierHeader,
    *,
    completed_ticks: int = 1,
) -> None:
    if completed_ticks <= 0:
        raise ValueError("completed native tick count must be positive")
    if (
        endpoint_header.endpoint_esp != root_header.root_esp
        or endpoint_header.endpoint_ebp != root_header.root_ebp
    ):
        raise NativeSnapshotUnknownError(
            "rolling update-chain call did not return to the exact root stack"
        )
    if endpoint_header.endpoint_manager_frame != (
        root_header.root_manager_frame + completed_ticks
    ):
        raise NativeSnapshotUnknownError(
            "rolling update-chain call reached an unexpected manager frame"
        )


def _compact_state(reader: object) -> dict[str, object]:
    state = observe_state(reader)
    if not state["gameplay_active"]:
        raise NativeSnapshotUnknownError(
            "native gameplay ended inside the rolling snapshot horizon"
        )
    player = state["player"]
    spell = state["spell"]
    assert isinstance(player, dict)
    assert isinstance(spell, dict)
    return {
        "manager_frame": int(state["enemy_manager_frame"]),
        "input_raw": int(state["input_raw"]),
        "input_current": int(state["input_current"]),
        "input_previous": int(state["input_previous"]),
        "rng_state": int(state["rng_state"]),
        "rng_calls": int(state["rng_calls"]),
        "time_scale_bits": int(state["time_scale_bits"]),
        "spell_id": int(spell["spell_id"]) if spell["active"] else None,
        "player_phase": int(player["phase"]),
        "player_x": float(player["x"]),
        "player_y": float(player["y"]),
        "focus_logic": int(player["focus_logic"]),
        "secondary_character_active": bool(player["secondary_character_active"]),
        "focus_transition_counter": int(player["focus_transition_counter"]),
        "predeath_counter": int(player["predeath_counter"]),
        "resources": state["resources"],
    }


def _compact_corpus_comparison(
    corpus_path: Path,
    *,
    target_manager_frame: int,
    branch: dict[str, object],
    comparison_ticks: int | None = None,
) -> dict[str, object]:
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    result = corpus.get("result")
    if not isinstance(result, dict):
        raise NativeSnapshotUnknownError("compact corpus has no result object")
    history = result.get("history")
    if not isinstance(history, list):
        raise NativeSnapshotUnknownError("compact corpus has no history array")
    ticks = branch.get("ticks")
    if not isinstance(ticks, list):
        raise NativeSnapshotUnknownError("recorded native branch has no tick history")
    if comparison_ticks is not None:
        if comparison_ticks <= 0:
            raise ValueError("compact corpus comparison ticks must be positive")
        if len(ticks) < comparison_ticks:
            raise NativeSnapshotUnknownError(
                "recorded native branch is shorter than the compact corpus gate"
            )
        ticks = ticks[:comparison_ticks]
    corpus_by_frame = {
        int(state["manager_frame"]): state
        for state in history
        if isinstance(state, dict) and "manager_frame" in state
    }
    comparisons: list[dict[str, object]] = []
    exact = True
    for tick_index, tick in enumerate(ticks):
        if not isinstance(tick, dict):
            raise NativeSnapshotUnknownError("recorded native branch tick is malformed")
        actual = tick.get("compact_state")
        if not isinstance(actual, dict):
            raise NativeSnapshotUnknownError(
                "recorded native branch tick omits compact state"
            )
        expected_frame = target_manager_frame + tick_index + 1
        expected = corpus_by_frame.get(expected_frame)
        if expected is None:
            raise NativeSnapshotUnknownError(
                f"compact corpus omits manager frame {expected_frame}"
            )
        field_changes = [
            {
                "field": field,
                "expected": expected.get(field),
                "actual": actual.get(field),
            }
            for field in sorted(set(expected) | set(actual))
            if expected.get(field) != actual.get(field)
        ]
        tick_exact = not field_changes
        exact = exact and tick_exact
        comparisons.append(
            {
                "tick_index": tick_index,
                "manager_frame": expected_frame,
                "exact": tick_exact,
                "field_changes": field_changes,
            }
        )
    return {
        "status": "exact" if exact else "mismatch",
        "exact": exact,
        "corpus_path": str(corpus_path),
        "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "corpus_schema": corpus.get("schema"),
        "corpus_result_status": result.get("status"),
        "compared_frames": [
            target_manager_frame + tick_index + 1 for tick_index in range(len(ticks))
        ],
        "ticks": comparisons,
    }


def _load_portfolio_corpus(
    corpus_path: Path,
    *,
    target_manager_frame: int,
    horizon: int,
    hold_frames: int,
) -> tuple[dict[int, dict[str, object]], dict[str, object]]:
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise NativeSnapshotUnknownError("all-36 corpus root is not an object")
    if int(payload.get("root_frame", -1)) != target_manager_frame:
        raise NativeSnapshotUnknownError(
            "all-36 corpus does not describe the requested snapshot root"
        )
    expected_stop = target_manager_frame + horizon
    if int(payload.get("stop_manager_frame", -1)) != expected_stop:
        raise NativeSnapshotUnknownError(
            "all-36 corpus stop frame does not match the rolling horizon"
        )
    if int(payload.get("hold_frames", -1)) != min(hold_frames, horizon):
        raise NativeSnapshotUnknownError(
            "all-36 corpus action hold does not match the rolling trial"
        )
    branches = payload.get("branches")
    if not isinstance(branches, list):
        raise NativeSnapshotUnknownError("all-36 corpus has no branch list")

    by_mask: dict[int, dict[str, object]] = {}
    for branch in branches:
        if not isinstance(branch, dict):
            raise NativeSnapshotUnknownError(
                "all-36 corpus contains a non-object branch"
            )
        mask = int(branch.get("complete_mask", -1))
        if mask < 0 or mask & ~SUPPORTED_INPUT_MASK or mask & 0x02 or mask in by_mask:
            raise NativeSnapshotUnknownError(
                "all-36 corpus contains an invalid, Bomb, or duplicate mask"
            )
        endpoint = branch.get("endpoint")
        if not isinstance(endpoint, dict):
            raise NativeSnapshotUnknownError(
                "all-36 corpus branch has no compact endpoint"
            )
        by_mask[mask] = branch

    if tuple(by_mask) != PORTFOLIO_NO_BOMB_MASKS:
        raise NativeSnapshotUnknownError(
            "all-36 corpus mask order/set is not the canonical no-Bomb portfolio"
        )
    return by_mask, {
        "path": str(corpus_path),
        "schema": payload.get("schema"),
        "source_sha256": payload.get("source_sha256"),
        "root_frame": target_manager_frame,
        "stop_manager_frame": expected_stop,
        "hold_frames": min(hold_frames, horizon),
        "mask_count": len(by_mask),
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
    }


def _compare_portfolio_branch_to_corpus(
    expected: dict[str, object],
    branch: dict[str, object],
) -> dict[str, object]:
    ticks = branch.get("ticks")
    if not isinstance(ticks, list) or not ticks:
        raise NativeSnapshotUnknownError(
            "rolling portfolio branch has no compact tick history"
        )
    compact_states: list[dict[str, object]] = []
    for tick in ticks:
        if not isinstance(tick, dict):
            raise NativeSnapshotUnknownError("rolling portfolio tick is not an object")
        state = tick.get("compact_state")
        if not isinstance(state, dict):
            raise NativeSnapshotUnknownError(
                "rolling portfolio tick has no compact state"
            )
        compact_states.append(state)

    expected_endpoint = expected.get("endpoint")
    if not isinstance(expected_endpoint, dict):
        raise NativeSnapshotUnknownError(
            "all-36 corpus branch has no expected endpoint"
        )
    expected_hit_value = expected.get("first_hit_manager_frame")
    expected_hit = None if expected_hit_value is None else int(expected_hit_value)
    observed_hit_state = next(
        (state for state in compact_states if int(state.get("player_phase", -1)) == 2),
        None,
    )
    observed_hit = (
        None if observed_hit_state is None else int(observed_hit_state["manager_frame"])
    )
    selected_state = (
        observed_hit_state if expected_hit is not None else compact_states[-1]
    )
    if selected_state is None:
        raise NativeSnapshotUnknownError(
            "rolling portfolio has no state at the expected comparison frame"
        )

    field_changes = [
        {
            "field": field,
            "expected": expected_value,
            "observed": selected_state.get(field),
        }
        for field, expected_value in expected_endpoint.items()
        if selected_state.get(field) != expected_value
    ]
    expected_frame = (
        expected_hit
        if expected_hit is not None
        else int(expected.get("stop_manager_frame", -1))
    )
    observed_frame = int(selected_state["manager_frame"])
    exact = (
        observed_hit == expected_hit
        and observed_frame == expected_frame
        and not field_changes
    )
    outcome_class_exact = (observed_hit is None) == (expected_hit is None)
    return {
        "schema": "th08-native-snapshot-all36-corpus-branch-comparison-v1",
        "complete_mask": int(expected["complete_mask"]),
        "expected_status": expected.get("status"),
        "expected_first_hit_manager_frame": expected_hit,
        "observed_first_hit_manager_frame": observed_hit,
        "comparison_manager_frame": observed_frame,
        "expected_comparison_manager_frame": expected_frame,
        "field_changes": field_changes,
        "outcome_class_exact": outcome_class_exact,
        "first_hit_frame_delta": (
            None
            if expected_hit is None or observed_hit is None
            else observed_hit - expected_hit
        ),
        "exact": exact,
    }


def _compact_portfolio_branch_record(
    branch: dict[str, object],
    *,
    comparison: dict[str, object],
    restore: dict[str, object],
    elapsed_ms: float,
) -> dict[str, object]:
    ticks = branch.get("ticks")
    if not isinstance(ticks, list):
        raise NativeSnapshotUnknownError("rolling portfolio branch has no tick records")
    compact_ticks: list[dict[str, object]] = []
    for tick in ticks:
        if not isinstance(tick, dict):
            raise NativeSnapshotUnknownError("rolling portfolio tick is not an object")
        native_projection = tick.get("native_projection")
        if not isinstance(native_projection, dict):
            raise NativeSnapshotUnknownError(
                "rolling portfolio tick has no native projection"
            )
        compact_ticks.append(
            {
                "tick_index": tick["tick_index"],
                "completed_ticks": tick["completed_ticks"],
                "selected_action": tick["selected_action"],
                "recorded_action": tick["recorded_action"],
                "action_word_written": tick["action_word_written"],
                "action_carrier": tick["action_carrier"],
                "endpoint_header": tick["endpoint_header"],
                "compact_state": tick["compact_state"],
                "native_projection_sha256": native_projection["sha256"],
                "native_projection_frame_bracket": native_projection["frame_bracket"],
                "collision_control_projection": tick["collision_control_projection"],
                "timing_ms": tick["timing_ms"],
            }
        )
    return {
        "action_override": branch["action_override"],
        "hold_frames": branch["hold_frames"],
        "horizon": branch["horizon"],
        "parameterized_root_baseline_sha256": branch[
            "parameterized_root_baseline_sha256"
        ],
        "parameterized_action_changes": branch["parameterized_action_changes"],
        "endpoint_sha256": branch["endpoint_sha256"],
        "dirty_to_baseline": branch["dirty_to_baseline"],
        "ticks": compact_ticks,
        "endpoint_capture_timing_ms": branch["timing_ms"],
        "corpus_comparison": comparison,
        "restore": restore,
        "branch_and_restore_elapsed_ms": elapsed_ms,
    }


def _assert_action_carrier_epoch(
    root_carrier: object,
    carrier: object,
    *,
    tick_index: int,
) -> None:
    if tick_index < 0:
        raise ValueError("native action tick index must be nonnegative")
    if (
        int(carrier.replay_object) != int(root_carrier.replay_object)
        or int(carrier.update_node) != int(root_carrier.update_node)
        or int(carrier.replay_frame_counter)
        != int(root_carrier.replay_frame_counter) + tick_index
        or int(carrier.input_cursor) != int(root_carrier.input_cursor) + 2 * tick_index
    ):
        raise NativeSnapshotUnknownError(
            "native replay action carrier left its exact rolling cursor epoch"
        )


def _capture_stable_baseline(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    excluded_allocation_bases: frozenset[int],
    maximum_attempts: int = 4,
) -> tuple[NativeSnapshot, tuple[dict[str, object], ...], float]:
    attempts: list[dict[str, object]] = []
    total_started = time.perf_counter()
    for attempt in range(1, maximum_attempts + 1):
        started = time.perf_counter()
        snapshot = capture_native_snapshot(
            api,
            barrier.handle,
            excluded_allocation_bases=excluded_allocation_bases,
            remote_base=barrier.remote_base,
        )
        map_after_capture = committed_map_identity(
            query_native_virtual_regions(api, barrier.handle)
        )
        before = set(snapshot.committed_map)
        after = set(map_after_capture)
        stable = snapshot.committed_map == map_after_capture
        attempts.append(
            {
                "attempt": attempt,
                "capture_ms": _duration_ms(started),
                "mapping_stable": stable,
                "removed_mapping_count": len(before - after),
                "added_mapping_count": len(after - before),
                "removed_mapping_first": sorted(before - after)[:8],
                "added_mapping_first": sorted(after - before)[:8],
            }
        )
        if stable:
            return snapshot, tuple(attempts), _duration_ms(total_started)
    raise NativeSnapshotUnknownError(
        "native snapshot observation did not reach a stable mapping epoch "
        f"after {maximum_attempts} attempts"
    )


def _capture_native_projection(
    reader: object,
    barrier: NativeCalculationBarrier,
    *,
    target_manager_frame: int,
) -> Route2NativeFutureBodyRootSlice:
    return capture_route2_native_future_body_root_slice(
        reader,
        root_identity=VersionIdentity.from_mapping(
            "th08-native-snapshot-branch-projection-v1",
            {
                "pid": barrier.pid,
                "target_manager_frame": target_manager_frame,
            },
        ),
        clock_version=VersionIdentity.from_mapping(
            "th08-native-snapshot-manager-clock-v1",
            {"manager_frame_semantics": "native_u32"},
        ),
        component_specs=route2_revalidated_native_root_component_specs(),
        active_slots_from_components=decode_route2_ordinary_pool_active_slots,
        maximum_attempts=1,
    )


def _projection_changes(
    left: Route2NativeFutureBodyRootSlice,
    right: Route2NativeFutureBodyRootSlice,
) -> tuple[dict[str, object], ...]:
    left_components = {component.spec.name: component for component in left.components}
    right_components = {
        component.spec.name: component for component in right.components
    }
    if left_components.keys() != right_components.keys():
        raise NativeSnapshotUnknownError(
            "native projection component inventory changed"
        )
    return tuple(
        {
            "name": name,
            "left_sha256": left_components[name].sha256,
            "right_sha256": right_components[name].sha256,
            "size": left_components[name].spec.size,
        }
        for name in sorted(left_components)
        if left_components[name].data != right_components[name].data
    )


def _projection_history_changes(
    left: tuple[Route2NativeFutureBodyRootSlice, ...],
    right: tuple[Route2NativeFutureBodyRootSlice, ...],
) -> tuple[dict[str, object], ...]:
    if len(left) != len(right):
        raise NativeSnapshotUnknownError(
            "native projection histories have different horizons"
        )
    changes: list[dict[str, object]] = []
    for tick_index, (left_tick, right_tick) in enumerate(zip(left, right, strict=True)):
        changes.extend(
            {"tick_index": tick_index, **change}
            for change in _projection_changes(left_tick, right_tick)
        )
    return tuple(changes)


def _projection_byte_changes(
    left: Route2NativeFutureBodyRootSlice,
    right: Route2NativeFutureBodyRootSlice,
    *,
    sample_limit: int = 128,
) -> tuple[dict[str, object], ...]:
    left_components = {component.spec.name: component for component in left.components}
    right_components = {
        component.spec.name: component for component in right.components
    }
    if left_components.keys() != right_components.keys():
        raise NativeSnapshotUnknownError(
            "native projection component inventory changed"
        )
    changes: list[dict[str, object]] = []
    for name in sorted(left_components):
        left_component = left_components[name]
        right_component = right_components[name]
        if left_component.data == right_component.data:
            continue
        offsets = [
            offset
            for offset, (before, after) in enumerate(
                zip(
                    left_component.data,
                    right_component.data,
                    strict=True,
                )
            )
            if before != after
        ]
        changes.append(
            {
                "name": name,
                "address": left_component.spec.address,
                "size": left_component.spec.size,
                "changed_byte_count": len(offsets),
                "samples": [
                    {
                        "offset": offset,
                        "address": left_component.spec.address + offset,
                        "headless": left_component.data[offset],
                        "natural": right_component.data[offset],
                    }
                    for offset in offsets[:sample_limit]
                ],
                "samples_truncated": len(offsets) > sample_limit,
            }
        )
    return tuple(changes)


def _rolling_branch(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    projection_reader: object,
    target_manager_frame: int,
    baseline_root: NativeSnapshot,
    root_header: NativeBarrierHeader,
    expected_thread_ids: tuple[int, ...],
    root_carrier: object,
    action_override: int | None,
    horizon: int,
    hold_frames: int,
) -> tuple[
    NativeSnapshot,
    tuple[Route2NativeFutureBodyRootSlice, ...],
    tuple[CollisionControlProjection, ...],
    tuple[dict[str, object], ...],
    tuple[NativeDirtyPage, ...],
    dict[str, object],
]:
    if horizon <= 0:
        raise ValueError("rolling native horizon must be positive")
    if hold_frames <= 0:
        raise ValueError("rolling native hold length must be positive")

    projections: list[Route2NativeFutureBodyRootSlice] = []
    collision_control_projections: list[CollisionControlProjection] = []
    compact_states: list[dict[str, object]] = []
    ticks: list[dict[str, object]] = []
    changed_action_addresses: list[int] = []
    for tick_index in range(horizon):
        carrier = resolve_native_replay_action_carrier(
            api,
            barrier.handle,
        )
        _assert_action_carrier_epoch(
            root_carrier,
            carrier,
            tick_index=tick_index,
        )
        recorded_action = int(carrier.recorded_mask)
        action = (
            int(action_override)
            if action_override is not None and tick_index < hold_frames
            else recorded_action
        )
        action_word_written = action != recorded_action
        if action_word_written:
            write_native_replay_action(
                api,
                barrier.handle,
                carrier,
                action,
            )
        changed_action_addresses.extend(
            carrier.input_cursor + index
            for index, (before, after) in enumerate(
                zip(
                    struct.pack("<H", recorded_action),
                    struct.pack("<H", action),
                    strict=True,
                )
            )
            if before != after
        )
        action_word = projection_reader.read(carrier.input_cursor, 2)
        if action_word != struct.pack("<H", action):
            raise NativeSnapshotUnknownError(
                "parameterized rolling replay action word did not verify"
            )
        _assert_thread_epoch(api, barrier.pid, expected_thread_ids)
        current_map = committed_map_identity(
            query_native_virtual_regions(api, barrier.handle)
        )
        if current_map != baseline_root.committed_map:
            raise NativeSnapshotUnknownError(
                "parameterizing a rolling replay action changed the mapping epoch"
            )

        started = time.perf_counter()
        endpoint_header = (
            barrier.step(timeout_seconds=5.0)
            if tick_index == 0
            else barrier.continue_step(timeout_seconds=5.0)
        )
        step_wait_ms = _duration_ms(started)
        _assert_endpoint_stack_and_clock(
            root_header,
            endpoint_header,
            completed_ticks=tick_index + 1,
        )
        _assert_thread_epoch(api, barrier.pid, expected_thread_ids)
        current_map = committed_map_identity(
            query_native_virtual_regions(api, barrier.handle)
        )
        if current_map != baseline_root.committed_map:
            raise NativeSnapshotUnknownError(
                "native mapping epoch changed after a rolling calculation tick"
            )

        started = time.perf_counter()
        projection = _capture_native_projection(
            projection_reader,
            barrier,
            target_manager_frame=target_manager_frame,
        )
        projection_capture_ms = _duration_ms(started)
        compact_state = _compact_state(projection_reader)
        started = time.perf_counter()
        collision_control_projection = capture_collision_control_projection(
            projection_reader,
            native_root_projection=projection,
            compact_state=compact_state,
        )
        collision_control_capture_ms = _duration_ms(started)
        expected_manager_frame = target_manager_frame + tick_index + 1
        if int(compact_state["manager_frame"]) != expected_manager_frame:
            raise NativeSnapshotUnknownError(
                "compact gameplay state is not aligned to the rolling endpoint"
            )
        projections.append(projection)
        collision_control_projections.append(collision_control_projection)
        compact_states.append(compact_state)
        ticks.append(
            {
                "tick_index": tick_index,
                "completed_ticks": tick_index + 1,
                "selected_action": action,
                "recorded_action": recorded_action,
                "action_word_written": action_word_written,
                "action_carrier": carrier.record(),
                "endpoint_header": endpoint_header.record(),
                "compact_state": compact_state,
                "native_projection": projection.record(),
                "collision_control_projection": (collision_control_projection.record()),
                "timing_ms": {
                    "step_wait": step_wait_ms,
                    "native_projection_capture": projection_capture_ms,
                    "collision_control_projection_capture": (
                        collision_control_capture_ms
                    ),
                },
            }
        )

    started = time.perf_counter()
    endpoint = recapture_native_snapshot(
        api,
        barrier.handle,
        baseline_root,
    )
    endpoint_capture_ms = _duration_ms(started)
    dirty_to_baseline = snapshot_dirty_pages(baseline_root, endpoint)
    return (
        endpoint,
        tuple(projections),
        tuple(collision_control_projections),
        tuple(compact_states),
        dirty_to_baseline,
        {
            "action_override": action_override,
            "hold_frames": min(hold_frames, horizon),
            "horizon": horizon,
            "parameterized_root_baseline_sha256": baseline_root.digest,
            "parameterized_action_changes": _compact_addresses(
                tuple(changed_action_addresses)
            ),
            "endpoint_sha256": endpoint.digest,
            "ticks": ticks,
            "dirty_to_baseline": _compact_dirty_pages(dirty_to_baseline),
            "timing_ms": {
                "endpoint_capture": endpoint_capture_ms,
            },
        },
    )


def _restore_baseline(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    baseline_root: NativeSnapshot,
    dirty_to_baseline: tuple[NativeDirtyPage, ...],
    expected_thread_ids: tuple[int, ...],
) -> dict[str, object]:
    started = time.perf_counter()
    restore_native_dirty_pages(
        api,
        barrier.handle,
        dirty_to_baseline,
    )
    restore_write_ms = _duration_ms(started)
    _assert_thread_epoch(api, barrier.pid, expected_thread_ids)

    started = time.perf_counter()
    current_map = committed_map_identity(
        query_native_virtual_regions(api, barrier.handle)
    )
    if current_map != baseline_root.committed_map:
        raise NativeSnapshotUnknownError(
            "native mapping epoch changed during dirty-page restore"
        )
    verify_native_dirty_pages(
        api,
        barrier.handle,
        dirty_to_baseline,
    )
    verify_dirty_ms = _duration_ms(started)
    started = time.perf_counter()
    header = barrier.mark_restore_ready(timeout_seconds=5.0)
    barrier_restore_ms = _duration_ms(started)
    return {
        "restored_sha256": baseline_root.digest,
        "restore_verification": ("mapping_epoch_and_all_dirty_spans_match_baseline"),
        "dirty_to_baseline": _compact_dirty_pages(dirty_to_baseline),
        "header": header.record(),
        "timing_ms": {
            "page_restore": restore_write_ms,
            "restore_verification_dirty_spans": verify_dirty_ms,
            "barrier_restore": barrier_restore_ms,
        },
    }


def _run_all36_portfolio(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    projection_reader: object,
    target_manager_frame: int,
    horizon: int,
    hold_frames: int,
    root_timeout_seconds: float,
    corpus_path: Path,
) -> dict[str, object]:
    transaction_started = time.perf_counter()
    corpus, corpus_record = _load_portfolio_corpus(
        corpus_path,
        target_manager_frame=target_manager_frame,
        horizon=horizon,
        hold_frames=hold_frames,
    )
    root_header = barrier.wait_for_root(
        timeout_seconds=root_timeout_seconds,
    )
    if (
        root_header.root_manager_frame != target_manager_frame
        or root_header.target_manager_frame != target_manager_frame
    ):
        raise NativeSnapshotUnknownError(
            "barrier stopped at an unexpected all-36 manager-frame root"
        )
    release_injected_keys(api)

    frozen = suspend_non_owner_threads(
        api,
        barrier.pid,
        owner_thread_id=root_header.owner_thread_id,
    )
    try:
        thread_ids = tuple(
            sorted(
                (
                    root_header.owner_thread_id,
                    *(thread.thread_id for thread in frozen),
                )
            )
        )
        _assert_thread_epoch(api, barrier.pid, thread_ids)
        virtual_regions = query_native_virtual_regions(
            api,
            barrier.handle,
        )
        excluded_bases = snapshot_excluded_allocation_bases(
            virtual_regions,
            owner_stack_pointer=root_header.root_esp,
            frozen_threads=frozen,
            remote_base=barrier.remote_base,
        )
        (
            baseline_root,
            baseline_stabilization,
            baseline_capture_ms,
        ) = _capture_stable_baseline(
            api,
            excluded_allocation_bases=excluded_bases,
            barrier=barrier,
        )
        carrier = resolve_native_replay_action_carrier(
            api,
            barrier.handle,
        )
        recorded_action = int(carrier.recorded_mask)
        if recorded_action & 0x02:
            raise NativeSnapshotUnknownError(
                "canonical replay root unexpectedly contains Bomb"
            )
        if recorded_action not in corpus:
            raise NativeSnapshotUnknownError(
                "recorded root action is absent from the all-36 corpus"
            )

        root_projection = _capture_native_projection(
            projection_reader,
            barrier,
            target_manager_frame=target_manager_frame,
        )
        root_compact_state = _compact_state(projection_reader)
        root_collision_control_projection = capture_collision_control_projection(
            projection_reader,
            native_root_projection=root_projection,
            compact_state=root_compact_state,
        )
        if int(root_compact_state["manager_frame"]) != target_manager_frame:
            raise NativeSnapshotUnknownError(
                "compact gameplay state is not aligned to the all-36 root"
            )

        canary_started = time.perf_counter()
        (
            _canary_endpoint,
            canary_projections,
            canary_collision_control,
            canary_compact,
            canary_dirty,
            canary_branch,
        ) = _rolling_branch(
            api,
            barrier,
            projection_reader=projection_reader,
            target_manager_frame=target_manager_frame,
            baseline_root=baseline_root,
            root_header=root_header,
            expected_thread_ids=thread_ids,
            root_carrier=carrier,
            action_override=None,
            horizon=horizon,
            hold_frames=hold_frames,
        )
        canary_restore = _restore_baseline(
            api,
            barrier,
            baseline_root=baseline_root,
            dirty_to_baseline=canary_dirty,
            expected_thread_ids=thread_ids,
        )
        canary_comparison = _compare_portfolio_branch_to_corpus(
            corpus[recorded_action],
            canary_branch,
        )
        canary_record = _compact_portfolio_branch_record(
            canary_branch,
            comparison=canary_comparison,
            restore=canary_restore,
            elapsed_ms=_duration_ms(canary_started),
        )

        branch_records: list[dict[str, object]] = []
        exact_count = 0
        outcome_class_exact_count = 0
        no_hit_masks: list[int] = []
        recorded_repeat_exact = False
        recorded_repeat_changes: dict[str, object] | None = None
        portfolio_started = time.perf_counter()
        for branch_index, mask in enumerate(PORTFOLIO_NO_BOMB_MASKS):
            print(
                (f"native snapshot all-36 {branch_index + 1:02d}/36 mask=0x{mask:02x}"),
                flush=True,
            )
            branch_started = time.perf_counter()
            (
                _endpoint,
                projections,
                collision_control,
                compact_states,
                dirty,
                branch,
            ) = _rolling_branch(
                api,
                barrier,
                projection_reader=projection_reader,
                target_manager_frame=target_manager_frame,
                baseline_root=baseline_root,
                root_header=root_header,
                expected_thread_ids=thread_ids,
                root_carrier=carrier,
                action_override=mask,
                horizon=horizon,
                hold_frames=hold_frames,
            )
            comparison = _compare_portfolio_branch_to_corpus(
                corpus[mask],
                branch,
            )
            restore = _restore_baseline(
                api,
                barrier,
                baseline_root=baseline_root,
                dirty_to_baseline=dirty,
                expected_thread_ids=thread_ids,
            )
            branch_record = _compact_portfolio_branch_record(
                branch,
                comparison=comparison,
                restore=restore,
                elapsed_ms=_duration_ms(branch_started),
            )
            branch_record["complete_mask"] = mask
            branch_records.append(branch_record)
            if bool(comparison["exact"]):
                exact_count += 1
            if bool(comparison["outcome_class_exact"]):
                outcome_class_exact_count += 1
            if comparison["observed_first_hit_manager_frame"] is None:
                no_hit_masks.append(mask)

            if mask == recorded_action:
                projection_changes = _projection_history_changes(
                    canary_projections,
                    projections,
                )
                collision_changes = tuple(
                    {
                        "tick_index": tick_index,
                        **change,
                    }
                    for tick_index, (left, right) in enumerate(
                        zip(
                            canary_collision_control,
                            collision_control,
                            strict=True,
                        )
                    )
                    for change in collision_control_projection_changes(
                        left,
                        right,
                    )
                )
                compact_exact = canary_compact == compact_states
                recorded_repeat_exact = (
                    not projection_changes and not collision_changes and compact_exact
                )
                recorded_repeat_changes = {
                    "native_projection_changes": list(projection_changes),
                    "collision_control_changes": list(collision_changes),
                    "compact_exact": compact_exact,
                }

        portfolio_elapsed_ms = _duration_ms(portfolio_started)
        portfolio_valid = (
            bool(canary_comparison["exact"])
            and outcome_class_exact_count == len(PORTFOLIO_NO_BOMB_MASKS)
            and recorded_repeat_exact
        )
        return {
            "status": (
                "rolling_native_all36_outcome_portfolio_passed"
                if portfolio_valid
                else "rolling_native_all36_outcome_portfolio_mismatch"
            ),
            "baseline_root": baseline_root.record(),
            "baseline_capture_ms": baseline_capture_ms,
            "baseline_mapping_stabilization": list(baseline_stabilization),
            "barrier_root": root_header.record(),
            "thread_epoch": {
                "thread_ids": list(thread_ids),
                "owner_thread_id": root_header.owner_thread_id,
                "frozen_thread_count": len(frozen),
            },
            "action_carrier": carrier.record(),
            "recorded_action": recorded_action,
            "root_native_projection": root_projection.record(),
            "root_collision_control_projection": (
                root_collision_control_projection.record()
            ),
            "root_compact_state": root_compact_state,
            "corpus": corpus_record,
            "recorded_action_canary": canary_record,
            "recorded_action_repeat_exact": recorded_repeat_exact,
            "recorded_action_repeat_changes": recorded_repeat_changes,
            "branches": branch_records,
            "branch_count": len(branch_records),
            "legacy_corpus_exact_count": exact_count,
            "legacy_corpus_outcome_class_exact_count": (outcome_class_exact_count),
            "legacy_corpus_comparison_authority": (
                "diagnostic_only_non_atomic_polling_observer"
            ),
            "no_hit_masks": no_hit_masks,
            "timing_ms": {
                "portfolio_36_branches": portfolio_elapsed_ms,
                "transaction_including_root_and_canary": _duration_ms(
                    transaction_started
                ),
            },
            "calculation_ticks_per_branch": horizon,
            "action_hold_frames": min(hold_frames, horizon),
            "render_ticks_per_branch": 0,
            "recorded_future_world_reused": True,
            "physical_predictive_authority": False,
            "authority": ("fixed_replay_root_collision_control_counterfactual_only"),
        }
    finally:
        release_frozen_threads(api, frozen)


def _run_transaction(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    projection_reader: object,
    target_manager_frame: int,
    action_b: int,
    horizon: int,
    hold_frames: int,
    root_timeout_seconds: float,
    reference_store: dict[str, object] | None = None,
) -> dict[str, object]:
    root_header = barrier.wait_for_root(
        timeout_seconds=root_timeout_seconds,
    )
    if (
        root_header.root_manager_frame != target_manager_frame
        or root_header.target_manager_frame != target_manager_frame
    ):
        raise NativeSnapshotUnknownError(
            "barrier stopped at an unexpected manager-frame root"
        )
    release_injected_keys(api)

    frozen = suspend_non_owner_threads(
        api,
        barrier.pid,
        owner_thread_id=root_header.owner_thread_id,
    )
    try:
        thread_ids = tuple(
            sorted(
                (
                    root_header.owner_thread_id,
                    *(thread.thread_id for thread in frozen),
                )
            )
        )
        _assert_thread_epoch(api, barrier.pid, thread_ids)
        virtual_regions = query_native_virtual_regions(
            api,
            barrier.handle,
        )
        excluded_bases = snapshot_excluded_allocation_bases(
            virtual_regions,
            owner_stack_pointer=root_header.root_esp,
            frozen_threads=frozen,
            remote_base=barrier.remote_base,
        )
        (
            baseline_root,
            baseline_stabilization,
            baseline_capture_ms,
        ) = _capture_stable_baseline(
            api,
            excluded_allocation_bases=excluded_bases,
            barrier=barrier,
        )
        carrier = resolve_native_replay_action_carrier(
            api,
            barrier.handle,
        )
        action_a = carrier.recorded_mask
        if action_a & 0x02:
            raise NativeSnapshotUnknownError(
                "canonical replay root unexpectedly contains Bomb"
            )
        if action_b == action_a:
            raise ValueError("action B must differ from the recorded action A")

        root_projection = _capture_native_projection(
            projection_reader,
            barrier,
            target_manager_frame=target_manager_frame,
        )
        root_compact_state = _compact_state(projection_reader)
        root_collision_control_projection = capture_collision_control_projection(
            projection_reader,
            native_root_projection=root_projection,
            compact_state=root_compact_state,
        )
        if int(root_compact_state["manager_frame"]) != target_manager_frame:
            raise NativeSnapshotUnknownError(
                "compact gameplay state is not aligned to the immutable root"
            )

        (
            endpoint_a1,
            projections_a1,
            collision_control_a1,
            compact_a1,
            dirty_a1,
            branch_a1,
        ) = _rolling_branch(
            api,
            barrier,
            projection_reader=projection_reader,
            target_manager_frame=target_manager_frame,
            baseline_root=baseline_root,
            root_header=root_header,
            expected_thread_ids=thread_ids,
            root_carrier=carrier,
            action_override=None,
            horizon=horizon,
            hold_frames=hold_frames,
        )
        restore_a1 = _restore_baseline(
            api,
            barrier,
            baseline_root=baseline_root,
            dirty_to_baseline=dirty_a1,
            expected_thread_ids=thread_ids,
        )

        (
            endpoint_a2,
            projections_a2,
            collision_control_a2,
            compact_a2,
            dirty_a2,
            branch_a2,
        ) = _rolling_branch(
            api,
            barrier,
            projection_reader=projection_reader,
            target_manager_frame=target_manager_frame,
            baseline_root=baseline_root,
            root_header=root_header,
            expected_thread_ids=thread_ids,
            root_carrier=carrier,
            action_override=None,
            horizon=horizon,
            hold_frames=hold_frames,
        )
        endpoint_aa_changes = changed_byte_addresses(
            endpoint_a1,
            endpoint_a2,
        )
        restore_a2 = _restore_baseline(
            api,
            barrier,
            baseline_root=baseline_root,
            dirty_to_baseline=dirty_a2,
            expected_thread_ids=thread_ids,
        )
        projection_aa_changes = _projection_history_changes(
            projections_a1,
            projections_a2,
        )
        collision_control_aa_changes = tuple(
            {
                "tick_index": tick_index,
                **change,
            }
            for tick_index, (left, right) in enumerate(
                zip(
                    collision_control_a1,
                    collision_control_a2,
                    strict=True,
                )
            )
            for change in collision_control_projection_changes(left, right)
        )
        compact_aa_exact = compact_a1 == compact_a2
        if (
            projection_aa_changes
            or collision_control_aa_changes
            or not compact_aa_exact
        ):
            return {
                "status": "same_action_rolling_native_nondeterministic",
                "baseline_root": baseline_root.record(),
                "baseline_capture_ms": baseline_capture_ms,
                "baseline_mapping_stabilization": list(baseline_stabilization),
                "barrier_root": root_header.record(),
                "thread_epoch": {
                    "thread_ids": list(thread_ids),
                    "owner_thread_id": root_header.owner_thread_id,
                    "frozen_thread_count": len(frozen),
                },
                "action_carrier": carrier.record(),
                "actions": {"a": action_a, "b_not_run": action_b},
                "root_native_projection": root_projection.record(),
                "root_collision_control_projection": (
                    root_collision_control_projection.record()
                ),
                "root_compact_state": root_compact_state,
                "branches": {
                    "a1": branch_a1,
                    "a2": branch_a2,
                },
                "restores": {
                    "after_a1": restore_a1,
                    "after_a2": restore_a2,
                },
                "same_action_endpoint_difference": (
                    _group_changes_by_region(
                        baseline_root,
                        endpoint_a1,
                        endpoint_a2,
                        endpoint_aa_changes,
                    )
                ),
                "same_action_projection_changes": list(projection_aa_changes),
                "same_action_collision_control_changes": list(
                    collision_control_aa_changes
                ),
                "same_action_compact_exact": compact_aa_exact,
                "same_action_compact_left": list(compact_a1),
                "same_action_compact_right": list(compact_a2),
                "calculation_ticks_per_branch": horizon,
                "render_ticks_per_branch": 0,
                "recorded_future_world_reused": True,
                "physical_predictive_authority": False,
                "external_effect_coverage": "demonstrably_incomplete",
            }

        (
            endpoint_b,
            projections_b,
            collision_control_b,
            compact_b,
            dirty_b,
            branch_b,
        ) = _rolling_branch(
            api,
            barrier,
            projection_reader=projection_reader,
            target_manager_frame=target_manager_frame,
            baseline_root=baseline_root,
            root_header=root_header,
            expected_thread_ids=thread_ids,
            root_carrier=carrier,
            action_override=action_b,
            horizon=horizon,
            hold_frames=hold_frames,
        )
        endpoint_ab_changes = changed_byte_addresses(
            endpoint_a1,
            endpoint_b,
        )
        projection_ab_changes = _projection_history_changes(
            projections_a1,
            projections_b,
        )
        collision_control_ab_changes = tuple(
            {
                "tick_index": tick_index,
                **change,
            }
            for tick_index, (left, right) in enumerate(
                zip(
                    collision_control_a1,
                    collision_control_b,
                    strict=True,
                )
            )
            for change in collision_control_projection_changes(left, right)
        )
        if not projection_ab_changes:
            raise NativeSnapshotUnknownError(
                "A/restore/B did not change the revalidated native gameplay projection"
            )
        restore_b = _restore_baseline(
            api,
            barrier,
            baseline_root=baseline_root,
            dirty_to_baseline=dirty_b,
            expected_thread_ids=thread_ids,
        )
        if reference_store is not None:
            reference_store.update(
                {
                    "root_projection": root_projection,
                    "root_collision_control_projection": (
                        root_collision_control_projection
                    ),
                    "a1_projections": projections_a1,
                    "a1_collision_control_projections": (collision_control_a1),
                    "b_projections": projections_b,
                    "b_collision_control_projections": collision_control_b,
                }
            )

        return {
            "status": "rolling_native_projection_snapshot_passed",
            "baseline_root": baseline_root.record(),
            "baseline_capture_ms": baseline_capture_ms,
            "baseline_mapping_stabilization": list(baseline_stabilization),
            "barrier_root": root_header.record(),
            "thread_epoch": {
                "thread_ids": list(thread_ids),
                "owner_thread_id": root_header.owner_thread_id,
                "frozen_thread_count": len(frozen),
            },
            "action_carrier": carrier.record(),
            "actions": {"a": action_a, "b": action_b},
            "root_native_projection": root_projection.record(),
            "root_collision_control_projection": (
                root_collision_control_projection.record()
            ),
            "root_compact_state": root_compact_state,
            "branches": {
                "a1": branch_a1,
                "a2": branch_a2,
                "b": branch_b,
            },
            "restores": {
                "after_a1": restore_a1,
                "after_a2": restore_a2,
                "after_b": restore_b,
            },
            "same_action_full_endpoint_exact": not endpoint_aa_changes,
            "same_action_full_endpoint_volatility": (
                _group_changes_by_region(
                    baseline_root,
                    endpoint_a1,
                    endpoint_a2,
                    endpoint_aa_changes,
                )
                if endpoint_aa_changes
                else None
            ),
            "same_action_native_projection_exact": True,
            "same_action_collision_control_projection_exact": True,
            "same_action_compact_exact": True,
            "different_action_unfiltered_endpoint_changes": (
                _compact_addresses(endpoint_ab_changes)
            ),
            "different_action_native_projection_changes": list(projection_ab_changes),
            "different_action_collision_control_changes": list(
                collision_control_ab_changes
            ),
            "different_action_compact_states": list(compact_b),
            "calculation_ticks_per_branch": horizon,
            "action_hold_frames": min(hold_frames, horizon),
            "render_ticks_per_branch": 0,
            "recorded_future_world_reused": True,
            "physical_predictive_authority": False,
            "external_effect_coverage": (
                "peripheral_process_state_not_deterministic"
                if endpoint_aa_changes
                else "unresolved"
            ),
        }
    finally:
        release_frozen_threads(api, frozen)


def _run_natural_reference(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    projection_reader: object,
    target_manager_frame: int,
    horizon: int,
    hold_frames: int,
    action_override: int | None,
    expected_branch: dict[str, object],
    expected_projections: tuple[Route2NativeFutureBodyRootSlice, ...],
    expected_collision_control_projections: tuple[CollisionControlProjection, ...],
    expected_root_projection: Route2NativeFutureBodyRootSlice,
    expected_root_collision_control_projection: CollisionControlProjection,
    expected_root_compact_state: dict[str, object],
) -> dict[str, object]:
    """Advance through the real frame pump and trap the next callsite seam."""

    root_header = barrier.header()
    if (
        root_header.root_manager_frame != target_manager_frame
        or root_header.status != STATUS_ROOT_WAIT
    ):
        raise NativeSnapshotUnknownError(
            "natural reference did not begin at the restored calculation root"
        )
    expected_ticks = expected_branch.get("ticks")
    if not isinstance(expected_ticks, list) or len(expected_ticks) != horizon:
        raise NativeSnapshotUnknownError(
            "natural reference has no matching headless tick history"
        )
    if len(expected_collision_control_projections) != horizon:
        raise NativeSnapshotUnknownError(
            "natural reference collision/control history has the wrong horizon"
        )

    root_projection = _capture_native_projection(
        projection_reader,
        barrier,
        target_manager_frame=target_manager_frame,
    )
    root_compact_state = _compact_state(projection_reader)
    root_collision_control_projection = capture_collision_control_projection(
        projection_reader,
        native_root_projection=root_projection,
        compact_state=root_compact_state,
    )
    root_projection_exact = root_projection.digest == expected_root_projection.digest
    root_collision_control_exact = (
        root_collision_control_projection.sha256
        == expected_root_collision_control_projection.sha256
    )
    root_compact_exact = root_compact_state == expected_root_compact_state
    if (
        not root_projection_exact
        or not root_collision_control_exact
        or not root_compact_exact
    ):
        raise NativeSnapshotUnknownError(
            "restored root changed before the natural reference began"
        )

    root_carrier = resolve_native_replay_action_carrier(
        api,
        barrier.handle,
    )
    ticks: list[dict[str, object]] = []
    any_mismatch = False
    for tick_index in range(horizon):
        before = barrier.header()
        if before.root_manager_frame != target_manager_frame + tick_index:
            raise NativeSnapshotUnknownError(
                "natural callsite trap reached an unexpected input frame"
            )
        if (
            before.owner_thread_id != root_header.owner_thread_id
            or before.root_esp != root_header.root_esp
            or before.root_ebp != root_header.root_ebp
        ):
            raise NativeSnapshotUnknownError(
                "natural frame pump changed the calculation-call owner or stack"
            )
        thread_ids_before = enumerate_target_thread_ids(api, barrier.pid)
        if root_header.owner_thread_id not in thread_ids_before:
            raise NativeSnapshotUnknownError(
                "natural reference lost its calculation owner thread"
            )
        map_before = committed_map_identity(
            query_native_virtual_regions(api, barrier.handle)
        )

        carrier = resolve_native_replay_action_carrier(
            api,
            barrier.handle,
        )
        _assert_action_carrier_epoch(
            root_carrier,
            carrier,
            tick_index=tick_index,
        )
        recorded_action = int(carrier.recorded_mask)
        action = (
            int(action_override)
            if action_override is not None and tick_index < hold_frames
            else recorded_action
        )
        action_word_written = action != recorded_action
        if action_word_written:
            write_native_replay_action(
                api,
                barrier.handle,
                carrier,
                action,
            )
        if projection_reader.read(carrier.input_cursor, 2) != struct.pack("<H", action):
            raise NativeSnapshotUnknownError(
                "natural reference replay action word did not verify"
            )

        started = time.perf_counter()
        next_header = barrier.natural_advance(timeout_seconds=5.0)
        natural_advance_ms = _duration_ms(started)
        expected_frame = target_manager_frame + tick_index + 1
        if next_header.root_manager_frame != expected_frame:
            raise NativeSnapshotUnknownError(
                "natural frame pump did not trap the next calculation frame"
            )
        thread_ids_after = enumerate_target_thread_ids(api, barrier.pid)
        if root_header.owner_thread_id not in thread_ids_after:
            raise NativeSnapshotUnknownError(
                "natural reference lost its calculation owner after frame-pump work"
            )
        map_after = committed_map_identity(
            query_native_virtual_regions(api, barrier.handle)
        )
        map_before_set = set(map_before)
        map_after_set = set(map_after)

        projection = _capture_native_projection(
            projection_reader,
            barrier,
            target_manager_frame=target_manager_frame,
        )
        compact_state = _compact_state(projection_reader)
        collision_control_projection = capture_collision_control_projection(
            projection_reader,
            native_root_projection=projection,
            compact_state=compact_state,
        )
        if int(compact_state["manager_frame"]) != expected_frame:
            raise NativeSnapshotUnknownError(
                "natural compact state is not aligned to the trapped callsite"
            )
        expected_tick = expected_ticks[tick_index]
        if not isinstance(expected_tick, dict):
            raise NativeSnapshotUnknownError(
                "headless reference tick has an invalid record"
            )
        expected_projection = expected_tick.get("native_projection")
        expected_compact = expected_tick.get("compact_state")
        projection_exact = (
            isinstance(expected_projection, dict)
            and projection.digest == expected_projection.get("sha256")
            and projection.digest == expected_projections[tick_index].digest
        )
        collision_control_exact = (
            collision_control_projection.sha256
            == expected_collision_control_projections[tick_index].sha256
        )
        compact_exact = compact_state == expected_compact
        projection_byte_changes = (
            ()
            if projection_exact
            else _projection_byte_changes(
                expected_projections[tick_index],
                projection,
            )
        )
        collision_control_changes = (
            ()
            if collision_control_exact
            else collision_control_projection_changes(
                expected_collision_control_projections[tick_index],
                collision_control_projection,
            )
        )
        any_mismatch = any_mismatch or not collision_control_exact or not compact_exact
        ticks.append(
            {
                "tick_index": tick_index,
                "manager_frame": expected_frame,
                "selected_action": action,
                "recorded_action": recorded_action,
                "action_word_written": action_word_written,
                "action_carrier": carrier.record(),
                "callsite_header": next_header.record(),
                "thread_epoch": {
                    "before_count": len(thread_ids_before),
                    "after_count": len(thread_ids_after),
                    "added": sorted(set(thread_ids_after) - set(thread_ids_before)),
                    "removed": sorted(set(thread_ids_before) - set(thread_ids_after)),
                    "owner_preserved": True,
                },
                "mapping_epoch": {
                    "before_count": len(map_before),
                    "after_count": len(map_after),
                    "added_count": len(map_after_set - map_before_set),
                    "removed_count": len(map_before_set - map_after_set),
                    "added_first": sorted(map_after_set - map_before_set)[:8],
                    "removed_first": sorted(map_before_set - map_after_set)[:8],
                },
                "compact_state": compact_state,
                "native_projection": projection.record(),
                "collision_control_projection": (collision_control_projection.record()),
                "headless_broad_projection_exact": projection_exact,
                "headless_collision_control_projection_exact": (
                    collision_control_exact
                ),
                "headless_compact_exact": compact_exact,
                "headless_broad_projection_byte_changes": list(projection_byte_changes),
                "headless_collision_control_changes": list(collision_control_changes),
                "natural_advance_ms": natural_advance_ms,
            }
        )

    return {
        "status": (
            "natural_frame_differential_mismatch"
            if any_mismatch
            else "natural_frame_differential_passed"
        ),
        "action_override": action_override,
        "horizon": horizon,
        "hold_frames": min(hold_frames, horizon),
        "root_projection_exact": root_projection_exact,
        "root_collision_control_projection_exact": (root_collision_control_exact),
        "root_compact_exact": root_compact_exact,
        "ticks": ticks,
        "frame_pump_work_included": True,
        "comparison_boundary": (
            "headless_post_calculation_vs_natural_next_pre_calculation_call"
        ),
        "broad_projection_is_diagnostic_not_acceptance_authority": True,
        "acceptance_authority": (
            "exact_collision_control_projection_and_compact_state"
        ),
        "physical_predictive_authority": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--armed", action="store_true")
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--launch-bat", type=Path)
    parser.add_argument("--replay-slot", type=int, default=DEFAULT_STAGE5_SLOT)
    parser.add_argument(
        "--expected-replay-sha256",
        default=DEFAULT_STAGE5_SHA256,
    )
    parser.add_argument("--route-id", type=int, default=2)
    parser.add_argument("--difficulty-index", type=int, default=3)
    parser.add_argument("--stage-route-index", type=int, default=5)
    parser.add_argument(
        "--target-manager-frame",
        type=int,
        default=DEFAULT_TARGET_MANAGER_FRAME,
    )
    parser.add_argument(
        "--action-b",
        type=lambda value: int(value, 0),
        default=DEFAULT_ACTION_B,
    )
    parser.add_argument("--horizon", type=int, default=DEFAULT_HORIZON)
    parser.add_argument(
        "--hold-frames",
        type=int,
        default=DEFAULT_HOLD_FRAMES,
    )
    parser.add_argument(
        "--compact-corpus",
        type=Path,
        default=DEFAULT_COMPACT_CORPUS,
        help=(
            "retained natural replay corpus used to verify the recorded "
            "action branch at every rolling endpoint"
        ),
    )
    parser.add_argument(
        "--compact-corpus-ticks",
        type=int,
        default=DEFAULT_COMPACT_CORPUS_TICKS,
        help="number of recorded-branch endpoints compared to the corpus",
    )
    parser.add_argument(
        "--portfolio-all36",
        action="store_true",
        help=(
            "run every canonical no-Bomb mask for one restored root and "
            "compare first-hit/survivor endpoints to the retained corpus"
        ),
    )
    parser.add_argument(
        "--portfolio-corpus",
        type=Path,
        default=DEFAULT_PORTFOLIO_CORPUS,
    )
    parser.add_argument(
        "--natural-reference",
        choices=("none", "a", "b"),
        default="a",
        help=(
            "after restored headless branches, advance the selected branch "
            "through the real frame pump and trap each next calculation call"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-timeout", type=float, default=30.0)
    parser.add_argument("--focus-timeout", type=float, default=10.0)
    parser.add_argument("--startup-settle", type=float, default=2.0)
    parser.add_argument("--menu-timeout", type=float, default=4.0)
    parser.add_argument("--tap-hold-ms", type=int, default=65)
    parser.add_argument("--tap-gap-ms", type=int, default=180)
    parser.add_argument("--screen-settle-ms", type=int, default=700)
    parser.add_argument("--gameplay-timeout", type=float, default=20.0)
    parser.add_argument("--root-timeout", type=float, default=90.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.armed:
        raise RuntimeError("native snapshot trial requires --armed")
    if (
        args.target_manager_frame <= 0
        or args.root_timeout <= 0.0
        or args.horizon <= 0
        or args.horizon > 16
        or args.hold_frames <= 0
        or args.compact_corpus_ticks <= 0
        or args.action_b < 0
        or args.action_b & ~SUPPORTED_INPUT_MASK
        or args.action_b & 0x02
    ):
        raise ValueError(
            "rolling trial requires horizon 1..16, positive hold/frame, "
            "and a supported no-Bomb action B"
        )
    if args.portfolio_all36 and args.natural_reference != "none":
        raise ValueError("all-36 portfolio mode requires --natural-reference none")

    game_dir = args.game_dir.resolve()
    expected_exe = game_dir / TARGET_EXE
    launch_bat = args.launch_bat or game_dir / DEFAULT_LAUNCH_BAT
    contract = validate_native_stage_replay(
        game_dir,
        slot=args.replay_slot,
        expected_sha256=args.expected_replay_sha256,
        expected_route_id=args.route_id,
        expected_difficulty_index=args.difficulty_index,
        expected_stage_route_index=args.stage_route_index,
    )
    envelope: dict[str, object] = {
        "schema": SCHEMA,
        "started_at": datetime.now().astimezone().isoformat(),
        "replay_contract": contract.compact_record(),
        "target_manager_frame": args.target_manager_frame,
        "horizon": args.horizon,
        "hold_frames": min(args.hold_frames, args.horizon),
        "natural_reference_branch": args.natural_reference,
        "compact_corpus": str(args.compact_corpus),
        "compact_corpus_ticks": args.compact_corpus_ticks,
        "portfolio_all36": args.portfolio_all36,
        "portfolio_corpus": str(args.portfolio_corpus),
        "gameplay_input": "native_replay_with_explicit_root_action_word",
        "changes_gameplay_input": True,
        "result": {"status": "not_started"},
    }
    launch_log = args.output.with_suffix(".launch.log")
    api = Win32()
    batch_process: subprocess.Popen[bytes] | None = None
    batch_log = None
    reader = None
    barrier: NativeCalculationBarrier | None = None
    pid: int | None = None
    try:
        if matching_targets(api, expected_exe):
            raise RuntimeError("verified TH08 is already running")
        batch_process, batch_log = launch_patch_batch(
            game_dir=game_dir,
            launch_bat=launch_bat,
            log_path=launch_log,
        )
        pid, identity = wait_for_patched_target(
            api,
            expected_exe=expected_exe,
            timeout_seconds=args.launch_timeout,
        )
        envelope["pid"] = pid
        envelope["executable_identity"] = identity
        focus_target_window(api, pid, timeout_seconds=args.focus_timeout)
        time.sleep(args.startup_settle)
        envelope["menu_trace"] = list(
            drive_native_stage_replay_menu(
                api,
                pid,
                contract=contract,
                hold_ms=args.tap_hold_ms,
                tap_gap_ms=args.tap_gap_ms,
                screen_settle_ms=args.screen_settle_ms,
                timeout_seconds=args.menu_timeout,
            )
        )
        reader, initial_state = wait_for_bound_replay_gameplay(
            api,
            pid,
            contract=contract,
            timeout_seconds=args.gameplay_timeout,
        )
        identity = verify_target(reader)
        envelope["initial_gameplay_state"] = initial_state
        envelope["executable_identity"] = identity
        if api.foreground_pid() != pid:
            raise RuntimeError(
                "native replay is not foreground before snapshot activation"
            )
        barrier = NativeCalculationBarrier.install(
            api,
            pid,
            target_manager_frame=args.target_manager_frame,
        )
        envelope["barrier"] = barrier.installation_record()
        send_scan_key(api, scan_code=0x1D, pressed=True)
        reference_store: dict[str, object] = {}
        transaction = (
            _run_all36_portfolio(
                api,
                barrier,
                projection_reader=reader,
                target_manager_frame=args.target_manager_frame,
                horizon=args.horizon,
                hold_frames=args.hold_frames,
                root_timeout_seconds=args.root_timeout,
                corpus_path=args.portfolio_corpus.resolve(),
            )
            if args.portfolio_all36
            else _run_transaction(
                api,
                barrier,
                projection_reader=reader,
                target_manager_frame=args.target_manager_frame,
                action_b=args.action_b,
                horizon=args.horizon,
                hold_frames=args.hold_frames,
                root_timeout_seconds=args.root_timeout,
                reference_store=reference_store,
            )
        )
        envelope["result"] = transaction
        if (
            not args.portfolio_all36
            and transaction["status"] == "rolling_native_projection_snapshot_passed"
        ):
            branches = transaction["branches"]
            assert isinstance(branches, dict)
            recorded_branch = branches["a1"]
            assert isinstance(recorded_branch, dict)
            corpus_comparison = _compact_corpus_comparison(
                args.compact_corpus.resolve(),
                target_manager_frame=args.target_manager_frame,
                branch=recorded_branch,
                comparison_ticks=args.compact_corpus_ticks,
            )
            transaction["recorded_action_compact_corpus"] = corpus_comparison
            if not corpus_comparison["exact"]:
                transaction["status"] = "recorded_action_compact_corpus_mismatch"
        if (
            not args.portfolio_all36
            and args.natural_reference != "none"
            and transaction["status"] == "rolling_native_projection_snapshot_passed"
        ):
            branches = transaction["branches"]
            assert isinstance(branches, dict)
            selected_branch = "a1" if args.natural_reference == "a" else "b"
            expected_branch = branches[selected_branch]
            assert isinstance(expected_branch, dict)
            root_projection = reference_store["root_projection"]
            expected_projections = reference_store[
                ("a1_projections" if args.natural_reference == "a" else "b_projections")
            ]
            expected_collision_control_projections = reference_store[
                (
                    "a1_collision_control_projections"
                    if args.natural_reference == "a"
                    else "b_collision_control_projections"
                )
            ]
            root_collision_control_projection = reference_store[
                "root_collision_control_projection"
            ]
            root_compact_state = transaction["root_compact_state"]
            assert isinstance(
                root_projection,
                Route2NativeFutureBodyRootSlice,
            )
            assert isinstance(expected_projections, tuple)
            assert isinstance(
                expected_collision_control_projections,
                tuple,
            )
            assert isinstance(
                root_collision_control_projection,
                CollisionControlProjection,
            )
            assert isinstance(root_compact_state, dict)
            natural_reference = _run_natural_reference(
                api,
                barrier,
                projection_reader=reader,
                target_manager_frame=args.target_manager_frame,
                horizon=args.horizon,
                hold_frames=args.hold_frames,
                action_override=(
                    None if args.natural_reference == "a" else args.action_b
                ),
                expected_branch=expected_branch,
                expected_projections=expected_projections,
                expected_collision_control_projections=(
                    expected_collision_control_projections
                ),
                expected_root_projection=root_projection,
                expected_root_collision_control_projection=(
                    root_collision_control_projection
                ),
                expected_root_compact_state=root_compact_state,
            )
            transaction["natural_reference"] = natural_reference
            if natural_reference["status"] != "natural_frame_differential_passed":
                transaction["status"] = natural_reference["status"]
    except Exception as exc:
        partial_result = envelope.get("result")
        error_result: dict[str, object] = {
            "status": "trial_error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "physical_predictive_authority": False,
        }
        if (
            isinstance(partial_result, dict)
            and partial_result.get("status") != "not_started"
        ):
            error_result["partial_result"] = partial_result
        envelope["result"] = error_result
        raise
    finally:
        cleanup_errors: list[str] = []
        try:
            release_injected_keys(api)
        except OSError as exc:
            cleanup_errors.append(f"release_injected_keys: {exc}")
        if reader is not None:
            reader.close()
        try:
            terminate_exact_target(api, expected_exe)
        except OSError as exc:
            cleanup_errors.append(f"terminate_exact_target: {exc}")
        if barrier is not None:
            barrier.close_after_target_termination()
        _stop_batch_process(batch_process)
        if batch_log is not None:
            batch_log.close()
        if cleanup_errors:
            envelope["cleanup_errors"] = cleanup_errors
        envelope["finished_at"] = datetime.now().astimezone().isoformat()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                envelope,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"native snapshot artifact: {args.output}", flush=True)

    result = envelope["result"]
    assert isinstance(result, dict)
    accepted_statuses = {
        "rolling_native_projection_snapshot_passed",
        "rolling_native_all36_outcome_portfolio_passed",
    }
    return 0 if result["status"] in accepted_statuses else 2


if __name__ == "__main__":
    raise SystemExit(main())
