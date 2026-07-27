#!/usr/bin/env python3
"""Deterministic temporal-join tests for the B5 bullet-birth audit."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from analysis.th08_bullet_birth_audit import (
    analyze_trace,
    canonical_report_bytes,
    main,
)


def _decision(frame: int, spell_id: int | None) -> dict[str, object]:
    spell = (
        {
            "active": True,
            "spell_id": spell_id,
            "name": f"spell-{spell_id}",
        }
        if spell_id is not None
        else {"active": False}
    )
    return {
        "kind": "decision",
        "frame": frame,
        "gameplay_epoch": 0,
        "stage_route_index": 3,
        "spell": spell,
        "boss_phase": None,
    }


def _intent(
    *,
    address: int,
    relative_frame: int,
) -> dict[str, object]:
    return {
        "instruction_frame": relative_frame,
        "activation_frame_support": [relative_frame, relative_frame],
        "instruction_address": address,
        "instruction_time": address & 0xFF,
        "opcode": 0x61,
        "mode": 1,
        "parameter_mask": 0,
        "intent_status": "literal_schedule",
        "arguments": None,
        "requested_bullets": 1,
        "dependencies": ["pool_capacity"],
        "coverage_authority": "trace_only",
    }


def _audit(
    frame: int,
    *,
    activation_support: tuple[int, int],
    intents: list[dict[str, object]],
    ecl_frame: int,
    schema_version: int = 2,
) -> dict[str, object]:
    evidence = {
        "slot": frame,
        "kind": "activation_edge",
        "observation_status": (
            "complete"
            if activation_support[0] == activation_support[1]
            else "capture_spanned"
        ),
        "state": 1,
        "age": 1,
        "previous_state": 0,
        "previous_age": 0,
        "activation_support": list(activation_support),
        "position": [0.0, 0.0],
        "velocity": [0.0, 1.0],
        "geometry": [8.0, 8.0],
        "transform_flags": 0,
        "geometry_finite": True,
    }
    return {
        "kind": "bullet_birth_audit",
        "schema_version": schema_version,
        "role": "trace_only_no_action_authority",
        "frame": frame,
        "snapshot_frame": frame,
        "gameplay_epoch": 0,
        "stage_route_index": 3,
        "scope": {
            "pool": "all_1536_hostile_bullet_slots",
            "intent": "active_spell_enemy_main_vm_only",
            "omitted_sources": ["non_spell_enemy_main_vm"],
        },
        "alignment": {
            "ecl_frame_before": ecl_frame,
            "ecl_frame_after": ecl_frame,
            "ecl_event_frame_offset": 0,
            "ecl_event_frame_uncertainty": 0,
        },
        "spell_enemy_pointer": 0x500000,
        "deferred_fire_state": {
            "spell_enemy_pointer": 0x500000,
            "observed_enemy_pointer": 0x500000,
            "enemy_flags": 0,
            "deferred_fire_flag_mask": 0x20000,
            "frame_before": ecl_frame,
            "frame_after": ecl_frame,
            "ecl_frame_before": ecl_frame,
            "ecl_frame_after": ecl_frame,
            "status": "aligned_complete",
            "active": False,
            "evidence_label": "observed_native_enemy_flags",
            "coverage_authority": "trace_only",
        },
        "observation": {
            "role": "trace_only_no_action_authority",
            "frame_before": frame,
            "frame_after": frame,
            "capture_span": (
                activation_support[1] - activation_support[0]
            ),
            "previous_frame_before": activation_support[0],
            "previous_frame_after": activation_support[0],
            "active_count": 1,
            "evidence_count": 1,
            "evidence": [evidence],
        },
        "observation_error": None,
        "intent": {
            "role": "trace_only_no_action_authority",
            "intents": intents,
            "instructions_scanned": len(intents),
            "stop_reason": "horizon",
            "horizon_covered": True,
        },
        "intent_error": None,
        "counts": {
            "observed_evidence": 1,
            "visible_intents": len(intents),
        },
        "timing_ms": {
            "observation": 0.03,
            "intent": 0.04,
            "previous_emit": 0.01,
        },
        "join": {
            "status": "unresolved_offline_join_required",
            "coverage_authority": "none",
        },
    }


class BulletBirthAuditTests(unittest.TestCase):
    def _trace(self, directory: str) -> Path:
        path = Path(directory) / "trace.jsonl"
        records = [
            _audit(
                10,
                activation_support=(10, 10),
                intents=[_intent(address=0x1000, relative_frame=2)],
                ecl_frame=8,
            ),
            _decision(10, 57),
            _audit(
                20,
                activation_support=(19, 21),
                intents=[_intent(address=0x2000, relative_frame=0)],
                ecl_frame=20,
            ),
            _decision(20, 57),
            _audit(
                30,
                activation_support=(30, 30),
                intents=[
                    _intent(address=0x3000, relative_frame=0),
                    _intent(address=0x3001, relative_frame=0),
                ],
                ecl_frame=30,
            ),
            _decision(30, 57),
            _audit(
                40,
                activation_support=(40, 40),
                intents=[],
                ecl_frame=40,
            ),
            _decision(40, None),
        ]
        path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        return path

    def test_classifies_exact_support_ambiguous_and_unmatched(self) -> None:
        with TemporaryDirectory() as directory:
            report = analyze_trace(self._trace(directory))
        self.assertTrue(report["passed"])
        self.assertEqual(
            report["join"]["classification"],
            {
                "ambiguous": 1,
                "exact": 1,
                "support": 1,
                "unmatched": 1,
            },
        )
        self.assertEqual(report["intent"]["deduplicated_timed_events"], 4)
        self.assertEqual(
            report["input"]["trace_schema_versions"],
            {"2": 4},
        )
        self.assertEqual(
            report["input"]["deferred_fire_state_values"],
            {"disabled": 4},
        )
        self.assertEqual(report["join"]["unique_temporal_matches"], 2)
        self.assertEqual(
            report["scope"]["physical_action_authority"],
            "none",
        )

    def test_repeated_sightings_deduplicate_one_absolute_event(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            records = [
                _audit(
                    48,
                    activation_support=(48, 48),
                    intents=[_intent(address=0x5000, relative_frame=2)],
                    ecl_frame=48,
                ),
                _decision(48, 57),
                _audit(
                    50,
                    activation_support=(50, 50),
                    intents=[_intent(address=0x5000, relative_frame=0)],
                    ecl_frame=50,
                ),
                _decision(50, 57),
            ]
            path.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            report = analyze_trace(path)
        self.assertEqual(report["intent"]["timed_event_sightings"], 2)
        self.assertEqual(report["intent"]["deduplicated_timed_events"], 1)

    def test_two_generations_are_byte_identical(self) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory)
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            self.assertEqual(
                main([str(trace), "--output", str(first)]),
                0,
            )
            self.assertEqual(
                main([str(trace), "--output", str(second)]),
                0,
            )
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                first.read_bytes(),
                canonical_report_bytes(analyze_trace(trace)),
            )

    def test_failed_schema_v1_trace_remains_auditable(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            audit = _audit(
                10,
                activation_support=(10, 10),
                intents=[],
                ecl_frame=10,
                schema_version=1,
            )
            audit.pop("deferred_fire_state")
            path.write_text(
                json.dumps(audit) + "\n" + json.dumps(_decision(10, 57)) + "\n",
                encoding="utf-8",
            )
            report = analyze_trace(path)
        self.assertFalse(report["passed"])
        self.assertEqual(
            report["input"]["trace_schema_versions"],
            {"1": 1},
        )
        self.assertEqual(
            report["input"]["deferred_fire_state_statuses"],
            {"schema_v1_unobserved": 1},
        )


if __name__ == "__main__":
    unittest.main()
