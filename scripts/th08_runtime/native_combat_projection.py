"""Exact-root TH08 player-shot and enemy-damage combat projection.

This module decodes combat state already retained by the rolling native-root
capture.  It does not install a probe or grant predictive/live authority.
The pass projection is deliberately narrow: only ordinary shot slots whose
native type gate and hit callback are fully supported contribute a numeric
subtotal.  Callback-dependent and type-4/5 overlaps remain explicit unknowns.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import dataclass, replace
from typing import Any, Iterable

from th08_enemy_damage_model import (
    EnemyPlayerShotDamageContext,
    evaluate_enemy_player_shot_damage_gate,
)
from th08_live.enemy_sensor import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_FLAGS_OFFSET,
    ENEMY_POOL_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_STRIDE,
)
from th08_runtime.game_state import (
    ADDR_PLAYER,
    ADDR_SPELL_CARD_STATE,
    PLAYER_BOMB_ACTIVE_OFFSET,
    PLAYER_DAMAGE_TIMER_OFFSET,
    PLAYER_SHOT_POOL_OFFSET,
    PLAYER_SHOT_POOL_SIZE,
    PLAYER_SHOT_SLOT_ANGLE_OFFSET,
    PLAYER_SHOT_SLOT_ANM_INDEX_OFFSET,
    PLAYER_SHOT_SLOT_DAMAGE_OFFSET,
    PLAYER_SHOT_SLOT_FOCUS_OFFSET,
    PLAYER_SHOT_SLOT_HITBOX_OFFSET,
    PLAYER_SHOT_SLOT_HIT_CALLBACK_OFFSET,
    PLAYER_SHOT_SLOT_POSITION_OFFSET,
    PLAYER_SHOT_SLOT_SOURCE_RECORD_OFFSET,
    PLAYER_SHOT_SLOT_SPEED_OFFSET,
    PLAYER_SHOT_SLOT_STATE_OFFSET,
    PLAYER_SHOT_SLOT_STRIDE,
    PLAYER_SHOT_SLOT_TIMER_OFFSET,
    PLAYER_SHOT_SLOT_TYPE_OFFSET,
    PLAYER_SHOT_SLOT_UPDATE_CALLBACK_OFFSET,
    PLAYER_SHOT_SLOT_VELOCITY_OFFSET,
    PLAYER_SHOT_TIMER_OFFSET,
    SPELL_STATE_CAPTURE_SIZE,
)
from th08_runtime.sensing import decode_spell_state


NATIVE_COMBAT_PROJECTION_SCHEMA = "th08-native-combat-root-projection-v1"
PLAYER_SHOT_COMBAT_STATE_SCHEMA = "th08-player-shot-combat-state-v1"
ENEMY_DAMAGE_TARGET_STATE_SCHEMA = "th08-enemy-damage-target-state-v1"
SUPPORTED_SHOT_PASS_SCHEMA = "th08-supported-ordinary-shot-pass-v1"

TH08_TIMER_SIZE = 12
PLAYER_SHOT_POOL_BYTES = PLAYER_SHOT_POOL_SIZE * PLAYER_SHOT_SLOT_STRIDE
PLAYER_SHOT_FRAME_DAMAGE_CAP = 50
PIERCING_SHOT_TYPES = frozenset((4, 5, 6))

ENEMY_DAMAGE_HITBOX_OFFSET = 0x2D70
ENEMY_ALTERNATE_HITBOX_OFFSET = 0x2D7C
ENEMY_POSITION_OFFSET = 0x2D88
ENEMY_HITPOINTS_OFFSET = 0x2DFC
ENEMY_MAX_HITPOINTS_OFFSET = 0x2E00
ENEMY_MAIN_VM_OFFSET = 0x7F8
ENEMY_MAIN_VM_TIMER_CURRENT_OFFSET = ENEMY_MAIN_VM_OFFSET + 0x0C
ENEMY_FLAGS2_OFFSET = 0x3328
ENEMY_FRAME_DAMAGE_OFFSET = 0x3354
ENEMY_CAUSAL_TAIL_OFFSET = 0x7F8

_ENEMY_COMPONENT_NAME = "ordinary_enemy_template_and_pool"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_digest(value: object) -> str:
    return _sha256(
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
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
class Th08TimerIdentity:
    previous: int
    fraction_bits: int
    current: int

    @classmethod
    def decode(cls, data: bytes) -> Th08TimerIdentity:
        if len(data) != TH08_TIMER_SIZE:
            raise ValueError("TH08 timer identity requires 12 exact bytes")
        return cls(*struct.unpack("<iIi", data))

    @property
    def integer_changed(self) -> bool:
        return self.previous != self.current

    def record(self) -> dict[str, object]:
        return {
            "previous": self.previous,
            "fraction_bits": self.fraction_bits,
            "current": self.current,
            "integer_changed": self.integer_changed,
        }


@dataclass(frozen=True)
class PlayerShotCombatSlot:
    slot: int
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    hitbox_width: float
    hitbox_height: float
    speed: float
    angle: float
    timer: Th08TimerIdentity
    damage: int
    state: int
    shot_type: int
    focus_logic_at_birth: int
    anm_index: int
    update_callback_pointer: int
    hit_callback_pointer: int
    source_record_pointer: int
    raw_sha256: str

    def __post_init__(self) -> None:
        if not 0 <= self.slot < PLAYER_SHOT_POOL_SIZE:
            raise ValueError("player-shot slot index is outside the native pool")
        if self.state == 0:
            raise ValueError("combat slot cannot represent an inactive shot")
        if not all(
            math.isfinite(value)
            for value in (
                self.x,
                self.y,
                self.velocity_x,
                self.velocity_y,
                self.hitbox_width,
                self.hitbox_height,
                self.speed,
                self.angle,
            )
        ):
            raise ValueError("active player-shot geometry is not finite")
        if self.hitbox_width < 0.0 or self.hitbox_height < 0.0:
            raise ValueError("active player-shot hitbox is negative")
        if self.damage < 0:
            raise ValueError("active player-shot damage is negative")
        if not 0 <= self.focus_logic_at_birth <= 0xFF:
            raise ValueError("player-shot Focus byte is invalid")
        for pointer in (
            self.update_callback_pointer,
            self.hit_callback_pointer,
            self.source_record_pointer,
        ):
            if not 0 <= pointer <= 0xFFFFFFFF:
                raise ValueError("player-shot pointer is outside uint32")
        if len(self.raw_sha256) != 64:
            raise ValueError("player-shot raw identity is not SHA-256")

    @property
    def damage_loop_eligible(self) -> bool:
        return self.state != 0 and (self.state == 1 or self.shot_type == 3)

    def record(self) -> dict[str, object]:
        return {
            "slot": self.slot,
            "position": {"x": self.x, "y": self.y},
            "velocity": {"x": self.velocity_x, "y": self.velocity_y},
            "hitbox": {
                "width": self.hitbox_width,
                "height": self.hitbox_height,
            },
            "speed": self.speed,
            "angle": self.angle,
            "timer": self.timer.record(),
            "damage": self.damage,
            "state": self.state,
            "type": self.shot_type,
            "focus_logic_at_birth": self.focus_logic_at_birth,
            "anm_index": self.anm_index,
            "update_callback_pointer": self.update_callback_pointer,
            "hit_callback_pointer": self.hit_callback_pointer,
            "source_record_pointer": self.source_record_pointer,
            "damage_loop_eligible": self.damage_loop_eligible,
            "raw_sha256": self.raw_sha256,
        }


def decode_player_shot_pool(data: bytes) -> tuple[PlayerShotCombatSlot, ...]:
    """Decode all active native player-shot slots from one exact pool image."""

    if len(data) != PLAYER_SHOT_POOL_BYTES:
        raise ValueError(
            "player-shot combat pool requires "
            f"{PLAYER_SHOT_POOL_BYTES:#x} exact bytes"
        )
    slots: list[PlayerShotCombatSlot] = []
    for slot in range(PLAYER_SHOT_POOL_SIZE):
        base = slot * PLAYER_SHOT_SLOT_STRIDE
        state = struct.unpack_from(
            "<h",
            data,
            base + PLAYER_SHOT_SLOT_STATE_OFFSET,
        )[0]
        if state == 0:
            continue
        x, y = struct.unpack_from(
            "<ff",
            data,
            base + PLAYER_SHOT_SLOT_POSITION_OFFSET,
        )
        hitbox_width, hitbox_height = struct.unpack_from(
            "<ff",
            data,
            base + PLAYER_SHOT_SLOT_HITBOX_OFFSET,
        )
        velocity_x, velocity_y = struct.unpack_from(
            "<ff",
            data,
            base + PLAYER_SHOT_SLOT_VELOCITY_OFFSET,
        )
        speed = struct.unpack_from(
            "<f",
            data,
            base + PLAYER_SHOT_SLOT_SPEED_OFFSET,
        )[0]
        angle = struct.unpack_from(
            "<f",
            data,
            base + PLAYER_SHOT_SLOT_ANGLE_OFFSET,
        )[0]
        slots.append(
            PlayerShotCombatSlot(
                slot=slot,
                x=x,
                y=y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                hitbox_width=hitbox_width,
                hitbox_height=hitbox_height,
                speed=speed,
                angle=angle,
                timer=Th08TimerIdentity.decode(
                    data[
                        base + PLAYER_SHOT_SLOT_TIMER_OFFSET :
                        base + PLAYER_SHOT_SLOT_TIMER_OFFSET + TH08_TIMER_SIZE
                    ]
                ),
                damage=struct.unpack_from(
                    "<h",
                    data,
                    base + PLAYER_SHOT_SLOT_DAMAGE_OFFSET,
                )[0],
                state=state,
                shot_type=struct.unpack_from(
                    "<h",
                    data,
                    base + PLAYER_SHOT_SLOT_TYPE_OFFSET,
                )[0],
                focus_logic_at_birth=data[
                    base + PLAYER_SHOT_SLOT_FOCUS_OFFSET
                ],
                anm_index=struct.unpack_from(
                    "<h",
                    data,
                    base + PLAYER_SHOT_SLOT_ANM_INDEX_OFFSET,
                )[0],
                update_callback_pointer=struct.unpack_from(
                    "<I",
                    data,
                    base + PLAYER_SHOT_SLOT_UPDATE_CALLBACK_OFFSET,
                )[0],
                hit_callback_pointer=struct.unpack_from(
                    "<I",
                    data,
                    base + PLAYER_SHOT_SLOT_HIT_CALLBACK_OFFSET,
                )[0],
                source_record_pointer=struct.unpack_from(
                    "<I",
                    data,
                    base + PLAYER_SHOT_SLOT_SOURCE_RECORD_OFFSET,
                )[0],
                raw_sha256=_sha256(data[base : base + PLAYER_SHOT_SLOT_STRIDE]),
            )
        )
    return tuple(slots)


@dataclass(frozen=True)
class PlayerShotCombatState:
    emission_timer: Th08TimerIdentity
    damage_timer: Th08TimerIdentity
    pool_sha256: str
    slots: tuple[PlayerShotCombatSlot, ...]

    @property
    def occupied_slot_indices(self) -> tuple[int, ...]:
        return tuple(slot.slot for slot in self.slots)

    @property
    def damage_eligible_slot_indices(self) -> tuple[int, ...]:
        return tuple(
            slot.slot for slot in self.slots if slot.damage_loop_eligible
        )

    def record(self) -> dict[str, object]:
        return {
            "schema": PLAYER_SHOT_COMBAT_STATE_SCHEMA,
            "emission_timer": self.emission_timer.record(),
            "damage_timer": self.damage_timer.record(),
            "pool": {
                "slot_count": PLAYER_SHOT_POOL_SIZE,
                "occupied_count": len(self.slots),
                "free_count": PLAYER_SHOT_POOL_SIZE - len(self.slots),
                "occupied_slot_indices": list(self.occupied_slot_indices),
                "damage_eligible_slot_indices": list(
                    self.damage_eligible_slot_indices
                ),
                "sha256": self.pool_sha256,
                "active_slots": [slot.record() for slot in self.slots],
            },
        }


def capture_player_shot_combat_state(reader: Any) -> PlayerShotCombatState:
    """Read both player timers and the complete 128-slot shot pool."""

    pool = _read_exact(
        reader,
        ADDR_PLAYER + PLAYER_SHOT_POOL_OFFSET,
        PLAYER_SHOT_POOL_BYTES,
        field="player-shot combat pool",
    )
    emission_timer = Th08TimerIdentity.decode(
        _read_exact(
            reader,
            ADDR_PLAYER + PLAYER_SHOT_TIMER_OFFSET,
            TH08_TIMER_SIZE,
            field="player-shot emission timer",
        )
    )
    damage_timer = Th08TimerIdentity.decode(
        _read_exact(
            reader,
            ADDR_PLAYER + PLAYER_DAMAGE_TIMER_OFFSET,
            TH08_TIMER_SIZE,
            field="player-shot damage timer",
        )
    )
    return PlayerShotCombatState(
        emission_timer=emission_timer,
        damage_timer=damage_timer,
        pool_sha256=_sha256(pool),
        slots=decode_player_shot_pool(pool),
    )


@dataclass(frozen=True)
class EnemyDamageTarget:
    slot: int
    enemy_pointer: int
    hitpoints: int
    maximum_hitpoints: int
    frame_damage: int
    flags: int
    flags2: int
    x: float
    y: float
    primary_width: float
    primary_height: float
    alternate_width: float
    alternate_height: float
    main_vm_pc: int
    main_vm_timer_current: int
    causal_tail_sha256: str

    def __post_init__(self) -> None:
        if not 0 <= self.slot < ENEMY_POOL_SIZE:
            raise ValueError("enemy damage target slot is outside the pool")
        if self.enemy_pointer != ENEMY_POOL_BASE + self.slot * ENEMY_STRIDE:
            raise ValueError("enemy damage target pointer/slot disagree")
        if not self.flags & ENEMY_ACTIVE_FLAG:
            raise ValueError("enemy damage target is inactive")
        if not all(
            math.isfinite(value)
            for value in (
                self.x,
                self.y,
                self.primary_width,
                self.primary_height,
                self.alternate_width,
                self.alternate_height,
            )
        ):
            raise ValueError("enemy damage target geometry is not finite")
        if self.primary_width < 0.0 or self.primary_height < 0.0:
            raise ValueError("enemy primary damage hitbox is negative")
        if self.alternate_width > 0.0 and self.alternate_height < 0.0:
            raise ValueError("enabled enemy alternate damage hitbox is negative")
        if len(self.causal_tail_sha256) != 64:
            raise ValueError("enemy causal-tail identity is not SHA-256")

    @property
    def alternate_enabled(self) -> bool:
        # 0x42D0EE..0x42D0FF enters the second native damage pass only for
        # ordered alternate width > +0.0; negative zero and NaN do not enter.
        return self.alternate_width > 0.0

    def record(self) -> dict[str, object]:
        return {
            "schema": ENEMY_DAMAGE_TARGET_STATE_SCHEMA,
            "slot": self.slot,
            "enemy_pointer": self.enemy_pointer,
            "hitpoints": self.hitpoints,
            "maximum_hitpoints": self.maximum_hitpoints,
            "frame_damage": self.frame_damage,
            "flags": self.flags,
            "flags2": self.flags2,
            "position": {"x": self.x, "y": self.y},
            "primary_hitbox": {
                "width": self.primary_width,
                "height": self.primary_height,
            },
            "alternate_hitbox": {
                "width": self.alternate_width,
                "height": self.alternate_height,
                "enabled": self.alternate_enabled,
            },
            "main_vm_pc": self.main_vm_pc,
            "main_vm_timer_current": self.main_vm_timer_current,
            "causal_tail_sha256": self.causal_tail_sha256,
        }


def _native_component(
    native_root_projection: object,
    name: str,
) -> object:
    matches = tuple(
        component
        for component in getattr(native_root_projection, "components")
        if getattr(getattr(component, "spec"), "name") == name
    )
    if len(matches) != 1:
        raise ValueError(f"native combat projection requires one {name!r}")
    return matches[0]


def decode_enemy_damage_targets(
    native_root_projection: object,
) -> tuple[EnemyDamageTarget, ...]:
    """Decode active targets from the already-retained template+pool bytes."""

    component = _native_component(
        native_root_projection,
        _ENEMY_COMPONENT_NAME,
    )
    spec = getattr(component, "spec")
    data = bytes(getattr(component, "data"))
    expected_pool_size = ENEMY_POOL_SIZE * ENEMY_STRIDE
    if (
        int(getattr(spec, "address")) == ENEMY_POOL_BASE
        and len(data) == expected_pool_size
    ):
        pool_offset = 0
    elif (
        int(getattr(spec, "address")) + ENEMY_STRIDE == ENEMY_POOL_BASE
        and len(data) == expected_pool_size + ENEMY_STRIDE
    ):
        pool_offset = ENEMY_STRIDE
    else:
        raise ValueError(
            "native combat enemy component is not the exact pool or "
            "template-plus-pool layout"
        )

    targets: list[EnemyDamageTarget] = []
    for slot in range(ENEMY_POOL_SIZE):
        base = pool_offset + slot * ENEMY_STRIDE
        flags = struct.unpack_from("<I", data, base + ENEMY_FLAGS_OFFSET)[0]
        if not flags & ENEMY_ACTIVE_FLAG:
            continue
        x, y = struct.unpack_from("<ff", data, base + ENEMY_POSITION_OFFSET)
        primary_width, primary_height = struct.unpack_from(
            "<ff",
            data,
            base + ENEMY_DAMAGE_HITBOX_OFFSET,
        )
        alternate_width, alternate_height = struct.unpack_from(
            "<ff",
            data,
            base + ENEMY_ALTERNATE_HITBOX_OFFSET,
        )
        targets.append(
            EnemyDamageTarget(
                slot=slot,
                enemy_pointer=ENEMY_POOL_BASE + slot * ENEMY_STRIDE,
                hitpoints=struct.unpack_from(
                    "<i",
                    data,
                    base + ENEMY_HITPOINTS_OFFSET,
                )[0],
                maximum_hitpoints=struct.unpack_from(
                    "<i",
                    data,
                    base + ENEMY_MAX_HITPOINTS_OFFSET,
                )[0],
                frame_damage=struct.unpack_from(
                    "<i",
                    data,
                    base + ENEMY_FRAME_DAMAGE_OFFSET,
                )[0],
                flags=flags,
                flags2=struct.unpack_from(
                    "<I",
                    data,
                    base + ENEMY_FLAGS2_OFFSET,
                )[0],
                x=x,
                y=y,
                primary_width=primary_width,
                primary_height=primary_height,
                alternate_width=alternate_width,
                alternate_height=alternate_height,
                main_vm_pc=struct.unpack_from(
                    "<I",
                    data,
                    base + ENEMY_MAIN_VM_OFFSET,
                )[0],
                main_vm_timer_current=struct.unpack_from(
                    "<i",
                    data,
                    base + ENEMY_MAIN_VM_TIMER_CURRENT_OFFSET,
                )[0],
                causal_tail_sha256=_sha256(
                    data[
                        base + ENEMY_CAUSAL_TAIL_OFFSET :
                        base + ENEMY_STRIDE
                    ]
                ),
            )
        )
    return tuple(targets)


def _overlaps(
    shot: PlayerShotCombatSlot,
    target: EnemyDamageTarget,
    *,
    width: float,
    height: float,
) -> bool:
    return (
        shot.x + shot.hitbox_width / 2.0 >= target.x - width / 2.0
        and shot.x - shot.hitbox_width / 2.0 <= target.x + width / 2.0
        and shot.y + shot.hitbox_height / 2.0 >= target.y - height / 2.0
        and shot.y - shot.hitbox_height / 2.0 <= target.y + height / 2.0
    )


def _shot_contribution(shot: PlayerShotCombatSlot, *, bomb_active: bool) -> int:
    if not bomb_active:
        return shot.damage
    return max(shot.damage // 5, 1)


def _supported_shot_pass(
    slots: Iterable[PlayerShotCombatSlot],
    target: EnemyDamageTarget,
    *,
    width: float,
    height: float,
    bomb_active: bool,
    pass_name: str,
) -> tuple[dict[str, object], tuple[PlayerShotCombatSlot, ...]]:
    supported_hits: list[int] = []
    callback_unknown: list[int] = []
    type45_unknown: list[int] = []
    contribution = 0
    updated: list[PlayerShotCombatSlot] = []
    for shot in slots:
        if (
            not shot.damage_loop_eligible
            or not _overlaps(shot, target, width=width, height=height)
        ):
            updated.append(shot)
            continue
        if shot.shot_type in (4, 5):
            type45_unknown.append(shot.slot)
            updated.append(shot)
            continue
        if shot.hit_callback_pointer:
            callback_unknown.append(shot.slot)
            updated.append(shot)
            continue
        supported_hits.append(shot.slot)
        contribution += _shot_contribution(shot, bomb_active=bomb_active)
        if shot.shot_type in PIERCING_SHOT_TYPES:
            updated.append(shot)
        else:
            updated.append(replace(shot, state=2))
    capped = min(contribution, PLAYER_SHOT_FRAME_DAMAGE_CAP)
    return (
        {
            "schema": SUPPORTED_SHOT_PASS_SCHEMA,
            "pass": pass_name,
            "hitbox": {"width": width, "height": height},
            "supported_hit_slots": supported_hits,
            "callback_dependent_overlap_slots": callback_unknown,
            "type45_mode_dependent_overlap_slots": type45_unknown,
            "supported_contribution_before_cap": contribution,
            "supported_contribution_after_cap": capped,
            "ordinary_shot_frame_cap": PLAYER_SHOT_FRAME_DAMAGE_CAP,
            "numeric_authority": (
                "supported_slot_subtotal_only_before_attack_regions_"
                "alternate_scaling_spell_boss_and_hp_write"
            ),
        },
        tuple(updated),
    )


def _target_combat_record(
    target: EnemyDamageTarget,
    shot_state: PlayerShotCombatState,
    *,
    bomb_active: bool,
    player_state: int,
    spell_active: bool,
    spell_enemy_pointer: int,
) -> dict[str, object]:
    gate = evaluate_enemy_player_shot_damage_gate(
        EnemyPlayerShotDamageContext(
            flags=target.flags,
            flags2=target.flags2,
            bomb_active=bomb_active,
            player_transition_state=player_state,
            damage_tick_due=shot_state.damage_timer.integer_changed,
            spell_active=spell_active,
            active_spell_owner=(
                spell_active and target.enemy_pointer == spell_enemy_pointer
            ),
        )
    )
    primary, after_primary = _supported_shot_pass(
        shot_state.slots,
        target,
        width=target.primary_width,
        height=target.primary_height,
        bomb_active=bomb_active,
        pass_name="primary",
    )
    alternate = None
    if target.alternate_enabled:
        alternate, _after_alternate = _supported_shot_pass(
            after_primary,
            target,
            width=target.alternate_width,
            height=target.alternate_height,
            bomb_active=bomb_active,
            pass_name="alternate_after_supported_primary_mutation",
        )
    return {
        **target.record(),
        "damage_gate": gate.record(),
        "ordinary_shot_passes": {
            "primary": primary,
            "alternate": alternate,
        },
    }


@dataclass(frozen=True)
class NativeCombatProjection:
    payload: dict[str, object]
    sha256: str
    summary: dict[str, object]

    def record(self, *, include_payload: bool = True) -> dict[str, object]:
        record: dict[str, object] = {
            "schema": NATIVE_COMBAT_PROJECTION_SCHEMA,
            "sha256": self.sha256,
            "summary": self.summary,
            "authority": (
                "offline_exact_root_combat_state_and_supported_"
                "ordinary_shot_subtotals_only"
            ),
            "physical_predictive_authority": False,
            "live_ranking_authority": False,
        }
        if include_payload:
            record["payload"] = self.payload
        return record


def capture_native_combat_projection(
    reader: Any,
    *,
    native_root_projection: object,
    compact_state: dict[str, object],
) -> NativeCombatProjection:
    """Capture one exact-root combat projection without another enemy read."""

    shot_state = capture_player_shot_combat_state(reader)
    spell = decode_spell_state(
        _read_exact(
            reader,
            ADDR_SPELL_CARD_STATE,
            SPELL_STATE_CAPTURE_SIZE,
            field="combat spell state",
        )
    )
    player_context = _read_exact(
        reader,
        ADDR_PLAYER,
        PLAYER_BOMB_ACTIVE_OFFSET + 4,
        field="combat player context",
    )
    player_state = player_context[0]
    bomb_active = bool(
        struct.unpack_from("<I", player_context, PLAYER_BOMB_ACTIVE_OFFSET)[0]
    )
    targets = decode_enemy_damage_targets(native_root_projection)
    target_records = [
        _target_combat_record(
            target,
            shot_state,
            bomb_active=bomb_active,
            player_state=player_state,
            spell_active=bool(spell["active"]),
            spell_enemy_pointer=int(spell["enemy_pointer"]),
        )
        for target in targets
    ]
    payload: dict[str, object] = {
        "schema": NATIVE_COMBAT_PROJECTION_SCHEMA,
        "manager_frame": int(compact_state["manager_frame"]),
        "active_input": int(compact_state["input_current"]),
        "focus_logic": int(compact_state["focus_logic"]),
        "player_state": player_state,
        "bomb_active": bomb_active,
        "spell": {
            "active": bool(spell["active"]),
            "enemy_pointer": int(spell["enemy_pointer"]),
            "spell_id": int(spell["spell_id"]) if spell["active"] else None,
        },
        "player_shots": shot_state.record(),
        "enemy_targets": target_records,
        "scope": {
            "root_identity": (
                "full_player_shot_pool_digest_plus_active_slot_fields_"
                "and_active_enemy_causal_tail_digests"
            ),
            "pass_projection": (
                "instantaneous_native_geometry_supported_slots_only"
            ),
            "omitted": [
                "future_action_delivery_and_focus_transition",
                "future_player_shot_update_callbacks",
                "type45_mode_predicate",
                "nonzero_hit_callback_semantics",
                "attack_region_damage",
                "alternate_route_scaling",
                "spell_boss_timeout_and_phase_scaling",
                "generation_safe_cross_frame_hp_attribution",
                "hostile_birth_prevention",
                "survival_feasibility",
            ],
        },
    }
    summary = {
        "manager_frame": int(compact_state["manager_frame"]),
        "active_shot_count": len(shot_state.slots),
        "damage_eligible_shot_count": len(
            shot_state.damage_eligible_slot_indices
        ),
        "hit_state_shot_count": sum(slot.state == 2 for slot in shot_state.slots),
        "active_enemy_target_count": len(targets),
        "positive_hp_target_count": sum(target.hitpoints > 0 for target in targets),
        "positive_hp_sum": sum(
            max(target.hitpoints, 0) for target in targets
        ),
        "published_frame_damage_sum": sum(
            max(target.frame_damage, 0) for target in targets
        ),
        "open_hp_gate_target_count": sum(
            bool(record["damage_gate"]["hp_subtraction_open"])
            for record in target_records
        ),
        "supported_primary_overlap_target_count": sum(
            bool(
                record["ordinary_shot_passes"]["primary"][
                    "supported_hit_slots"
                ]
            )
            for record in target_records
        ),
        "unresolved_overlap_target_count": sum(
            bool(
                record["ordinary_shot_passes"]["primary"][
                    "callback_dependent_overlap_slots"
                ]
                or record["ordinary_shot_passes"]["primary"][
                    "type45_mode_dependent_overlap_slots"
                ]
                or (
                    record["ordinary_shot_passes"]["alternate"] is not None
                    and (
                        record["ordinary_shot_passes"]["alternate"][
                            "callback_dependent_overlap_slots"
                        ]
                        or record["ordinary_shot_passes"]["alternate"][
                            "type45_mode_dependent_overlap_slots"
                        ]
                    )
                )
            )
            for record in target_records
        ),
        "supported_primary_contribution_sum": sum(
            int(
                record["ordinary_shot_passes"]["primary"][
                    "supported_contribution_after_cap"
                ]
            )
            for record in target_records
        ),
        "open_gate_supported_primary_contribution_sum": sum(
            int(
                record["ordinary_shot_passes"]["primary"][
                    "supported_contribution_after_cap"
                ]
            )
            for record in target_records
            if bool(record["damage_gate"]["hp_subtraction_open"])
        ),
        "supported_alternate_contribution_sum": sum(
            int(
                alternate["supported_contribution_after_cap"]
            )
            for record in target_records
            if (
                alternate
                := record["ordinary_shot_passes"]["alternate"]
            )
            is not None
        ),
        "player_shot_pool_sha256": shot_state.pool_sha256,
    }
    return NativeCombatProjection(
        payload=payload,
        sha256=_canonical_digest(payload),
        summary=summary,
    )


def native_combat_projection_changes(
    left: NativeCombatProjection,
    right: NativeCombatProjection,
) -> tuple[dict[str, object], ...]:
    if left.sha256 == right.sha256:
        return ()
    changes: list[dict[str, object]] = []
    for field in sorted(set(left.payload) | set(right.payload)):
        left_value = left.payload.get(field)
        right_value = right.payload.get(field)
        if left_value == right_value:
            continue
        changes.append(
            {
                "field": field,
                "left_sha256": _canonical_digest(left_value),
                "right_sha256": _canonical_digest(right_value),
            }
        )
    return tuple(changes)


__all__ = [
    "ENEMY_ALTERNATE_HITBOX_OFFSET",
    "ENEMY_DAMAGE_HITBOX_OFFSET",
    "ENEMY_DAMAGE_TARGET_STATE_SCHEMA",
    "NATIVE_COMBAT_PROJECTION_SCHEMA",
    "PLAYER_SHOT_COMBAT_STATE_SCHEMA",
    "PLAYER_SHOT_POOL_BYTES",
    "SUPPORTED_SHOT_PASS_SCHEMA",
    "EnemyDamageTarget",
    "NativeCombatProjection",
    "PlayerShotCombatSlot",
    "PlayerShotCombatState",
    "Th08TimerIdentity",
    "capture_native_combat_projection",
    "capture_player_shot_combat_state",
    "decode_enemy_damage_targets",
    "decode_player_shot_pool",
    "native_combat_projection_changes",
]
