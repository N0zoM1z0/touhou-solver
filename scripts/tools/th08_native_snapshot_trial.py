#!/usr/bin/env python3
"""Run a same-root A/restore/A and A/restore/B native one-tick trial."""

from __future__ import annotations

import argparse
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
from th08_runtime_agent import (  # noqa: E402
    SUPPORTED_INPUT_MASK,
    TARGET_EXE,
    Win32,
    release_injected_keys,
    send_scan_key,
    verify_target,
)
from touhou_control.pipeline_identity import VersionIdentity  # noqa: E402


SCHEMA = "th08-native-snapshot-one-tick-trial-v1"
DEFAULT_GAME_DIR = Path(
    "D:/Entertainment/Game/Touhou/[th08] 东方永夜抄 (日文版)__codex_wind_tunnel"
)
DEFAULT_STAGE5_SLOT = 15
DEFAULT_STAGE5_SHA256 = (
    "de1e4e941adc8c2899eb3ae1bedd2b4faaf14362d4ce2af984d1c9e5a32da613"
)
DEFAULT_TARGET_MANAGER_FRAME = 2129
DEFAULT_ACTION_B = 0x15


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
) -> None:
    if (
        endpoint_header.endpoint_esp != root_header.root_esp
        or endpoint_header.endpoint_ebp != root_header.root_ebp
    ):
        raise NativeSnapshotUnknownError(
            "one update-chain call did not return to the exact root stack"
        )
    if endpoint_header.endpoint_manager_frame != (root_header.root_manager_frame + 1):
        raise NativeSnapshotUnknownError(
            "one update-chain call did not advance manager time by one"
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


def _branch(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    projection_reader: object,
    target_manager_frame: int,
    baseline_root: NativeSnapshot,
    root_header: NativeBarrierHeader,
    expected_thread_ids: tuple[int, ...],
    carrier: object,
    action: int,
) -> tuple[
    NativeSnapshot,
    Route2NativeFutureBodyRootSlice,
    tuple[NativeDirtyPage, ...],
    dict[str, object],
]:
    action_word_written = action != int(carrier.recorded_mask)
    if action_word_written:
        write_native_replay_action(
            api,
            barrier.handle,
            carrier,
            action,
        )
    baseline_mask = int(carrier.recorded_mask)
    root_changes = tuple(
        carrier.input_cursor + index
        for index, (before, after) in enumerate(
            zip(
                struct.pack("<H", baseline_mask),
                struct.pack("<H", action),
                strict=True,
            )
        )
        if before != after
    )
    action_word = projection_reader.read(carrier.input_cursor, 2)
    if action_word != struct.pack("<H", action):
        raise NativeSnapshotUnknownError(
            "parameterized replay action word did not verify"
        )
    current_map = committed_map_identity(
        query_native_virtual_regions(api, barrier.handle)
    )
    if current_map != baseline_root.committed_map:
        raise NativeSnapshotUnknownError(
            "parameterizing the replay action changed the mapping epoch"
        )

    started = time.perf_counter()
    endpoint_header = barrier.step(timeout_seconds=5.0)
    step_wait_ms = _duration_ms(started)
    _assert_endpoint_stack_and_clock(root_header, endpoint_header)
    _assert_thread_epoch(api, barrier.pid, expected_thread_ids)

    started = time.perf_counter()
    endpoint = recapture_native_snapshot(
        api,
        barrier.handle,
        baseline_root,
    )
    endpoint_capture_ms = _duration_ms(started)
    started = time.perf_counter()
    projection = _capture_native_projection(
        projection_reader,
        barrier,
        target_manager_frame=target_manager_frame,
    )
    projection_capture_ms = _duration_ms(started)
    dirty_to_baseline = snapshot_dirty_pages(baseline_root, endpoint)
    return (
        endpoint,
        projection,
        dirty_to_baseline,
        {
            "action": action,
            "action_word_written": action_word_written,
            "parameterized_root_baseline_sha256": baseline_root.digest,
            "parameterized_root_changes": _compact_addresses(root_changes),
            "endpoint_sha256": endpoint.digest,
            "endpoint_header": endpoint_header.record(),
            "native_projection": projection.record(),
            "dirty_to_baseline": _compact_dirty_pages(dirty_to_baseline),
            "timing_ms": {
                "step_wait": step_wait_ms,
                "endpoint_capture": endpoint_capture_ms,
                "native_projection_capture": projection_capture_ms,
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


def _run_transaction(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    projection_reader: object,
    target_manager_frame: int,
    action_b: int,
    root_timeout_seconds: float,
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

        endpoint_a1, projection_a1, dirty_a1, branch_a1 = _branch(
            api,
            barrier,
            projection_reader=projection_reader,
            target_manager_frame=target_manager_frame,
            baseline_root=baseline_root,
            root_header=root_header,
            expected_thread_ids=thread_ids,
            carrier=carrier,
            action=action_a,
        )
        restore_a1 = _restore_baseline(
            api,
            barrier,
            baseline_root=baseline_root,
            dirty_to_baseline=dirty_a1,
            expected_thread_ids=thread_ids,
        )

        endpoint_a2, projection_a2, dirty_a2, branch_a2 = _branch(
            api,
            barrier,
            projection_reader=projection_reader,
            target_manager_frame=target_manager_frame,
            baseline_root=baseline_root,
            root_header=root_header,
            expected_thread_ids=thread_ids,
            carrier=carrier,
            action=action_a,
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
        projection_aa_changes = _projection_changes(
            projection_a1,
            projection_a2,
        )
        if projection_aa_changes:
            return {
                "status": "same_action_native_projection_nondeterministic",
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
                "calculation_ticks_per_branch": 1,
                "render_ticks_per_branch": 0,
                "recorded_future_world_reused": True,
                "physical_predictive_authority": False,
                "external_effect_coverage": "demonstrably_incomplete",
            }

        endpoint_b, projection_b, dirty_b, branch_b = _branch(
            api,
            barrier,
            projection_reader=projection_reader,
            target_manager_frame=target_manager_frame,
            baseline_root=baseline_root,
            root_header=root_header,
            expected_thread_ids=thread_ids,
            carrier=carrier,
            action=action_b,
        )
        endpoint_ab_changes = changed_byte_addresses(
            endpoint_a1,
            endpoint_b,
        )
        projection_ab_changes = _projection_changes(
            projection_a1,
            projection_b,
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

        return {
            "status": "one_tick_native_projection_snapshot_passed",
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
            "different_action_unfiltered_endpoint_changes": (
                _compact_addresses(endpoint_ab_changes)
            ),
            "different_action_native_projection_changes": list(projection_ab_changes),
            "calculation_ticks_per_branch": 1,
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
        or args.action_b < 0
        or args.action_b & ~SUPPORTED_INPUT_MASK
        or args.action_b & 0x02
    ):
        raise ValueError("action B must be a supported no-Bomb mask and frame positive")

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
        envelope["result"] = _run_transaction(
            api,
            barrier,
            projection_reader=reader,
            target_manager_frame=args.target_manager_frame,
            action_b=args.action_b,
            root_timeout_seconds=args.root_timeout,
        )
    except Exception as exc:
        envelope["result"] = {
            "status": "trial_error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "physical_predictive_authority": False,
        }
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
    return 0 if result["status"] == "one_tick_native_projection_snapshot_passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
