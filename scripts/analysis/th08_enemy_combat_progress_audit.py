#!/usr/bin/env python3
"""Compatibility entry point for the enemy combat-progress physical audit."""

from __future__ import annotations

from analysis.enemy_combat_progress_audit import (
    EnemyCombatProgressAuditError,
    audit_enemy_combat_progress,
)
from analysis.enemy_combat_progress_audit.cli import main


__all__ = [
    "EnemyCombatProgressAuditError",
    "audit_enemy_combat_progress",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
