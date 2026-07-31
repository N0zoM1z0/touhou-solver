from __future__ import annotations

import struct
import unittest
from pathlib import Path

from th08_runtime.game_state import (
    ADDR_PLAYER,
    PLAYER_PRIMARY_SHT_POINTER_OFFSET,
)
from th08_runtime.route2_sht_provenance import (
    PRIMARY_SPEC,
    RANDOM_SPREAD_CALLBACK_POINTER,
    SECONDARY_SPEC,
    SHT_CALLBACK_OFFSETS,
    SHT_FIXED_HEADER_SIZE,
    SHT_LEVEL_ENTRY_SIZE,
    SHT_SHOT_RECORD_SIZE,
    capture_loaded_route2_sht_state,
    decode_loaded_route2_sht_profile,
)
from th08_runtime.ordinary_future_source_capture import (
    _normal_future_damage_by_cadence_phase,
)


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_PATH = ROOT / "artifacts" / "decoded" / "ply02a.sht"
SECONDARY_PATH = ROOT / "artifacts" / "decoded" / "ply02as.sht"
PRIMARY_BASE = 0x03000000
SECONDARY_BASE = 0x03100000


def _relocate_sht(path: Path, *, base_pointer: int) -> bytes:
    data = bytearray(path.read_bytes())
    level_count = struct.unpack_from("<H", data, 2)[0]
    level_offsets = []
    for level in range(level_count):
        table_offset = SHT_FIXED_HEADER_SIZE + level * SHT_LEVEL_ENTRY_SIZE
        record_offset = struct.unpack_from("<I", data, table_offset)[0]
        level_offsets.append(record_offset)
        struct.pack_into("<I", data, table_offset, base_pointer + record_offset)
    level_ends = (*level_offsets[1:], len(data))
    for start, end in zip(level_offsets, level_ends, strict=True):
        cursor = start
        while cursor < end:
            if struct.unpack_from("<h", data, cursor)[0] < 0:
                break
            for callback_slot, callback_offset in enumerate(
                SHT_CALLBACK_OFFSETS
            ):
                index = struct.unpack_from(
                    "<I",
                    data,
                    cursor + callback_offset,
                )[0]
                pointer = (
                    RANDOM_SPREAD_CALLBACK_POINTER
                    if callback_slot == 0 and index == 7
                    else 0
                )
                if index not in (0, 7) or (
                    callback_slot != 0 and index != 0
                ):
                    raise AssertionError("unexpected Route-2 callback fixture")
                struct.pack_into(
                    "<I",
                    data,
                    cursor + callback_offset,
                    pointer,
                )
            cursor += SHT_SHOT_RECORD_SIZE
    return bytes(data)


class _Reader:
    def __init__(self, primary: bytes, secondary: bytes) -> None:
        self._memory = {
            (ADDR_PLAYER + PLAYER_PRIMARY_SHT_POINTER_OFFSET, 8): (
                struct.pack("<II", PRIMARY_BASE, SECONDARY_BASE)
            ),
            (PRIMARY_BASE, len(primary)): primary,
            (SECONDARY_BASE, len(secondary)): secondary,
        }

    def read(self, address: int, size: int) -> bytes:
        try:
            return self._memory[(address, size)]
        except KeyError as exc:
            raise AssertionError(f"unexpected read {address:#x}/{size:#x}") from exc


class Route2ShtProvenanceTests(unittest.TestCase):
    def test_loaded_pair_normalizes_to_pinned_content_and_records(self) -> None:
        state = capture_loaded_route2_sht_state(
            _Reader(
                _relocate_sht(PRIMARY_PATH, base_pointer=PRIMARY_BASE),
                _relocate_sht(SECONDARY_PATH, base_pointer=SECONDARY_BASE),
            )
        )

        self.assertEqual(
            state.primary.normalized_sha256,
            PRIMARY_SPEC.raw_sha256,
        )
        self.assertEqual(
            state.secondary.normalized_sha256,
            SECONDARY_SPEC.raw_sha256,
        )
        self.assertEqual(len(state.primary.records), 26)
        self.assertEqual(len(state.secondary.records), 61)
        self.assertEqual(
            sum(
                record.normal_selector_reachable
                for record in state.records_by_pointer.values()
            ),
            53,
        )
        primary_record = state.primary.records[0]
        self.assertEqual(primary_record.fire_period, 5)
        self.assertEqual(primary_record.fire_phase, 0)
        self.assertEqual(primary_record.damage, 48)
        self.assertEqual(primary_record.shot_type, 0)
        self.assertEqual(primary_record.callback_indices, (0, 0, 0, 0))
        cadence_damage = _normal_future_damage_by_cadence_phase(state)
        self.assertEqual(
            cadence_damage,
            (
                162, 0, 0, 82, 0, 130, 46, 0, 42, 40,
                156, 0, 46, 42, 0, 162, 0, 0, 82, 0,
            ),
        )
        self.assertEqual(sum(cadence_damage), 990)
        self.assertEqual(
            state.provenance_for_pointer(primary_record.record_pointer),
            primary_record,
        )
        self.assertIsNone(state.provenance_for_pointer(0xDEADBEEF))

    def test_loaded_scalar_corruption_fails_normalized_digest(self) -> None:
        loaded = bytearray(
            _relocate_sht(PRIMARY_PATH, base_pointer=PRIMARY_BASE)
        )
        loaded[4] ^= 1

        with self.assertRaisesRegex(ValueError, "normalized loaded SHT"):
            decode_loaded_route2_sht_profile(
                bytes(loaded),
                base_pointer=PRIMARY_BASE,
                spec=PRIMARY_SPEC,
            )

    def test_unknown_relocated_callback_fails_closed(self) -> None:
        loaded = bytearray(
            _relocate_sht(PRIMARY_PATH, base_pointer=PRIMARY_BASE)
        )
        first_record_offset = struct.unpack_from("<I", PRIMARY_PATH.read_bytes(), 0x38)[
            0
        ]
        struct.pack_into(
            "<I",
            loaded,
            first_record_offset + SHT_CALLBACK_OFFSETS[1],
            0xDEADBEEF,
        )

        with self.assertRaisesRegex(ValueError, "callback-1 pointer"):
            decode_loaded_route2_sht_profile(
                bytes(loaded),
                base_pointer=PRIMARY_BASE,
                spec=PRIMARY_SPEC,
            )


if __name__ == "__main__":
    unittest.main()
