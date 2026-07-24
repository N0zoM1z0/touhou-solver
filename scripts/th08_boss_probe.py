#!/usr/bin/env python3
"""Print one read-only native boss/owner snapshot from a running TH08."""

from __future__ import annotations

import json

from th08_boss_phase import (
    BOSS_REGISTRY_ADDRESS,
    BOSS_REGISTRY_SLOTS,
    ENEMY_CURRENT_HEALTH_OFFSET,
    ENEMY_FLAGS2_OFFSET,
    ENEMY_FLAGS_OFFSET,
    capture_boss_phase_snapshot,
    serialize_boss_phase_snapshot,
)
from th08_runtime_agent import ProcessReader, TARGET_EXE, Win32, observe_state


def main() -> int:
    api = Win32()
    pid = api.find_pid(TARGET_EXE)
    reader = ProcessReader(api, pid)
    try:
        state = observe_state(reader)
        spell = state["spell"]
        pointer = int(spell.get("enemy_pointer", 0))
        owner = None
        if pointer:
            owner = {
                "pointer": pointer,
                "flags": reader.u32(pointer + ENEMY_FLAGS_OFFSET),
                "flags2": reader.u32(pointer + ENEMY_FLAGS2_OFFSET),
                "current_health": reader.i32(
                    pointer + ENEMY_CURRENT_HEALTH_OFFSET
                ),
            }
        registry = [
            reader.u32(BOSS_REGISTRY_ADDRESS + index * 4)
            for index in range(BOSS_REGISTRY_SLOTS)
        ]
        registry_entries = [
            {
                "slot": index,
                "pointer": entry,
                "flags": reader.u32(entry + ENEMY_FLAGS_OFFSET),
                "flags2": reader.u32(entry + ENEMY_FLAGS2_OFFSET),
                "current_health": reader.i32(
                    entry + ENEMY_CURRENT_HEALTH_OFFSET
                ),
            }
            for index, entry in enumerate(registry)
            if entry
        ]
        snapshot = capture_boss_phase_snapshot(
            reader,
            preferred_pointer=pointer,
        )
        print(
            json.dumps(
                {
                    "pid": pid,
                    "frame": state["enemy_manager_frame"],
                    "spell": spell,
                    "owner": owner,
                    "registry": registry,
                    "registry_entries": registry_entries,
                    "boss_phase": serialize_boss_phase_snapshot(snapshot),
                },
                ensure_ascii=False,
            )
        )
    finally:
        reader.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
