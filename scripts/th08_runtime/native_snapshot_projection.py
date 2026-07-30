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
from th08_live.enemy_sensor import (
    ENEMY_POOL_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_STRIDE,
    PLAYER_LETHAL_AABB_OFFSET,
    PLAYER_LETHAL_AABB_SIZE,
    decode_enemy_bodies,
    decode_player_lethal_aabb,
)
from th08_live.hazard_decode import decode_lasers
from th08_live.models import serialize_bullet_trace
from th08_live.sensor import (
    BULLET_POOL_BASE,
    BULLET_POOL_SIZE,
    BULLET_STRIDE,
    LASER_POOL_BASE,
    LASER_POOL_SIZE,
    LASER_STRIDE,
)
from th08_runtime.game_state import ADDR_PLAYER


COLLISION_CONTROL_PROJECTION_SCHEMA = (
    "th08-native-snapshot-collision-control-projection-v2"
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
        "normalized_native_components": list(normalized_components),
    }
    summary = {
        "manager_frame": int(compact_state["manager_frame"]),
        "bullet_count": len(bullets),
        "laser_count": len(lasers),
        "enemy_body_count": len(enemy_bodies),
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
