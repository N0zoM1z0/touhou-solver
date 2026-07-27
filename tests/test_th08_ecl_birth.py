from __future__ import annotations

import math
import struct
import unittest

from th08_ecl_birth import (
    ENEMY_DEFERRED_FIRE_FLAG,
    INTENT_CURRENT_PATTERN,
    INTENT_DEFERRED,
    INTENT_DYNAMIC_PARAMETER,
    INTENT_LITERAL_SCHEDULE,
    INTENT_PLAYER_AIM,
    INTENT_RNG,
    analyze_ecl_birth_intents,
    observe_deferred_fire_state,
)
from th08_ecl_runtime import EclVmSnapshot, RuntimeEclInstruction


BASE = 0x100000


def _snapshot(
    *,
    instruction_pointer: int = BASE,
    timer_elapsed: int = 0,
    timer_fraction: float = 0.0,
    time_scale: float = 1.0,
) -> EclVmSnapshot:
    return EclVmSnapshot(
        instruction_pointer,
        timer_fraction,
        timer_elapsed,
        0,
        0.0,
        0.0,
        time_scale,
    )


def _instruction(
    address: int,
    *,
    time: int,
    opcode: int,
    payload: bytes = b"",
    difficulty_mask: int = 1,
    parameter_mask: int = 0,
) -> RuntimeEclInstruction:
    return RuntimeEclInstruction(
        address,
        time,
        opcode,
        12 + len(payload),
        difficulty_mask,
        parameter_mask,
        payload,
    )


def _fire_payload(
    *,
    bullet_type: int = 2,
    color: int = 3,
    count1: int = 4,
    count2: int = 5,
    speed1: float = 2.0,
    speed2: float = 1.0,
    angle1: float = 0.25,
    angle2: float = 0.125,
    transform_flags: int = 0,
) -> bytes:
    return struct.pack(
        "<hhii4fI",
        bullet_type,
        color,
        count1,
        count2,
        speed1,
        speed2,
        angle1,
        angle2,
        transform_flags,
    )


def _analyze(
    instructions: tuple[RuntimeEclInstruction, ...],
    **kwargs,
):
    by_address = {instruction.address: instruction for instruction in instructions}
    return analyze_ecl_birth_intents(
        _snapshot(),
        instruction_at=by_address.__getitem__,
        horizon_frames=20,
        active_difficulty_mask=1,
        deferred_fire_active=False,
        spell_active=True,
        minimum_fire_distance_clear=True,
        fire_filter_clear=True,
        available_slots=1536,
        template_geometry_resolved=True,
        emission_origin_resolved=True,
        **kwargs,
    )


class EclBirthIntentTests(unittest.TestCase):
    def test_native_deferred_flag_requires_exact_ecl_capture_alignment(self) -> None:
        aligned = observe_deferred_fire_state(
            spell_enemy_pointer=0x500000,
            observed_enemy_pointer=0x500000,
            enemy_flags=ENEMY_DEFERRED_FIRE_FLAG | 1,
            frame_before=100,
            frame_after=100,
            ecl_frame_before=100,
            ecl_frame_after=100,
        )
        self.assertEqual(aligned.status, "aligned_complete")
        self.assertTrue(aligned.active)
        self.assertEqual(
            aligned.record()["deferred_fire_flag_mask"],
            ENEMY_DEFERRED_FIRE_FLAG,
        )

        misaligned = observe_deferred_fire_state(
            spell_enemy_pointer=0x500000,
            observed_enemy_pointer=0x500000,
            enemy_flags=0,
            frame_before=100,
            frame_after=100,
            ecl_frame_before=101,
            ecl_frame_after=101,
        )
        self.assertEqual(misaligned.status, "capture_misaligned")
        self.assertIsNone(misaligned.active)

    def test_native_deferred_flag_rejects_wrong_enemy_pointer(self) -> None:
        observation = observe_deferred_fire_state(
            spell_enemy_pointer=0x500000,
            observed_enemy_pointer=0x600000,
            enemy_flags=0,
            frame_before=100,
            frame_after=100,
            ecl_frame_before=100,
            ecl_frame_after=100,
        )
        self.assertEqual(observation.status, "enemy_pointer_mismatch")
        self.assertIsNone(observation.active)

    def test_literal_absolute_fire_decodes_payload_and_schedule(self) -> None:
        fire = _instruction(
            BASE,
            time=4,
            opcode=0x61,
            payload=_fire_payload(),
        )
        terminate = _instruction(
            fire.address + fire.size,
            time=5,
            opcode=0x01,
        )
        result = _analyze((fire, terminate))
        self.assertEqual(result.stop_reason, "terminate")
        self.assertTrue(result.horizon_covered)
        self.assertEqual(len(result.intents), 1)
        intent = result.intents[0]
        self.assertEqual(intent.instruction_frame, 4)
        self.assertEqual(intent.activation_frame_support, (4, 4))
        self.assertEqual(intent.mode, 1)
        self.assertEqual(intent.intent_status, INTENT_LITERAL_SCHEDULE)
        self.assertEqual(intent.requested_bullets, 20)
        self.assertEqual(intent.dependencies, ())
        self.assertEqual(intent.arguments.bullet_type, 2)
        self.assertEqual(intent.arguments.transform_flags, 0)

    def test_dynamic_parameter_bits_are_named_and_fail_closed(self) -> None:
        fire = _instruction(
            BASE,
            time=0,
            opcode=0x61,
            payload=_fire_payload(),
            parameter_mask=0x14,
        )
        result = _analyze((fire,), max_instructions=1)
        intent = result.intents[0]
        self.assertEqual(intent.intent_status, INTENT_DYNAMIC_PARAMETER)
        self.assertIsNone(intent.requested_bullets)
        self.assertIn("vm_parameter:count1", intent.dependencies)
        self.assertIn("vm_parameter:speed1", intent.dependencies)
        self.assertIn("pool_capacity", intent.dependencies)

    def test_aimed_and_rng_modes_are_separate_residuals(self) -> None:
        aimed = _instruction(
            BASE,
            time=1,
            opcode=0x62,
            payload=_fire_payload(),
        )
        rng = _instruction(
            aimed.address + aimed.size,
            time=2,
            opcode=0x68,
            payload=_fire_payload(),
        )
        terminate = _instruction(
            rng.address + rng.size,
            time=3,
            opcode=0x01,
        )
        result = _analyze((aimed, rng, terminate))
        self.assertEqual(
            [intent.intent_status for intent in result.intents],
            [INTENT_PLAYER_AIM, INTENT_RNG],
        )
        self.assertIn(
            "player_aim_at_emission",
            result.intents[0].dependencies,
        )
        self.assertIn("gameplay_rng", result.intents[1].dependencies)

    def test_unknown_or_enabled_deferred_state_has_no_activation_frame(self) -> None:
        fire = _instruction(
            BASE,
            time=1,
            opcode=0x61,
            payload=_fire_payload(),
        )
        for deferred, dependency in (
            (None, "deferred_state"),
            (True, "deferred_emission"),
        ):
            with self.subTest(deferred=deferred):
                result = analyze_ecl_birth_intents(
                    _snapshot(),
                    instruction_at={BASE: fire}.__getitem__,
                    horizon_frames=2,
                    active_difficulty_mask=1,
                    deferred_fire_active=deferred,
                    spell_active=True,
                    minimum_fire_distance_clear=True,
                    fire_filter_clear=True,
                    available_slots=1536,
                    template_geometry_resolved=True,
                    emission_origin_resolved=True,
                    max_instructions=1,
                )
                intent = result.intents[0]
                self.assertEqual(intent.intent_status, INTENT_DEFERRED)
                self.assertIsNone(intent.activation_frame_support)
                self.assertIn(dependency, intent.dependencies)

    def test_deferred_enable_and_disable_are_tracked_on_literal_path(self) -> None:
        enable = _instruction(BASE, time=0, opcode=0x6B)
        queued = _instruction(
            enable.address + enable.size,
            time=1,
            opcode=0x61,
            payload=_fire_payload(),
        )
        disable = _instruction(
            queued.address + queued.size,
            time=2,
            opcode=0x6C,
        )
        immediate = _instruction(
            disable.address + disable.size,
            time=3,
            opcode=0x61,
            payload=_fire_payload(),
        )
        terminate = _instruction(
            immediate.address + immediate.size,
            time=4,
            opcode=0x01,
        )
        result = _analyze((enable, queued, disable, immediate, terminate))
        self.assertEqual(
            [intent.intent_status for intent in result.intents],
            [INTENT_DEFERRED, INTENT_LITERAL_SCHEDULE],
        )
        self.assertIsNone(result.intents[0].activation_frame_support)
        self.assertEqual(result.intents[1].activation_frame_support, (3, 3))

    def test_emit_current_pattern_is_explicitly_descriptor_unknown(self) -> None:
        emit = _instruction(BASE, time=2, opcode=0x6D)
        result = _analyze((emit,), max_instructions=1)
        intent = result.intents[0]
        self.assertEqual(intent.intent_status, INTENT_CURRENT_PATTERN)
        self.assertEqual(intent.activation_frame_support, (2, 2))
        self.assertIn("current_emission_descriptor", intent.dependencies)
        self.assertIsNone(intent.arguments)

    def test_rank_distance_template_pool_and_transform_dependencies_remain(self) -> None:
        fire = _instruction(
            BASE,
            time=0,
            opcode=0x61,
            payload=_fire_payload(transform_flags=0x8040),
        )
        result = analyze_ecl_birth_intents(
            _snapshot(),
            instruction_at={BASE: fire}.__getitem__,
            horizon_frames=1,
            active_difficulty_mask=1,
            deferred_fire_active=False,
            spell_active=False,
            minimum_fire_distance_clear=None,
            fire_filter_clear=None,
            available_slots=10,
            template_geometry_resolved=False,
            emission_origin_resolved=False,
            max_instructions=1,
        )
        dependencies = result.intents[0].dependencies
        self.assertIn("rank_adjustment", dependencies)
        self.assertIn("minimum_fire_distance", dependencies)
        self.assertIn("route_or_enemy_fire_filter", dependencies)
        self.assertIn("bullet_template_geometry", dependencies)
        self.assertIn("emission_origin", dependencies)
        self.assertIn("transform_program", dependencies)
        self.assertIn("pool_capacity", dependencies)

    def test_nonfinite_literal_is_retained_as_residual(self) -> None:
        fire = _instruction(
            BASE,
            time=0,
            opcode=0x61,
            payload=_fire_payload(speed1=math.nan),
        )
        result = _analyze((fire,), max_instructions=1)
        self.assertIn("nonfinite_literal", result.intents[0].dependencies)

    def test_dynamic_nonfinite_storage_is_not_treated_as_a_literal(self) -> None:
        fire = _instruction(
            BASE,
            time=0,
            opcode=0x61,
            payload=_fire_payload(speed1=math.nan),
            parameter_mask=0x10,
        )
        result = _analyze((fire,), max_instructions=1)
        self.assertNotIn(
            "nonfinite_literal",
            result.intents[0].dependencies,
        )

    def test_counts_use_the_signed_low_word_written_by_the_vm(self) -> None:
        fire = _instruction(
            BASE,
            time=0,
            opcode=0x61,
            payload=_fire_payload(count1=0x10004, count2=2),
        )
        result = _analyze((fire,), max_instructions=1)
        self.assertEqual(result.intents[0].arguments.count1, 4)
        self.assertEqual(result.intents[0].requested_bullets, 8)

    def test_literal_jump_follows_target_and_updates_timer(self) -> None:
        target = BASE + 0x80
        jump = _instruction(
            BASE,
            time=0,
            opcode=0x04,
            payload=struct.pack("<ii", 3, target - BASE),
        )
        fire = _instruction(
            target,
            time=5,
            opcode=0x61,
            payload=_fire_payload(),
        )
        terminate = _instruction(
            fire.address + fire.size,
            time=6,
            opcode=0x01,
        )
        result = _analyze((jump, fire, terminate))
        self.assertEqual(result.intents[0].instruction_frame, 2)

    def test_unsupported_control_or_source_topology_stops_before_fire(self) -> None:
        for opcode, reason in (
            (0x28, "unsupported_control_flow"),
            (0x58, "source_topology_change"),
            (0x5A, "source_topology_change"),
            (0x87, "unsupported_auxiliary_or_callback"),
            (0x54, "unknown_opcode"),
        ):
            with self.subTest(opcode=opcode):
                blocker = _instruction(BASE, time=0, opcode=opcode)
                fire = _instruction(
                    blocker.address + blocker.size,
                    time=1,
                    opcode=0x61,
                    payload=_fire_payload(),
                )
                result = _analyze((blocker, fire))
                self.assertEqual(result.stop_reason, reason)
                self.assertEqual(result.intents, ())
                self.assertEqual(result.coverage_status, "unknown")
                self.assertEqual(result.unknown_from_frame, 1)

    def test_emission_state_mutation_stops_instead_of_using_root_values(self) -> None:
        for opcode in (0x52, 0x69, 0x6A, 0x6E, 0x6F):
            with self.subTest(opcode=opcode):
                mutation = _instruction(BASE, time=0, opcode=opcode)
                result = _analyze((mutation,))
                self.assertEqual(
                    result.stop_reason,
                    "unsupported_emission_state_mutation",
                )
                self.assertEqual(result.intents, ())

    def test_ineligible_fire_is_skipped_without_mutating_deferred_state(self) -> None:
        skipped = _instruction(
            BASE,
            time=1,
            opcode=0x61,
            payload=_fire_payload(),
            difficulty_mask=2,
        )
        terminate = _instruction(
            skipped.address + skipped.size,
            time=2,
            opcode=0x01,
        )
        result = _analyze((skipped, terminate))
        self.assertEqual(result.intents, ())
        self.assertEqual(result.stop_reason, "terminate")

    def test_horizon_and_invalid_payload_fail_closed(self) -> None:
        later = _instruction(
            BASE,
            time=30,
            opcode=0x61,
            payload=_fire_payload(),
        )
        horizon = _analyze((later,))
        self.assertEqual(horizon.stop_reason, "horizon")
        self.assertTrue(horizon.horizon_covered)
        self.assertEqual(horizon.coverage_status, "complete")
        self.assertEqual(horizon.covered_through_frame, 20)
        self.assertIsNone(horizon.unknown_from_frame)
        self.assertEqual(horizon.intents, ())

        malformed = _instruction(
            BASE,
            time=0,
            opcode=0x61,
            payload=b"\x00" * 31,
        )
        invalid = _analyze((malformed,))
        self.assertEqual(invalid.stop_reason, "invalid_direct_fire_payload")
        self.assertEqual(invalid.coverage_status, "unknown")
        self.assertEqual(
            invalid.record()["coverage"]["result_kind"],
            "prefix_only",
        )
        self.assertEqual(invalid.intents, ())

    def test_instruction_limit_retains_only_prefix_intent_authority(self) -> None:
        fire = _instruction(
            BASE,
            time=3,
            opcode=0x61,
            payload=_fire_payload(),
        )
        result = _analyze((fire,), max_instructions=1)
        self.assertEqual(len(result.intents), 1)
        self.assertEqual(result.stop_reason, "instruction_limit")
        self.assertFalse(result.horizon_covered)
        self.assertEqual(result.stop_frame, 3)
        self.assertEqual(result.covered_through_frame, 2)
        self.assertEqual(result.unknown_from_frame, 3)
        self.assertEqual(result.coverage_status, "unknown")


if __name__ == "__main__":
    unittest.main()
