"""Trace-to-dossier schema lowering shared by offline report builders."""

from __future__ import annotations

from pathlib import Path


def compact_decision(
    row: dict[str, object],
    *,
    trace_index: int,
    trace_path: Path,
) -> dict[str, object]:
    """Lower one live decision without changing the retained dossier schema."""
    resources = row["resources"]
    player = row["player"]
    corridor = row.get("corridor")
    target = corridor.get("target") if isinstance(corridor, dict) else None
    viability = (
        corridor.get("viability")
        if isinstance(corridor, dict) and isinstance(corridor.get("viability"), dict)
        else {}
    )
    enemy_body_snapshot_value = row.get(
        "enemy_body_snapshot_frame",
        row["frame"],
    )
    compact = {
        "frame": int(row["frame"]),
        "gameplay_epoch": int(row.get("gameplay_epoch", 0)),
        "trace_index": trace_index,
        "trace_path": str(trace_path),
        "stage_route_index": int(row["stage_route_index"]),
        "resources": {
            "lives": float(resources["lives"]),
            "bombs": float(resources["bombs"]),
            "power": float(resources["power"]),
        },
        "player": {
            "x": float(player["x"]),
            "y": float(player["y"]),
            "phase": int(player["phase"]),
            "phase_at_action": int(player["phase_at_action"]),
            "predeath_at_action": int(player["predeath_at_action"]),
        },
        "active_bullets": int(row.get("active_bullets", 0)),
        "active_lasers": int(row.get("active_lasers", 0)),
        "active_items": int(row.get("active_items", 0)),
        "active_enemy_bodies": int(row.get("active_enemy_bodies", 0)),
        "enemy_body_contact_enabled_count": int(
            row.get(
                "enemy_body_contact_enabled_count",
                row.get("active_enemy_bodies", 0),
            )
        ),
        "enemy_body_anticipatory_count": int(
            row.get("enemy_body_anticipatory_count", 0)
        ),
        "enemy_body_dormant_count": int(row.get("enemy_body_dormant_count", 0)),
        "enemy_body_snapshot_frame": (
            int(enemy_body_snapshot_value)
            if enemy_body_snapshot_value is not None
            else None
        ),
        "enemy_body_pointers": [
            int(body[0])
            for body in row.get("enemy_bodies", ())
            if isinstance(body, list) and len(body) >= 8
        ],
        "action": str(row.get("action", "")),
        "mask": int(row.get("mask", 0)),
        "input_snapshot": {
            key: int(value)
            for key, value in (
                row.get("input_snapshot")
                if isinstance(row.get("input_snapshot"), dict)
                else {}
            ).items()
            if key in {"raw", "current", "previous"}
        },
        "bomb": bool(row.get("bomb")),
        "hit_started": bool(row.get("hit_started")),
        "auto_confirm": row.get("auto_confirm"),
        "snapshot_frame": int(row.get("snapshot_frame", row["frame"])),
        "snapshot_lag": int(row.get("snapshot_lag", 0)),
        "action_lag": int(row.get("action_lag", 0)),
        "deadline_guard": (
            row.get("deadline_guard")
            if isinstance(row.get("deadline_guard"), dict)
            else {}
        ),
        "control_delay_frames": int(row.get("control_delay_frames", 3)),
        "control_delay_candidates": [
            int(value) for value in row.get("control_delay_candidates", [])
        ],
        "control_delay_estimator": (
            row.get("control_delay_estimator")
            if isinstance(row.get("control_delay_estimator"), dict)
            else {}
        ),
        "action_hold_frames": int(row.get("action_hold_frames", 2)),
        "read_ms": float(row.get("read_ms", 0.0)),
        "plan_ms": float(row.get("plan_ms", 0.0)),
        "timing_ms": row.get("timing_ms"),
        "pipeline_clearance": float(row.get("pipeline_clearance", 9999.0)),
        "minimum_clearance": float(row.get("minimum_clearance", 9999.0)),
        "robust_control": (
            row.get("robust_control")
            if isinstance(row.get("robust_control"), dict)
            else {}
        ),
        "terminal_threat": (
            row.get("terminal_threat")
            if isinstance(row.get("terminal_threat"), dict)
            else {}
        ),
        "corridor_lane": (
            str(corridor["lane"]) if isinstance(corridor, dict) else None
        ),
        "corridor_slack": (
            float(target["slack"]) if isinstance(target, dict) else None
        ),
        "corridor_planning_mode": (
            str(corridor.get("planning_mode"))
            if isinstance(corridor, dict) and corridor.get("planning_mode") is not None
            else None
        ),
        "corridor_source_frame": (
            int(corridor["source_frame"])
            if isinstance(corridor, dict) and corridor.get("source_frame") is not None
            else None
        ),
        "corridor_snapshot_frame": (
            int(corridor["snapshot_frame"])
            if isinstance(corridor, dict) and corridor.get("snapshot_frame") is not None
            else None
        ),
        "corridor_forecast_lead_frames": (
            int(corridor["forecast_lead_frames"])
            if isinstance(corridor, dict)
            and corridor.get("forecast_lead_frames") is not None
            else None
        ),
        "corridor_solve_ms": (
            float(corridor.get("solve_ms", 0.0)) if isinstance(corridor, dict) else None
        ),
        "corridor_age": (
            int(corridor.get("age", 0)) if isinstance(corridor, dict) else None
        ),
        "corridor_stale": (
            bool(corridor.get("stale")) if isinstance(corridor, dict) else None
        ),
        "corridor_policy_status": (
            str(corridor.get("policy_status"))
            if isinstance(corridor, dict) and corridor.get("policy_status") is not None
            else None
        ),
        "corridor_viability_backend": (
            str(corridor.get("viability_backend"))
            if isinstance(corridor, dict)
            and corridor.get("viability_backend") is not None
            else None
        ),
        "corridor_solver_timing_ms": (
            {
                str(key): float(value)
                for key, value in corridor.get(
                    "solver_timing_ms",
                    {},
                ).items()
            }
            if isinstance(corridor, dict)
            and isinstance(corridor.get("solver_timing_ms"), dict)
            else {}
        ),
        "corridor_serial_coverage_margin_frames": (
            int(corridor["serial_coverage_margin_frames"])
            if isinstance(corridor, dict)
            and corridor.get("serial_coverage_margin_frames") is not None
            else None
        ),
        "corridor_serial_worker_serviceable": (
            bool(corridor["serial_worker_serviceable"])
            if isinstance(corridor, dict)
            and corridor.get("serial_worker_serviceable") is not None
            else None
        ),
        "viability": viability,
        "spell": row.get("spell"),
        "spell_enemy_body_guard": (
            row.get("spell_enemy_body_guard")
            if isinstance(row.get("spell_enemy_body_guard"), dict)
            else None
        ),
        "issue_time_enemy_guard": (
            row.get("issue_time_enemy_guard")
            if isinstance(row.get("issue_time_enemy_guard"), dict)
            else None
        ),
    }
    if compact["hit_started"]:
        compact["nearby_bullets"] = row.get("nearby_bullets", [])
        compact["lasers"] = row.get("lasers", [])
        compact["enemy_bodies"] = row.get("enemy_bodies", [])
        compact["hit_contact_observation"] = row.get("hit_contact_observation")
    return compact
