"""Collision/control projection for TH08 native snapshot differentials.

This projection is deliberately narrower than a whole-process or whole-game
state identity.  It retains the native state that can explain a player hit:
input/RNG/clock state, hostile bullet and laser lifecycle state, enemy body
and ECL state, player collision state, and the route-2 option recurrence.
Renderer-owned ANM bytes remain visible in the broad native-root diagnostic
but do not decide collision/control equivalence.
"""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from th08_live.bullet_decode import BULLET_STATE_OFFSET, decode_bullets
from th08_live.enemy_ecl_inventory import (
    EnemyMainEclVmInventory,
    decode_enemy_main_ecl_vm_inventory,
)
from th08_live.enemy_sensor import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_FLAGS_OFFSET,
    ENEMY_POOL_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_STRIDE,
    PLAYER_LETHAL_AABB_OFFSET,
    PLAYER_LETHAL_AABB_SIZE,
    decode_enemy_bodies,
    decode_player_lethal_aabb,
)
from th08_live.hazard_decode import decode_lasers
from th08_live.auxiliary_vm.model import (
    ACTIVE_VM_BYTES,
    CONTEXT_ACTIVE_VM_OFFSET,
    CONTEXT_CALL_DEPTH_OFFSET,
    CONTEXT_TARGET_OFFSET,
    MAXIMUM_RESTORABLE_FRAMES,
)
from th08_live.models import serialize_bullet_trace
from th08_live.sensor import (
    BULLET_POOL_BASE,
    BULLET_POOL_SIZE,
    BULLET_STRIDE,
    LASER_POOL_BASE,
    LASER_POOL_SIZE,
    LASER_STRIDE,
)
from th08_ecl_auxiliary_core.model import AuxiliaryEclVmState
from th08_ecl_runtime import EclInstructionCache, ENEMY_MAIN_ECL_VM_OFFSET
from th08_native_future_body_root import TH08_TIMELINE_RUNTIME_BASE
from th08_runtime.game_state import ADDR_PLAYER


COLLISION_CONTROL_PROJECTION_SCHEMA = (
    "th08-native-snapshot-collision-control-projection-v7"
)

# Revalidated in bullet_manager_update (0x00431240).  These two adjacent
# Th08Timer objects are advanced separately at the end of each active bullet
# update.  Keep offset-based names here: +0xD8C/+0xD94 is used as the
# collision-age gate, but the complete interpretation of both timers across
# every spawn/fade state is not yet claimed.
BULLET_TIMER_D80_OFFSET = 0x0D80
BULLET_TIMER_D8C_OFFSET = 0x0D8C
TH08_TIMER_FRACTION_OFFSET = 0x04
TH08_TIMER_ELAPSED_OFFSET = 0x08

# Native spawn-state motion before the ordinary state-1 update.  A finishing
# ANM VM can transition to state 1 in the same manager call, so these divisors
# alone are exact only while the spawn/fade state remains active.
BULLET_STATE_MOTION_DIVISORS = {
    1: 1.0,
    2: 2.0,
    3: 2.5,
    4: 3.0,
    5: 2.0,
}

# Revalidated native layout:
# - enemy main ECL VM begins at +0x7F8; render/ANM state is before it;
# - route-2 option records begin at player +0x40C, have stride 0x2F4,
#   and their update recurrence consumes/writes the +0x2A4..+0x2F4 tail.
ENEMY_ANM_PREFIX_SIZE = 0x7F8
ROUTE2_OPTION_BASE_OFFSET = 0x40C
ROUTE2_OPTION_COUNT = 4
ROUTE2_OPTION_STRIDE = 0x2F4
ROUTE2_OPTION_CAUSAL_TAIL_OFFSET = 0x2A4

# Revalidated in the ECL 0x60..0x68 handler (0x0041B4E6) and the periodic
# post-VM emitter (0x00423150).  An enemy may stage one exact 44-byte fire
# instruction, then emit it whenever its period timer reaches the configured
# interval after the main and auxiliary VMs have run.
ENEMY_HITPOINTS_OFFSET = 0x2DFC
ENEMY_PERIODIC_EMISSION_DESCRIPTOR_OFFSET = 0x3034
ENEMY_PERIODIC_EMISSION_DESCRIPTOR_SIZE = 0x2C
ENEMY_PERIODIC_EMISSION_PERIOD_OFFSET = 0x3060
ENEMY_PERIODIC_EMISSION_TIMER_OFFSET = 0x3064

_ENEMY_COMPONENT_NAMES = frozenset(
    {
        "ordinary_enemy_template_and_pool",
        "ordinary_enemy_ecl_and_callback_roots",
    }
)
_PLAYER_BROAD_COMPONENT_NAME = "player_state_through_resource_transitions"
_SCHEDULER_COMPONENT_NAME = "scheduler_gate_globals"
FRSCREEN_NOTIFICATION_COUNTERS_OFFSET = 0x04
FRSCREEN_NOTIFICATION_COUNTERS_SIZE = 0x04

# Revalidated in ecl_load_file (0x00418330), stage_timeline_step
# (0x0042A8A0), and enemy_manager_update (0x0042C660).  The file header is
# relocated in place: its timeline offsets and data-end sentinel are absolute
# process pointers after load.
ECL_FILE_CONTEXT_ADDRESS = 0x004ECCB8
ECL_FILE_HEADER_SIZE = 0x48
ECL_FILE_MAGIC = 0x800
ECL_MAXIMUM_TIMELINE_COUNT = 15
TIMELINE_RUNTIME_SLOT_COUNT = 16
TIMELINE_RUNTIME_SLOT_SIZE = 0x10
TIMELINE_RUNTIME_INSTRUCTION_POINTER_OFFSET = 0x0C
TIMELINE_MARKERS_ADDRESS = 0x00F54E1C
TIMELINE_SPAWN_SUPPRESSED_ADDRESS = 0x00F54E2C
INDEXED_ENEMY_REGISTRY_ADDRESS = 0x00F54CC0
INDEXED_ENEMY_REGISTRY_COUNT = 8
FRSCREEN_STATE_ADDRESS = 0x0160F428
FRSCREEN_INNER_POINTER_OFFSET = 0x08
FRSCREEN_TIMELINE_SPAWN_GATE_OFFSET = 0x2C
FRSCREEN_INNER_MESSAGE_TIMER_OFFSET = 0x2181C
FRSCREEN_INNER_MESSAGE_OVERRIDE_OFFSET = 0x22D78
ECL_DIFFICULTY_MASK_ADDRESS = 0x0160F53C
STAGE_TIMELINE_FLAG_10_ADDRESS = 0x0164D0BB


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_digest(value: object) -> str:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return _sha256(payload)


def _read_exact(
    reader: Any,
    address: int,
    size: int,
    *,
    field: str,
) -> bytes:
    data = reader.read(address, size)
    if len(data) != size:
        raise ValueError(
            f"short {field} read at {address:#x}: "
            f"expected {size:#x}, received {len(data):#x}"
        )
    return data


def _enemy_causal_tail_digest(data: bytes) -> tuple[str, int]:
    if len(data) % ENEMY_STRIDE:
        raise ValueError("enemy native-root component is not record aligned")
    digest = hashlib.sha256()
    record_count = len(data) // ENEMY_STRIDE
    for record_index in range(record_count):
        base = record_index * ENEMY_STRIDE
        digest.update(data[base + ENEMY_ANM_PREFIX_SIZE : base + ENEMY_STRIDE])
    return digest.hexdigest(), record_count


def normalized_causal_component_records(
    components: Iterable[object],
) -> tuple[dict[str, object], ...]:
    """Normalize broad root components without hiding non-render state.

    Enemy records retain every byte from the revalidated main-ECL boundary
    onward.  The broad player component is replaced by explicit
    collision/control fields in :func:`capture_collision_control_projection`.
    Every other component remains byte-exact.
    """

    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for component in components:
        spec = getattr(component, "spec")
        name = str(getattr(spec, "name"))
        data = bytes(getattr(component, "data"))
        if name in seen:
            raise ValueError(f"duplicate native-root component {name!r}")
        seen.add(name)
        if name == _PLAYER_BROAD_COMPONENT_NAME:
            records.append(
                {
                    "name": name,
                    "mode": "replaced_by_explicit_collision_control_fields",
                    "source_size": len(data),
                }
            )
            continue
        if name in _ENEMY_COMPONENT_NAMES:
            digest, record_count = _enemy_causal_tail_digest(data)
            records.append(
                {
                    "name": name,
                    "mode": "exact_per_record_tail_after_render_anm_prefix",
                    "source_size": len(data),
                    "record_count": record_count,
                    "retained_offset": ENEMY_ANM_PREFIX_SIZE,
                    "retained_bytes_per_record": (ENEMY_STRIDE - ENEMY_ANM_PREFIX_SIZE),
                    "sha256": digest,
                }
            )
            continue
        if name == _SCHEDULER_COMPONENT_NAME:
            excluded_end = (
                FRSCREEN_NOTIFICATION_COUNTERS_OFFSET
                + FRSCREEN_NOTIFICATION_COUNTERS_SIZE
            )
            if len(data) < excluded_end:
                raise ValueError("scheduler native-root component omits FRScreen flags")
            normalized = (
                data[:FRSCREEN_NOTIFICATION_COUNTERS_OFFSET] + data[excluded_end:]
            )
            records.append(
                {
                    "name": name,
                    "mode": (
                        "exact_except_render_consumed_frscreen_"
                        "resource_notification_counters"
                    ),
                    "source_size": len(data),
                    "excluded_offset": FRSCREEN_NOTIFICATION_COUNTERS_OFFSET,
                    "excluded_size": FRSCREEN_NOTIFICATION_COUNTERS_SIZE,
                    "sha256": _sha256(normalized),
                }
            )
            continue
        records.append(
            {
                "name": name,
                "mode": "exact",
                "source_size": len(data),
                "sha256": _sha256(data),
            }
        )
    return tuple(sorted(records, key=lambda record: str(record["name"])))


def _route2_option_causal_tails(reader: Any) -> tuple[str, ...]:
    tails: list[str] = []
    for option_index in range(ROUTE2_OPTION_COUNT):
        address = (
            ADDR_PLAYER
            + ROUTE2_OPTION_BASE_OFFSET
            + option_index * ROUTE2_OPTION_STRIDE
            + ROUTE2_OPTION_CAUSAL_TAIL_OFFSET
        )
        size = ROUTE2_OPTION_STRIDE - ROUTE2_OPTION_CAUSAL_TAIL_OFFSET
        tails.append(reader.read(address, size).hex())
    return tuple(tails)


def _player_lethal_aabb(reader: Any) -> list[float] | None:
    blob = reader.read(
        ADDR_PLAYER + PLAYER_LETHAL_AABB_OFFSET,
        PLAYER_LETHAL_AABB_SIZE,
    )
    decoded = decode_player_lethal_aabb(blob)
    return list(decoded) if decoded is not None else None


def _nearest_bullet_summary(
    bullets: tuple[object, ...],
    *,
    player_x: float,
    player_y: float,
    limit: int = 12,
) -> list[dict[str, object]]:
    ranked: list[tuple[float, object]] = []
    for bullet in bullets:
        dx = abs(float(getattr(bullet, "x")) - player_x) - float(
            getattr(bullet, "half_width")
        )
        dy = abs(float(getattr(bullet, "y")) - player_y) - float(
            getattr(bullet, "half_height")
        )
        signed_box_separation = max(dx, dy)
        ranked.append((signed_box_separation, bullet))
    ranked.sort(key=lambda item: (item[0], int(getattr(item[1], "slot"))))
    return [
        {
            "slot": int(getattr(bullet, "slot")),
            "signed_box_separation": separation,
            "x": float(getattr(bullet, "x")),
            "y": float(getattr(bullet, "y")),
            "vx": float(getattr(bullet, "vx")),
            "vy": float(getattr(bullet, "vy")),
            "half_width": float(getattr(bullet, "half_width")),
            "half_height": float(getattr(bullet, "half_height")),
            "transform_flags": int(getattr(bullet, "transform_flags")),
        }
        for separation, bullet in ranked[:limit]
    ]


def _bullet_lifecycle_records(
    bullet_blob: bytes | bytearray | memoryview,
    bullets: Iterable[object],
) -> list[dict[str, object]]:
    """Retain lifecycle fields omitted by the legacy geometry trace.

    The positional ``serialize_bullet_trace`` format predates native
    ModelTrajectory work and intentionally remains stable.  The separate
    slot-keyed ledger prevents spawn states 2..5 from being silently merged
    with ordinary state 1 merely because geometry/velocity/transform fields
    agree.
    """

    view = memoryview(bullet_blob)
    expected_size = BULLET_POOL_SIZE * BULLET_STRIDE
    if len(view) != expected_size:
        raise ValueError(
            "bullet lifecycle capture requires the complete native pool: "
            f"expected {expected_size} bytes, got {len(view)}"
        )
    records: list[dict[str, object]] = []
    for bullet in bullets:
        slot = int(getattr(bullet, "slot"))
        if not 0 <= slot < BULLET_POOL_SIZE:
            raise ValueError(f"decoded bullet slot is outside native pool: {slot}")
        base = slot * BULLET_STRIDE
        state = struct.unpack_from(
            "<H",
            view,
            base + BULLET_STATE_OFFSET,
        )[0]
        records.append(
            {
                "slot": slot,
                "state": int(state),
                "timer_d80_fraction_bits": struct.unpack_from(
                    "<I",
                    view,
                    base
                    + BULLET_TIMER_D80_OFFSET
                    + TH08_TIMER_FRACTION_OFFSET,
                )[0],
                "timer_d80_elapsed": struct.unpack_from(
                    "<i",
                    view,
                    base
                    + BULLET_TIMER_D80_OFFSET
                    + TH08_TIMER_ELAPSED_OFFSET,
                )[0],
                "timer_d8c_fraction_bits": struct.unpack_from(
                    "<I",
                    view,
                    base
                    + BULLET_TIMER_D8C_OFFSET
                    + TH08_TIMER_FRACTION_OFFSET,
                )[0],
                "timer_d8c_elapsed": struct.unpack_from(
                    "<i",
                    view,
                    base
                    + BULLET_TIMER_D8C_OFFSET
                    + TH08_TIMER_ELAPSED_OFFSET,
                )[0],
            }
        )
    return records


def _enemy_main_ecl_inventory_record(
    enemy_blob: bytes,
) -> tuple[EnemyMainEclVmInventory, dict[str, object]]:
    """Decode one deterministic active-enemy VM inventory.

    ``decode_ms`` is intentionally excluded from collision/control identity:
    it is observer timing, not native state.
    """

    inventory = decode_enemy_main_ecl_vm_inventory(
        enemy_blob,
        pool_base=ENEMY_POOL_BASE,
        pool_size=ENEMY_POOL_SIZE,
        enemy_stride=ENEMY_STRIDE,
        enemy_flags_offset=ENEMY_FLAGS_OFFSET,
        enemy_active_flag=ENEMY_ACTIVE_FLAG,
    )
    record = inventory.record()
    record.pop("decode_ms", None)
    return inventory, record


def _runtime_instruction_record(
    cache: EclInstructionCache,
    reader: Any,
    instruction_pointer: int,
) -> dict[str, object]:
    instruction = cache.instruction(reader.read, instruction_pointer)
    return {
        "instruction_pointer": instruction_pointer,
        "time": instruction.time,
        "opcode": instruction.opcode,
        "size": instruction.size,
        "difficulty_mask": instruction.difficulty_mask,
        "parameter_mask": instruction.parameter_mask,
        "payload_hex": instruction.payload.hex(),
    }


def _stored_ecl_instruction_record(data: bytes) -> dict[str, object] | None:
    if len(data) != ENEMY_PERIODIC_EMISSION_DESCRIPTOR_SIZE:
        raise ValueError("stored ECL fire descriptor has the wrong size")
    if not any(data):
        return None
    time, opcode, size, unknown_byte, difficulty_mask, parameter_mask = (
        struct.unpack_from("<iHHBBH", data)
    )
    if size < 12 or size > len(data):
        raise ValueError(f"invalid stored ECL fire descriptor size {size}")
    return {
        "time": time,
        "opcode": opcode,
        "size": size,
        "unknown_byte": unknown_byte,
        "difficulty_mask": difficulty_mask,
        "parameter_mask": parameter_mask,
        "payload_hex": data[12:size].hex(),
        "retained_bytes_hex": data.hex(),
    }


def _enemy_periodic_emission_records(
    enemy_blob: bytes,
    inventory: EnemyMainEclVmInventory,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for observation in inventory.observations:
        base = observation.slot * ENEMY_STRIDE
        descriptor = bytes(
            enemy_blob[
                base + ENEMY_PERIODIC_EMISSION_DESCRIPTOR_OFFSET :
                base
                + ENEMY_PERIODIC_EMISSION_DESCRIPTOR_OFFSET
                + ENEMY_PERIODIC_EMISSION_DESCRIPTOR_SIZE
            ]
        )
        hitpoints = struct.unpack_from(
            "<i",
            enemy_blob,
            base + ENEMY_HITPOINTS_OFFSET,
        )[0]
        period = struct.unpack_from(
            "<i",
            enemy_blob,
            base + ENEMY_PERIODIC_EMISSION_PERIOD_OFFSET,
        )[0]
        timer_previous, timer_fraction_bits, timer_elapsed = struct.unpack_from(
            "<iIi",
            enemy_blob,
            base + ENEMY_PERIODIC_EMISSION_TIMER_OFFSET,
        )
        enabled = hitpoints > 0 and period > 0
        rows.append(
            {
                "slot": observation.slot,
                "enemy_pointer": observation.enemy_pointer,
                "hitpoints": hitpoints,
                "period": period,
                "timer_previous": timer_previous,
                "timer_fraction_bits": timer_fraction_bits,
                "timer_elapsed": timer_elapsed,
                "enabled": enabled,
                "stored_fire_descriptor": (
                    _stored_ecl_instruction_record(descriptor)
                    if enabled
                    else None
                ),
            }
        )
    return {
        "schema": "th08-active-enemy-periodic-emission-state-v1",
        "scope": (
            "fixed_post_vm_staged_descriptor_period_and_timer_"
            "before_one_native_timer_advance"
        ),
        "rows": rows,
    }


def _enemy_current_instruction_records(
    reader: Any,
    inventory: EnemyMainEclVmInventory,
) -> dict[str, object]:
    """Capture only each initialized main VM's current immutable instruction."""

    cache = EclInstructionCache()
    rows: list[dict[str, object]] = []
    for observation in inventory.observations:
        rows.append(
            {
                "slot": observation.slot,
                **_runtime_instruction_record(
                    cache,
                    reader,
                    observation.instruction_pointer,
                ),
            }
        )
    return {
        "schema": "th08-active-enemy-current-ecl-instruction-v1",
        "scope": "current_instruction_only_no_control_flow_closure",
        "rows": rows,
    }


def _installed_callback_record(
    cache: EclInstructionCache,
    reader: Any,
    *,
    function_pointer: int,
    argument_record_pointer: int,
) -> dict[str, object]:
    return {
        "function_pointer": function_pointer,
        "argument_record_pointer": argument_record_pointer,
        "argument_record_instruction": (
            _runtime_instruction_record(
                cache,
                reader,
                argument_record_pointer,
            )
            if function_pointer and argument_record_pointer
            else None
        ),
        "authority": (
            "root_identity_and_argument_record_only_callback_semantics_"
            "require_address_specific_lowering"
        ),
    }


def _enemy_main_ecl_callback_records(
    reader: Any,
    enemy_blob: bytes,
    inventory: EnemyMainEclVmInventory,
) -> dict[str, object]:
    cache = EclInstructionCache()
    rows: list[dict[str, object]] = []
    for observation in inventory.observations:
        base = (
            observation.slot * ENEMY_STRIDE
            + ENEMY_MAIN_ECL_VM_OFFSET
        )
        function_pointer, argument_record_pointer = struct.unpack_from(
            "<II",
            enemy_blob,
            base + 0x10,
        )
        rows.append(
            {
                "slot": observation.slot,
                "enemy_pointer": observation.enemy_pointer,
                "vm_kind": "main",
                "installed_callback": _installed_callback_record(
                    cache,
                    reader,
                    function_pointer=function_pointer,
                    argument_record_pointer=argument_record_pointer,
                ),
            }
        )
    return {
        "schema": "th08-active-enemy-main-ecl-installed-callback-v1",
        "execution_order": (
            "after_selected_main_interpreter_before_auxiliary_context_zero"
        ),
        "rows": rows,
    }


def _enemy_auxiliary_ecl_context_records(
    reader: Any,
    inventory: EnemyMainEclVmInventory,
) -> dict[str, object]:
    """Dereference only non-null active auxiliary contexts at the seam."""

    cache = EclInstructionCache()
    rows: list[dict[str, object]] = []
    for owner in inventory.auxiliary_contexts:
        for auxiliary_index, context_pointer in enumerate(
            owner.context_pointers
        ):
            if context_pointer == 0:
                continue
            context = reader.read(
                context_pointer,
                CONTEXT_ACTIVE_VM_OFFSET + ACTIVE_VM_BYTES,
            )
            if len(context) != CONTEXT_ACTIVE_VM_OFFSET + ACTIVE_VM_BYTES:
                raise ValueError("short auxiliary ECL context read")
            target_subroutine = struct.unpack_from(
                "<I",
                context,
                CONTEXT_TARGET_OFFSET,
            )[0]
            call_depth = struct.unpack_from(
                "<H",
                context,
                CONTEXT_CALL_DEPTH_OFFSET,
            )[0]
            if call_depth > MAXIMUM_RESTORABLE_FRAMES:
                raise ValueError(
                    "auxiliary ECL call depth exceeds retained native layout"
                )
            active_vm = bytes(
                context[
                    CONTEXT_ACTIVE_VM_OFFSET :
                    CONTEXT_ACTIVE_VM_OFFSET + ACTIVE_VM_BYTES
                ]
            )
            state = AuxiliaryEclVmState.from_active_vm(active_vm)
            callback_function, callback_argument_record = struct.unpack_from(
                "<II",
                active_vm,
                0x10,
            )
            rows.append(
                {
                    "slot": owner.slot,
                    "auxiliary_index": auxiliary_index,
                    "enemy_pointer": owner.enemy_pointer,
                    "context_pointer": context_pointer,
                    "target_subroutine": target_subroutine,
                    "call_depth": call_depth,
                    "state": state.record(),
                    "installed_callback": _installed_callback_record(
                        cache,
                        reader,
                        function_pointer=callback_function,
                        argument_record_pointer=callback_argument_record,
                    ),
                    "current_instruction": _runtime_instruction_record(
                        cache,
                        reader,
                        state.instruction_pointer,
                    ),
                }
            )
    return {
        "schema": "th08-active-enemy-auxiliary-ecl-context-v1",
        "scope": (
            "active_vm_and_current_instruction_only_"
            "no_saved_frame_or_control_flow_closure"
        ),
        "rows": rows,
    }


def _runtime_timeline_instruction_record(
    reader: Any,
    *,
    instruction_pointer: int,
    ecl_file_base: int,
    ecl_data_end_pointer: int,
) -> dict[str, object]:
    if not ecl_file_base <= instruction_pointer < ecl_data_end_pointer:
        raise ValueError(
            "timeline instruction pointer lies outside the loaded ECL image"
        )
    header = _read_exact(
        reader,
        instruction_pointer,
        8,
        field="timeline instruction header",
    )
    time, opcode, size, difficulty_mask = struct.unpack("<iHBB", header)
    record: dict[str, object] = {
        "instruction_pointer": instruction_pointer,
        "static_offset": instruction_pointer - ecl_file_base,
        "time": time,
        "opcode": opcode,
        "size": size,
        "difficulty_mask": difficulty_mask,
    }
    if time < 0:
        record["payload_hex"] = ""
        record["terminal"] = True
        return record
    if size < 8 or size % 4 or size > 0x400:
        raise ValueError(f"invalid live timeline instruction size {size}")
    if instruction_pointer + size > ecl_data_end_pointer:
        raise ValueError("timeline instruction crosses the loaded ECL image")
    payload = _read_exact(
        reader,
        instruction_pointer + 8,
        size - 8,
        field="timeline instruction payload",
    )
    record["payload_hex"] = payload.hex()
    record["terminal"] = False
    return record


def _timeline_external_state_record(reader: Any) -> dict[str, object]:
    markers = struct.unpack(
        "<4i",
        _read_exact(
            reader,
            TIMELINE_MARKERS_ADDRESS,
            16,
            field="timeline markers",
        ),
    )
    spawn_suppressed_raw = struct.unpack(
        "<I",
        _read_exact(
            reader,
            TIMELINE_SPAWN_SUPPRESSED_ADDRESS,
            4,
            field="timeline spawn suppression",
        ),
    )[0]
    frscreen_spawn_gate_raw = _read_exact(
        reader,
        FRSCREEN_STATE_ADDRESS + FRSCREEN_TIMELINE_SPAWN_GATE_OFFSET,
        1,
        field="FRScreen timeline spawn gate",
    )[0]
    frscreen_inner_pointer = struct.unpack(
        "<I",
        _read_exact(
            reader,
            FRSCREEN_STATE_ADDRESS + FRSCREEN_INNER_POINTER_OFFSET,
            4,
            field="FRScreen inner pointer",
        ),
    )[0]
    message_timer: int | None = None
    message_override_raw: int | None = None
    if frscreen_inner_pointer:
        message_timer = struct.unpack(
            "<i",
            _read_exact(
                reader,
                frscreen_inner_pointer + FRSCREEN_INNER_MESSAGE_TIMER_OFFSET,
                4,
                field="FRScreen message timer",
            ),
        )[0]
        message_override_raw = struct.unpack(
            "<I",
            _read_exact(
                reader,
                frscreen_inner_pointer + FRSCREEN_INNER_MESSAGE_OVERRIDE_OFFSET,
                4,
                field="FRScreen message override",
            ),
        )[0]
    conditional_gate_blocked = bool(
        frscreen_inner_pointer
        and message_override_raw == 0
        and message_timer is not None
        and message_timer >= 0
    )

    registry_blob = _read_exact(
        reader,
        INDEXED_ENEMY_REGISTRY_ADDRESS,
        INDEXED_ENEMY_REGISTRY_COUNT * 4,
        field="indexed enemy registry",
    )
    indexed_enemies: list[dict[str, object] | None] = []
    for pointer in struct.unpack(
        f"<{INDEXED_ENEMY_REGISTRY_COUNT}I",
        registry_blob,
    ):
        if pointer == 0:
            indexed_enemies.append(None)
            continue
        flags = struct.unpack(
            "<I",
            _read_exact(
                reader,
                pointer + ENEMY_FLAGS_OFFSET,
                4,
                field="indexed enemy flags",
            ),
        )[0]
        indexed_enemies.append(
            {
                "enemy_pointer": pointer,
                "flags": flags,
                "active": bool(flags & ENEMY_ACTIVE_FLAG),
            }
        )

    return {
        "schema": "th08-stage-timeline-external-state-v1",
        "markers": list(markers),
        "spawn_suppressed": bool(spawn_suppressed_raw),
        "spawn_suppressed_raw": spawn_suppressed_raw,
        "stage_transition_busy": bool(frscreen_spawn_gate_raw),
        "frscreen_spawn_gate_raw": frscreen_spawn_gate_raw,
        "conditional_gate_blocked": conditional_gate_blocked,
        "frscreen_inner_pointer": frscreen_inner_pointer,
        "message_timer": message_timer,
        "message_override_raw": message_override_raw,
        "indexed_enemies": indexed_enemies,
    }


def _timeline_runtime_inventory_record(reader: Any) -> dict[str, object]:
    """Capture the causal root needed by the existing stage-timeline model."""

    context = _read_exact(
        reader,
        ECL_FILE_CONTEXT_ADDRESS,
        8,
        field="runtime ECL file context",
    )
    ecl_file_base, subroutine_pointer_table = struct.unpack("<II", context)
    if ecl_file_base == 0:
        raise ValueError("runtime ECL file base is null")
    header = _read_exact(
        reader,
        ecl_file_base,
        ECL_FILE_HEADER_SIZE,
        field="relocated runtime ECL header",
    )
    magic, subroutine_count, timeline_count = struct.unpack_from(
        "<IHH",
        header,
    )
    if magic != ECL_FILE_MAGIC:
        raise ValueError(f"unexpected runtime ECL magic {magic:#x}")
    if not 0 <= timeline_count <= ECL_MAXIMUM_TIMELINE_COUNT:
        raise ValueError(
            f"runtime ECL timeline count {timeline_count} has no sentinel slot"
        )
    if subroutine_pointer_table != ecl_file_base + ECL_FILE_HEADER_SIZE:
        raise ValueError("runtime ECL subroutine table pointer is inconsistent")
    relocated_timeline_pointers = struct.unpack_from("<16I", header, 8)
    ecl_data_end_pointer = relocated_timeline_pointers[timeline_count]
    if ecl_data_end_pointer <= ecl_file_base:
        raise ValueError("runtime ECL data-end sentinel is invalid")

    runtime_table = _read_exact(
        reader,
        TH08_TIMELINE_RUNTIME_BASE,
        TIMELINE_RUNTIME_SLOT_COUNT * TIMELINE_RUNTIME_SLOT_SIZE,
        field="timeline runtime table",
    )
    rows: list[dict[str, object]] = []
    for timeline_index in range(timeline_count):
        base = timeline_index * TIMELINE_RUNTIME_SLOT_SIZE
        previous_elapsed, fraction_bits, elapsed, instruction_pointer = (
            struct.unpack_from("<iIiI", runtime_table, base)
        )
        initialized = instruction_pointer != 0
        effective_instruction_pointer = (
            instruction_pointer
            if initialized
            else relocated_timeline_pointers[timeline_index]
        )
        rows.append(
            {
                "timeline_index": timeline_index,
                "previous_elapsed": previous_elapsed,
                "fraction_bits": fraction_bits,
                "elapsed": elapsed,
                "initialized": initialized,
                "instruction_pointer": instruction_pointer,
                "effective_instruction_pointer": effective_instruction_pointer,
                "timeline_start_pointer": relocated_timeline_pointers[
                    timeline_index
                ],
                "timeline_start_static_offset": (
                    relocated_timeline_pointers[timeline_index] - ecl_file_base
                ),
                "current_instruction": _runtime_timeline_instruction_record(
                    reader,
                    instruction_pointer=effective_instruction_pointer,
                    ecl_file_base=ecl_file_base,
                    ecl_data_end_pointer=ecl_data_end_pointer,
                ),
            }
        )

    difficulty_mask = _read_exact(
        reader,
        ECL_DIFFICULTY_MASK_ADDRESS,
        1,
        field="ECL difficulty mask",
    )[0]
    stage_flag_10 = _read_exact(
        reader,
        STAGE_TIMELINE_FLAG_10_ADDRESS,
        1,
        field="stage timeline flag 0x10",
    )[0]
    return {
        "schema": "th08-stage-timeline-runtime-inventory-v1",
        "scope": (
            "causal_root_clocks_current_instructions_and_external_gates_"
            "no_enemy_spawn_or_main_vm_execution"
        ),
        "ecl_file": {
            "context_address": ECL_FILE_CONTEXT_ADDRESS,
            "file_base": ecl_file_base,
            "subroutine_pointer_table": subroutine_pointer_table,
            "magic": magic,
            "subroutine_count": subroutine_count,
            "timeline_count": timeline_count,
            "data_end_pointer": ecl_data_end_pointer,
            "static_data_end_offset": ecl_data_end_pointer - ecl_file_base,
            "timeline_start_pointers": list(
                relocated_timeline_pointers[:timeline_count]
            ),
        },
        "difficulty_mask": difficulty_mask,
        "stage_flag_10": bool(stage_flag_10),
        "stage_flag_10_raw": stage_flag_10,
        "rows": rows,
        "external": _timeline_external_state_record(reader),
    }


@dataclass(frozen=True)
class CollisionControlProjection:
    payload: dict[str, object]
    sha256: str
    summary: dict[str, object]

    def record(
        self,
        *,
        include_model_payload: bool = False,
    ) -> dict[str, object]:
        record: dict[str, object] = {
            "schema": COLLISION_CONTROL_PROJECTION_SCHEMA,
            "sha256": self.sha256,
            "summary": self.summary,
            "authority": (
                "collision_control_equivalence_only_not_full_gameplay_identity"
            ),
        }
        if include_model_payload:
            record["model_payload"] = self.payload
            record["model_payload_authority"] = (
                "decoded_native_state_for_offline_model_differential_only"
            )
        return record


def capture_collision_control_projection(
    reader: Any,
    *,
    native_root_projection: object,
    compact_state: dict[str, object],
) -> CollisionControlProjection:
    """Capture exact decoded hit-relevant state at one calculation seam."""

    bullet_blob = reader.read(
        BULLET_POOL_BASE,
        BULLET_POOL_SIZE * BULLET_STRIDE,
    )
    laser_blob = reader.read(
        LASER_POOL_BASE,
        LASER_POOL_SIZE * LASER_STRIDE,
    )
    enemy_blob = reader.read(
        ENEMY_POOL_BASE,
        ENEMY_POOL_SIZE * ENEMY_STRIDE,
    )
    bullets = decode_bullets(bullet_blob, retain_transform_runtime=True)
    lasers = decode_lasers(laser_blob)
    enemy_bodies = decode_enemy_bodies(
        enemy_blob,
        pool_size=ENEMY_POOL_SIZE,
        include_contact_disabled=True,
    )
    enemy_ecl_inventory, enemy_ecl_inventory_record = (
        _enemy_main_ecl_inventory_record(enemy_blob)
    )
    player_x = float(compact_state["player_x"])
    player_y = float(compact_state["player_y"])
    normalized_components = normalized_causal_component_records(
        getattr(native_root_projection, "components")
    )
    payload: dict[str, object] = {
        "schema": COLLISION_CONTROL_PROJECTION_SCHEMA,
        "compact_state": compact_state,
        "player_lethal_aabb": _player_lethal_aabb(reader),
        "route2_option_causal_tails": list(_route2_option_causal_tails(reader)),
        "bullets": [serialize_bullet_trace(bullet) for bullet in bullets],
        "bullet_lifecycle": _bullet_lifecycle_records(bullet_blob, bullets),
        "bullet_lifecycle_semantics": {
            "state_motion_divisors": {
                str(state): divisor
                for state, divisor in BULLET_STATE_MOTION_DIVISORS.items()
            },
            "transition_authority": (
                "state-local motion observed; same-update ANM completion "
                "remains UNKNOWN without the corresponding ANM VM"
            ),
        },
        "lasers": [asdict(laser) for laser in lasers],
        "enemy_bodies": [asdict(body) for body in enemy_bodies],
        "enemy_main_ecl_vm_inventory": enemy_ecl_inventory_record,
        "enemy_periodic_emission_state": (
            _enemy_periodic_emission_records(
                enemy_blob,
                enemy_ecl_inventory,
            )
        ),
        "enemy_main_ecl_installed_callbacks": (
            _enemy_main_ecl_callback_records(
                reader,
                enemy_blob,
                enemy_ecl_inventory,
            )
        ),
        "enemy_current_ecl_instructions": (
            _enemy_current_instruction_records(reader, enemy_ecl_inventory)
        ),
        "enemy_auxiliary_ecl_contexts": (
            _enemy_auxiliary_ecl_context_records(
                reader,
                enemy_ecl_inventory,
            )
        ),
        "stage_timeline_runtime": _timeline_runtime_inventory_record(reader),
        "normalized_native_components": list(normalized_components),
    }
    summary = {
        "manager_frame": int(compact_state["manager_frame"]),
        "bullet_count": len(bullets),
        "laser_count": len(lasers),
        "enemy_body_count": len(enemy_bodies),
        "active_enemy_main_ecl_vm_count": len(
            enemy_ecl_inventory.observations
        ),
        "active_enemy_auxiliary_ecl_context_count": len(
            payload["enemy_auxiliary_ecl_contexts"]["rows"]
        ),
        "active_enemy_periodic_emitter_count": sum(
            bool(row["enabled"])
            for row in payload["enemy_periodic_emission_state"]["rows"]
        ),
        "active_enemy_installed_callback_count": (
            sum(
                bool(row["installed_callback"]["function_pointer"])
                for row in payload[
                    "enemy_main_ecl_installed_callbacks"
                ]["rows"]
            )
            + sum(
                bool(row["installed_callback"]["function_pointer"])
                for row in payload[
                    "enemy_auxiliary_ecl_contexts"
                ]["rows"]
            )
        ),
        "stage_timeline_count": len(
            payload["stage_timeline_runtime"]["rows"]
        ),
        "player_lethal_aabb": payload["player_lethal_aabb"],
        "nearest_bullets": _nearest_bullet_summary(
            bullets,
            player_x=player_x,
            player_y=player_y,
        ),
        "normalized_native_components": list(normalized_components),
        "presentation_exclusions": {
            "enemy_per_record_prefix": ENEMY_ANM_PREFIX_SIZE,
            "frscreen_resource_notification_counters": {
                "component": _SCHEDULER_COMPONENT_NAME,
                "offset": FRSCREEN_NOTIFICATION_COUNTERS_OFFSET,
                "size": FRSCREEN_NOTIFICATION_COUNTERS_SIZE,
                "consumer": "FRScreen render 0x0043625D",
            },
            "broad_player_component": (
                "replaced by compact player/resource state, lethal AABB, "
                "route-2 option causal tails, hostile hazards, enemy state"
            ),
        },
    }
    return CollisionControlProjection(
        payload=payload,
        sha256=_canonical_json_digest(payload),
        summary=summary,
    )


def collision_control_projection_changes(
    left: CollisionControlProjection,
    right: CollisionControlProjection,
) -> tuple[dict[str, object], ...]:
    if left.sha256 == right.sha256:
        return ()
    changes: list[dict[str, object]] = []
    keys = sorted(set(left.payload) | set(right.payload))
    for key in keys:
        left_value = left.payload.get(key)
        right_value = right.payload.get(key)
        if left_value == right_value:
            continue
        record: dict[str, object] = {"field": key}
        if isinstance(left_value, list) and isinstance(right_value, list):
            first_difference = None
            for index, (left_item, right_item) in enumerate(
                zip(left_value, right_value)
            ):
                if left_item != right_item:
                    first_difference = index
                    break
            if first_difference is None and len(left_value) != len(right_value):
                first_difference = min(len(left_value), len(right_value))
            record.update(
                {
                    "left_count": len(left_value),
                    "right_count": len(right_value),
                    "first_difference": first_difference,
                }
            )
        else:
            record.update(
                {
                    "left": left_value,
                    "right": right_value,
                }
            )
        changes.append(record)
    return tuple(changes)


__all__ = [
    "COLLISION_CONTROL_PROJECTION_SCHEMA",
    "CollisionControlProjection",
    "ENEMY_ANM_PREFIX_SIZE",
    "FRSCREEN_NOTIFICATION_COUNTERS_OFFSET",
    "FRSCREEN_NOTIFICATION_COUNTERS_SIZE",
    "ROUTE2_OPTION_BASE_OFFSET",
    "ROUTE2_OPTION_CAUSAL_TAIL_OFFSET",
    "ROUTE2_OPTION_COUNT",
    "ROUTE2_OPTION_STRIDE",
    "capture_collision_control_projection",
    "collision_control_projection_changes",
    "normalized_causal_component_records",
]
