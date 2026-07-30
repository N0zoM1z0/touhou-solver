#!/usr/bin/env python3
"""Search secondary no-Bomb actions from promoted rolling Native subroots."""

from __future__ import annotations

import argparse
import json
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
from th08_runtime.native_snapshot import (  # noqa: E402
    NativeBarrierRootCheckpoint,
    NativeCalculationBarrier,
    NativeDirtyPage,
    NativeSnapshot,
    NativeSnapshotUnknownError,
    committed_map_identity,
    query_native_virtual_regions,
    release_frozen_threads,
    resolve_native_replay_action_carrier,
    restore_native_dirty_pages,
    snapshot_excluded_allocation_bases,
    suspend_non_owner_threads,
    verify_native_dirty_pages,
)
from th08_runtime.native_combat_projection import (  # noqa: E402
    capture_native_combat_projection,
)
from th08_runtime.native_snapshot_projection import (  # noqa: E402
    capture_collision_control_projection,
    collision_control_projection_changes,
)
from th08_runtime_agent import (  # noqa: E402
    SUPPORTED_INPUT_MASK,
    TARGET_EXE,
    Win32,
    release_injected_keys,
    send_scan_key,
    verify_target,
)
from tools.th08_native_snapshot_trial import (  # noqa: E402
    DEFAULT_GAME_DIR,
    DEFAULT_STAGE5_SHA256,
    DEFAULT_STAGE5_SLOT,
    DEFAULT_TARGET_MANAGER_FRAME,
    PORTFOLIO_NO_BOMB_MASKS,
    _assert_action_carrier_epoch,
    _assert_mapping_epoch,
    _assert_thread_epoch,
    _capture_native_projection,
    _capture_stable_baseline,
    _compact_state,
    _duration_ms,
    _parse_action_schedule,
    _projection_history_changes,
    _restore_baseline,
    _rolling_branch,
    _validate_action_schedule,
)


SCHEMA = "th08-native-snapshot-causal-secondary-search-v4"
DEFAULT_PREFIX_MASKS = (0x14, 0x15, 0x90, 0x91, 0x94, 0x95)
DEFAULT_PREFIX_HORIZON = 8
DEFAULT_SECONDARY_HORIZON = 8
DEFAULT_HOLD_FRAMES = 3


def _parse_masks(value: str) -> tuple[int, ...]:
    try:
        masks = tuple(
            int(token.strip(), 0) for token in value.split(",") if token.strip()
        )
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "action masks must be comma-separated integers"
        ) from exc
    if not masks:
        raise argparse.ArgumentTypeError("at least one action mask is required")
    if len(set(masks)) != len(masks) or any(
        mask < 0 or mask & ~SUPPORTED_INPUT_MASK or mask & 0x02 for mask in masks
    ):
        raise argparse.ArgumentTypeError(
            "action masks must be unique, supported, and no-Bomb"
        )
    return masks


def _first_hit_manager_frame(
    compact_states: tuple[dict[str, object], ...],
) -> int | None:
    return next(
        (
            int(state["manager_frame"])
            for state in compact_states
            if int(state["player_phase"]) == 2
        ),
        None,
    )


def _compact_tick(tick: dict[str, object]) -> dict[str, object]:
    native_projection = tick.get("native_projection")
    collision_projection = tick.get("collision_control_projection")
    combat_projection = tick.get("native_combat_projection")
    if not isinstance(native_projection, dict) or not isinstance(
        collision_projection,
        dict,
    ) or not isinstance(combat_projection, dict):
        raise NativeSnapshotUnknownError(
            "causal-search tick omits a semantic projection"
        )
    return {
        "tick_index": tick["tick_index"],
        "completed_ticks": tick["completed_ticks"],
        "selected_action": tick["selected_action"],
        "recorded_action": tick["recorded_action"],
        "action_word_written": tick["action_word_written"],
        "action_carrier": tick["action_carrier"],
        "compact_state": tick["compact_state"],
        "native_projection_sha256": native_projection["sha256"],
        "collision_control_projection_sha256": collision_projection["sha256"],
        "collision_control_summary": collision_projection["summary"],
        "native_combat_projection_sha256": combat_projection["sha256"],
        "native_combat_summary": combat_projection["summary"],
        "timing_ms": tick["timing_ms"],
    }


def _compact_branch(
    branch: dict[str, object],
    *,
    first_hit_manager_frame: int | None,
    elapsed_ms: float,
    restore: dict[str, object] | None,
) -> dict[str, object]:
    ticks = branch.get("ticks")
    if not isinstance(ticks, list):
        raise NativeSnapshotUnknownError("causal-search branch has no tick history")
    endpoint_state = ticks[-1].get("compact_state") if ticks else None
    if not isinstance(endpoint_state, dict):
        raise NativeSnapshotUnknownError("causal-search branch has no compact endpoint")
    return {
        "action_override": branch["action_override"],
        "action_schedule": branch["action_schedule"],
        "hold_frames": branch["hold_frames"],
        "horizon": branch["horizon"],
        "root_baseline_sha256": branch["parameterized_root_baseline_sha256"],
        "endpoint_sha256": branch["endpoint_sha256"],
        "first_hit_manager_frame": first_hit_manager_frame,
        "survived_to_endpoint": first_hit_manager_frame is None,
        "endpoint": endpoint_state,
        "ticks": [_compact_tick(tick) for tick in ticks if isinstance(tick, dict)],
        "dirty_to_baseline": branch["dirty_to_baseline"],
        "endpoint_capture_timing_ms": branch["timing_ms"],
        "restore": restore,
        "branch_and_restore_elapsed_ms": elapsed_ms,
    }


def _collision_history_changes(
    left: tuple[object, ...],
    right: tuple[object, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "tick_index": tick_index,
            **change,
        }
        for tick_index, (left_tick, right_tick) in enumerate(
            zip(left, right, strict=True)
        )
        for change in collision_control_projection_changes(
            left_tick,
            right_tick,
        )
    )


def _restore_parent_root(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    parent_snapshot: NativeSnapshot,
    child_dirty_to_parent: tuple[NativeDirtyPage, ...],
    parent_checkpoint: NativeBarrierRootCheckpoint,
    expected_thread_ids: tuple[int, ...],
    parent_carrier: object,
) -> dict[str, object]:
    started = time.perf_counter()
    restore_native_dirty_pages(
        api,
        barrier.handle,
        child_dirty_to_parent,
    )
    page_restore_ms = _duration_ms(started)

    started = time.perf_counter()
    verify_native_dirty_pages(
        api,
        barrier.handle,
        child_dirty_to_parent,
    )
    current_map = committed_map_identity(
        query_native_virtual_regions(api, barrier.handle)
    )
    _assert_mapping_epoch(
        parent_snapshot.committed_map,
        current_map,
        context="mapping epoch changed while restoring the parent Native root",
    )
    _assert_thread_epoch(api, barrier.pid, expected_thread_ids)
    verify_ms = _duration_ms(started)

    started = time.perf_counter()
    restored_header = barrier.restore_root_checkpoint(parent_checkpoint)
    checkpoint_restore_ms = _duration_ms(started)
    restored_carrier = resolve_native_replay_action_carrier(
        api,
        barrier.handle,
    )
    _assert_action_carrier_epoch(
        parent_carrier,
        restored_carrier,
        tick_index=0,
    )
    if restored_carrier.recorded_mask != parent_carrier.recorded_mask:
        raise NativeSnapshotUnknownError(
            "parent replay action carrier did not restore exactly"
        )
    return {
        "restored_parent_snapshot_sha256": parent_snapshot.digest,
        "restored_parent_checkpoint": parent_checkpoint.record(),
        "restored_header": restored_header.record(),
        "restored_action_carrier": restored_carrier.record(),
        "verification": ("dirty_spans_mapping_thread_epoch_action_carrier_and_root_fx"),
        "timing_ms": {
            "page_restore": page_restore_ms,
            "dirty_span_and_epoch_verification": verify_ms,
            "root_checkpoint_restore": checkpoint_restore_ms,
        },
    }


def _run_secondary_search(
    api: object,
    barrier: NativeCalculationBarrier,
    *,
    projection_reader: object,
    target_manager_frame: int,
    prefix_masks: tuple[int, ...],
    prefix_action_schedule: tuple[int | None, ...] | None,
    secondary_masks: tuple[int, ...],
    prefix_horizon: int,
    secondary_horizon: int,
    hold_frames: int,
    root_timeout_seconds: float,
) -> dict[str, object]:
    transaction_started = time.perf_counter()
    if prefix_action_schedule is not None:
        _validate_action_schedule(
            prefix_action_schedule,
            horizon=prefix_horizon,
        )
        prefix_jobs: tuple[
            tuple[int | None, tuple[int | None, ...] | None],
            ...,
        ] = ((None, prefix_action_schedule),)
    else:
        prefix_jobs = tuple((mask, None) for mask in prefix_masks)
    root_header = barrier.wait_for_root(timeout_seconds=root_timeout_seconds)
    if (
        root_header.root_manager_frame != target_manager_frame
        or root_header.target_manager_frame != target_manager_frame
    ):
        raise NativeSnapshotUnknownError(
            "causal search stopped at an unexpected manager-frame root"
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
        regions = query_native_virtual_regions(api, barrier.handle)
        excluded_bases = snapshot_excluded_allocation_bases(
            regions,
            owner_stack_pointer=root_header.root_esp,
            frozen_threads=frozen,
            remote_base=barrier.remote_base,
        )
        (
            origin_snapshot,
            baseline_stabilization,
            baseline_capture_ms,
        ) = _capture_stable_baseline(
            api,
            barrier=barrier,
            excluded_allocation_bases=excluded_bases,
        )
        origin_checkpoint = barrier.capture_root_checkpoint()
        origin_carrier = resolve_native_replay_action_carrier(
            api,
            barrier.handle,
        )
        if origin_carrier.recorded_mask & 0x02:
            raise NativeSnapshotUnknownError(
                "canonical causal-search root unexpectedly contains Bomb"
            )
        origin_projection = _capture_native_projection(
            projection_reader,
            barrier,
            target_manager_frame=target_manager_frame,
        )
        origin_compact = _compact_state(projection_reader)
        origin_collision = capture_collision_control_projection(
            projection_reader,
            native_root_projection=origin_projection,
            compact_state=origin_compact,
        )
        origin_combat = capture_native_combat_projection(
            projection_reader,
            native_root_projection=origin_projection,
            compact_state=origin_compact,
        )

        (
            _canary_endpoint,
            canary_projections,
            canary_collision,
            canary_compact,
            canary_dirty,
            canary_branch,
        ) = _rolling_branch(
            api,
            barrier,
            projection_reader=projection_reader,
            target_manager_frame=target_manager_frame,
            baseline_root=origin_snapshot,
            root_header=root_header,
            expected_thread_ids=thread_ids,
            root_carrier=origin_carrier,
            action_override=None,
            horizon=prefix_horizon,
            hold_frames=hold_frames,
        )
        canary_restore = _restore_baseline(
            api,
            barrier,
            baseline_root=origin_snapshot,
            dirty_to_baseline=canary_dirty,
            expected_thread_ids=thread_ids,
        )

        prefix_results: list[dict[str, object]] = []
        total_continuations = 0
        all_survivors: list[dict[str, object]] = []
        search_started = time.perf_counter()
        for prefix_index, (prefix_mask, prefix_schedule) in enumerate(prefix_jobs):
            prefix_label = (
                f"mask=0x{prefix_mask:02x}"
                if prefix_mask is not None
                else "exact-schedule"
            )
            print(
                (
                    "causal prefix "
                    f"{prefix_index + 1:02d}/{len(prefix_jobs):02d} "
                    f"{prefix_label}"
                ),
                flush=True,
            )
            prefix_started = time.perf_counter()
            (
                prefix_endpoint,
                _prefix_projections,
                _prefix_collision,
                prefix_compact,
                prefix_dirty,
                prefix_branch,
            ) = _rolling_branch(
                api,
                barrier,
                projection_reader=projection_reader,
                target_manager_frame=target_manager_frame,
                baseline_root=origin_snapshot,
                root_header=barrier.header(),
                expected_thread_ids=thread_ids,
                root_carrier=origin_carrier,
                action_override=prefix_mask,
                horizon=prefix_horizon,
                hold_frames=hold_frames,
                action_schedule=prefix_schedule,
            )
            prefix_branch_elapsed_ms = _duration_ms(prefix_started)
            prefix_hit = _first_hit_manager_frame(prefix_compact)
            if prefix_hit is not None:
                raise NativeSnapshotUnknownError(
                    "declared causal prefix hit before the promotion frame"
                )

            subroot_checkpoint, subroot_header = barrier.promote_endpoint_to_root(
                timeout_seconds=5.0
            )
            expected_subroot_frame = target_manager_frame + prefix_horizon
            if subroot_header.root_manager_frame != expected_subroot_frame:
                raise NativeSnapshotUnknownError(
                    "promoted causal subroot reached an unexpected frame"
                )
            _assert_thread_epoch(api, barrier.pid, thread_ids)
            current_map = committed_map_identity(
                query_native_virtual_regions(api, barrier.handle)
            )
            _assert_mapping_epoch(
                prefix_endpoint.committed_map,
                current_map,
                context="mapping epoch changed while promoting a causal subroot",
            )
            subroot_carrier = resolve_native_replay_action_carrier(
                api,
                barrier.handle,
            )
            subroot_projection = _capture_native_projection(
                projection_reader,
                barrier,
                target_manager_frame=expected_subroot_frame,
            )
            subroot_compact = _compact_state(projection_reader)
            subroot_collision = capture_collision_control_projection(
                projection_reader,
                native_root_projection=subroot_projection,
                compact_state=subroot_compact,
            )
            subroot_combat = capture_native_combat_projection(
                projection_reader,
                native_root_projection=subroot_projection,
                compact_state=subroot_compact,
            )
            if subroot_compact != prefix_compact[-1]:
                raise NativeSnapshotUnknownError(
                    "promoted subroot compact state changed after promotion"
                )

            continuations: list[dict[str, object]] = []
            prefix_survivors: list[int] = []
            for continuation_index, continuation_mask in enumerate(secondary_masks):
                print(
                    (
                        "  secondary "
                        f"{continuation_index + 1:02d}/"
                        f"{len(secondary_masks):02d} "
                        f"mask=0x{continuation_mask:02x}"
                    ),
                    flush=True,
                )
                branch_started = time.perf_counter()
                (
                    _endpoint,
                    _projections,
                    _collision,
                    compact_states,
                    dirty,
                    branch,
                ) = _rolling_branch(
                    api,
                    barrier,
                    projection_reader=projection_reader,
                    target_manager_frame=expected_subroot_frame,
                    baseline_root=prefix_endpoint,
                    root_header=subroot_header,
                    expected_thread_ids=thread_ids,
                    root_carrier=subroot_carrier,
                    action_override=continuation_mask,
                    horizon=secondary_horizon,
                    hold_frames=hold_frames,
                )
                first_hit = _first_hit_manager_frame(compact_states)
                restore = _restore_baseline(
                    api,
                    barrier,
                    baseline_root=prefix_endpoint,
                    dirty_to_baseline=dirty,
                    expected_thread_ids=thread_ids,
                )
                continuations.append(
                    {
                        "complete_mask": continuation_mask,
                        **_compact_branch(
                            branch,
                            first_hit_manager_frame=first_hit,
                            elapsed_ms=_duration_ms(branch_started),
                            restore=restore,
                        ),
                    }
                )
                total_continuations += 1
                if first_hit is None:
                    prefix_survivors.append(continuation_mask)
                    all_survivors.append(
                        {
                            "prefix_mask": prefix_mask,
                            "prefix_action_schedule": (
                                list(prefix_schedule)
                                if prefix_schedule is not None
                                else None
                            ),
                            "continuation_mask": continuation_mask,
                        }
                    )

            parent_restore = _restore_parent_root(
                api,
                barrier,
                parent_snapshot=origin_snapshot,
                child_dirty_to_parent=prefix_dirty,
                parent_checkpoint=origin_checkpoint,
                expected_thread_ids=thread_ids,
                parent_carrier=origin_carrier,
            )
            prefix_results.append(
                {
                    "prefix_mask": prefix_mask,
                    "prefix_action_schedule": (
                        list(prefix_schedule) if prefix_schedule is not None else None
                    ),
                    "prefix": _compact_branch(
                        prefix_branch,
                        first_hit_manager_frame=None,
                        elapsed_ms=prefix_branch_elapsed_ms,
                        restore=None,
                    ),
                    "subroot": {
                        "manager_frame": expected_subroot_frame,
                        "snapshot_sha256": prefix_endpoint.digest,
                        "barrier_checkpoint": subroot_checkpoint.record(),
                        "action_carrier": subroot_carrier.record(),
                        "native_projection_sha256": subroot_projection.digest,
                        "collision_control_projection": (subroot_collision.record()),
                        "native_combat_projection": subroot_combat.record(),
                        "compact_state": subroot_compact,
                    },
                    "continuation_count": len(continuations),
                    "survivor_masks": prefix_survivors,
                    "continuations": continuations,
                    "parent_restore": parent_restore,
                }
            )

        (
            _repeat_endpoint,
            repeat_projections,
            repeat_collision,
            repeat_compact,
            repeat_dirty,
            repeat_branch,
        ) = _rolling_branch(
            api,
            barrier,
            projection_reader=projection_reader,
            target_manager_frame=target_manager_frame,
            baseline_root=origin_snapshot,
            root_header=barrier.header(),
            expected_thread_ids=thread_ids,
            root_carrier=origin_carrier,
            action_override=None,
            horizon=prefix_horizon,
            hold_frames=hold_frames,
        )
        repeat_restore = _restore_baseline(
            api,
            barrier,
            baseline_root=origin_snapshot,
            dirty_to_baseline=repeat_dirty,
            expected_thread_ids=thread_ids,
        )
        projection_changes = _projection_history_changes(
            canary_projections,
            repeat_projections,
        )
        collision_changes = _collision_history_changes(
            canary_collision,
            repeat_collision,
        )
        compact_exact = canary_compact == repeat_compact
        native_combat_exact = tuple(
            tick["native_combat_projection"]["sha256"]
            for tick in canary_branch["ticks"]
        ) == tuple(
            tick["native_combat_projection"]["sha256"]
            for tick in repeat_branch["ticks"]
        )
        parent_repeat_exact = (
            not projection_changes
            and not collision_changes
            and compact_exact
            and native_combat_exact
        )
        status = (
            "causal_secondary_search_passed"
            if parent_repeat_exact
            and total_continuations == len(prefix_jobs) * len(secondary_masks)
            else "causal_secondary_search_failed"
        )
        return {
            "status": status,
            "origin": {
                "manager_frame": target_manager_frame,
                "snapshot": origin_snapshot.record(include_regions=False),
                "barrier_checkpoint": origin_checkpoint.record(),
                "barrier_root": root_header.record(),
                "action_carrier": origin_carrier.record(),
                "native_projection_sha256": origin_projection.digest,
                "collision_control_projection": origin_collision.record(),
                "native_combat_projection": origin_combat.record(),
                "compact_state": origin_compact,
                "baseline_capture_ms": baseline_capture_ms,
                "baseline_mapping_stabilization": list(baseline_stabilization),
            },
            "thread_epoch": {
                "thread_ids": list(thread_ids),
                "owner_thread_id": root_header.owner_thread_id,
                "frozen_thread_count": len(frozen),
            },
            "prefix_horizon": prefix_horizon,
            "secondary_horizon": secondary_horizon,
            "action_hold_frames": hold_frames,
            "prefix_masks": list(prefix_masks),
            "prefix_action_schedule": (
                list(prefix_action_schedule)
                if prefix_action_schedule is not None
                else None
            ),
            "secondary_masks": list(secondary_masks),
            "prefixes": prefix_results,
            "total_continuations": total_continuations,
            "survivor_pairs": all_survivors,
            "parent_root_repeat": {
                "exact": parent_repeat_exact,
                "native_projection_changes": list(projection_changes),
                "collision_control_changes": list(collision_changes),
                "compact_exact": compact_exact,
                "native_combat_projection_exact": native_combat_exact,
                "canary": _compact_branch(
                    canary_branch,
                    first_hit_manager_frame=_first_hit_manager_frame(canary_compact),
                    elapsed_ms=0.0,
                    restore=canary_restore,
                ),
                "repeat": _compact_branch(
                    repeat_branch,
                    first_hit_manager_frame=_first_hit_manager_frame(repeat_compact),
                    elapsed_ms=0.0,
                    restore=repeat_restore,
                ),
            },
            "timing_ms": {
                "secondary_search": _duration_ms(search_started),
                "transaction": _duration_ms(transaction_started),
            },
            "recorded_future_world_reused": False,
            "physical_predictive_authority": False,
            "authority": (
                "fixed_replay_root_causal_continuation_native_counterfactual_only"
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
        "--prefix-masks",
        type=_parse_masks,
        default=DEFAULT_PREFIX_MASKS,
    )
    parser.add_argument(
        "--prefix-action-schedule",
        type=_parse_action_schedule,
        help=(
            "one exact per-tick causal prefix; use recorded, r, or - for "
            "a replay action tick and ignore --prefix-masks"
        ),
    )
    parser.add_argument(
        "--secondary-masks",
        type=_parse_masks,
        default=PORTFOLIO_NO_BOMB_MASKS,
    )
    parser.add_argument(
        "--prefix-horizon",
        type=int,
        default=DEFAULT_PREFIX_HORIZON,
    )
    parser.add_argument(
        "--secondary-horizon",
        type=int,
        default=DEFAULT_SECONDARY_HORIZON,
    )
    parser.add_argument(
        "--hold-frames",
        type=int,
        default=DEFAULT_HOLD_FRAMES,
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
        raise RuntimeError("native snapshot causal search requires --armed")
    if (
        args.target_manager_frame <= 0
        or args.root_timeout <= 0.0
        or not 1 <= args.prefix_horizon <= 32
        or not 1 <= args.secondary_horizon <= 16
        or args.hold_frames <= 0
    ):
        raise ValueError(
            "causal search requires a prefix horizon 1..32, a secondary "
            "horizon 1..16, and positive roots/holds"
        )
    if args.prefix_action_schedule is not None:
        _validate_action_schedule(
            args.prefix_action_schedule,
            horizon=args.prefix_horizon,
        )

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
        "prefix_horizon": args.prefix_horizon,
        "secondary_horizon": args.secondary_horizon,
        "hold_frames": args.hold_frames,
        "prefix_masks": list(args.prefix_masks),
        "prefix_action_schedule": (
            list(args.prefix_action_schedule)
            if args.prefix_action_schedule is not None
            else None
        ),
        "secondary_masks": list(args.secondary_masks),
        "changes_gameplay_input": True,
        "result": {"status": "not_started"},
    }
    launch_log = args.output.with_suffix(".launch.log")
    api = Win32()
    batch_process: subprocess.Popen[bytes] | None = None
    batch_log = None
    reader = None
    barrier: NativeCalculationBarrier | None = None
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
        # The launcher console can finish its last foreground transition during
        # startup settle. Reacquire immediately before the first guarded menu tap.
        focus_target_window(api, pid, timeout_seconds=args.focus_timeout)
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
        envelope["initial_gameplay_state"] = initial_state
        envelope["executable_identity"] = verify_target(reader)
        if api.foreground_pid() != pid:
            raise RuntimeError("native replay is not foreground before causal search")
        barrier = NativeCalculationBarrier.install(
            api,
            pid,
            target_manager_frame=args.target_manager_frame,
        )
        envelope["barrier"] = barrier.installation_record()
        send_scan_key(api, scan_code=0x1D, pressed=True)
        envelope["result"] = _run_secondary_search(
            api,
            barrier,
            projection_reader=reader,
            target_manager_frame=args.target_manager_frame,
            prefix_masks=args.prefix_masks,
            prefix_action_schedule=args.prefix_action_schedule,
            secondary_masks=args.secondary_masks,
            prefix_horizon=args.prefix_horizon,
            secondary_horizon=args.secondary_horizon,
            hold_frames=args.hold_frames,
            root_timeout_seconds=args.root_timeout,
        )
    except Exception as exc:
        partial = envelope.get("result")
        error_result: dict[str, object] = {
            "status": "causal_search_error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "physical_predictive_authority": False,
        }
        if isinstance(partial, dict) and partial.get("status") != "not_started":
            error_result["partial_result"] = partial
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
        print(f"causal search artifact: {args.output}", flush=True)

    result = envelope["result"]
    assert isinstance(result, dict)
    return 0 if result["status"] == "causal_secondary_search_passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
