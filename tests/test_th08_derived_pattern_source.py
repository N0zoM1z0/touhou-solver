import json
import math
import random
import struct
import unittest

from th08_bullet_transform_model import TransformKind
from th08_live.bullet_birth import BULLET_TIMER_CURRENT_OFFSET
from th08_live.bullet_decode import (
    BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
    BULLET_POSITION_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STRIDE,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_TRANSFORM_PROGRAM_OFFSET,
    BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
)
from th08_live.derived_pattern_source import (
    TRANSFORM_RECORD_SIZE,
    observe_derived_pattern_sources,
)
from th08_live.derived_pattern_source_native import (
    NativeDerivedPatternSourceObserver,
    native_derived_pattern_source_available,
)
from th08_live.sensor import BULLET_POOL_SIZE


def _pool() -> bytearray:
    return bytearray(BULLET_POOL_SIZE * BULLET_STRIDE)


def _signed_i32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value if value < 0x80000000 else value - 0x100000000


def _record(
    *,
    kind: int,
    allow_while_active: bool = False,
    float_0: float = 0.25,
    float_1: float = 0.75,
    int_0: int = 0,
    int_1: int = 0,
) -> bytes:
    return struct.pack(
        "<ffiiII",
        float_0,
        float_1,
        _signed_i32(int_0),
        _signed_i32(int_1),
        kind,
        int(allow_while_active),
    )


def _set_source(
    blob: bytearray,
    slot: int,
    *,
    active: bool = True,
    age: int = 12,
    position: tuple[float, float] = (96.0, 128.0),
    transform_flags: int = 0,
    original_flags: int = int(TransformKind.EMIT_DERIVED_PATTERN),
    cursor: int = 3,
    first_kind: int = int(TransformKind.EMIT_DERIVED_PATTERN),
    second_kind: int = int(TransformKind.DERIVED_PATTERN_PARAMETERS),
    allow_while_active: bool = False,
    count_1: int = 3,
    count_2: int = 1,
    child_flags: int = 0x200,
) -> None:
    base = slot * BULLET_STRIDE
    struct.pack_into(
        "<H",
        blob,
        base + BULLET_STATE_OFFSET,
        1 if active else 0,
    )
    struct.pack_into(
        "<i",
        blob,
        base + BULLET_TIMER_CURRENT_OFFSET,
        age,
    )
    struct.pack_into(
        "<ff",
        blob,
        base + BULLET_POSITION_OFFSET,
        *position,
    )
    struct.pack_into(
        "<I",
        blob,
        base + BULLET_TRANSFORM_FLAGS_OFFSET,
        transform_flags,
    )
    struct.pack_into(
        "<I",
        blob,
        base + BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
        original_flags,
    )
    struct.pack_into(
        "<i",
        blob,
        base + BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
        cursor,
    )
    if 0 <= cursor < 18:
        first_offset = (
            base
            + BULLET_TRANSFORM_PROGRAM_OFFSET
            + cursor * TRANSFORM_RECORD_SIZE
        )
        blob[first_offset : first_offset + TRANSFORM_RECORD_SIZE] = _record(
            kind=first_kind,
            allow_while_active=allow_while_active,
            int_0=0x01020304,
            int_1=count_1,
        )
        if cursor + 1 < 18:
            second_offset = first_offset + TRANSFORM_RECORD_SIZE
            blob[
                second_offset : second_offset + TRANSFORM_RECORD_SIZE
            ] = _record(
                kind=second_kind,
                float_0=1.25,
                float_1=2.5,
                int_0=count_2,
                int_1=child_flags,
            )


@unittest.skipUnless(
    native_derived_pattern_source_available(),
    "native derived-pattern source library unavailable",
)
class DerivedPatternSourceParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.native = NativeDerivedPatternSourceObserver()

    def assert_parity(self, blob: bytearray) -> None:
        expected = observe_derived_pattern_sources(
            blob,
            frame_before=100,
            frame_after=101,
        )
        actual = self.native.observe(
            blob,
            frame_before=100,
            frame_after=101,
        )
        self.assertEqual(expected.record(), actual.record())

    def test_ready_source_decodes_complete_pair(self) -> None:
        blob = _pool()
        _set_source(blob, 17)
        self.assert_parity(blob)
        observation = observe_derived_pattern_sources(
            blob,
            frame_before=10,
            frame_after=10,
        )
        self.assertEqual(observation.active_count, 1)
        self.assertEqual(len(observation.candidates), 1)
        evidence = observation.candidates[0]
        self.assertEqual(evidence.slot, 17)
        self.assertEqual(evidence.pattern.count_1, 3)
        self.assertEqual(evidence.pattern.count_2, 1)
        self.assertEqual(evidence.pattern.child_transform_flags, 0x200)
        self.assertEqual(
            evidence.record()["pattern"]["predicted_child_count"],
            3,
        )

    def test_readiness_predicate_boundaries(self) -> None:
        blob = _pool()
        _set_source(blob, 1, transform_flags=0x10)
        _set_source(
            blob,
            2,
            transform_flags=0x10,
            allow_while_active=True,
        )
        _set_source(blob, 3, original_flags=0)
        _set_source(blob, 4, second_kind=0)
        _set_source(blob, 5, cursor=17)
        _set_source(blob, 6, active=False)
        self.assert_parity(blob)
        observation = observe_derived_pattern_sources(
            blob,
            frame_before=10,
            frame_after=11,
        )
        self.assertEqual(observation.active_count, 5)
        self.assertEqual(
            tuple(candidate.slot for candidate in observation.candidates),
            (2,),
        )

    def test_nonfinite_parent_is_retained_but_strict_json_safe(self) -> None:
        blob = _pool()
        _set_source(blob, 9, position=(math.nan, math.inf))
        self.assert_parity(blob)
        record = self.native.observe(
            blob,
            frame_before=20,
            frame_after=20,
        ).record()
        self.assertFalse(record["candidates"][0]["geometry_finite"])
        self.assertIsNone(record["candidates"][0]["position"])
        json.dumps(record, allow_nan=False)

    def test_randomized_full_pool_layout_matches_scalar_oracle(self) -> None:
        randomizer = random.Random(0xD3A1)
        blob = _pool()
        expected_slots = []
        for slot in randomizer.sample(range(BULLET_POOL_SIZE), 96):
            category = randomizer.randrange(7)
            arguments = {
                "age": randomizer.randrange(0, 600),
                "position": (
                    randomizer.uniform(-64.0, 448.0),
                    randomizer.uniform(-64.0, 512.0),
                ),
                "cursor": randomizer.randrange(0, 17),
            }
            if category == 0:
                expected_slots.append(slot)
            elif category == 1:
                arguments["transform_flags"] = 0x40
            elif category == 2:
                arguments["original_flags"] = 0
            elif category == 3:
                arguments["second_kind"] = 0
            elif category == 4:
                arguments["first_kind"] = 0x20000
            elif category == 5:
                arguments["active"] = False
            else:
                arguments["allow_while_active"] = True
                arguments["transform_flags"] = 0x80
                expected_slots.append(slot)
            _set_source(blob, slot, **arguments)
        self.assert_parity(blob)
        observation = self.native.observe(
            blob,
            frame_before=500,
            frame_after=503,
        )
        self.assertEqual(
            tuple(candidate.slot for candidate in observation.candidates),
            tuple(sorted(expected_slots)),
        )

    def test_rejected_observation_does_not_poison_next_result(self) -> None:
        with self.assertRaises(ValueError):
            self.native.observe(
                bytearray(10),
                frame_before=1,
                frame_after=1,
            )
        blob = _pool()
        _set_source(blob, 21)
        self.assert_parity(blob)
        diagnostics = self.native.diagnostics()
        self.assertGreaterEqual(diagnostics.prepare_ms, 0.0)
        self.assertGreaterEqual(diagnostics.native_call_ms, 0.0)
        self.assertGreaterEqual(diagnostics.materialize_ms, 0.0)


class DerivedPatternSourceValidationTests(unittest.TestCase):
    def test_invalid_capture_interval_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "capture frame"):
            observe_derived_pattern_sources(
                _pool(),
                frame_before=9,
                frame_after=8,
            )


if __name__ == "__main__":
    unittest.main()
