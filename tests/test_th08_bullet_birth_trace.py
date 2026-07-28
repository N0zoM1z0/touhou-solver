#!/usr/bin/env python3
"""Tests for compact, authority-free bullet-birth trace records."""

from __future__ import annotations

from dataclasses import replace
import unittest

from th08_ecl_birth import (
    EclBirthIntent,
    EclBirthLookaheadResult,
    INTENT_LITERAL_SCHEDULE,
    observe_deferred_fire_state,
)
from th08_live.birth_trace import (
    BULLET_BIRTH_AUXILIARY_POINTER_TRACE_SCHEMA_VERSION,
    BULLET_BIRTH_BASE_TRACE_SCHEMA_VERSION,
    BULLET_BIRTH_INTENT_SCOPE,
    BULLET_BIRTH_POOL_SCOPE,
    BULLET_BIRTH_TRACE_ROLE,
    BULLET_BIRTH_TRACE_SCHEMA_VERSION,
    BulletBirthTraceInput,
    birth_trace_requires_immediate_flush,
    build_bullet_birth_trace_record,
)
from th08_live.bullet_birth import (
    BIRTH_KIND_ACTIVATION_EDGE,
    OBSERVATION_COMPLETE,
    BulletBirthEvidence,
    BulletBirthObservation,
)
from th08_live.birth_contention import (
    FUTURE_ABSENT,
    BirthObserverContention,
    BirthObserverFutureStates,
)
from th08_live.derived_pattern_source import (
    DerivedPatternSourceObservation,
)
from th08_live.enemy_ecl_inventory import (
    EnemyAuxiliaryEclContextPointerObservation,
    EnemyMainEclVmInventory,
    EnemyMainEclVmObservation,
)
from th08_live.controller import _build_birth_trace_observers
from th08_ecl_vm_state import EclVmLocalProjection


def _trace_input(
    *,
    observation: BulletBirthObservation | None = None,
    intent: EclBirthLookaheadResult | None = None,
    observation_error: str | None = None,
    intent_error: str | None = None,
) -> BulletBirthTraceInput:
    future_states = BirthObserverFutureStates(
        FUTURE_ABSENT,
        FUTURE_ABSENT,
        FUTURE_ABSENT,
    )
    return BulletBirthTraceInput(
        frame=120,
        snapshot_frame=117,
        gameplay_epoch=4,
        stage_route_index=3,
        observation=observation,
        observation_error=observation_error,
        intent=intent,
        intent_error=intent_error,
        deferred_fire_state=observe_deferred_fire_state(
            spell_enemy_pointer=0x4B5A30,
            observed_enemy_pointer=0x4B5A30,
            enemy_flags=0,
            frame_before=118,
            frame_after=118,
            ecl_frame_before=118,
            ecl_frame_after=118,
        ),
        spell_enemy_pointer=0x4B5A30,
        ecl_frame_before=118,
        ecl_frame_after=118,
        ecl_event_frame_offset=2,
        ecl_event_frame_uncertainty=0,
        observation_ms=0.031,
        observation_cpu_ms=0.021,
        intent_ms=0.044,
        previous_emit_ms=0.012,
        observer_contention=BirthObserverContention(
            future_states,
            future_states,
        ),
        derived_source_observation=DerivedPatternSourceObservation(
            frame_before=117,
            frame_after=118,
            active_count=1,
            candidates=(),
        ),
        derived_source_ms=0.009,
    )


def _observation() -> BulletBirthObservation:
    evidence = BulletBirthEvidence(
        slot=7,
        kind=BIRTH_KIND_ACTIVATION_EDGE,
        observation_status=OBSERVATION_COMPLETE,
        state=1,
        age=1,
        previous_state=0,
        previous_age=0,
        activation_support_start=115,
        activation_support_end=118,
        x=64.0,
        y=128.0,
        velocity_x=1.0,
        velocity_y=2.0,
        width=8.0,
        height=8.0,
        transform_flags=0,
        geometry_finite=True,
    )
    return BulletBirthObservation(
        frame_before=117,
        frame_after=118,
        previous_frame_before=115,
        previous_frame_after=115,
        active_count=1,
        evidence=(evidence,),
    )


def _intent() -> EclBirthLookaheadResult:
    item = EclBirthIntent(
        instruction_frame=3,
        activation_frame_support=(3, 3),
        instruction_address=0x401000,
        instruction_time=30,
        opcode=0x60,
        mode=1,
        parameter_mask=0,
        intent_status=INTENT_LITERAL_SCHEDULE,
        arguments=None,
        requested_bullets=8,
        dependencies=("bullet_template_geometry",),
    )
    return EclBirthLookaheadResult(
        intents=(item,),
        instructions_scanned=4,
        stop_reason="horizon",
        horizon_covered=True,
        requested_horizon_frames=80,
        stop_frame=80,
    )


class BulletBirthTraceTests(unittest.TestCase):
    def test_source_opt_in_does_not_disable_base_birth_tracker(self) -> None:
        tracker, source = _build_birth_trace_observers(
            trace_bullet_births=True,
            trace_derived_pattern_sources=False,
            backend="python",
            native_call_mode="gil-released",
        )
        self.assertIsNotNone(tracker)
        self.assertIsNone(source)

        tracker, source = _build_birth_trace_observers(
            trace_bullet_births=False,
            trace_derived_pattern_sources=False,
            backend="python",
            native_call_mode="gil-released",
        )
        self.assertIsNone(tracker)
        self.assertIsNone(source)

        with self.assertRaisesRegex(ValueError, "requires"):
            _build_birth_trace_observers(
                trace_bullet_births=False,
                trace_derived_pattern_sources=True,
                backend="python",
                native_call_mode="gil-released",
            )

    def test_base_trace_stays_schema_v9_without_failed_source_shadow(
        self,
    ) -> None:
        record = build_bullet_birth_trace_record(
            replace(
                _trace_input(),
                derived_source_observation=None,
                derived_source_ms=0.0,
            )
        )
        self.assertEqual(
            record["schema_version"],
            BULLET_BIRTH_BASE_TRACE_SCHEMA_VERSION,
        )
        self.assertNotIn("derived_source_observation", record)
        self.assertNotIn("ready_derived_sources", record["counts"])
        self.assertNotIn(
            "combined_pool_observation",
            record["timing_ms"],
        )

    def test_only_errors_require_a_predecision_flush(self) -> None:
        self.assertFalse(
            birth_trace_requires_immediate_flush(
                observation_error=None,
                intent_error=None,
            )
        )
        self.assertTrue(
            birth_trace_requires_immediate_flush(
                observation_error="ValueError: failed",
                intent_error=None,
            )
        )
        self.assertTrue(
            birth_trace_requires_immediate_flush(
                observation_error=None,
                intent_error="RuntimeError: failed",
            )
        )

    def test_record_retains_observation_intent_and_alignment(self) -> None:
        record = build_bullet_birth_trace_record(
            _trace_input(observation=_observation(), intent=_intent())
        )
        self.assertEqual(record["kind"], "bullet_birth_audit")
        self.assertEqual(
            record["schema_version"],
            BULLET_BIRTH_TRACE_SCHEMA_VERSION,
        )
        self.assertEqual(record["role"], BULLET_BIRTH_TRACE_ROLE)
        self.assertEqual(record["observation_backend"], "python")
        self.assertIsNone(record["native_call_mode"])
        self.assertIsNone(record["observation_diagnostics"])
        self.assertEqual(record["counts"]["observed_evidence"], 1)
        self.assertEqual(record["counts"]["visible_intents"], 1)
        self.assertEqual(record["counts"]["ready_derived_sources"], 0)
        self.assertEqual(
            record["derived_source_observation"]["schema_version"],
            1,
        )
        self.assertEqual(
            record["timing_ms"]["combined_pool_observation"],
            0.04,
        )
        self.assertEqual(
            record["observation"]["evidence"]["format"],
            "columnar_v1",
        )
        self.assertEqual(record["observation"]["evidence"]["slot"][0], 7)
        self.assertEqual(record["observation"]["evidence"]["status"][0], 4)
        self.assertEqual(record["intent"]["intents"][0]["opcode"], 0x60)
        self.assertEqual(record["intent"]["coverage"]["status"], "complete")
        self.assertEqual(
            record["intent"]["coverage"]["covered_through_frame"],
            80,
        )
        self.assertIsNone(
            record["intent"]["coverage"]["unknown_from_frame"]
        )
        self.assertEqual(record["alignment"]["ecl_frame_before"], 118)
        self.assertEqual(
            record["deferred_fire_state"]["status"],
            "aligned_complete",
        )
        self.assertFalse(record["deferred_fire_state"]["active"])
        self.assertNotIn(
            "deferred_emission_runtime_state",
            record["scope"]["omitted_sources"],
        )
        self.assertEqual(
            record["timing_ms"]["boundary"],
            "post_issue_before_same_iteration_decision_flush",
        )
        self.assertEqual(record["timing_ms"]["observation_cpu"], 0.021)
        self.assertEqual(
            record["flush_policy"],
            "errors_immediate_otherwise_same_iteration_decision_flush",
        )
        self.assertIsNone(record["timing_ms"]["build"])
        self.assertIsNone(record["timing_ms"]["pre_emit_total"])
        self.assertEqual(record["timing_ms"]["previous_emit"], 0.012)

    def test_nonspell_inventory_uses_explicit_auxiliary_pointer_schema(
        self,
    ) -> None:
        inventory = EnemyMainEclVmInventory(
            scanned_slots=64,
            active_slots=1,
            observations=(
                EnemyMainEclVmObservation(
                    slot=0,
                    enemy_pointer=0x005826C0,
                    enemy_flags=5,
                    instruction_pointer=0x015A1234,
                    timer_fraction_bits=0x3E800000,
                    timer_elapsed=17,
                    local_projection=EclVmLocalProjection(
                        tuple(range(8)),
                        tuple(0x3F800000 + index for index in range(8)),
                        (101, 102, 103, 104),
                    ),
                ),
            ),
            invalid=(),
            auxiliary_contexts=(
                EnemyAuxiliaryEclContextPointerObservation(
                    slot=0,
                    enemy_pointer=0x005826C0,
                    enemy_flags=5,
                    context_pointers=(0x02100000, 0, 0x021024B0, 0),
                ),
            ),
            invalid_auxiliary_contexts=(),
            decode_ms=0.025,
        )
        record = build_bullet_birth_trace_record(
            replace(
                _trace_input(observation=_observation()),
                nonspell_main_vm_inventory=inventory,
                enemy_prefix_frame_before=116,
                enemy_prefix_frame_after=116,
                enemy_prefix_capture_ms=0.35,
            )
        )
        self.assertEqual(
            record["schema_version"],
            BULLET_BIRTH_AUXILIARY_POINTER_TRACE_SCHEMA_VERSION,
        )
        self.assertEqual(
            record["counts"]["valid_nonspell_main_vms"],
            1,
        )
        self.assertEqual(
            record["counts"]["non_null_auxiliary_contexts"],
            2,
        )
        self.assertEqual(
            record["alignment"]["enemy_prefix_frame_before"],
            116,
        )
        self.assertEqual(
            record["timing_ms"]["nonspell_main_vm_decode"],
            0.025,
        )
        self.assertIn(
            "ordinary_enemy_pool_first_64_main_vm_state",
            record["scope"]["observed_sources"],
        )
        self.assertIn(
            "ordinary_enemy_pool_first_64_auxiliary_context_pointers_only",
            record["scope"]["observed_sources"],
        )
        self.assertIn(
            "auxiliary_vm_state_or_instruction_semantics",
            record["scope"]["omitted_sources"],
        )

    def test_native_schema_requires_explicit_reconciled_diagnostics(self) -> None:
        observation = _observation()
        diagnostics = {
            "native_segments_ms": {
                "prepare": 0.001,
                "native_call": 0.010,
                "materialize": 0.015,
                "controller_residual": 0.005,
            },
            "gc_completed": {
                "prepare": [0, 0, 0],
                "native_call": [1, 0, 0],
                "materialize": [0, 0, 0],
            },
            "thread_cycles": {
                "source": "windows_query_thread_cycle_time",
                "prepare": 100,
                "native_call": 200,
                "materialize": 300,
            },
        }
        trace_input = replace(
            _trace_input(observation=observation),
            observation_backend="native",
            native_call_mode="gil-held",
            observation_diagnostics=diagnostics,
            derived_source_diagnostics={
                "native_segments_ms": {
                    "prepare": 0.001,
                    "native_call": 0.003,
                    "materialize": 0.002,
                    "controller_residual": 0.003,
                },
            },
        )
        record = build_bullet_birth_trace_record(trace_input)
        self.assertEqual(record["schema_version"], 10)
        self.assertEqual(record["native_call_mode"], "gil-held")
        self.assertEqual(record["observation_diagnostics"], diagnostics)

        with self.assertRaisesRegex(ValueError, "requires diagnostics"):
            build_bullet_birth_trace_record(
                replace(
                    trace_input,
                    observation_diagnostics=None,
                )
            )
        without_cycles = dict(diagnostics)
        without_cycles.pop("thread_cycles")
        with self.assertRaisesRegex(ValueError, "thread cycles"):
            build_bullet_birth_trace_record(
                replace(
                    trace_input,
                    observation_diagnostics=without_cycles,
                )
            )
        with self.assertRaisesRegex(ValueError, "may not publish"):
            build_bullet_birth_trace_record(
                replace(
                    trace_input,
                    observation_backend="python",
                    native_call_mode=None,
                )
            )
        with self.assertRaisesRegex(ValueError, "explicit call mode"):
            build_bullet_birth_trace_record(
                replace(
                    trace_input,
                    native_call_mode=None,
                )
            )
        with self.assertRaisesRegex(ValueError, "native call mode"):
            build_bullet_birth_trace_record(
                replace(
                    _trace_input(observation=observation),
                    native_call_mode="gil-held",
                )
            )

    def test_scope_and_join_remain_explicitly_incomplete(self) -> None:
        record = build_bullet_birth_trace_record(_trace_input())
        self.assertEqual(record["scope"]["pool"], BULLET_BIRTH_POOL_SCOPE)
        self.assertEqual(record["scope"]["intent"], BULLET_BIRTH_INTENT_SCOPE)
        self.assertIn(
            "child_enemy_or_auxiliary_vm",
            record["scope"]["omitted_sources"],
        )
        self.assertEqual(
            record["join"]["status"],
            "unresolved_offline_join_required",
        )
        self.assertEqual(record["join"]["coverage_authority"], "none")

    def test_errors_are_retained_without_synthetic_evidence(self) -> None:
        record = build_bullet_birth_trace_record(
            _trace_input(
                observation_error="ValueError: regressed",
                intent_error="RuntimeError: unreadable",
            )
        )
        self.assertIsNone(record["observation"])
        self.assertIsNone(record["intent"])
        self.assertEqual(record["counts"]["observed_evidence"], 0)
        self.assertEqual(record["counts"]["visible_intents"], 0)
        self.assertEqual(
            record["observation_error"],
            "ValueError: regressed",
        )
        self.assertEqual(
            record["intent_error"],
            "RuntimeError: unreadable",
        )


if __name__ == "__main__":
    unittest.main()
