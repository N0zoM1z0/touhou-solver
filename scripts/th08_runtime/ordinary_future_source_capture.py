"""Coherent, sparse-read native root for ordinary future-source closure."""

from __future__ import annotations

import hashlib
import struct
import time
from dataclasses import dataclass
from typing import Any

from th08_ecl_tool.core import EclFile
from th08_live.enemy_sensor import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_FLAGS_OFFSET,
    ENEMY_MANAGER_TEMPLATE_BASE,
    ENEMY_POOL_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_STRIDE,
)
from th08_runtime.game_state import ADDR_ENEMY_MANAGER_FRAME
from th08_runtime.native_snapshot_projection import (
    COLLISION_CONTROL_PROJECTION_SCHEMA,
    _bullet_template_geometry_record,
    _enemy_source_record,
    _timeline_runtime_inventory_record,
)
from th08_runtime.sensing import observe_state
from th08_ordinary_future_sources import (
    OrdinaryFutureSourceClosure,
    project_ordinary_future_sources,
)


ORDINARY_FUTURE_SOURCE_SNAPSHOT_SCHEMA = (
    "th08-ordinary-future-source-snapshot-v1"
)


@dataclass(frozen=True)
class OrdinaryFutureSourceSnapshot:
    frame_before: int
    frame_after: int
    payload: dict[str, object]
    read_ms: float
    attempts: int

    @property
    def stable(self) -> bool:
        return self.frame_before == self.frame_after


@dataclass(frozen=True)
class OrdinaryFutureSourceCaptureResult:
    snapshot: OrdinaryFutureSourceSnapshot
    closure: OrdinaryFutureSourceClosure


def _read_active_enemy_records(
    reader: Any,
) -> tuple[bytes, bytes, int]:
    manager_blob = bytearray(ENEMY_STRIDE)
    active_record_count = 0
    manager_flags = reader.u32(
        ENEMY_MANAGER_TEMPLATE_BASE + ENEMY_FLAGS_OFFSET
    )
    if manager_flags & ENEMY_ACTIVE_FLAG:
        manager_blob[:] = reader.read(
            ENEMY_MANAGER_TEMPLATE_BASE,
            ENEMY_STRIDE,
        )
        active_record_count += 1

    # Keep native slot coordinates while avoiding a 10 MiB process read.
    # Only active records cross the process boundary; the zero-filled local
    # image lets the existing complete decoder retain its slot identity.
    ordinary_blob = bytearray(ENEMY_POOL_SIZE * ENEMY_STRIDE)
    for slot in range(ENEMY_POOL_SIZE):
        pointer = ENEMY_POOL_BASE + slot * ENEMY_STRIDE
        flags = reader.u32(pointer + ENEMY_FLAGS_OFFSET)
        if not flags & ENEMY_ACTIVE_FLAG:
            continue
        base = slot * ENEMY_STRIDE
        ordinary_blob[base : base + ENEMY_STRIDE] = reader.read(
            pointer,
            ENEMY_STRIDE,
        )
        active_record_count += 1
    return bytes(manager_blob), bytes(ordinary_blob), active_record_count


def _canonical_runtime_ecl_sha256(
    reader: Any,
    timeline_runtime: dict[str, object],
) -> str:
    ecl_file = timeline_runtime["ecl_file"]
    assert isinstance(ecl_file, dict)
    file_base = int(ecl_file["file_base"])
    size = int(ecl_file["static_data_end_offset"])
    subroutine_count = int(ecl_file["subroutine_count"])
    if size < 0x48 + subroutine_count * 4:
        raise ValueError("runtime ECL image is shorter than its pointer tables")
    canonical = bytearray(reader.read(file_base, size))
    if len(canonical) != size:
        raise ValueError("runtime ECL image read is truncated")
    # ecl_load_file relocates the 16 timeline/data-end slots and every
    # subroutine-table entry in place.  Undo only those documented pointer
    # tables; instruction bytes remain the shipped file bytes.
    for offset in range(0x08, 0x48, 4):
        pointer = struct.unpack_from("<I", canonical, offset)[0]
        if pointer:
            if not file_base <= pointer <= file_base + size:
                raise ValueError("runtime ECL timeline pointer is out of range")
            struct.pack_into("<I", canonical, offset, pointer - file_base)
    for index in range(subroutine_count):
        offset = 0x48 + index * 4
        pointer = struct.unpack_from("<I", canonical, offset)[0]
        if not file_base <= pointer < file_base + size:
            raise ValueError("runtime ECL subroutine pointer is out of range")
        struct.pack_into("<I", canonical, offset, pointer - file_base)
    return hashlib.sha256(canonical).hexdigest()


def _compact_state(state: dict[str, object]) -> dict[str, object]:
    player = state["player"]
    spell = state["spell"]
    assert isinstance(player, dict)
    assert isinstance(spell, dict)
    return {
        "manager_frame": int(state["enemy_manager_frame"]),
        "time_scale_bits": int(state["time_scale_bits"]),
        "rng_state": int(state["rng_state"]),
        "rng_calls": int(state["rng_calls"]),
        "player_x": float(player["x"]),
        "player_y": float(player["y"]),
        "player_phase": int(player["phase"]),
        "predeath_counter": int(player["predeath_counter"]),
        "spell_id": (
            int(spell["spell_id"]) if bool(spell["active"]) else None
        ),
    }


def _payload(
    reader: Any,
    *,
    manager_blob: bytes,
    ordinary_blob: bytes,
    state: dict[str, object],
) -> dict[str, object]:
    manager = _enemy_source_record(
        reader,
        enemy_blob=manager_blob,
        pool_base=ENEMY_MANAGER_TEMPLATE_BASE,
        pool_size=1,
        source_role="enemy_manager_template_or_special_singleton",
    )
    ordinary = _enemy_source_record(
        reader,
        enemy_blob=ordinary_blob,
        pool_base=ENEMY_POOL_BASE,
        pool_size=ENEMY_POOL_SIZE,
        source_role="ordinary_enemy_pool",
    )
    timeline = _timeline_runtime_inventory_record(reader)
    ecl_file = timeline["ecl_file"]
    assert isinstance(ecl_file, dict)
    ecl_file["canonical_sha256"] = _canonical_runtime_ecl_sha256(
        reader,
        timeline,
    )
    return {
        "schema": COLLISION_CONTROL_PROJECTION_SCHEMA,
        "compact_state": _compact_state(state),
        "enemy_manager_template_source": manager,
        "enemy_bodies": ordinary["enemy_bodies"],
        "enemy_main_ecl_vm_inventory": ordinary[
            "main_ecl_vm_inventory"
        ],
        "enemy_main_ecl_installed_callbacks": ordinary[
            "main_ecl_installed_callbacks"
        ],
        "enemy_periodic_emission_state": ordinary[
            "periodic_emission_state"
        ],
        "enemy_emission_state": ordinary["emission_state"],
        "enemy_motion_state": ordinary["motion_state"],
        "enemy_phase_transition_state": ordinary[
            "phase_transition_state"
        ],
        "enemy_auxiliary_ecl_contexts": ordinary[
            "auxiliary_ecl_contexts"
        ],
        "bullet_template_geometry": _bullet_template_geometry_record(reader),
        "stage_timeline_runtime": timeline,
    }


def capture_ordinary_future_source_snapshot(
    reader: Any,
    *,
    maximum_attempts: int = 2,
) -> OrdinaryFutureSourceSnapshot:
    """Capture one complete future-source root under a manager-frame bracket."""

    if maximum_attempts <= 0:
        raise ValueError("future-source capture attempts must be positive")
    started = time.perf_counter()
    snapshot: OrdinaryFutureSourceSnapshot | None = None
    for attempt in range(1, maximum_attempts + 1):
        frame_before = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
        manager_blob, ordinary_blob, _active_count = (
            _read_active_enemy_records(reader)
        )
        state = observe_state(reader)
        payload = _payload(
            reader,
            manager_blob=manager_blob,
            ordinary_blob=ordinary_blob,
            state=state,
        )
        frame_after = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
        snapshot = OrdinaryFutureSourceSnapshot(
            frame_before=frame_before,
            frame_after=frame_after,
            payload=payload,
            read_ms=(time.perf_counter() - started) * 1000.0,
            attempts=attempt,
        )
        if (
            snapshot.stable
            and int(payload["compact_state"]["manager_frame"])
            == frame_before
        ):
            return snapshot
    assert snapshot is not None
    return snapshot


def capture_and_project_ordinary_future_sources(
    reader: Any,
    ecl: EclFile,
    *,
    horizon_frames: int,
    maximum_attempts: int = 2,
) -> OrdinaryFutureSourceCaptureResult:
    snapshot = capture_ordinary_future_source_snapshot(
        reader,
        maximum_attempts=maximum_attempts,
    )
    if not snapshot.stable:
        raise RuntimeError(
            "ordinary future-source snapshot crossed manager frames "
            f"{snapshot.frame_before}->{snapshot.frame_after}"
        )
    closure = project_ordinary_future_sources(
        snapshot.payload,
        ecl,
        horizon_frames=horizon_frames,
    )
    return OrdinaryFutureSourceCaptureResult(
        snapshot=snapshot,
        closure=closure,
    )


__all__ = [
    "ORDINARY_FUTURE_SOURCE_SNAPSHOT_SCHEMA",
    "OrdinaryFutureSourceSnapshot",
    "OrdinaryFutureSourceCaptureResult",
    "capture_and_project_ordinary_future_sources",
    "capture_ordinary_future_source_snapshot",
]
