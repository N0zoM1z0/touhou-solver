from __future__ import annotations

from pathlib import Path
import struct
import unittest

from th08_native_future_body_root import TH08_TIMELINE_RUNTIME_BASE
from th08_runtime.timeline_spawn_forecast import (
    ECL_DIFFICULTY_MASK_ADDRESS,
    ECL_FILE_CONTEXT_ADDRESS,
    ECL_FILE_HEADER_SIZE,
    FRSCREEN_STATE_ADDRESS,
    FRSCREEN_TIMELINE_SPAWN_GATE_OFFSET,
    StageTimelineSpawnForecaster,
    TIMELINE_RUNTIME_SLOT_COUNT,
    TIMELINE_RUNTIME_SLOT_SIZE,
    TIMELINE_SPAWN_SUPPRESSED_ADDRESS,
    TimelineClockObservation,
    forecast_upcoming_fixed_spawn,
)
from th08_runtime_agent import ADDR_ENEMY_MANAGER_FRAME


ROOT = Path(__file__).resolve().parents[1]
STAGE4A_ECL = ROOT / "artifacts" / "decoded" / "ecldata4a.ecl"
RUNTIME_BASE = 0x10000000


class _TimelineReader:
    def __init__(self, *, corrupt_forecast_bytes: bool = False) -> None:
        self.static = STAGE4A_ECL.read_bytes()
        self.header = bytearray(self.static[:ECL_FILE_HEADER_SIZE])
        _, _, timeline_count = struct.unpack_from("<IHH", self.header)
        offsets = list(struct.unpack_from("<16I", self.header, 8))
        for index in range(timeline_count + 1):
            offsets[index] += RUNTIME_BASE
        struct.pack_into("<16I", self.header, 8, *offsets)
        self.runtime_table = bytearray(
            TIMELINE_RUNTIME_SLOT_COUNT * TIMELINE_RUNTIME_SLOT_SIZE
        )
        struct.pack_into(
            "<iIiI",
            self.runtime_table,
            0,
            3594,
            0,
            3595,
            RUNTIME_BASE + 0xADEC,
        )
        self.corrupt_forecast_bytes = corrupt_forecast_bytes

    def u32(self, address: int) -> int:
        if address != ADDR_ENEMY_MANAGER_FRAME:
            raise OSError(f"unexpected u32 address {address:#x}")
        return 3595

    def read(self, address: int, size: int) -> bytes:
        if address == ECL_FILE_CONTEXT_ADDRESS:
            return struct.pack(
                "<II",
                RUNTIME_BASE,
                RUNTIME_BASE + ECL_FILE_HEADER_SIZE,
            )
        if address == RUNTIME_BASE and size == ECL_FILE_HEADER_SIZE:
            return bytes(self.header)
        if address == ECL_DIFFICULTY_MASK_ADDRESS:
            return b"\x08"
        if address == TIMELINE_SPAWN_SUPPRESSED_ADDRESS:
            return b"\x00\x00\x00\x00"
        if (
            address
            == FRSCREEN_STATE_ADDRESS
            + FRSCREEN_TIMELINE_SPAWN_GATE_OFFSET
        ):
            return b"\x00"
        if address == TH08_TIMELINE_RUNTIME_BASE:
            return bytes(self.runtime_table)
        if RUNTIME_BASE <= address < RUNTIME_BASE + len(self.static):
            offset = address - RUNTIME_BASE
            result = bytearray(self.static[offset : offset + size])
            if self.corrupt_forecast_bytes and result:
                result[-1] ^= 0x01
            return bytes(result)
        raise OSError(f"unexpected read {address:#x}+{size:#x}")


class TimelineSpawnForecastTests(unittest.TestCase):
    def test_stage4a_clock_forecasts_middle_spawn_before_exhaustion(
        self,
    ) -> None:
        forecaster = StageTimelineSpawnForecaster(
            STAGE4A_ECL,
            expected_difficulty_mask=0x08,
        )

        target = forecast_upcoming_fixed_spawn(
            forecaster.ecl,
            (
                TimelineClockObservation(
                    timeline_index=0,
                    elapsed=3595,
                    instruction_offset=0xADEC,
                ),
            ),
            active_difficulty_mask=0x08,
        )

        self.assertIsNotNone(target)
        assert target is not None
        self.assertEqual(target.instruction_time, 3660)
        self.assertEqual(target.lead_frames, 65)
        self.assertEqual(target.x, 320.0)
        self.assertEqual(target.y, -16.0)

    def test_live_observer_requires_exact_runtime_instruction_bytes(
        self,
    ) -> None:
        forecaster = StageTimelineSpawnForecaster(
            STAGE4A_ECL,
            expected_difficulty_mask=0x08,
        )

        observed = forecaster.observe(_TimelineReader())
        corrupted = forecaster.observe(
            _TimelineReader(corrupt_forecast_bytes=True)
        )

        self.assertEqual(
            observed.reason,
            "upcoming_fixed_spawn_observed",
        )
        self.assertIsNotNone(observed.target)
        assert observed.target is not None
        self.assertEqual(observed.target.x, 320.0)
        self.assertIsNone(corrupted.target)
        self.assertIn(
            "runtime forecast instruction bytes mismatch",
            corrupted.reason,
        )


if __name__ == "__main__":
    unittest.main()
