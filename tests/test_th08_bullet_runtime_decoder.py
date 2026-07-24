#!/usr/bin/env python3
"""Regression tests for CE-0084 live bullet-transform observation."""

from __future__ import annotations

import struct
import unittest

import numpy as np

from th08_bullet_transform_model import (
    BulletTransformRuntime,
    TransformKind,
    TransformRecord,
    parse_next_transform_record,
    parse_transform_record,
)
from th08_corridor_adapter import lower_bullets
from th08_ecl_runtime import EclVmSnapshot, TaggedVelocityToggle
from th08_live_dodge_agent import (
    BULLET_ANGLE_OFFSET,
    BULLET_GEOMETRY_OFFSET,
    BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
    BULLET_POOL_SIZE,
    BULLET_POSITION_OFFSET,
    BULLET_SPEED_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STOP_ANGLE_OPERAND_OFFSET,
    BULLET_STOP_DURATION_OFFSET,
    BULLET_STOP_REPEAT_COUNT_OFFSET,
    BULLET_STOP_REPEAT_LIMIT_OFFSET,
    BULLET_STOP_RESUME_SPEED_OFFSET,
    BULLET_STOP_TIMER_ELAPSED_OFFSET,
    BULLET_STOP_TIMER_FRACTION_OFFSET,
    BULLET_STRIDE,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_TRANSFORM_PROGRAM_OFFSET,
    BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
    BULLET_VELOCITY_OFFSET,
    Bullet,
    _build_bullet_frames,
    attach_tagged_velocity_toggles,
    decode_bullets,
    serialize_bullet_trace,
)
from touhou_control.trajectory import VelocityChange


def _record(
    *,
    index: int = 0,
    kind: int = TransformKind.STOP_REAIM_REPEAT,
) -> TransformRecord:
    return TransformRecord(
        index=index,
        kind=kind,
        allow_while_active=True,
        int_0=30,
        int_1=4,
        float_0=0.25,
        float_1=2.5,
    )


class BulletRuntimeDecoderTests(unittest.TestCase):
    def test_native_record_parser_preserves_signed_operands_and_gate(self) -> None:
        blob = struct.pack(
            "<ffiiII",
            1.25,
            -2.5,
            -3,
            4,
            TransformKind.STOP_REAIM_REPEAT,
            1,
        )
        record = parse_transform_record(blob, index=7)
        self.assertEqual(record.index, 7)
        self.assertEqual(record.kind, TransformKind.STOP_REAIM_REPEAT)
        self.assertTrue(record.allow_while_active)
        self.assertEqual((record.int_0, record.int_1), (-3, 4))
        self.assertEqual((record.float_0, record.float_1), (1.25, -2.5))

    def test_queue_cursor_selects_next_unconsumed_record(self) -> None:
        blob = bytearray(18 * 24)
        struct.pack_into(
            "<ffiiII",
            blob,
            5 * 24,
            0.5,
            3.0,
            12,
            2,
            TransformKind.STOP_TURN_REPEAT,
            0,
        )
        record = parse_next_transform_record(
            blob,
            program_offset=0,
            queue_cursor=5,
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.index, 5)
        self.assertEqual(record.kind, TransformKind.STOP_TURN_REPEAT)
        self.assertFalse(record.allow_while_active)
        self.assertIsNone(
            parse_next_transform_record(
                blob,
                program_offset=0,
                queue_cursor=18,
            )
        )

    def test_ce_0084_stopped_bullet_retains_pending_queue_and_stop_state(
        self,
    ) -> None:
        slot = 23
        base = slot * BULLET_STRIDE
        blob = bytearray(BULLET_POOL_SIZE * BULLET_STRIDE)
        struct.pack_into("<H", blob, base + BULLET_STATE_OFFSET, 2)
        struct.pack_into("<ff", blob, base + BULLET_GEOMETRY_OFFSET, 4.0, 6.0)
        struct.pack_into("<ff", blob, base + BULLET_POSITION_OFFSET, 120.0, 80.0)
        struct.pack_into("<ff", blob, base + BULLET_VELOCITY_OFFSET, 0.0, 0.0)
        struct.pack_into("<f", blob, base + BULLET_SPEED_OFFSET, 0.0)
        struct.pack_into("<f", blob, base + BULLET_ANGLE_OFFSET, 1.5)
        struct.pack_into("<I", blob, base + BULLET_TRANSFORM_FLAGS_OFFSET, 0)
        struct.pack_into(
            "<I",
            blob,
            base + BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
            TransformKind.STOP_REAIM_REPEAT | TransformKind.REFLECT_ALL_EDGES,
        )
        struct.pack_into(
            "<i",
            blob,
            base + BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
            3,
        )
        struct.pack_into(
            "<ffiiII",
            blob,
            base + BULLET_TRANSFORM_PROGRAM_OFFSET + 3 * 24,
            -1.0,
            2.0,
            4,
            5,
            TransformKind.REFLECT_ALL_EDGES,
            0,
        )
        struct.pack_into(
            "<f",
            blob,
            base + BULLET_STOP_TIMER_FRACTION_OFFSET,
            0.25,
        )
        struct.pack_into(
            "<i",
            blob,
            base + BULLET_STOP_TIMER_ELAPSED_OFFSET,
            17,
        )
        struct.pack_into(
            "<f",
            blob,
            base + BULLET_STOP_RESUME_SPEED_OFFSET,
            2.75,
        )
        struct.pack_into(
            "<f",
            blob,
            base + BULLET_STOP_ANGLE_OPERAND_OFFSET,
            0.125,
        )
        struct.pack_into(
            "<i",
            blob,
            base + BULLET_STOP_DURATION_OFFSET,
            30,
        )
        struct.pack_into(
            "<i",
            blob,
            base + BULLET_STOP_REPEAT_LIMIT_OFFSET,
            4,
        )
        struct.pack_into(
            "<i",
            blob,
            base + BULLET_STOP_REPEAT_COUNT_OFFSET,
            2,
        )

        bullets = decode_bullets(bytes(blob))
        self.assertEqual(len(bullets), 1)
        bullet = bullets[0]
        self.assertEqual((bullet.slot, bullet.transform_flags), (slot, 0))
        self.assertEqual((bullet.speed, bullet.angle), (0.0, 1.5))
        runtime = bullet.transform_runtime
        self.assertIsNotNone(runtime)
        self.assertEqual(
            runtime.original_flags,
            TransformKind.STOP_REAIM_REPEAT | TransformKind.REFLECT_ALL_EDGES,
        )
        self.assertEqual((runtime.queue_cursor, runtime.timer_elapsed), (3, 17))
        self.assertEqual(
            (runtime.duration, runtime.repeat_limit, runtime.repeat_count),
            (30, 4, 2),
        )
        self.assertEqual(
            (runtime.resume_speed, runtime.angle_operand, runtime.timer_fraction),
            (2.75, 0.125, 0.25),
        )
        self.assertEqual(
            (runtime.next_record.index, runtime.next_record.kind),
            (3, TransformKind.REFLECT_ALL_EDGES),
        )

    def test_trace_keeps_first_eight_fields_and_appends_compact_runtime(
        self,
    ) -> None:
        runtime = BulletTransformRuntime(
            original_flags=TransformKind.STOP_REAIM_REPEAT,
            queue_cursor=4,
            next_record=_record(index=4),
            timer_fraction=0.5,
            timer_elapsed=12,
            resume_speed=2.5,
            angle_operand=0.25,
            duration=30,
            repeat_limit=4,
            repeat_count=1,
        )
        bullet = Bullet(
            10.0,
            20.0,
            1.0,
            -1.0,
            2.0,
            3.0,
            0,
            7,
            1.5,
            0.75,
            runtime,
        )
        values = serialize_bullet_trace(bullet)
        self.assertEqual(
            values[:8],
            [7, 10.0, 20.0, 1.0, -1.0, 2.0, 3.0, 0],
        )
        self.assertEqual(
            values[8],
            [
                1.5,
                0.75,
                TransformKind.STOP_REAIM_REPEAT,
                4,
                [4, TransformKind.STOP_REAIM_REPEAT, 1, 0.25, 2.5, 30, 4],
                0.5,
                12,
                30,
                2.5,
                0.25,
                4,
                1,
                0,
                0,
                [],
                0.0,
                0.0,
            ],
        )
        self.assertEqual(
            serialize_bullet_trace(Bullet(1.0, 2.0, 0.0, 0.0, 2.0, 2.0))[8],
            None,
        )

    def test_runtime_observation_is_behavior_neutral_until_projection_gate(
        self,
    ) -> None:
        plain = Bullet(40.0, 50.0, 1.0, -2.0, 2.0, 3.0)
        observed = Bullet(
            40.0,
            50.0,
            1.0,
            -2.0,
            2.0,
            3.0,
            speed=2.25,
            angle=-1.0,
            transform_runtime=BulletTransformRuntime(
                original_flags=TransformKind.STOP_REAIM_REPEAT,
                queue_cursor=18,
                next_record=None,
                timer_fraction=0.0,
                timer_elapsed=0,
                resume_speed=2.25,
                angle_operand=0.0,
                duration=30,
                repeat_limit=3,
                repeat_count=0,
            ),
        )
        plain_frames = _build_bullet_frames((plain,), horizon=3, snapshot_lag=2)
        observed_frames = _build_bullet_frames(
            (observed,),
            horizon=3,
            snapshot_lag=2,
        )
        for plain_frame, observed_frame in zip(plain_frames, observed_frames):
            for plain_values, observed_values in zip(plain_frame, observed_frame):
                np.testing.assert_array_equal(plain_values, observed_values)
        self.assertEqual(
            lower_bullets((plain,), snapshot_lag=2),
            lower_bullets((observed,), snapshot_lag=2),
        )

    def test_local_projection_applies_velocity_event_on_native_update(self) -> None:
        bullet = Bullet(
            10.0,
            20.0,
            2.0,
            -1.0,
            2.0,
            3.0,
            velocity_changes=(VelocityChange(3, 0.0, 0.0),),
        )
        frames = _build_bullet_frames(
            (bullet,),
            horizon=5,
            snapshot_lag=0,
        )
        self.assertEqual(
            [float(frame[0][0]) for frame in frames],
            [12.0, 14.0, 14.0, 14.0, 14.0],
        )
        self.assertEqual(
            [float(frame[1][0]) for frame in frames],
            [19.0, 18.0, 18.0, 18.0, 18.0],
        )

    def test_callback_event_is_rebased_to_bullet_snapshot_epoch(self) -> None:
        bullet = Bullet(
            10.0,
            20.0,
            2.0,
            0.0,
            2.0,
            3.0,
            speed=2.0,
            angle=0.0,
            transform_runtime=BulletTransformRuntime(
                original_flags=0x100202,
                queue_cursor=0,
                next_record=None,
                timer_fraction=0.0,
                timer_elapsed=0,
                resume_speed=0.0,
                angle_operand=0.0,
                duration=0,
                repeat_limit=0,
                repeat_count=0,
            ),
            callback_phase_state=1,
        )
        snapshot = EclVmSnapshot(
            0x500000,
            0.0,
            300,
            0x100000,
            0.0,
            0.0,
            1.0,
        )
        attached = attach_tagged_velocity_toggles(
            (bullet,),
            vm_snapshot=snapshot,
            toggles=(
                TaggedVelocityToggle(
                    3,
                    12,
                    0x100000,
                    0.0,
                    0.0,
                ),
            ),
            frame_offset=2,
            event_frame_uncertainty=1,
        )[0]
        self.assertEqual(attached.velocity_changes[0].frame, 5)
        self.assertEqual(attached.trajectory_uncertainty_x, 2.0)
        frames = _build_bullet_frames(
            (attached,),
            horizon=6,
            snapshot_lag=0,
        )
        self.assertEqual(
            [float(frame[0][0]) for frame in frames],
            [12.0, 14.0, 16.0, 18.0, 18.0, 18.0],
        )


if __name__ == "__main__":
    unittest.main()
