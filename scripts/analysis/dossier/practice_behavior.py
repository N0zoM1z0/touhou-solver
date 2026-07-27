"""Practice-run pre-hit and per-spell behavior summaries."""

from __future__ import annotations

import statistics

from analysis.dossier.planner_consistency import (
    planner_consistency_summary as _planner_consistency_summary,
)
from analysis.dossier.practice_control import (
    _robust_viability_summary,
)
from analysis.dossier.practice_timing import (
    _decision_cadence,
    _runtime_timing,
)


def _behavior_slice(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    if not rows:
        return {"sample_count": 0}
    slacks = [
        float(row["corridor_slack"])
        for row in rows
        if row["corridor_slack"] is not None
    ]
    count = len(rows)
    recovery_guided = 0
    recovery_selected = 0
    distant_recovery_guided = 0
    distant_recovery_selected = 0
    control_reserve_deficits = []
    for row in rows:
        robust_control = row.get("robust_control")
        if (
            isinstance(robust_control, dict)
            and robust_control.get(
                "viability_control_reserve_deficit"
            ) is not None
        ):
            control_reserve_deficits.append(
                float(
                    robust_control[
                        "viability_control_reserve_deficit"
                    ]
                )
            )
        viability = row.get("viability")
        if not isinstance(viability, dict) or bool(
            viability.get("state_viable")
        ):
            continue
        repair_volumes = viability.get("repair_volumes", {})
        if isinstance(repair_volumes, dict) and any(
            int(volume) > 0 for volume in repair_volumes.values()
        ):
            recovery_guided += 1
        if int(viability.get("selected_repair_volume", 0)) > 0:
            recovery_selected += 1
        recovery_distances = viability.get("recovery_distances", {})
        if isinstance(recovery_distances, dict) and recovery_distances:
            distant_recovery_guided += 1
        if viability.get("selected_recovery_distance") is not None:
            distant_recovery_selected += 1
    return {
        "sample_count": count,
        "fast_fraction": sum(
            "_fast" in str(row["action"]) for row in rows
        )
        / count,
        "focused_fraction": sum(
            bool(int(row["mask"]) & 0x04) for row in rows
        )
        / count,
        "bottom_8px_fraction": sum(
            float(row["player"]["y"]) >= 424.0 for row in rows
        )
        / count,
        "nonpositive_pipeline_fraction": sum(
            float(row["pipeline_clearance"]) <= 0.0 for row in rows
        )
        / count,
        "negative_corridor_slack_fraction": (
            sum(slack < 0.0 for slack in slacks) / len(slacks)
            if slacks
            else None
        ),
        "action_lag_over_model_fraction": sum(
            int(row["action_lag"]) > int(row["control_delay_frames"])
            for row in rows
        )
        / count,
        "recovery_guided_fraction": recovery_guided / count,
        "recovery_selected_fraction": recovery_selected / count,
        "distant_recovery_guided_fraction": (
            distant_recovery_guided / count
        ),
        "distant_recovery_selected_fraction": (
            distant_recovery_selected / count
        ),
        "control_reserve_deficit_mean": (
            statistics.mean(control_reserve_deficits)
            if control_reserve_deficits
            else None
        ),
        "positive_control_reserve_deficit_fraction": (
            sum(value > 1e-6 for value in control_reserve_deficits)
            / len(control_reserve_deficits)
            if control_reserve_deficits
            else None
        ),
    }


def _behavior_context(
    decisions: list[dict[str, object]],
    deaths: list[dict[str, object]],
) -> dict[str, object]:
    death_frames = [int(death["frame"]) for death in deaths]
    alive = [
        row for row in decisions if int(row["player"]["phase"]) == 0
    ]

    def prehit(row: dict[str, object]) -> bool:
        frame = int(row["frame"])
        return any(
            0 <= death_frame - frame <= 60
            for death_frame in death_frames
        )

    def spell_50(row: dict[str, object]) -> bool:
        spell = row.get("spell")
        return (
            isinstance(spell, dict)
            and bool(spell.get("active"))
            and int(spell.get("spell_id", -1)) == 50
        )

    prehit_rows = [row for row in alive if prehit(row)]
    other_rows = [row for row in alive if not prehit(row)]
    spell_50_rows = [row for row in alive if spell_50(row)]
    return {
        "alive_all": _behavior_slice(alive),
        "alive_preceding_hit_60f": _behavior_slice(prehit_rows),
        "alive_outside_preceding_hit_60f": _behavior_slice(other_rows),
        "spell_50_alive_all": _behavior_slice(spell_50_rows),
        "spell_50_alive_preceding_hit_60f": _behavior_slice(
            [row for row in spell_50_rows if prehit(row)]
        ),
        "spell_50_alive_other": _behavior_slice(
            [row for row in spell_50_rows if not prehit(row)]
        ),
    }


def _spell_phase_summary(
    decisions: list[dict[str, object]],
    deaths: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows_by_key: dict[str, list[dict[str, object]]] = {}
    spell_names: dict[str, str | None] = {}
    for row in decisions:
        spell = row.get("spell")
        if (
            isinstance(spell, dict)
            and bool(spell.get("active"))
            and spell.get("spell_id") is not None
        ):
            key = str(int(spell["spell_id"]))
            name = (
                str(spell["spell_name"])
                if spell.get("spell_name") is not None
                else None
            )
        else:
            key = "nonspell"
            name = None
        rows_by_key.setdefault(key, []).append(row)
        if name is not None:
            spell_names[key] = name

    death_frames: dict[str, list[int]] = {}
    for death in deaths:
        spell = death["spell_attribution"]
        spell_id = spell.get("spell_id")
        key = str(int(spell_id)) if spell_id is not None else "nonspell"
        death_frames.setdefault(key, []).append(int(death["frame"]))
        if spell.get("spell_name") is not None:
            spell_names[key] = str(spell["spell_name"])

    def sort_key(key: str) -> tuple[int, int]:
        return (0, -1) if key == "nonspell" else (1, int(key))

    result = []
    for key in sorted(rows_by_key, key=sort_key):
        rows = rows_by_key[key]
        alive = [
            row for row in rows if int(row["player"]["phase"]) == 0
        ]
        viability = _robust_viability_summary(rows)
        result.append(
            {
                "phase_key": key,
                "spell_id": None if key == "nonspell" else int(key),
                "spell_name": spell_names.get(key),
                "decision_count": len(rows),
                "alive_decision_count": len(alive),
                "hit_count": len(death_frames.get(key, [])),
                "hit_frames": death_frames.get(key, []),
                "max_active_bullets": max(
                    int(row["active_bullets"]) for row in rows
                ),
                "max_active_lasers": max(
                    int(row["active_lasers"]) for row in rows
                ),
                "behavior_alive": _behavior_slice(alive),
                "decision_cadence_frames": _decision_cadence(rows),
                "runtime_timing_ms": _runtime_timing(rows),
                "robust_viability": viability,
                "planner_consistency": _planner_consistency_summary(rows),
            }
        )
    return result




__all__ = [
    "_behavior_context",
    "_behavior_slice",
    "_spell_phase_summary",
]
