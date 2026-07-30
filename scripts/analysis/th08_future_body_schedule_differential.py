#!/usr/bin/env python3
"""Publish offline body-set parity for immutable future schedule sets."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from th08_enemy_mode import (  # noqa: E402
    ENEMY_ACTIVE_FLAG,
    ENEMY_CONTACT_ENABLED_FLAG,
    ENEMY_MANAGER_BLOCKING_FLAGS,
    ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG,
    ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG,
    ENEMY_SECONDARY_CHARACTER_SYNC_FLAG,
)
from th08_future_body_schedule import (  # noqa: E402
    Route2FutureBodyFrame,
    Route2FutureBodySample,
    Route2FutureBodyScheduleBranch,
    Route2FutureBodyScheduleSet,
    merge_route2_versioned_async_mode_observation_classes,
    project_route2_versioned_async_mode_decision_branches,
)
from touhou_control.ordered_input_transaction_oracle import (  # noqa: E402
    OrderedInputBelief,
    OrderedInputExactState,
)
from touhou_control.pipeline_identity import VersionIdentity  # noqa: E402


SUPPORTED_MASK = 0xF7
ACTION_MASKS = {
    "shot": 0x01,
    "focus_shot": 0x05,
}
CE0176_FLAGS = 0x0100114D
SYNC_CONTACT_DAMAGE = (
    ENEMY_ACTIVE_FLAG
    | ENEMY_CONTACT_ENABLED_FLAG
    | ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG
    | ENEMY_SECONDARY_CHARACTER_SYNC_FLAG
)
SOURCE_PATHS = (
    Path("scripts/analysis/th08_future_body_schedule_differential.py"),
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
    schedule: Route2FutureBodyScheduleSet
    input_belief: OrderedInputBelief
    selected_action: str
    delays: tuple[int, ...]
    dispatch_callbacks: tuple[int, ...]
    cadence: tuple[int, ...]
    initial_mode_state: tuple[int, bool, int]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _body(
    identity: int,
    flags: int,
    *,
    x: float,
) -> Route2FutureBodySample:
    return Route2FutureBodySample(
        identity=identity,
        base_flags=flags,
        x=x,
        y=96.0,
        half_width=8.0,
        half_height=12.0,
        uncertainty=0.0,
    )


def _branch(
    frames: tuple[tuple[Route2FutureBodySample, ...], ...],
) -> Route2FutureBodyScheduleBranch:
    return Route2FutureBodyScheduleBranch(
        tuple(
            Route2FutureBodyFrame(step, bodies)
            for step, bodies in enumerate(frames, start=1)
        )
    )


def _schedule(
    *,
    identity: str,
    branches: tuple[Route2FutureBodyScheduleBranch, ...],
) -> Route2FutureBodyScheduleSet:
    source_sha256 = hashlib.sha256(identity.encode("ascii")).hexdigest()
    return Route2FutureBodyScheduleSet.from_branches(
        root_physical_update=10064,
        clock_version=VersionIdentity.from_mapping(
            "th08-priority9-11-physical-update-fixture-v1",
            {
                "manager_frame_is_clock": False,
                "offline_fixture": True,
            },
        ),
        source=identity,
        source_sha256=source_sha256,
        branches=branches,
    )


def _settled(mask: int) -> OrderedInputBelief:
    return OrderedInputBelief.from_states(
        (OrderedInputExactState(mask, mask),)
    )


def _ce0176_case() -> Case:
    final_bodies = tuple(
        _body(slot, CE0176_FLAGS, x=float(16 + slot * 16))
        for slot in range(16)
    )
    return Case(
        identity="ce0176_frame_10065_to_10075_semantic_fixture",
        schedule=_schedule(
            identity="ce0176_semantic_flags_with_synthetic_geometry",
            branches=(
                _branch(((), (), (), (), (), (), (), final_bodies)),
            ),
        ),
        input_belief=_settled(0x01),
        selected_action="shot",
        delays=(),
        dispatch_callbacks=(),
        cadence=(8,),
        initial_mode_state=(1, True, 7),
    )


def _focus_acquire_case() -> Case:
    bodies = (_body(0x1000, SYNC_CONTACT_DAMAGE, x=64.0),)
    return Case(
        identity="async_focus_acquire",
        schedule=_schedule(
            identity="adversarial_focus_acquire",
            branches=(_branch((bodies, bodies, bodies)),),
        ),
        input_belief=_settled(0x01),
        selected_action="focus_shot",
        delays=(1, 2),
        dispatch_callbacks=(0, 1),
        cadence=(3,),
        initial_mode_state=(0, False, 4),
    )


def _hidden_geometry_case() -> Case:
    converged = (_body(0x1000, SYNC_CONTACT_DAMAGE, x=48.0),)
    return Case(
        identity="hidden_geometry_history_converges_before_observation",
        schedule=_schedule(
            identity="adversarial_hidden_geometry",
            branches=(
                _branch(
                    (
                        (_body(0x1000, SYNC_CONTACT_DAMAGE, x=32.0),),
                        converged,
                    )
                ),
                _branch(
                    (
                        (_body(0x1000, SYNC_CONTACT_DAMAGE, x=40.0),),
                        converged,
                    )
                ),
            ),
        ),
        input_belief=_settled(0x01),
        selected_action="shot",
        delays=(),
        dispatch_callbacks=(),
        cadence=(2,),
        initial_mode_state=(0, False, 0),
    )


def differential_cases() -> tuple[Case, ...]:
    return (
        _ce0176_case(),
        _focus_acquire_case(),
        _hidden_geometry_case(),
    )


def _oracle_mode_step(
    state: tuple[int, bool, int],
    *,
    focused: bool,
) -> tuple[int, bool, int]:
    previous_focus, secondary, counter = state
    if focused:
        counter = counter + 1 if previous_focus == 1 else 0
        if counter >= 7:
            secondary = True
        next_focus = 1
    else:
        counter = 0 if previous_focus != 0 else counter + 1
        if counter >= 7:
            secondary = False
        next_focus = 0
    return next_focus, secondary, counter


def _oracle_body_sets(
    bodies: tuple[Route2FutureBodySample, ...],
    *,
    secondary: bool,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    contact = []
    damage = []
    for body in bodies:
        flags = body.base_flags
        if (
            flags & ENEMY_ACTIVE_FLAG
            and flags & ENEMY_SECONDARY_CHARACTER_SYNC_FLAG
        ):
            if secondary:
                flags |= ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG
            else:
                flags &= ~ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG
        gate = bool(
            flags & ENEMY_ACTIVE_FLAG
            and not flags & ENEMY_MANAGER_BLOCKING_FLAGS
        )
        if gate and flags & ENEMY_CONTACT_ENABLED_FLAG:
            contact.append(body.identity)
        if gate and flags & ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG:
            damage.append(body.identity)
    return tuple(contact), tuple(damage)


def _branch_record(case: Case, branch) -> tuple[dict[str, object], int]:
    schedule_branch = next(
        candidate
        for candidate in case.schedule.branches
        if candidate.digest == branch.future_schedule_branch
    )
    oracle_mode = case.initial_mode_state
    frames = []
    mismatch_count = 0
    for frame in branch.mode_branch.hazard_branch.frames:
        oracle_mode = _oracle_mode_step(
            oracle_mode,
            focused=bool(frame.active_mask & 0x04),
        )
        bodies = schedule_branch.frames[frame.physical_step - 1].bodies
        contact, damage = _oracle_body_sets(
            bodies,
            secondary=oracle_mode[1],
        )
        matches = (
            frame.mode_state_after == oracle_mode
            and frame.contact_body_ids == contact
            and frame.player_shot_damage_body_ids == damage
        )
        mismatch_count += not matches
        frames.append(
            {
                "physical_step": frame.physical_step,
                "active_mask": frame.active_mask,
                "mode_state": list(frame.mode_state_after),
                "contact_body_ids": list(frame.contact_body_ids),
                "damage_body_ids": list(
                    frame.player_shot_damage_body_ids
                ),
                "oracle_mode_state": list(oracle_mode),
                "oracle_contact_body_ids": list(contact),
                "oracle_damage_body_ids": list(damage),
                "matches": matches,
            }
        )
    return (
        {
            "schedule_branch_sha256": branch.future_schedule_branch,
            "cadence_frames": branch.mode_branch.cadence_frames,
            "issue": {
                "dispatch_callbacks": (
                    branch.mode_branch.hazard_branch.issue_branch
                    .dispatch_callback_count
                ),
                "publications_during_dispatch": list(
                    branch.mode_branch.hazard_branch.issue_branch
                    .publications_during_dispatch
                ),
            },
            "next_observed_body_state": [
                list(body) for body in branch.observed_body_state
            ],
            "frames": frames,
        },
        mismatch_count,
    )


def build_report() -> dict:
    case_rows = []
    total_branches = 0
    total_frames = 0
    mismatch_count = 0
    for case in differential_cases():
        branches = project_route2_versioned_async_mode_decision_branches(
            future_schedule=case.schedule,
            input_belief=case.input_belief,
            selected_action=case.selected_action,
            action_masks=ACTION_MASKS,
            supported_mask=SUPPORTED_MASK,
            post_dispatch_delay_frames=case.delays,
            dispatch_callback_count_support=case.dispatch_callbacks,
            decision_frame_support=case.cadence,
            initial_mode_state=case.initial_mode_state,
        )
        branch_rows = []
        for branch in branches:
            row, branch_mismatches = _branch_record(case, branch)
            branch_rows.append(row)
            mismatch_count += branch_mismatches
            total_frames += len(row["frames"])
        total_branches += len(branches)
        classes = merge_route2_versioned_async_mode_observation_classes(
            branches,
            base_observation=lambda _branch, frame: (
                frame.contact_body_ids,
                frame.player_shot_damage_body_ids,
            ),
        )
        case_rows.append(
            {
                "identity": case.identity,
                "future_schedule": case.schedule.record(),
                "selected_action": case.selected_action,
                "initial_mode_state": list(case.initial_mode_state),
                "branch_count": len(branches),
                "observation_class_count": len(classes),
                "branches": branch_rows,
            }
        )

    ce0176 = case_rows[0]
    ce0176_last_frames = [
        branch["frames"][-1] for branch in ce0176["branches"]
    ]
    ce0176_passed = bool(ce0176_last_frames) and all(
        frame["contact_body_ids"] == list(range(16))
        and frame["damage_body_ids"] == list(range(16))
        for frame in ce0176_last_frames
    )
    return {
        "schema_version": "th08.future_body_schedule_differential.v1",
        "authority": {
            "status": "offline_fixture_composition_only",
            "physical_predictive_authority": False,
            "hard_survival_authority": False,
            "geometry_note": (
                "CE-0176 body flags/count are retained semantic evidence; "
                "fixture geometry is synthetic and has no physical authority."
            ),
        },
        "producer_audit": {
            "complete_predictive_producer_available": False,
            "live_future_coverage": "UNKNOWN_from_root_plus_one",
            "missing_classes": [
                "unseen_enemy_births",
                "future_non_mode_flag_writes",
                "despawns_and_transforms",
                "per_physical_update_geometry",
                "joint_scheduler_cadence_support",
            ],
        },
        "physical_provenance": {
            "ce0176_frames": [10065, 10068, 10071, 10073, 10075],
            "ce0176_final_body_count": 16,
            "ce0176_final_flags": CE0176_FLAGS,
            "stage5_raw_sha256": (
                "773cbdb322dc5e15f80da4800ce82bcd0f41c1e6f82826812087edc9a328dca9"
            ),
        },
        "source_sha256": {
            path.as_posix(): _sha256(ROOT / path)
            for path in SOURCE_PATHS
        },
        "scope": {
            "case_count": len(case_rows),
            "branch_count": total_branches,
            "frame_comparison_count": total_frames,
        },
        "cases": case_rows,
        "integrity": {
            "passed": mismatch_count == 0 and ce0176_passed,
            "mismatch_count": mismatch_count,
            "ce0176_semantic_capsule_passed": ce0176_passed,
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
