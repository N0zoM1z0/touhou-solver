#!/usr/bin/env python3
"""Publish causal input-history/future-body schedule pairing evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from th08_causal_future_body_schedule import (  # noqa: E402
    Route2CausalFutureBodyScheduleFamily,
    Route2ConditionedFutureBodySchedule,
    merge_route2_causal_future_body_observation_classes,
    project_route2_causal_future_body_decision_branches,
)
from th08_enemy_mode import (  # noqa: E402
    ENEMY_ACTIVE_FLAG,
    ENEMY_CONTACT_ENABLED_FLAG,
)
from th08_future_body_schedule import (  # noqa: E402
    Route2FutureBodyFrame,
    Route2FutureBodySample,
    Route2FutureBodyScheduleBranch,
    Route2FutureBodyScheduleSet,
)
from touhou_control.ordered_input_transaction_oracle import (  # noqa: E402
    OrderedInputBelief,
    OrderedInputExactState,
)
from touhou_control.pipeline_identity import VersionIdentity  # noqa: E402


SUPPORTED_MASK = 0xF7
BODY_FLAGS = ENEMY_ACTIVE_FLAG | ENEMY_CONTACT_ENABLED_FLAG
SOURCE_PATHS = (
    Path(
        "scripts/analysis/"
        "th08_causal_future_body_schedule_differential.py"
    ),
    Path("scripts/th08_causal_future_body_schedule.py"),
    Path("scripts/th08_future_body_schedule.py"),
    Path("scripts/th08_enemy_mode.py"),
    Path(
        "scripts/touhou_control/"
        "ordered_input_transaction_oracle.py"
    ),
)


@dataclass(frozen=True)
class Case:
    identity: str
    family: Route2CausalFutureBodyScheduleFamily
    input_belief: OrderedInputBelief
    action_masks: dict[str, int]
    delays: tuple[int, ...]
    callbacks: tuple[int, ...]
    cadence: tuple[int, ...]
    initial_mode_state: tuple[int, bool, int]
    expected_final_x: dict[tuple[int, ...], float]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _float32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def _body(x: float) -> Route2FutureBodySample:
    return Route2FutureBodySample(
        identity=0x1000,
        base_flags=BODY_FLAGS,
        x=x,
        y=96.0,
        half_width=8.0,
        half_height=12.0,
        uncertainty=0.0,
    )


def _schedule(
    identity: str,
    history: tuple[int, ...],
    final_x: float,
) -> Route2FutureBodyScheduleSet:
    frames = tuple(
        Route2FutureBodyFrame(
            physical_step=step,
            bodies=(
                _body(final_x if step == len(history) else 32.0),
            ),
        )
        for step in range(1, len(history) + 1)
    )
    branch = Route2FutureBodyScheduleBranch(frames)
    return Route2FutureBodyScheduleSet.from_branches(
        root_physical_update=500,
        clock_version=VersionIdentity.from_mapping(
            "causal-future-body-differential-clock-v1",
            {"physical_update": True},
        ),
        source=identity,
        source_sha256=hashlib.sha256(
            identity.encode("ascii")
        ).hexdigest(),
        branches=(branch,),
    )


def _family(
    identity: str,
    *,
    selected_action: str,
    selected_mask: int,
    expected_final_x: dict[tuple[int, ...], float],
) -> Route2CausalFutureBodyScheduleFamily:
    return Route2CausalFutureBodyScheduleFamily.from_members(
        selected_action=selected_action,
        selected_mask=selected_mask,
        members=tuple(
            Route2ConditionedFutureBodySchedule(
                history,
                _schedule(
                    f"{identity}_{'_'.join(map(str, history))}",
                    history,
                    final_x,
                ),
            )
            for history, final_x in expected_final_x.items()
        ),
    )


def _settled(mask: int) -> OrderedInputBelief:
    return OrderedInputBelief.from_states(
        (OrderedInputExactState(mask, mask),)
    )


def differential_cases() -> tuple[Case, ...]:
    direction_histories = {
        (0x21, 0x01): 16.0,
        (0x21, 0x21): 48.0,
        (0x21, 0x41): 80.0,
    }
    focus_histories = {
        (0x01, 0x01, 0x01): 40.0,
        (0x01, 0x01, 0x05): 56.0,
        (0x01, 0x05, 0x05): 72.0,
    }
    return (
        Case(
            identity="two_edge_direction_reversal",
            family=_family(
                "direction",
                selected_action="right_shot",
                selected_mask=0x41,
                expected_final_x=direction_histories,
            ),
            input_belief=_settled(0x21),
            action_masks={
                "shot": 0x01,
                "left_shot": 0x21,
                "right_shot": 0x41,
            },
            delays=(1, 2),
            callbacks=(0,),
            cadence=(2,),
            initial_mode_state=(0, False, 0),
            expected_final_x=direction_histories,
        ),
        Case(
            identity="asynchronous_focus_acquire",
            family=_family(
                "focus",
                selected_action="focus_shot",
                selected_mask=0x05,
                expected_final_x=focus_histories,
            ),
            input_belief=_settled(0x01),
            action_masks={
                "shot": 0x01,
                "focus_shot": 0x05,
            },
            delays=(1, 2),
            callbacks=(0, 1),
            cadence=(3,),
            initial_mode_state=(0, False, 4),
            expected_final_x=focus_histories,
        ),
    )


def _case_record(case: Case) -> tuple[dict[str, object], int]:
    branches = project_route2_causal_future_body_decision_branches(
        family=case.family,
        input_belief=case.input_belief,
        selected_action=case.family.selected_action,
        action_masks=case.action_masks,
        supported_mask=SUPPORTED_MASK,
        post_dispatch_delay_frames=case.delays,
        dispatch_callback_count_support=case.callbacks,
        decision_frame_support=case.cadence,
        initial_mode_state=case.initial_mode_state,
    )
    schedule_by_history = {
        member.active_mask_history: member.schedule.digest
        for member in case.family.members
    }
    rows = []
    mismatch_count = 0
    for branch in branches:
        actual_history = tuple(
            frame.active_mask
            for frame in branch.mode_branch.hazard_branch.frames
        )
        expected_x = case.expected_final_x.get(actual_history)
        observed_x_bits = branch.observed_body_state[0][2]
        matches = (
            actual_history == branch.conditioned_active_mask_history
            and expected_x is not None
            and observed_x_bits == _float32_bits(expected_x)
            and branch.supplied_schedule_version
            == schedule_by_history[actual_history]
        )
        mismatch_count += not matches
        rows.append(
            {
                "active_mask_history": list(actual_history),
                "conditioned_history": list(
                    branch.conditioned_active_mask_history
                ),
                "schedule_sha256": (
                    branch.supplied_schedule_version
                ),
                "schedule_branch_sha256": (
                    branch.supplied_schedule_branch
                ),
                "observed_x_bits": f"0x{observed_x_bits:08x}",
                "expected_x_bits": (
                    None
                    if expected_x is None
                    else f"0x{_float32_bits(expected_x):08x}"
                ),
                "matches": matches,
            }
        )

    converged_family = _family(
        f"{case.identity}_converged",
        selected_action=case.family.selected_action,
        selected_mask=case.family.selected_mask,
        expected_final_x={
            history: 64.0 for history in case.expected_final_x
        },
    )
    converged = project_route2_causal_future_body_decision_branches(
        family=converged_family,
        input_belief=case.input_belief,
        selected_action=converged_family.selected_action,
        action_masks=case.action_masks,
        supported_mask=SUPPORTED_MASK,
        post_dispatch_delay_frames=case.delays,
        dispatch_callback_count_support=case.callbacks,
        decision_frame_support=case.cadence,
        initial_mode_state=case.initial_mode_state,
    )
    converged_classes = (
        merge_route2_causal_future_body_observation_classes(
            converged,
            base_observation=lambda _branch, _frame: "same_other_fields",
        )
    )
    input_branch_count = len(branches)
    schedule_count = len(case.family.members)
    return (
        {
            "identity": case.identity,
            "family": case.family.record(),
            "reachable_history_count": len(
                case.expected_final_x
            ),
            "input_branch_count": input_branch_count,
            "conditioned_schedule_count": schedule_count,
            "naive_cartesian_pair_count": (
                input_branch_count * schedule_count
            ),
            "causal_pair_count": len(branches),
            "incompatible_pair_count": mismatch_count,
            "converged_observation_class_count": len(
                converged_classes
            ),
            "branches": rows,
        },
        mismatch_count,
    )


def build_report() -> dict[str, object]:
    cases = []
    mismatch_count = 0
    naive_pairs = 0
    causal_pairs = 0
    for case in differential_cases():
        row, local_mismatches = _case_record(case)
        cases.append(row)
        mismatch_count += local_mismatches
        naive_pairs += int(row["naive_cartesian_pair_count"])
        causal_pairs += int(row["causal_pair_count"])
    return {
        "schema_version": (
            "th08.causal_future_body_schedule_differential.v1"
        ),
        "authority": {
            "status": "offline_conditioned_schedule_family_only",
            "physical_predictive_authority": False,
            "live_action_authority": False,
            "hard_survival_authority": False,
        },
        "native_boundary": {
            "observed_order": [
                "stage_timelines",
                "slot_allocation_and_immediate_initial_vm",
                "ascending_480_slot_enemy_loop",
                "mode_sync_ecl_motion_lifecycle",
                "contact_and_player_shot_damage",
            ],
            "predictive_producer_available": False,
            "open_event_classes": [
                "live_timeline_root_and_allocation_generation",
                "complete_main_and_auxiliary_vm",
                "final_world_geometry_and_non_mode_flags",
                "despawn_damage_phase_and_shared_rng",
                "joint_external_scheduler_support",
            ],
            "ida_database_changes": [
                {
                    "address": "0x0042C180",
                    "name": "enemy_clamp_internal_motion_bounds",
                },
                {
                    "address": "0x0042DEB0",
                    "name": (
                        "enemy_advance_internal_motion_component"
                    ),
                },
            ],
        },
        "source_sha256": {
            path.as_posix(): _sha256(ROOT / path)
            for path in SOURCE_PATHS
        },
        "scope": {
            "case_count": len(cases),
            "naive_cartesian_pair_count": naive_pairs,
            "causal_pair_count": causal_pairs,
            "rejected_incompatible_pair_count": (
                naive_pairs - causal_pairs
            ),
        },
        "cases": cases,
        "integrity": {
            "passed": mismatch_count == 0,
            "mismatch_count": mismatch_count,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as destination:
        destination.write(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
    return 0 if report["integrity"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
