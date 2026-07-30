#!/usr/bin/env python3
"""Publish scalar/native parity for asynchronous ordered-input issue."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from touhou_control.native.library import library_path  # noqa: E402
from touhou_control.native.ordered_input import (  # noqa: E402
    issue_ordered_input_state_asynchronously_native,
)
from touhou_control.ordered_input_transaction_oracle import (  # noqa: E402
    OrderedInputBelief,
    OrderedInputExactState,
    issue_ordered_input_belief_asynchronously,
    ordered_mask_path,
)


SUPPORTED_MASK = 0xF7
FORBIDDEN_MASK = 0x02
DEFAULT_DELAYS = (1, 2)
DEFAULT_CALLBACK_COUNTS = (0, 1, 2)
SOURCE_PATHS = (
    Path("scripts/analysis/async_ordered_input_native_differential.py"),
    Path("scripts/touhou_control/ordered_input_transaction_oracle.py"),
    Path("scripts/touhou_control/native/ordered_input.py"),
    Path("native/src/pipeline/ordered_input_transaction.cpp"),
    Path("native/src/abi/ordered_input_abi.cpp"),
    Path("native/include/touhou_native/abi.h"),
)


@dataclass(frozen=True)
class DifferentialCase:
    identity: str
    state: OrderedInputExactState
    selected_mask: int
    delays: tuple[int, ...]
    callback_counts: tuple[int, ...]
    evidence: str = "adversarial"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _state_record(state: OrderedInputExactState) -> dict:
    return {
        "active_mask": state.active_mask,
        "held_desired_mask": state.held_desired_mask,
        "queued_masks": list(state.queued_masks),
        "completion_remaining": state.completion_remaining,
    }


def _branch_record(branch) -> dict:
    return {
        "selected_mask": branch.selected_mask,
        "write_required": branch.write_required,
        "older_remaining": branch.older_remaining,
        "new_delay": branch.new_delay,
        "active_masks_consumed_during_dispatch": list(
            branch.active_masks_consumed_during_dispatch
        ),
        "publications_during_dispatch": list(
            branch.publications_during_dispatch
        ),
        "successor_state": _state_record(branch.successor_state),
    }


def _canonical_records(branches) -> list[dict]:
    records = [_branch_record(branch) for branch in branches]
    return sorted(
        records,
        key=lambda record: json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )


def _records_sha256(records: list[dict]) -> str:
    payload = json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def differential_cases() -> tuple[DifferentialCase, ...]:
    """Return the deterministic physical/adversarial parity corpus."""

    cases = [
        DifferentialCase(
            identity="physical_ce0193_0x65_to_0x41",
            state=OrderedInputExactState(0x65, 0x65),
            selected_mask=0x41,
            delays=DEFAULT_DELAYS,
            callback_counts=DEFAULT_CALLBACK_COUNTS,
            evidence="observed_physical_endpoint",
        ),
        DifferentialCase(
            identity="physical_superseded_0x04_target_to_0x05",
            state=OrderedInputExactState(
                active_mask=0x05,
                held_desired_mask=0x04,
                queued_masks=(0x04,),
                completion_remaining=2,
            ),
            selected_mask=0x05,
            delays=DEFAULT_DELAYS,
            callback_counts=DEFAULT_CALLBACK_COUNTS,
            evidence="observed_physical_replacement_censoring",
        ),
    ]
    masks = (0x00, 0x01, 0x04, 0x05, 0x40, 0x41, 0x44, 0x45, 0x84)
    for active_mask in masks:
        for selected_mask in masks:
            no_write = selected_mask == active_mask
            cases.append(
                DifferentialCase(
                    identity=(
                        f"settled_{active_mask:04x}_to_{selected_mask:04x}"
                    ),
                    state=OrderedInputExactState(active_mask, active_mask),
                    selected_mask=selected_mask,
                    delays=() if no_write else (1, 3),
                    callback_counts=() if no_write else (0, 1, 3),
                )
            )

    roots_and_targets = (
        (0x65, 0x41),
        (0x41, 0x84),
        (0x84, 0x05),
    )
    selected_masks = (0x00, 0x04, 0x41, 0x84)
    for root, held in roots_and_targets:
        path = ordered_mask_path(
            root,
            held,
            supported_mask=SUPPORTED_MASK,
            forbidden_mask=FORBIDDEN_MASK,
        )
        for prefix_count in range(len(path)):
            active = root if prefix_count == 0 else path[prefix_count - 1]
            state = OrderedInputExactState(
                active_mask=active,
                held_desired_mask=held,
                queued_masks=path[prefix_count:],
                completion_remaining=2,
            )
            for selected_mask in selected_masks:
                no_write = selected_mask == held
                cases.append(
                    DifferentialCase(
                        identity=(
                            f"pending_{root:04x}_{held:04x}_"
                            f"p{prefix_count}_to_{selected_mask:04x}"
                        ),
                        state=state,
                        selected_mask=selected_mask,
                        delays=() if no_write else DEFAULT_DELAYS,
                        callback_counts=(
                            () if no_write else (0, 2)
                        ),
                    )
                )
    return tuple(cases)


def build_report() -> dict:
    """Run every exact branch differential and return a compact report."""

    case_results = []
    mismatches = []
    physical_witnesses = []
    total_scalar_branches = 0
    total_native_branches = 0
    for case in differential_cases():
        scalar = issue_ordered_input_belief_asynchronously(
            OrderedInputBelief.from_states((case.state,)),
            selected_mask=case.selected_mask,
            post_dispatch_delay_support=case.delays,
            dispatch_callback_count_support=case.callback_counts,
            supported_mask=SUPPORTED_MASK,
            forbidden_mask=FORBIDDEN_MASK,
        )
        native = issue_ordered_input_state_asynchronously_native(
            case.state,
            selected_mask=case.selected_mask,
            post_dispatch_delay_support=case.delays,
            dispatch_callback_count_support=case.callback_counts,
            supported_mask=SUPPORTED_MASK,
            forbidden_mask=FORBIDDEN_MASK,
        )
        scalar_records = _canonical_records(scalar)
        native_records = _canonical_records(native)
        matches = scalar_records == native_records
        total_scalar_branches += len(scalar_records)
        total_native_branches += len(native_records)
        result = {
            "identity": case.identity,
            "evidence": case.evidence,
            "state": _state_record(case.state),
            "selected_mask": case.selected_mask,
            "post_dispatch_delay_support": list(case.delays),
            "dispatch_callback_count_support": list(
                case.callback_counts
            ),
            "scalar_branch_count": len(scalar_records),
            "native_branch_count": len(native_records),
            "branch_set_sha256": _records_sha256(scalar_records),
            "matches": matches,
        }
        case_results.append(result)
        if case.evidence.startswith("observed_physical"):
            physical_witnesses.append(
                {
                    **result,
                    "exact_branches": scalar_records,
                }
            )
        if not matches and len(mismatches) < 8:
            mismatches.append(
                {
                    "case": asdict(case),
                    "scalar": scalar_records,
                    "native": native_records,
                }
            )

    binary = library_path()
    passed = not mismatches and all(
        result["matches"] for result in case_results
    )
    return {
        "schema_version": "th08.async_ordered_input_native_differential.v1",
        "authority": {
            "status": "offline_implementation_parity_only",
            "live_action_authority": False,
            "hard_survival_authority": False,
            "physical_support_upper_bound": False,
            "note": (
                "Observed callback supports are proposal inputs only; "
                "scalar/native parity does not validate physical completeness."
            ),
        },
        "platform": "windows" if os.name == "nt" else "linux",
        "native_binary": {
            "path": str(binary.relative_to(ROOT)),
            "sha256": _sha256(binary),
        },
        "source_sha256": {
            path.as_posix(): _sha256(ROOT / path)
            for path in SOURCE_PATHS
        },
        "scope": {
            "supported_mask": SUPPORTED_MASK,
            "forbidden_mask": FORBIDDEN_MASK,
            "case_count": len(case_results),
            "scalar_branch_count": total_scalar_branches,
            "native_branch_count": total_native_branches,
            "physical_witness_count": len(physical_witnesses),
        },
        "physical_witness_provenance": {
            "stage5_run": "lunatic_route2_stage5_unattended_20260730_083416",
            "priority17_report_sha256": (
                "395ce5384e14e815afe6a5ce1977b165a94344906f3eb483a56c2484056be9b8"
            ),
            "ce0193": (
                "ordered intermediate endpoint 0x65 -> 0x61 -> 0x41"
            ),
            "replacement_censoring": (
                "0x04 transient target superseded by 0x05 before observation"
            ),
        },
        "case_results": case_results,
        "physical_witnesses": physical_witnesses,
        "retained_mismatches": mismatches,
        "integrity": {
            "passed": passed,
            "mismatch_count": sum(
                not result["matches"] for result in case_results
            ),
            "all_case_digests_present": all(
                len(result["branch_set_sha256"]) == 64
                for result in case_results
            ),
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
