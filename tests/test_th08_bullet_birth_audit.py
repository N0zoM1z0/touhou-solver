#!/usr/bin/env python3
"""Deterministic temporal-join tests for the B5 bullet-birth audit."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from analysis.th08_bullet_birth_audit import (
    BulletBirthAuditError,
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
    record = {
        "kind": "decision",
        "frame": frame,
        "gameplay_epoch": 0,
        "stage_route_index": 3,
        "spell": spell,
        "boss_phase": None,
        "bullet_velocity_lookahead": {
            "instructions_scanned": 4,
            "stop_reason": "horizon",
            "horizon_covered": True,
            "coverage_status": "complete",
            "requested_horizon_frames": 80,
            "stop_frame": 80,
            "covered_through_frame": 80,
            "unknown_from_frame": None,
            "result_kind": "complete_schedule",
            "prefix_events": [],
            "events": [],
            "lowering_status": "complete_schedule_lowered",
            "tagged_bullets": 0,
            "error": None,
        },
    }
    return record


def _intent(
    *,
    address: int,
    relative_frame: int,
) -> dict[str, object]:
    record = {
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
    return record


def _audit(
    frame: int,
    *,
    activation_support: tuple[int, int],
    intents: list[dict[str, object]],
    ecl_frame: int,
    schema_version: int = 3,
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
    observation_evidence: object = [evidence]
    if schema_version >= 3:
        observation_evidence = {
            "format": "columnar_v1",
            "slot": [frame],
            "code": [3],
            "status": [
                4
                if activation_support[0] == activation_support[1]
                else 2
            ],
            "state": [1],
            "age": [1],
            "previous_state": [0],
            "previous_age": [0],
            "geometry": [[0.0, 0.0, 0.0, 1.0, 8.0, 8.0]],
            "transform_flags": [0],
            "geometry_finite": [True],
        }
    record = {
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
            "evidence": observation_evidence,
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
            "observation_cpu": 0.02,
            "intent": 0.04,
            "build": 0.02,
            "pre_emit_total": 0.09,
            "previous_emit": 0.01,
        },
        "join": {
            "status": "unresolved_offline_join_required",
            "coverage_authority": "none",
        },
    }
    if schema_version >= 5:
        record["observation_backend"] = "native"
    if schema_version >= 6:
        record["observation_diagnostics"] = {
            "native_segments_ms": {
                "prepare": 0.002,
                "native_call": 0.010,
                "materialize": 0.015,
                "controller_residual": 0.003,
            },
            "gc_completed": {
                "prepare": [0, 0, 0],
                "native_call": [0, 0, 0],
                "materialize": [0, 0, 0],
            },
        }
    if schema_version >= 7:
        record["native_call_mode"] = "gil-held"
    if schema_version >= 8:
        record["intent"]["coverage"] = {
            "status": "complete",
            "requested_horizon_frames": 80,
            "stop_frame": 80,
            "covered_through_frame": 80,
            "unknown_from_frame": None,
            "result_kind": "complete_schedule",
        }
    if schema_version >= 9:
        record["observation_diagnostics"]["thread_cycles"] = {
            "source": "windows_query_thread_cycle_time",
            "prepare": 100,
            "native_call": 200,
            "materialize": 300,
        }
        record["observer_contention"] = {
            "corridor_future": {
                "before": "inflight",
                "after": "inflight",
            },
            "survival_future": {
                "before": "absent",
                "after": "absent",
            },
            "enemy_future": {
                "before": "inflight",
                "after": "done",
            },
            "omitted_sources": [
                "game_process",
                "os_scheduler_and_other_processes",
                "native_internal_workers_after_endpoint_ambiguity",
                "candidate_supplemental_and_prewarm_services",
                "allocator_and_page_faults",
            ],
        }
    if schema_version >= 10:
        record["derived_source_observation"] = {
            "schema_version": 1,
            "role": "trace_only_no_action_authority",
            "frame_before": frame,
            "frame_after": frame,
            "capture_span": 0,
            "active_count": 1,
            "candidate_count": 0,
            "candidates": [],
            "coverage": {
                "source_class": (
                    "ready_visible_parent_bullet_transform_only"
                ),
                "future_hazard_coverage": "unknown",
                "physical_action_authority": "none",
            },
        }
        record["derived_source_error"] = None
        record["derived_source_diagnostics"] = {
            "native_segments_ms": {
                "prepare": 0.001,
                "native_call": 0.004,
                "materialize": 0.003,
                "controller_residual": 0.002,
            },
        }
        record["timing_ms"]["derived_source_observation"] = 0.01
        record["timing_ms"]["combined_pool_observation"] = 0.04
        record["timing_ms"]["pre_emit_total"] = 0.10
    if schema_version >= 11:
        if schema_version == 11:
            record["scope"]["observed_sources"] = [
                "ordinary_enemy_pool_first_64_main_vm_state_only"
            ]
            record["scope"]["omitted_sources"] = [
                (
                    "non_spell_enemy_main_vm_outside_first_64_"
                    "or_instruction_semantics"
                )
            ]
        else:
            record["scope"]["observed_sources"] = [
                "ordinary_enemy_pool_first_64_main_vm_state",
                (
                    "ordinary_enemy_pool_first_64_"
                    "auxiliary_context_pointers_only"
                ),
            ]
            record["scope"]["omitted_sources"] = [
                "ordinary_enemy_outside_first_64",
                "auxiliary_vm_state_or_instruction_semantics",
            ]
        record["alignment"]["enemy_prefix_frame_before"] = frame
        record["alignment"]["enemy_prefix_frame_after"] = frame
        record["counts"]["active_ordinary_enemy_slots"] = 1
        record["counts"]["valid_nonspell_main_vms"] = 1
        record["counts"]["invalid_nonspell_main_vms"] = 0
        inventory = {
            "layout": (
                "th08-enemy-main-ecl-vm-inventory-v1"
                if schema_version == 11
                else "th08-enemy-main-ecl-vm-inventory-v2"
            ),
            "vm_local_layout": "th08-ecl-vm-local-projection-v1",
            "scope": (
                "ordinary_enemy_pool_prefix_main_vm_only"
                if schema_version == 11
                else (
                    "ordinary_enemy_pool_prefix_main_vm_"
                    "and_auxiliary_pointers"
                )
            ),
            "scanned_slots": 64,
            "active_slots": 1,
            "valid_vms": 1,
            "invalid_active_vms": 0,
            "rows": [
                [
                    0,
                    0x005826C0,
                    5,
                    0x015A0000 + frame,
                    0x3E800000,
                    frame,
                    list(range(8)),
                    [0x3F800000] * 8,
                    [1, 2, 3, 4],
                ]
            ],
            "invalid_rows": [],
            "decode_ms": 0.02,
        }
        if schema_version >= 12:
            inventory.update(
                {
                    "auxiliary_context_row_layout": (
                        "slot_enemy_pointer_enemy_flags_"
                        "four_raw_context_pointers"
                    ),
                    "auxiliary_context_rows": [
                        [0, 0x005826C0, 5, [0x02100000, 0, 0, 0]]
                    ],
                    "non_null_auxiliary_contexts": 1,
                    "invalid_auxiliary_contexts": 0,
                    "invalid_auxiliary_context_rows": [],
                }
            )
            record["counts"]["non_null_auxiliary_contexts"] = 1
            record["counts"]["invalid_auxiliary_contexts"] = 0
        record["nonspell_main_vm_inventory"] = inventory
        record["timing_ms"]["nonspell_main_vm_decode"] = 0.02
        record["timing_ms"]["enemy_prefix_capture"] = 0.30
    return record


class BulletBirthAuditTests(unittest.TestCase):
    def _trace(self, directory: str, *, schema_version: int = 3) -> Path:
        path = Path(directory) / "trace.jsonl"
        records = [
            _audit(
                10,
                activation_support=(10, 10),
                intents=[_intent(address=0x1000, relative_frame=2)],
                ecl_frame=8,
                schema_version=schema_version,
            ),
            _decision(10, 57),
            _audit(
                20,
                activation_support=(19, 21),
                intents=[_intent(address=0x2000, relative_frame=0)],
                ecl_frame=20,
                schema_version=schema_version,
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
                schema_version=schema_version,
            ),
            _decision(30, 57),
            _audit(
                40,
                activation_support=(40, 40),
                intents=[],
                ecl_frame=40,
                schema_version=schema_version,
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
            {"3": 4},
        )
        self.assertEqual(
            report["input"]["deferred_fire_state_values"],
            {"disabled": 4},
        )
        self.assertEqual(report["join"]["unique_temporal_matches"], 2)
        self.assertEqual(
            report["by_phase_at_intent"]["stage_3:spell_57"][
                "timed_sightings"
            ],
            4,
        )
        self.assertEqual(
            report["by_phase_at_intent"]["stage_3:nonspell"]["audit_rows"],
            1,
        )
        self.assertEqual(
            report["timing_by_evidence_count"]["observation"]["1_8"][
                "count"
            ],
            4,
        )
        self.assertEqual(
            report["timing_by_evidence_count"]["observation_cpu"]["1_8"][
                "p95"
            ],
            0.02,
        )
        self.assertEqual(
            report["timing_by_evidence_count"]["previous_emit"]["1_8"][
                "count"
            ],
            3,
        )
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

    def test_schema_v2_and_v3_have_identical_audit_semantics(self) -> None:
        with TemporaryDirectory() as directory:
            v2_directory = Path(directory) / "v2"
            v3_directory = Path(directory) / "v3"
            v2_directory.mkdir()
            v3_directory.mkdir()
            v2 = analyze_trace(
                self._trace(str(v2_directory), schema_version=2)
            )
            v3 = analyze_trace(
                self._trace(str(v3_directory), schema_version=3)
            )
        for field in (
            "observation",
            "intent",
            "join",
            "by_phase_at_capture",
            "by_phase_at_intent",
            "velocity_lookahead_read_ms_by_phase",
            "timing_ms",
            "timing_by_evidence_count",
            "scope",
        ):
            self.assertEqual(v2[field], v3[field])

    def test_schema_v5_requires_and_reports_explicit_backend(self) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=5)
            report = analyze_trace(trace)
            self.assertEqual(
                report["input"]["observation_backends"],
                {"native": 4},
            )
            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            records[0].pop("observation_backend")
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "observation backend",
            ):
                analyze_trace(trace)

    def test_schema_v6_validates_and_reports_native_diagnostics(self) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=6)
            report = analyze_trace(trace)
            diagnostics = report["native_diagnostics"]
            self.assertEqual(diagnostics["rows"], 4)
            self.assertEqual(diagnostics["rows_with_gc"], 0)
            self.assertEqual(
                diagnostics["segments_ms"]["native_call"]["p95"],
                0.01,
            )
            self.assertEqual(
                diagnostics["observation_ms_by_gc_overlap"][
                    "without_gc"
                ]["count"],
                4,
            )

            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            records[0]["observation_diagnostics"][
                "native_segments_ms"
            ]["controller_residual"] = -0.001
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "invalid native segment",
            ):
                analyze_trace(trace)

    def test_schema_v6_rejects_fabricated_python_diagnostics(self) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=6)
            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            records[0]["observation_backend"] = "python"
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "fabricates native diagnostics",
            ):
                analyze_trace(trace)

    def test_schema_v7_requires_one_explicit_native_call_mode(self) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=7)
            report = analyze_trace(trace)
            self.assertEqual(
                report["input"]["native_call_modes"],
                {"gil-held": 4},
            )
            self.assertEqual(report["native_diagnostics"]["rows"], 4)

            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            records[0].pop("native_call_mode")
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(BulletBirthAuditError, "call mode"):
                analyze_trace(trace)

            records[0]["native_call_mode"] = "gil-released"
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(BulletBirthAuditError, "mixes"):
                analyze_trace(trace)

            records[0]["observation_backend"] = "python"
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(BulletBirthAuditError, "fabricates"):
                analyze_trace(trace)

    def test_schema_v8_requires_consistent_callback_and_intent_coverage(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=8)
            report = analyze_trace(trace)
            self.assertEqual(
                report["callback_lookahead"]["coverage_status_rows"],
                {"complete": 4},
            )
            self.assertEqual(
                report["callback_lookahead"]["lowering_status_rows"],
                {"complete_schedule_lowered": 4},
            )
            self.assertEqual(report["native_diagnostics"]["rows"], 4)

            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            records[1]["bullet_velocity_lookahead"].update(
                {
                    "instructions_scanned": 256,
                    "stop_reason": "repeated_state",
                    "horizon_covered": False,
                    "coverage_status": "unknown",
                    "stop_frame": 4,
                    "covered_through_frame": 3,
                    "unknown_from_frame": 4,
                    "result_kind": "prefix_only",
                    "prefix_events": [[4, 12, 16, 0.0, 0.0]],
                    "events": [],
                    "lowering_status": "incomplete_prefix_not_lowered",
                    "tagged_bullets": 3,
                }
            )
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            unknown_report = analyze_trace(trace)
            self.assertEqual(
                unknown_report["callback_lookahead"][
                    "coverage_status_rows"
                ],
                {"complete": 3, "unknown": 1},
            )
            self.assertEqual(
                unknown_report["callback_lookahead"]["prefix_events"],
                1,
            )
            self.assertEqual(
                unknown_report["callback_lookahead"]["lowered_events"],
                0,
            )
            self.assertEqual(
                unknown_report["callback_lookahead"][
                    "incomplete_tagged_rows"
                ],
                1,
            )
            self.assertEqual(
                unknown_report["callback_lookahead"][
                    "incomplete_tagged_max"
                ],
                3,
            )

            records[0]["intent"]["coverage"]["unknown_from_frame"] = 1
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "intent coverage is inconsistent",
            ):
                analyze_trace(trace)

            records[0]["intent"]["coverage"]["unknown_from_frame"] = None
            records[1]["bullet_velocity_lookahead"][
                "lowering_status"
            ] = "complete_schedule_lowered"
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "callback coverage",
            ):
                analyze_trace(trace)

            records[1]["bullet_velocity_lookahead"][
                "lowering_status"
            ] = "incomplete_prefix_not_lowered"
            records[1]["bullet_velocity_lookahead"][
                "stop_reason"
            ] = "horizon"
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "callback coverage",
            ):
                analyze_trace(trace)

    def test_schema_v7_callback_rows_are_labeled_legacy_not_reinterpreted(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=7)
            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            for record in records:
                lookahead = record.get("bullet_velocity_lookahead")
                if not isinstance(lookahead, dict):
                    continue
                for field in (
                    "coverage_status",
                    "requested_horizon_frames",
                    "stop_frame",
                    "covered_through_frame",
                    "unknown_from_frame",
                    "result_kind",
                    "prefix_events",
                    "lowering_status",
                ):
                    lookahead.pop(field)
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            report = analyze_trace(trace)
            self.assertEqual(
                report["callback_lookahead"]["coverage_status_rows"],
                {"legacy_declared_complete": 4},
            )
            self.assertEqual(
                report["callback_lookahead"]["lowering_status_rows"],
                {"legacy_complete_events_lowered_unchecked": 4},
            )

    def test_schema_v9_requires_cycles_and_future_endpoints(self) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=9)
            report = analyze_trace(trace)
            self.assertTrue(
                report["gates"]["cycle_attribution_available"]
            )
            self.assertEqual(
                report["native_diagnostics"]["thread_cycle_sources"],
                {"windows_query_thread_cycle_time": 4},
            )
            self.assertEqual(
                report["native_diagnostics"][
                    "thread_cycle_attribution_rows"
                ],
                4,
            )
            self.assertEqual(
                report["native_diagnostics"]["observer_contention"][
                    "classifications"
                ],
                {"definite_known_future_overlap": 4},
            )

            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            cycles = records[0]["observation_diagnostics"]["thread_cycles"]
            cycles.update(
                {
                    "source": "unavailable_non_windows",
                    "prepare": None,
                    "native_call": None,
                    "materialize": None,
                }
            )
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            unavailable = analyze_trace(trace)
            self.assertFalse(
                unavailable["gates"]["cycle_attribution_available"]
            )
            self.assertFalse(unavailable["passed"])

            cycles["materialize"] = 3
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "fabricate",
            ):
                analyze_trace(trace)

            cycles.update(
                {
                    "source": "windows_query_thread_cycle_time",
                    "prepare": 1,
                    "native_call": 2,
                    "materialize": 3,
                }
            )
            records[0]["observer_contention"]["enemy_future"][
                "after"
            ] = "waiting"
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "enemy_future",
            ):
                analyze_trace(trace)

            records[0]["observer_contention"]["enemy_future"][
                "after"
            ] = "done"
            records[0]["observer_contention"]["omitted_sources"].append(
                "game_process"
            )
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "omitted sources",
            ):
                analyze_trace(trace)

    def test_schema_v10_requires_and_budgets_derived_source_shadow(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=10)
            report = analyze_trace(trace)
            self.assertEqual(
                report["derived_pattern_source"]["schema_v10_rows"],
                4,
            )
            self.assertEqual(
                report["derived_pattern_source"]["candidate_sightings"],
                0,
            )
            self.assertEqual(
                report["gates"]["observer_limits_ms"]["boundary"],
                "combined_birth_and_derived_source",
            )
            self.assertEqual(
                report["timing_ms"]["combined_pool_observation"]["p95"],
                0.04,
            )

            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            records[0].pop("derived_source_observation")
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "derived-source observation",
            ):
                analyze_trace(trace)

    def test_schema_v11_validates_and_reports_main_vm_inventory(self) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=11)
            report = analyze_trace(trace)
            inventory = report["nonspell_main_vm_inventory"]
            self.assertEqual(inventory["schema_v11_rows"], 4)
            self.assertEqual(inventory["active_slots_per_row"]["p95"], 1.0)
            self.assertEqual(inventory["valid_vms_per_row"]["p95"], 1.0)
            self.assertEqual(inventory["invalid_active_vms_per_row"]["max"], 0.0)
            self.assertEqual(inventory["stability"], {"stable": 4})
            self.assertEqual(inventory["decode_ms"]["p95"], 0.02)
            self.assertEqual(inventory["enemy_prefix_capture_ms"]["p95"], 0.3)
            self.assertEqual(inventory["source_proof"], "none")

            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            records[0]["nonspell_main_vm_inventory"]["rows"][0][1] += 4
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "main-VM identity",
            ):
                analyze_trace(trace)

    def test_schema_v12_validates_and_reports_auxiliary_pointers(self) -> None:
        with TemporaryDirectory() as directory:
            trace = self._trace(directory, schema_version=12)
            report = analyze_trace(trace)
            inventory = report["nonspell_main_vm_inventory"]
            self.assertEqual(inventory["schema_v11_rows"], 0)
            self.assertEqual(inventory["schema_v12_rows"], 4)
            self.assertEqual(
                inventory["auxiliary_pointer_owners_per_row"]["p95"],
                1.0,
            )
            self.assertEqual(
                inventory["non_null_auxiliary_contexts_per_row"]["p95"],
                1.0,
            )
            self.assertEqual(
                inventory["invalid_auxiliary_contexts_per_row"]["max"],
                0.0,
            )

            records = [
                json.loads(line)
                for line in trace.read_text(encoding="utf-8").splitlines()
            ]
            records[0]["nonspell_main_vm_inventory"][
                "auxiliary_context_rows"
            ][0][3][0] = 0xFFFFFFFF
            trace.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BulletBirthAuditError,
                "auxiliary-context counts",
            ):
                analyze_trace(trace)

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
