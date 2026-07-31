"""Exact loaded-SHT provenance for Route-2 player-shot records."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from typing import Any

from th08_runtime.game_state import (
    ADDR_PLAYER,
    PLAYER_PRIMARY_SHT_POINTER_OFFSET,
    PLAYER_SECONDARY_SHT_POINTER_OFFSET,
)


LOADED_ROUTE2_SHT_STATE_SCHEMA = "th08-loaded-route2-sht-state-v1"
SHT_FIXED_HEADER_SIZE = 0x38
SHT_LEVEL_ENTRY_SIZE = 8
SHT_SHOT_RECORD_SIZE = 56
SHT_SENTINEL_SIZE = 4
SHT_CALLBACK_OFFSETS = (0x28, 0x2C, 0x30, 0x34)
RANDOM_SPREAD_CALLBACK_POINTER = 0x004501B0


@dataclass(frozen=True)
class Route2ShtProfileSpec:
    profile: str
    size: int
    level_count: int
    normal_level_count: int
    power_upper_bounds: tuple[int, ...]
    raw_sha256: str


PRIMARY_SPEC = Route2ShtProfileSpec(
    profile="unfocused_primary",
    size=1584,
    level_count=6,
    normal_level_count=6,
    power_upper_bounds=(8, 24, 48, 80, 128, 999),
    raw_sha256=(
        "4765744ab5bbf797746469d5a6afc6ec7d4b0371422b5aa5a2e54ae668c48885"
    ),
)
SECONDARY_SPEC = Route2ShtProfileSpec(
    profile="focused_secondary",
    size=3568,
    level_count=8,
    normal_level_count=6,
    power_upper_bounds=(8, 24, 48, 80, 128, 999, 999, 999),
    raw_sha256=(
        "f7554b3a32e16da01de9432e22609482a1c98a33212eb904ad47789079abebd3"
    ),
)


def _read_exact(reader: Any, address: int, size: int, *, field: str) -> bytes:
    data = reader.read(address, size)
    if len(data) != size:
        raise ValueError(
            f"short {field} read at {address:#x}: "
            f"expected {size:#x}, received {len(data):#x}"
        )
    return data


@dataclass(frozen=True)
class LoadedShtRecordProvenance:
    profile: str
    level: int
    record_offset: int
    record_pointer: int
    normal_selector_reachable: bool
    fire_period: int
    fire_phase: int
    damage: int
    source_index: int
    shot_type: int
    callback_indices: tuple[int, int, int, int]

    def record(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "level": self.level,
            "record_offset": self.record_offset,
            "record_pointer": self.record_pointer,
            "normal_selector_reachable": self.normal_selector_reachable,
            "fire_period": self.fire_period,
            "fire_phase": self.fire_phase,
            "damage": self.damage,
            "source_index": self.source_index,
            "shot_type": self.shot_type,
            "callback_indices": list(self.callback_indices),
        }


@dataclass(frozen=True)
class LoadedRoute2ShtProfile:
    spec: Route2ShtProfileSpec
    base_pointer: int
    normalized_sha256: str
    records: tuple[LoadedShtRecordProvenance, ...]

    def record(self) -> dict[str, object]:
        return {
            "profile": self.spec.profile,
            "base_pointer": self.base_pointer,
            "size": self.spec.size,
            "level_count": self.spec.level_count,
            "normal_level_count": self.spec.normal_level_count,
            "power_upper_bounds": list(self.spec.power_upper_bounds),
            "normalized_sha256": self.normalized_sha256,
            "expected_raw_sha256": self.spec.raw_sha256,
            "record_count": len(self.records),
            "normal_record_count": sum(
                record.normal_selector_reachable for record in self.records
            ),
            "special_record_count": sum(
                not record.normal_selector_reachable
                for record in self.records
            ),
        }


@dataclass(frozen=True)
class LoadedRoute2ShtState:
    primary: LoadedRoute2ShtProfile
    secondary: LoadedRoute2ShtProfile
    records_by_pointer: dict[int, LoadedShtRecordProvenance]

    def provenance_for_pointer(
        self,
        pointer: int,
    ) -> LoadedShtRecordProvenance | None:
        return self.records_by_pointer.get(pointer)

    def record(self) -> dict[str, object]:
        return {
            "schema": LOADED_ROUTE2_SHT_STATE_SCHEMA,
            "profiles": [
                self.primary.record(),
                self.secondary.record(),
            ],
            "exact_loaded_content": True,
            "normal_source_record_count": sum(
                record.normal_selector_reachable
                for record in self.records_by_pointer.values()
            ),
            "special_source_record_count": sum(
                not record.normal_selector_reachable
                for record in self.records_by_pointer.values()
            ),
            "authority": (
                "normalized_loaded_bytes_match_pinned_shipped_sht_content"
            ),
        }


def _callback_index(
    pointer: int,
    *,
    callback_slot: int,
    profile: str,
    level: int,
    record_offset: int,
) -> int:
    if pointer == 0:
        return 0
    if callback_slot == 0 and pointer == RANDOM_SPREAD_CALLBACK_POINTER:
        return 7
    raise ValueError(
        f"{profile} level {level} record {record_offset:#x} has "
        f"unknown callback-{callback_slot} pointer {pointer:#x}"
    )


def decode_loaded_route2_sht_profile(
    data: bytes,
    *,
    base_pointer: int,
    spec: Route2ShtProfileSpec,
) -> LoadedRoute2ShtProfile:
    if base_pointer <= 0:
        raise ValueError(f"{spec.profile} SHT base pointer is null")
    if len(data) != spec.size:
        raise ValueError(
            f"{spec.profile} loaded SHT requires {spec.size} exact bytes"
        )
    normalized = bytearray(data)
    level_count = struct.unpack_from("<H", data, 2)[0]
    if level_count != spec.level_count:
        raise ValueError(
            f"{spec.profile} loaded SHT level count {level_count} "
            f"does not match {spec.level_count}"
        )
    table_end = SHT_FIXED_HEADER_SIZE + level_count * SHT_LEVEL_ENTRY_SIZE
    if table_end > len(data):
        raise ValueError(f"{spec.profile} loaded SHT level table is truncated")

    level_offsets: list[int] = []
    power_bounds: list[int] = []
    for level in range(level_count):
        table_offset = SHT_FIXED_HEADER_SIZE + level * SHT_LEVEL_ENTRY_SIZE
        pointer, power_bound = struct.unpack_from("<Ii", data, table_offset)
        record_offset = pointer - base_pointer
        if (
            record_offset < table_end
            or record_offset >= len(data)
            or record_offset % 4
        ):
            raise ValueError(
                f"{spec.profile} level {level} pointer {pointer:#x} "
                "is outside the loaded SHT"
            )
        level_offsets.append(record_offset)
        power_bounds.append(power_bound)
        struct.pack_into("<I", normalized, table_offset, record_offset)
    if tuple(power_bounds) != spec.power_upper_bounds:
        raise ValueError(
            f"{spec.profile} loaded SHT Power bounds {tuple(power_bounds)!r} "
            f"do not match {spec.power_upper_bounds!r}"
        )
    if level_offsets != sorted(level_offsets) or len(set(level_offsets)) != len(
        level_offsets
    ):
        raise ValueError(f"{spec.profile} loaded SHT level pointers are unordered")

    records: list[LoadedShtRecordProvenance] = []
    level_ends = (*level_offsets[1:], len(data))
    for level, (start, end) in enumerate(
        zip(level_offsets, level_ends, strict=True)
    ):
        cursor = start
        while cursor < end:
            if cursor + SHT_SENTINEL_SIZE > end:
                raise ValueError(
                    f"{spec.profile} level {level} has a truncated sentinel"
                )
            fire_period = struct.unpack_from("<h", data, cursor)[0]
            if fire_period < 0:
                if cursor + SHT_SENTINEL_SIZE != end:
                    raise ValueError(
                        f"{spec.profile} level {level} sentinel is not terminal"
                    )
                break
            if cursor + SHT_SHOT_RECORD_SIZE > end:
                raise ValueError(
                    f"{spec.profile} level {level} record crosses its region"
                )
            callback_indices: list[int] = []
            for callback_slot, callback_offset in enumerate(
                SHT_CALLBACK_OFFSETS
            ):
                pointer = struct.unpack_from(
                    "<I",
                    data,
                    cursor + callback_offset,
                )[0]
                index = _callback_index(
                    pointer,
                    callback_slot=callback_slot,
                    profile=spec.profile,
                    level=level,
                    record_offset=cursor,
                )
                callback_indices.append(index)
                struct.pack_into(
                    "<I",
                    normalized,
                    cursor + callback_offset,
                    index,
                )
            records.append(
                LoadedShtRecordProvenance(
                    profile=spec.profile,
                    level=level,
                    record_offset=cursor,
                    record_pointer=base_pointer + cursor,
                    normal_selector_reachable=level < spec.normal_level_count,
                    fire_period=fire_period,
                    fire_phase=struct.unpack_from("<h", data, cursor + 0x02)[0],
                    damage=struct.unpack_from("<h", data, cursor + 0x1C)[0],
                    source_index=struct.unpack_from("<h", data, cursor + 0x20)[0],
                    shot_type=struct.unpack_from("<h", data, cursor + 0x22)[0],
                    callback_indices=tuple(callback_indices),
                )
            )
            cursor += SHT_SHOT_RECORD_SIZE
        else:
            raise ValueError(
                f"{spec.profile} level {level} has no negative-period sentinel"
            )

    normalized_sha256 = hashlib.sha256(normalized).hexdigest()
    if normalized_sha256 != spec.raw_sha256:
        raise ValueError(
            f"{spec.profile} normalized loaded SHT SHA-256 "
            f"{normalized_sha256} does not match pinned {spec.raw_sha256}"
        )
    return LoadedRoute2ShtProfile(
        spec=spec,
        base_pointer=base_pointer,
        normalized_sha256=normalized_sha256,
        records=tuple(records),
    )


def capture_loaded_route2_sht_state(reader: Any) -> LoadedRoute2ShtState:
    pointer_span_size = (
        PLAYER_SECONDARY_SHT_POINTER_OFFSET
        - PLAYER_PRIMARY_SHT_POINTER_OFFSET
        + 4
    )
    if pointer_span_size != 8:
        raise AssertionError("Route-2 SHT pointer fields are not adjacent")
    pointer_bytes = _read_exact(
        reader,
        ADDR_PLAYER + PLAYER_PRIMARY_SHT_POINTER_OFFSET,
        pointer_span_size,
        field="Route-2 loaded SHT pointers",
    )
    primary_pointer, secondary_pointer = struct.unpack("<II", pointer_bytes)
    if primary_pointer == secondary_pointer:
        raise ValueError("Route-2 primary and secondary SHT pointers alias")
    primary = decode_loaded_route2_sht_profile(
        _read_exact(
            reader,
            primary_pointer,
            PRIMARY_SPEC.size,
            field="Route-2 primary loaded SHT",
        ),
        base_pointer=primary_pointer,
        spec=PRIMARY_SPEC,
    )
    secondary = decode_loaded_route2_sht_profile(
        _read_exact(
            reader,
            secondary_pointer,
            SECONDARY_SPEC.size,
            field="Route-2 secondary loaded SHT",
        ),
        base_pointer=secondary_pointer,
        spec=SECONDARY_SPEC,
    )
    records = (*primary.records, *secondary.records)
    records_by_pointer = {record.record_pointer: record for record in records}
    if len(records_by_pointer) != len(records):
        raise ValueError("Route-2 loaded SHT record pointers overlap")
    return LoadedRoute2ShtState(
        primary=primary,
        secondary=secondary,
        records_by_pointer=records_by_pointer,
    )
