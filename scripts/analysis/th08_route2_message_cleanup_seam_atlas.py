#!/usr/bin/env python3
"""Build the Route-2 message-cleanup/item-homing seam atlas."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from th08_ecl import parse_ecl


SCHEMA = "th08-route2-message-cleanup-seam-atlas-v1"
EXPECTED_CONTENT_MANIFEST_SHA256 = (
    "3a52b6f485ada63c833f77ae8cd1653f469ae4fadeef3c38336a737c7e753ae1"
)
ROUTE_ID = 2
DIFFICULTY_INDEX = 3
DIFFICULTY_MASK = 0x08
MESSAGE_START_OPCODE = 0x06


@dataclass(frozen=True)
class StageSpec:
    key: str
    label: str
    route_stage_index: int
    ecl_name: str


STAGES = (
    StageSpec("stage1", "Stage 1", 0, "ecldata1.ecl"),
    StageSpec("stage2", "Stage 2", 1, "ecldata2.ecl"),
    StageSpec("stage3", "Stage 3", 2, "ecldata3.ecl"),
    StageSpec("stage4a", "Stage 4A / Reimu", 3, "ecldata4a.ecl"),
    StageSpec("stage5", "Stage 5", 5, "ecldata5.ecl"),
    StageSpec("final_b", "Final B / Kaguya", 7, "ecldata7.ecl"),
)


class MessageCleanupAtlasError(ValueError):
    """Raised when immutable content or seam semantics cannot be preserved."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def _content_assets(
    manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise MessageCleanupAtlasError("content manifest assets are missing")
    result: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("category") != "ecl":
            continue
        name = asset.get("name")
        if not isinstance(name, str) or name in result:
            raise MessageCleanupAtlasError(
                "content manifest has invalid or duplicate ECL assets"
            )
        result[name] = asset
    return result


def _stage_rows(
    *,
    decoded_dir: Path,
    stage: StageSpec,
    assets: dict[str, dict[str, Any]],
) -> dict[str, object]:
    ecl = parse_ecl(decoded_dir / stage.ecl_name)
    asset = assets.get(stage.ecl_name)
    if asset is None:
        raise MessageCleanupAtlasError(
            f"content manifest omits {stage.ecl_name}"
        )
    if (
        asset.get("decoded_sha256") != ecl.sha256
        or asset.get("thtk_decoded_sha256") != ecl.sha256
        or asset.get("thtk_repository_payload_exact_match") is not True
    ):
        raise MessageCleanupAtlasError(
            f"decoded ECL identity mismatch for {stage.ecl_name}"
        )

    occurrences: list[dict[str, object]] = []
    for timeline in ecl.timelines:
        for instruction in timeline.instructions:
            if (
                instruction.opcode != MESSAGE_START_OPCODE
                or not instruction.difficulty_mask & DIFFICULTY_MASK
            ):
                continue
            if len(instruction.arguments) != 1:
                raise MessageCleanupAtlasError(
                    f"timeline 0x06 at {instruction.offset:#x} does not "
                    "have one selector argument"
                )
            selector = _signed(instruction.arguments[0])
            occurrences.append(
                {
                    "symbolic_id": (
                        f"{ecl.path.name}:timeline:{timeline.index}:"
                        f"0x{instruction.offset:08x}"
                    ),
                    "timeline_index": timeline.index,
                    "file_offset": instruction.offset,
                    "instruction_time": instruction.time,
                    "opcode": instruction.opcode,
                    "opcode_hex": "0x06",
                    "opcode_name": "start_message_script_and_cleanup",
                    "difficulty_mask": instruction.difficulty_mask,
                    "size": instruction.size,
                    "message_script_selector": selector,
                    "native_semantics_key": "timeline:0x06",
                    "static_status": (
                        "lunatic_eligible_timeline_schedule_candidate"
                    ),
                    "runtime_execution_observed": False,
                }
            )
    occurrences.sort(
        key=lambda row: (
            int(row["timeline_index"]),
            int(row["file_offset"]),
        )
    )
    return {
        "key": stage.key,
        "label": stage.label,
        "route_stage_index": stage.route_stage_index,
        "ecl_name": stage.ecl_name,
        "ecl_sha256": ecl.sha256,
        "timeline_count": ecl.header.timeline_count,
        "occurrence_count": len(occurrences),
        "occurrences": occurrences,
    }


def build_message_cleanup_atlas(
    *,
    decoded_dir: Path,
    content_manifest_path: Path,
) -> dict[str, object]:
    if _sha256_path(content_manifest_path) != EXPECTED_CONTENT_MANIFEST_SHA256:
        raise MessageCleanupAtlasError(
            "unexpected immutable content-manifest SHA-256"
        )
    manifest = json.loads(content_manifest_path.read_bytes())
    if (
        manifest.get("schema") != "th08-immutable-content-manifest-v1"
        or manifest.get("classification", {}).get(
            "content_identity_gate_passed"
        )
        is not True
    ):
        raise MessageCleanupAtlasError(
            "content manifest has no identity authority"
        )
    assets = _content_assets(manifest)
    stages = [
        _stage_rows(
            decoded_dir=decoded_dir,
            stage=stage,
            assets=assets,
        )
        for stage in STAGES
    ]
    report: dict[str, object] = {
        "schema": SCHEMA,
        "taskbook_cards": [
            "CONTENT-02",
            "COMBAT-KILL-01",
            "POWER-ROUTE-01",
        ],
        "status": "route_wide_static_seams_and_item_subtransition_exact",
        "immutable_content_manifest": {
            "path": (
                "artifacts/runtime_reports/"
                "th08_immutable_content_manifest_20260731.json"
            ),
            "sha256": EXPECTED_CONTENT_MANIFEST_SHA256,
            "content_set_sha256": manifest["content_scope"][
                "content_set_sha256"
            ],
        },
        "route_profile": {
            "team": "Sakuya/Remilia",
            "route_id": ROUTE_ID,
            "difficulty": "Lunatic",
            "difficulty_index": DIFFICULTY_INDEX,
            "difficulty_mask": DIFFICULTY_MASK,
            "natural_route_stages": [stage.key for stage in STAGES],
        },
        "stage_count": len(stages),
        "occurrence_count": sum(
            int(stage["occurrence_count"]) for stage in stages
        ),
        "stage_occurrence_counts": {
            str(stage["key"]): int(stage["occurrence_count"])
            for stage in stages
        },
        "native_semantics": {
            "timeline_dispatch": "0x0042abd2",
            "message_start": "0x0043396d",
            "enemy_cleanup": "0x0042efb0",
            "item_homing": "0x004413e0",
            "ordered_boundary": (
                "message state reset and selector branches; eligible enemy "
                "HP zero, score-item allocation, parent unlink, and end-sub "
                "start; then all active items forced homing"
            ),
        },
        "post_allocation_item_subtransition": {
            "implementation": (
                "th08_item_pool.force_all_active_items_homing"
            ),
            "input_boundary": (
                "the complete item pool after every same-update message "
                "cleanup score-item allocation"
            ),
            "writes": {
                "motion_state": 1,
                "velocity_x": 0.0,
                "velocity_y": -0.5,
            },
            "preserves": [
                "slot identity",
                "active-list order",
                "allocation cursor",
                "position",
                "timer",
                "item type",
                "full-value flag",
                "resources",
                "RNG state and call count",
            ],
            "immediate_pickup_or_resource_commit": False,
        },
        "stages": stages,
        "classification": {
            "route_wide_lunatic_static_seams_complete": True,
            "stage1_and_stage2_route_history_included": True,
            "post_allocation_item_subtransition_exact": True,
            "full_message_enemy_item_transition_exact": False,
            "runtime_image_pc_join_complete": False,
            "event_execution_observed": False,
        },
        "authority": {
            "static_occurrence_authority": True,
            "item_subtransition_authority": (
                "shipped_instruction_dataflow_and_scalar_recurrence"
            ),
            "enemy_cleanup_execution_authority": False,
            "causal_kill_or_collection_authority": False,
            "planner_or_live_action_authority": False,
            "physical_trial_run": False,
        },
        "next_gate": {
            "requires_exact_runtime_image_and_pc_join": True,
            "requires_complete_enemy_message_item_consumer": True,
            "integrated_simulator_remains_fail_closed": True,
        },
    }
    payload = json.dumps(
        report,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report["report_digest"] = _sha256_bytes(payload)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoded-dir", type=Path, required=True)
    parser.add_argument("--content-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_message_cleanup_atlas(
        decoded_dir=args.decoded_dir,
        content_manifest_path=args.content_manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
