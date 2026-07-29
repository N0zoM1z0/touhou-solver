#!/usr/bin/env python3
"""Retain SEM-SCALE-C causal Final-B/Extra schedule evidence.

The static workloads are isolated single-writer ECL programs, not declarations
that the whole live enemy/auxiliary inventory is complete. Historical Final-B
rows add a shipped-runtime transition check and explicit censoring where the
old trace stopped recording scale before or at scene freeze.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analysis.th08_ecl_scale_schedule_raw_oracle import (  # noqa: E402
    ORACLE_SEMANTICS_VERSION,
    oracle_ecl_scale_schedule_raw,
)
from th08_ecl_runtime import (  # noqa: E402
    EclInstructionCache,
    EclVmSnapshot,
)
from th08_ecl_scale_schedule import (  # noqa: E402
    TH08_ECL_SCALE_SCHEDULE_SEMANTICS_VERSION,
    EclScaleEnvironment,
    EclScaleSourceAuthority,
    synthesize_ecl_time_scale_schedule,
)
from th08_ecl_vm_state import (  # noqa: E402
    EclVmLocalProjection,
    float32_bits,
)
from th08_time_scale import (  # noqa: E402
    TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
)


SCHEMA = "th08-ecl-scale-schedule-capsule-v1"
QUARTER_BITS = 0x3E800000
UNIT_BITS = 0x3F800000
DEFAULT_OUTPUT = (
    "artifacts/benchmarks/th08_ecl_scale_schedule_capsule_20260729.json"
)


@dataclass(frozen=True)
class Workload:
    name: str
    ecl_path: str
    start_offset: int
    restore_offset: int
    spell_flags: int


WORKLOADS = (
    Workload(
        "lunatic_final_b_spell_190_isolated_source",
        "artifacts/decoded/ecldata7.ecl",
        0x5C58,
        0x6018,
        0x825,
    ),
    Workload(
        "extra_spell_222_isolated_source",
        "artifacts/decoded/ecldata8.ecl",
        0x87E8,
        0x8B58,
        0x825,
    ),
)

DEFAULT_TRACES = (
    "artifacts/runtime_reports/"
    "lunatic_route2_stage6b_unattended_20260726_004142.jsonl",
    "artifacts/runtime_reports/"
    "lunatic_route2_stage6b_unattended_20260726_011639.jsonl",
    "artifacts/runtime_reports/"
    "lunatic_route2_stage6b_unattended_20260726_163501.jsonl",
)


class _MappedBytes:
    def __init__(self, code: bytes, *, base: int) -> None:
        self.code = code
        self.base = base

    def read(self, address: int, size: int) -> bytes:
        start = address - self.base
        end = start + size
        if size <= 0 or start < 0 or end > len(self.code):
            raise OSError(f"unmapped ECL read at {address:#x}")
        return self.code[start:end]

    def instruction_bytes(self, address: int) -> bytes:
        header = self.read(address, 12)
        size = struct.unpack_from("<H", header, 6)[0]
        return self.read(address, size)


def _projection(counter: int) -> EclVmLocalProjection:
    return EclVmLocalProjection(
        (0, 1, 2, 3, 4, 5, 6, 7),
        (0, 0, 2, 3, 4, 5, 6, 7),
        (counter, 8, 7, 6),
    )


def _authority(source_id: int, provenance: str) -> EclScaleSourceAuthority:
    return EclScaleSourceAuthority(
        scale_writer_source_ids=(source_id,),
        writer_inventory_complete=True,
        scheduler_order_complete=True,
        installed_scale_callbacks_absent=True,
        unmodeled_phase_transitions_absent=True,
        post_update_capture=True,
        external_state_coherent=True,
        no_hit_no_bomb_continuation=True,
        provenance=provenance,
    )


def _integer_values(
    projection: EclVmLocalProjection,
) -> dict[int, int]:
    return {
        **{
            10000 + index: value
            for index, value in enumerate(projection.integer_locals)
        },
        **{
            10036 + index: value
            for index, value in enumerate(projection.scratch_integers)
        },
    }


def _write_rows(result: Any) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            write.frame,
            write.callback_index,
            write.scale_bits_before,
            write.scale_bits_after,
            write.instruction_address,
            write.scales_active_bullet_velocity,
        )
        for write in result.writes
    )


def _parity(result: Any, oracle: dict[str, object]) -> dict[str, bool]:
    return {
        "player_scale_bits": (
            result.schedule.player_scale_bits
            == oracle["player_scale_bits"]
        ),
        "laser_scale_bits": (
            result.schedule.laser_scale_bits
            == oracle["laser_scale_bits"]
        ),
        "writes": _write_rows(result) == oracle["writes"],
        "instructions_scanned": (
            result.instructions_scanned
            == oracle["instructions_scanned"]
        ),
        "stop": (
            result.stop_reason == oracle["stop_reason"]
            and result.horizon_covered == oracle["horizon_covered"]
            and result.stop_frame == oracle["stop_frame"]
        ),
        "final_vm": (
            result.final_instruction_pointer == oracle["pc"]
            and result.final_timer_elapsed == oracle["timer_elapsed"]
            and result.final_timer_fraction_bits
            == oracle["timer_fraction_bits"]
        ),
        "external_variables": (
            result.consumed_external_variables
            == oracle["consumed_external_variables"]
        ),
    }


def _run_schedule(
    *,
    code: bytes,
    runtime_base: int,
    pc: int,
    timer_elapsed: int,
    timer_fraction_bits: int,
    counter: int,
    spell_flags: int,
    source_id: int,
    source_frame: int,
    horizon: int,
    provenance: str,
) -> tuple[Any, dict[str, object], dict[str, bool]]:
    mapped = _MappedBytes(code, base=runtime_base)
    projection = _projection(counter)
    timer_fraction = struct.unpack(
        "<f",
        struct.pack("<I", timer_fraction_bits),
    )[0]
    snapshot = EclVmSnapshot(
        pc,
        timer_fraction,
        timer_elapsed,
        0,
        0.0,
        0.0,
        0.25,
        projection,
    )
    environment = EclScaleEnvironment(
        difficulty_index=3,
        route_id=2,
        spell_flags=spell_flags,
    )
    cache = EclInstructionCache()
    product = synthesize_ecl_time_scale_schedule(
        snapshot,
        source_id=source_id,
        source_frame=source_frame,
        authority=_authority(source_id, provenance),
        environment=environment,
        instruction_at=lambda address: cache.instruction(
            mapped.read,
            address,
        ),
        horizon_frames=horizon,
        active_difficulty_mask=0x08,
    )
    oracle = oracle_ecl_scale_schedule_raw(
        instruction_bytes_at=mapped.instruction_bytes,
        start_pc=pc,
        timer_elapsed=timer_elapsed,
        timer_fraction_bits=timer_fraction_bits,
        root_scale_bits=QUARTER_BITS,
        integer_values=_integer_values(projection),
        difficulty_index=3,
        route_id=2,
        spell_flags=spell_flags,
        spell_timer_elapsed_by_frame=(),
        horizon_frames=horizon,
        active_difficulty_mask=0x08,
        no_hit_no_bomb_continuation=True,
    )
    return product, oracle, _parity(product, oracle)


def _static_workload(root: Path, workload: Workload) -> dict[str, object]:
    path = root / workload.ecl_path
    code = path.read_bytes()
    runtime_base = 0x00600000
    source_id = 0x00580000
    product, _oracle, parity = _run_schedule(
        code=code,
        runtime_base=runtime_base,
        pc=runtime_base + workload.start_offset,
        timer_elapsed=0,
        timer_fraction_bits=0,
        counter=0,
        spell_flags=workload.spell_flags,
        source_id=source_id,
        source_frame=0,
        horizon=300,
        provenance="isolated_static_single_writer_workload",
    )
    writes = [
        {
            "frame": write.frame,
            "callback_index": write.callback_index,
            "instruction_offset": (
                f"{write.instruction_address - runtime_base:#x}"
            ),
            "scale_bits_before": f"{write.scale_bits_before:#010x}",
            "scale_bits_after": f"{write.scale_bits_after:#010x}",
            "scales_active_bullet_velocity": (
                write.scales_active_bullet_velocity
            ),
        }
        for write in product.writes
    ]
    return {
        "name": workload.name,
        "ecl": {
            "path": workload.ecl_path,
            "bytes": len(code),
            "sha256": hashlib.sha256(code).hexdigest(),
        },
        "root": {
            "instruction_offset": f"{workload.start_offset:#x}",
            "timer_elapsed": 0,
            "timer_fraction_bits": "0x00000000",
            "scale_bits": f"{QUARTER_BITS:#010x}",
            "spell_flags": f"{workload.spell_flags:#010x}",
        },
        "result": {
            "coverage": product.schedule.coverage,
            "horizon": product.schedule.complete_horizon,
            "stop_reason": product.stop_reason,
            "instructions_scanned": product.instructions_scanned,
            "writes": writes,
            "expected_restore_offset": f"{workload.restore_offset:#x}",
            "quarter_player_frames": sum(
                bits == QUARTER_BITS
                for bits in product.schedule.player_scale_bits
            ),
            "quarter_laser_frames": sum(
                bits == QUARTER_BITS
                for bits in product.schedule.laser_scale_bits
            ),
            "consumed_external_variables": (
                product.consumed_external_variables
            ),
            "bullet_velocity_rescale_frames": (
                product.bullet_velocity_rescale_frames
            ),
        },
        "product_oracle_parity": parity,
        "passed": (
            all(parity.values())
            and product.horizon_covered
            and len(product.writes) == 1
            and product.writes[0].frame == 241
            and product.writes[0].instruction_address
            == runtime_base + workload.restore_offset
            and product.schedule.player_scale_bits[240] == QUARTER_BITS
            and product.schedule.laser_scale_bits[240] == UNIT_BITS
        ),
        "authority": (
            "Exact only for the declared isolated single-writer ECL workload; "
            "this does not prove a complete live enemy/auxiliary source inventory."
        ),
    }


def _scale_row(row: dict[str, object], line: int) -> dict[str, object] | None:
    if row.get("kind") != "decision":
        return None
    spell = row.get("spell")
    lookahead = row.get("bullet_velocity_lookahead")
    if (
        not isinstance(spell, dict)
        or spell.get("spell_id") != 190
        or not isinstance(lookahead, dict)
    ):
        return None
    scale = lookahead.get("time_scale")
    pc = lookahead.get("instruction_pointer")
    elapsed = lookahead.get("timer_elapsed")
    fraction = lookahead.get("timer_fraction")
    snapshot_frame = row.get("snapshot_frame")
    flags = spell.get("flags")
    if not all(
        isinstance(value, (int, float))
        for value in (
            scale,
            pc,
            elapsed,
            fraction,
            snapshot_frame,
            flags,
        )
    ):
        return None
    alignment = row.get("hazard_alignment")
    return {
        "line": line,
        "snapshot_frame": int(snapshot_frame),
        "decision_frame": int(row["frame"]),
        "scale_bits": float32_bits(float(scale)),
        "instruction_pointer": int(pc),
        "timer_elapsed": int(elapsed),
        "timer_fraction_bits": float32_bits(float(fraction)),
        "spell_flags": int(flags),
        "ecl_frame_before": (
            alignment.get("ecl_frame_before")
            if isinstance(alignment, dict)
            else None
        ),
        "ecl_frame_after": (
            alignment.get("ecl_frame_after")
            if isinstance(alignment, dict)
            else None
        ),
    }


def _physical_trace(
    root: Path,
    relative_path: str,
    final_b_code: bytes,
) -> dict[str, object]:
    path = root / relative_path
    digest = hashlib.sha256()
    lines = 0
    rows: list[dict[str, object]] = []
    last_manager_frame: int | None = None
    inactive_frame: int | None = None
    with path.open("rb") as raw:
        for line, payload in enumerate(raw, 1):
            digest.update(payload)
            lines = line
            try:
                record = json.loads(payload)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(record, dict):
                continue
            frame = record.get("frame")
            if isinstance(frame, int):
                last_manager_frame = frame
            if record.get("kind") == "scene_inactive" and isinstance(frame, int):
                inactive_frame = frame
            selected = _scale_row(record, line)
            if selected is not None:
                rows.append(selected)
    quarter = [row for row in rows if row["scale_bits"] == QUARTER_BITS]
    unit_after = [
        row
        for row in rows
        if quarter
        and row["scale_bits"] == UNIT_BITS
        and row["ecl_frame_after"] is not None
        and quarter[0]["ecl_frame_after"] is not None
        and row["ecl_frame_after"] > quarter[0]["ecl_frame_after"]
    ]
    if not quarter:
        raise ValueError(f"{relative_path} has no spell-190 quarter-scale row")
    first = quarter[0]
    runtime_base = int(first["instruction_pointer"]) - 0x5C90
    product, _oracle, parity = _run_schedule(
        code=final_b_code,
        runtime_base=runtime_base,
        pc=int(first["instruction_pointer"]),
        timer_elapsed=int(first["timer_elapsed"]),
        timer_fraction_bits=int(first["timer_fraction_bits"]),
        counter=6,
        spell_flags=int(first["spell_flags"]),
        source_id=0x00580000,
        source_frame=int(first["ecl_frame_after"]),
        horizon=300,
        provenance="historical_isolated_source_replay",
    )
    restore = product.writes[0] if product.writes else None
    predicted_frame = (
        int(first["ecl_frame_after"]) + restore.frame
        if restore is not None
        else None
    )
    observed_unit = unit_after[0] if unit_after else None
    exact_observed = (
        observed_unit is not None
        and observed_unit["ecl_frame_after"] == predicted_frame
    )
    return {
        "source": {
            "path": relative_path,
            "bytes": path.stat().st_size,
            "lines": lines,
            "sha256": digest.hexdigest(),
        },
        "observed": {
            "spell_190_scale_rows": len(rows),
            "quarter_scale_rows": len(quarter),
            "first_quarter_root": {
                **first,
                "scale_bits": f"{int(first['scale_bits']):#010x}",
                "timer_fraction_bits": (
                    f"{int(first['timer_fraction_bits']):#010x}"
                ),
                "spell_flags": f"{int(first['spell_flags']):#010x}",
                "instruction_offset": (
                    f"{int(first['instruction_pointer']) - runtime_base:#x}"
                ),
            },
            "last_quarter_snapshot_frame": quarter[-1]["snapshot_frame"],
            "first_later_unit_snapshot_frame": (
                observed_unit["snapshot_frame"]
                if observed_unit is not None
                else None
            ),
            "first_later_unit_ecl_frame": (
                observed_unit["ecl_frame_after"]
                if observed_unit is not None
                else None
            ),
            "scene_inactive_frame": inactive_frame,
            "last_manager_frame": last_manager_frame,
        },
        "isolated_source_prediction": {
            "inferred_loop_counter": 6,
            "counter_evidence": (
                "Shipped Final-B sub44 sets VM int 10036 to 6 at offset "
                "0x5c6c before the observed first-cycle PC 0x5c90."
            ),
            "runtime_base": f"{runtime_base:#x}",
            "restore_relative_frame": (
                restore.frame if restore is not None else None
            ),
            "predicted_restore_ecl_frame": predicted_frame,
            "product_oracle_parity": parity,
            "exact_observed_unit_transition": exact_observed,
            "censoring": (
                None
                if observed_unit is not None
                else (
                    "The historical trace stopped ECL scale capture at spell "
                    "finish/scene freeze before a later unit row was retained."
                )
            ),
        },
        "authority": (
            "Observed shipped-runtime PC/timer/root/transition evidence joined "
            "to a statically inferred literal loop counter. The old trace did "
            "not capture a complete scale-writer inventory or VM locals."
        ),
    }


def build_report(
    root: Path,
    trace_paths: tuple[str, ...],
) -> dict[str, object]:
    static = [_static_workload(root, workload) for workload in WORKLOADS]
    final_b_code = (root / WORKLOADS[0].ecl_path).read_bytes()
    physical = [
        _physical_trace(root, path, final_b_code)
        for path in trace_paths
    ]
    exact_transitions = sum(
        bool(
            item["isolated_source_prediction"][
                "exact_observed_unit_transition"
            ]
        )
        for item in physical
    )
    report = {
        "schema": SCHEMA,
        "gate": {
            "name": "SEM-SCALE-C2/C3 causal schedule and static Extra capsule",
            "passed": (
                all(item["passed"] for item in static)
                and exact_transitions >= 1
            ),
            "scope": (
                "isolated-source product/oracle parity, shipped Final-B/Extra "
                "ECL, and one exact historical physical transition"
            ),
        },
        "semantics": {
            "product": TH08_ECL_SCALE_SCHEDULE_SEMANTICS_VERSION,
            "oracle": ORACLE_SEMANTICS_VERSION,
            "phase_schedule": TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
        },
        "static_workloads": static,
        "historical_physical_transitions": physical,
        "aggregate": {
            "static_workloads": len(static),
            "static_workloads_passed": sum(
                bool(item["passed"]) for item in static
            ),
            "historical_sources": len(physical),
            "exact_observed_restore_transitions": exact_transitions,
            "right_censored_sources": sum(
                item["isolated_source_prediction"]["censoring"] is not None
                for item in physical
            ),
        },
        "authority": {
            "observed": (
                "The shipped ECL bytes and historical physical trace supply "
                "PC/timer/scale/flags plus one exact 0.25-to-1.0 transition."
            ),
            "inferred": (
                "Historical VM counter 10036=6 is inferred from the literal "
                "set at 0x5c6c and the first observed PC at 0x5c90."
            ),
            "not_proved": (
                "No historical row proves complete live main/auxiliary writer "
                "inventory, installed-callback absence, clean survival, laser "
                "side-effect parity, or NMNB."
            ),
            "continuation": (
                "Final-B's 10099 path is valid only for the declared no-hit, "
                "no-Bomb continuation; losing histories are not promoted."
            ),
        },
    }
    payload = json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    report["capsule_payload_sha256"] = hashlib.sha256(payload).hexdigest()
    return report


def render_report(report: dict[str, object]) -> bytes:
    """Render platform-independent UTF-8/LF report bytes."""

    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument(
        "--trace",
        action="append",
        dest="traces",
        help="repo-relative historical Final-B JSONL (repeatable)",
    )
    parser.add_argument("-o", "--output", type=Path, default=Path(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    traces = tuple(args.traces or DEFAULT_TRACES)
    report = build_report(root, traces)
    output = args.output
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(render_report(report))
    print(output)
    return 0 if report["gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
