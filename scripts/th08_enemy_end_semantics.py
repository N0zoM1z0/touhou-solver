"""Fail-closed TH08 ordinary-enemy retirement semantics.

This module does not infer lifetimes from endpoint active bits.  It lowers
only an ordered native control-edge observation into the generational
lifecycle ledger used by the offline future-body model.
"""

from __future__ import annotations

from dataclasses import dataclass

from th08_future_body_identity import Route2SlotLifecycleEvent


ENEMY_END_EVIDENCE_SCHEMA = "th08-ordinary-enemy-end-evidence-v1"
ENEMY_END_CLASSIFICATION_SCHEMA = (
    "th08-ordinary-enemy-end-classification-v1"
)
ENEMY_FORCED_HP_ZERO_SCHEMA = "th08-ordinary-enemy-forced-hp-zero-v1"

TIMELINE_INITIAL_VM_RETIRE = (
    "timeline_initial_vm_return_minus_one@0x0042a5f5"
)
INHERITED_VM_INITIAL_RETIRE = (
    "inherited_vm_initial_return_minus_one@0x0042a787"
)
MANAGER_MAIN_VM_RETIRE = "manager_main_vm_return_minus_one@0x0042c9a2"
MANAGER_OFFSCREEN_RETIRE = "manager_offscreen_cull@0x0042cded"
MANAGER_HP_DEFEAT_MODE0_RETIRE = (
    "manager_hp_defeat_mode0_active_clear@0x0042d899"
)

RETIREMENT_SOURCES = frozenset(
    {
        TIMELINE_INITIAL_VM_RETIRE,
        INHERITED_VM_INITIAL_RETIRE,
        MANAGER_MAIN_VM_RETIRE,
        MANAGER_OFFSCREEN_RETIRE,
        MANAGER_HP_DEFEAT_MODE0_RETIRE,
    }
)

OPCODE_5F_FORCED_HP_ZERO = "opcode_5f@0x0041da89"
SPELL_FINISH_FORCED_HP_ZERO = "spell_finish@0x00416225"
BOSS_DEFEAT_FORCED_HP_ZERO = "boss_defeat_cleanup@0x0042d93c"
MESSAGE_START_FORCED_HP_ZERO = "message_start@0x00433d9f"

FORCED_HP_ZERO_SOURCES = frozenset(
    {
        OPCODE_5F_FORCED_HP_ZERO,
        SPELL_FINISH_FORCED_HP_ZERO,
        BOSS_DEFEAT_FORCED_HP_ZERO,
        MESSAGE_START_FORCED_HP_ZERO,
    }
)

_NON_HP_END_REASONS = {
    TIMELINE_INITIAL_VM_RETIRE: "scripted_initial_vm_end",
    INHERITED_VM_INITIAL_RETIRE: "scripted_initial_vm_end",
    MANAGER_MAIN_VM_RETIRE: "scripted_main_vm_end",
    MANAGER_OFFSCREEN_RETIRE: "offscreen_cull",
}


def _nonnegative_int(name: str, value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def _slot(value: int) -> None:
    if type(value) is not int or not 0 <= value < 480:
        raise ValueError("enemy slot must belong to the 480-slot native pool")


@dataclass(frozen=True, slots=True)
class PlayerShotDamageTransition:
    """One exact damage subtraction from the native manager iteration."""

    hp_before_damage: int
    resolved_damage: int
    hp_after_damage: int

    def __post_init__(self) -> None:
        for name, value in (
            ("hp_before_damage", self.hp_before_damage),
            ("resolved_damage", self.resolved_damage),
            ("hp_after_damage", self.hp_after_damage),
        ):
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer")
        if self.resolved_damage <= 0:
            raise ValueError("resolved player-shot damage must be positive")
        if (
            self.hp_after_damage
            != self.hp_before_damage - self.resolved_damage
        ):
            raise ValueError("damage transition does not preserve HP arithmetic")

    @property
    def crosses_zero(self) -> bool:
        return self.hp_before_damage > 0 and self.hp_after_damage <= 0

    def record(self) -> dict[str, int]:
        return {
            "hp_before_damage": self.hp_before_damage,
            "resolved_damage": self.resolved_damage,
            "hp_after_damage": self.hp_after_damage,
        }


@dataclass(frozen=True, slots=True)
class EnemyForcedHpZeroEvidence:
    """One native forced-zero effect that is explicitly not retirement."""

    physical_update: int
    sequence: int
    slot: int
    source: str
    active_before: bool
    active_after: bool
    hp_after: int
    schema: str = ENEMY_FORCED_HP_ZERO_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != ENEMY_FORCED_HP_ZERO_SCHEMA:
            raise ValueError("unsupported forced-HP-zero evidence schema")
        _nonnegative_int("physical_update", self.physical_update)
        _nonnegative_int("sequence", self.sequence)
        _slot(self.slot)
        if self.source not in FORCED_HP_ZERO_SOURCES:
            raise ValueError("unsupported forced-HP-zero native source")
        if self.active_before is not True or self.active_after is not True:
            raise ValueError(
                "forced-HP-zero evidence must preserve the active lifetime"
            )
        if type(self.hp_after) is not int or self.hp_after != 0:
            raise ValueError("forced-HP-zero evidence must retain HP zero")

    def record(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "physical_update": self.physical_update,
            "sequence": self.sequence,
            "slot": self.slot,
            "source": self.source,
            "active_before": self.active_before,
            "active_after": self.active_after,
            "hp_after": self.hp_after,
            "retires_lifetime": False,
            "verified_player_shot_kill": False,
        }


@dataclass(frozen=True, slots=True)
class EnemyRetirementEvidence:
    """One ordered native active-bit clear with only available causal data."""

    physical_update: int
    sequence: int
    slot: int
    source: str
    active_bit_cleared: bool
    defeat_mode: int | None = None
    post_current_health: int | None = None
    damage_transition: PlayerShotDamageTransition | None = None
    preceding_forced_hp_zero_source: str | None = None
    schema: str = ENEMY_END_EVIDENCE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != ENEMY_END_EVIDENCE_SCHEMA:
            raise ValueError("unsupported enemy-end evidence schema")
        _nonnegative_int("physical_update", self.physical_update)
        _nonnegative_int("sequence", self.sequence)
        _slot(self.slot)
        if self.source not in RETIREMENT_SOURCES:
            raise ValueError("unsupported enemy retirement native source")
        if self.active_bit_cleared is not True:
            raise ValueError(
                "enemy retirement requires an observed active-bit clear"
            )
        if (
            self.preceding_forced_hp_zero_source is not None
            and self.preceding_forced_hp_zero_source
            not in FORCED_HP_ZERO_SOURCES
        ):
            raise ValueError("unsupported preceding forced-HP-zero source")

        is_hp_defeat = self.source == MANAGER_HP_DEFEAT_MODE0_RETIRE
        if is_hp_defeat:
            if self.defeat_mode != 0:
                raise ValueError("mode-0 HP retirement requires defeat mode 0")
            if (
                type(self.post_current_health) is not int
                or self.post_current_health > 0
            ):
                raise ValueError(
                    "mode-0 HP retirement requires nonpositive post HP"
                )
            if (
                self.damage_transition is not None
                and self.damage_transition.hp_after_damage
                != self.post_current_health
            ):
                raise ValueError(
                    "damage transition and retirement HP disagree"
                )
            return

        if any(
            value is not None
            for value in (
                self.defeat_mode,
                self.damage_transition,
                self.preceding_forced_hp_zero_source,
            )
        ):
            raise ValueError(
                "non-HP retirement cannot carry HP-defeat causal fields"
            )


@dataclass(frozen=True, slots=True)
class EnemyRetirementClassification:
    """Fail-closed end reason plus the exact ledger retirement event."""

    reason: str
    reason_authority: str
    verified_player_shot_kill: bool
    lifecycle_event: Route2SlotLifecycleEvent
    schema: str = ENEMY_END_CLASSIFICATION_SCHEMA

    def record(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "reason": self.reason,
            "reason_authority": self.reason_authority,
            "verified_player_shot_kill": self.verified_player_shot_kill,
            "lifecycle_event": self.lifecycle_event.record(),
        }


def classify_enemy_retirement(
    evidence: EnemyRetirementEvidence,
) -> EnemyRetirementClassification:
    """Classify one exact native retirement without inventing kill causality."""

    if type(evidence) is not EnemyRetirementEvidence:
        raise ValueError("retirement evidence must use the exact schema")
    lifecycle_event = Route2SlotLifecycleEvent(
        physical_update=evidence.physical_update,
        sequence=evidence.sequence,
        kind="retire",
        slot=evidence.slot,
        source=evidence.source,
    )
    if evidence.source in _NON_HP_END_REASONS:
        return EnemyRetirementClassification(
            reason=_NON_HP_END_REASONS[evidence.source],
            reason_authority="observed_native_control_edge",
            verified_player_shot_kill=False,
            lifecycle_event=lifecycle_event,
        )

    if evidence.preceding_forced_hp_zero_source is not None:
        return EnemyRetirementClassification(
            reason="forced_hp_zero_defeat",
            reason_authority="observed_ordered_forced_zero_and_active_clear",
            verified_player_shot_kill=False,
            lifecycle_event=lifecycle_event,
        )

    damage = evidence.damage_transition
    if damage is not None and damage.crosses_zero:
        return EnemyRetirementClassification(
            reason="player_shot_lethal_damage",
            reason_authority="observed_ordered_damage_and_active_clear",
            verified_player_shot_kill=True,
            lifecycle_event=lifecycle_event,
        )

    return EnemyRetirementClassification(
        reason="hp_defeat_unattributed",
        reason_authority="observed_active_clear_only",
        verified_player_shot_kill=False,
        lifecycle_event=lifecycle_event,
    )


__all__ = [
    "BOSS_DEFEAT_FORCED_HP_ZERO",
    "ENEMY_END_CLASSIFICATION_SCHEMA",
    "ENEMY_END_EVIDENCE_SCHEMA",
    "ENEMY_FORCED_HP_ZERO_SCHEMA",
    "FORCED_HP_ZERO_SOURCES",
    "INHERITED_VM_INITIAL_RETIRE",
    "MANAGER_HP_DEFEAT_MODE0_RETIRE",
    "MANAGER_MAIN_VM_RETIRE",
    "MANAGER_OFFSCREEN_RETIRE",
    "MESSAGE_START_FORCED_HP_ZERO",
    "OPCODE_5F_FORCED_HP_ZERO",
    "RETIREMENT_SOURCES",
    "SPELL_FINISH_FORCED_HP_ZERO",
    "TIMELINE_INITIAL_VM_RETIRE",
    "EnemyForcedHpZeroEvidence",
    "EnemyRetirementClassification",
    "EnemyRetirementEvidence",
    "PlayerShotDamageTransition",
    "classify_enemy_retirement",
]
