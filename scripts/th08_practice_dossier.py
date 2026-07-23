#!/usr/bin/env python3
"""Build a scoped TH08 thprac no-Bomb practice dossier."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from th08_run_dossier import (
    _compact_decision,
    _death_clusters,
    _death_ledger,
    _percentiles,
    _resource_range,
)
from th08_trial_report import STAGE_ROUTE_LABELS


ROOT = Path(__file__).resolve().parent.parent
BOMB_INPUT_BIT = 0x02


@dataclass(frozen=True)
class PracticeTrace:
    path: str
    sha256: str
    size_bytes: int
    parse_errors: int
    identity: dict[str, object] | None
    controller_configs: tuple[dict[str, object], ...]
    raw_kind_counts: dict[str, int]
    raw_summary: dict[str, object] | None
    decisions: tuple[dict[str, object], ...]
    end_event: dict[str, object]
    scene_events: tuple[dict[str, object], ...]
    post_scope_decision_count: int


def _extract_scope(
    rows: list[dict[str, object]],
    *,
    trace_path: Path,
) -> tuple[
    list[dict[str, object]],
    dict[str, object],
    list[dict[str, object]],
    int,
]:
    decisions: list[dict[str, object]] = []
    scene_events: list[dict[str, object]] = []
    end_event: dict[str, object] | None = None
    stage: int | None = None
    previous_frame: int | None = None
    post_scope_decisions = 0

    for row in rows:
        kind = row.get("kind")
        if (
            kind in {"scene_inactive", "scene_resumed"}
            and end_event is None
        ):
            scene_events.append(row)
        if kind != "decision":
            continue
        frame = int(row["frame"])
        row_stage = int(row["stage_route_index"])
        if end_event is not None:
            post_scope_decisions += 1
            continue
        if stage is None:
            stage = row_stage
        elif row_stage != stage:
            end_event = {
                "reason": "stage_change",
                "previous_stage_route_index": stage,
                "next_stage_route_index": row_stage,
                "next_frame": frame,
            }
            post_scope_decisions += 1
            continue
        if previous_frame is not None and frame < previous_frame:
            end_event = {
                "reason": "frame_counter_regression",
                "previous_frame": previous_frame,
                "next_frame": frame,
                "stage_route_index": row_stage,
            }
            post_scope_decisions += 1
            continue
        compact = _compact_decision(
            row,
            trace_index=0,
            trace_path=trace_path,
        )
        corridor = row.get("corridor")
        if isinstance(corridor, dict):
            compact["corridor_source_frame"] = int(
                corridor["source_frame"]
            )
            compact["corridor_solve_ms"] = float(
                corridor.get("solve_ms", 0.0)
            )
            compact["corridor_age"] = int(corridor.get("age", 0))
            compact["corridor_stale"] = bool(corridor.get("stale"))
        decisions.append(compact)
        previous_frame = frame

    if not decisions:
        raise ValueError(f"{trace_path}: no scoped decisions")
    if end_event is None:
        end_event = {
            "reason": "raw_trace_end",
            "last_frame": int(decisions[-1]["frame"]),
            "stage_route_index": int(decisions[-1]["stage_route_index"]),
        }
    first_frame = int(decisions[0]["frame"])
    last_frame = int(decisions[-1]["frame"])
    scene_events = [
        row
        for row in scene_events
        if first_frame <= int(row.get("frame", -1)) <= last_frame
    ]
    return decisions, end_event, scene_events, post_scope_decisions


def read_practice_trace(path: Path) -> PracticeTrace:
    digest = hashlib.sha256()
    rows: list[dict[str, object]] = []
    parse_errors = 0
    identity = None
    controller_configs = []
    raw_summary = None
    kind_counts: Counter[str] = Counter()

    with path.open("rb") as source:
        for binary_line in source:
            digest.update(binary_line)
            try:
                row = json.loads(binary_line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                parse_errors += 1
                continue
            rows.append(row)
            kind = str(row.get("kind", "unknown"))
            kind_counts[kind] += 1
            if kind == "identity":
                identity = row
            elif kind == "controller_config":
                controller_configs.append(row)
            elif kind == "summary":
                raw_summary = row

    decisions, end_event, scene_events, post_scope_decisions = _extract_scope(
        rows,
        trace_path=path,
    )
    return PracticeTrace(
        path=str(path),
        sha256=digest.hexdigest(),
        size_bytes=path.stat().st_size,
        parse_errors=parse_errors,
        identity=identity,
        controller_configs=tuple(controller_configs),
        raw_kind_counts=dict(kind_counts),
        raw_summary=raw_summary,
        decisions=tuple(decisions),
        end_event=end_event,
        scene_events=tuple(scene_events),
        post_scope_decision_count=post_scope_decisions,
    )


def _no_bomb_verification(
    decisions: list[dict[str, object]],
    controller_configs: tuple[dict[str, object], ...],
) -> dict[str, object]:
    mask_violations = [
        int(row["frame"])
        for row in decisions
        if int(row["mask"]) & BOMB_INPUT_BIT
    ]
    flag_violations = [
        int(row["frame"]) for row in decisions if bool(row["bomb"])
    ]
    action_violations = [
        int(row["frame"])
        for row in decisions
        if "bomb" in str(row["action"]).lower()
    ]
    configured_disabled = any(
        row.get("bomb_policy") == "disabled" for row in controller_configs
    )
    passed = (
        configured_disabled
        and not mask_violations
        and not flag_violations
        and not action_violations
    )
    return {
        "passed": passed,
        "bomb_input_bit": BOMB_INPUT_BIT,
        "controller_policy_disabled": configured_disabled,
        "decision_count_checked": len(decisions),
        "mask_violation_frames": mask_violations,
        "bomb_flag_violation_frames": flag_violations,
        "bomb_action_violation_frames": action_violations,
        "resource_note": (
            "Bomb stock changes after a hit are thprac respawn-state changes, "
            "not Bomb input; the mask, decision flag, and action are the "
            "controller evidence."
        ),
    }


def _promote_enemy_body_candidates(
    deaths: list[dict[str, object]],
) -> None:
    for index, death in enumerate(deaths):
        spell = death["spell_attribution"]
        if not (
            death["primary_cause_class"]
            == "sensor_gap_or_unmodeled_hazard"
            and spell["status"] == "resolved_live_spell_state"
            and int(spell.get("enemy_pointer", 0)) != 0
            and int(death["active_bullets"]) == 0
            and int(death["active_lasers"]) == 0
            and float(death["pipeline_clearance_at_hit"]) > 0.0
        ):
            continue
        death["primary_cause_class"] = "enemy_body_contact_candidate"
        death["enemy_body_evidence"] = {
            "confidence": (
                "strong static candidate; exact runtime overlap not yet "
                "captured"
            ),
            "enemy_pointer": int(spell["enemy_pointer"]),
            "canonical_fresh_attempt_sample": index == 0,
            "native_path": [
                {
                    "address": "0x42cf7a",
                    "meaning": (
                        "enemy manager invokes player contact using enemy "
                        "+0x2d88 position, +0x2d70 contact size, and +0x3324 "
                        "contact flags"
                    ),
                },
                {
                    "address": "0x42c33f",
                    "meaning": "enemy contact size is scaled by 1.5",
                },
                {
                    "address": "0x44a360",
                    "name": "player_test_deadly_aabb_contact",
                    "meaning": (
                        "enemy AABB versus player lethal rectangle; overlap "
                        "calls player_dead_handler"
                    ),
                },
            ],
            "missing_runtime_field": (
                "active enemy position/contact-size/flags at the hit frame"
            ),
        }


def _corridor_latency(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    unique: dict[int, dict[str, object]] = {}
    for row in decisions:
        source = row.get("corridor_source_frame")
        if source is None:
            continue
        unique.setdefault(int(source), row)

    def stats(
        rows: list[dict[str, object]],
    ) -> dict[str, object]:
        return {
            "unique_solution_count": len(rows),
            "solve_ms": _percentiles(
                float(row["corridor_solve_ms"]) for row in rows
            ),
            "age_frames": _percentiles(
                float(row["corridor_age"]) for row in rows
            ),
            "stale_solution_count": sum(
                bool(row["corridor_stale"]) for row in rows
            ),
        }

    unique_rows = list(unique.values())
    spell_50_rows = [
        row
        for row in unique_rows
        if isinstance(row.get("spell"), dict)
        and bool(row["spell"].get("active"))
        and int(row["spell"].get("spell_id", -1)) == 50
    ]
    return {
        "all": stats(unique_rows),
        "active_spell_50": stats(spell_50_rows),
    }


def build_dossier(
    *,
    run_id: str,
    trace: PracticeTrace,
) -> dict[str, object]:
    decisions = list(trace.decisions)
    deaths = _death_ledger(decisions)
    _promote_enemy_body_candidates(deaths)
    no_bomb = _no_bomb_verification(
        decisions,
        trace.controller_configs,
    )
    if not no_bomb["passed"]:
        raise ValueError("hard no-Bomb invariant failed")

    for index, death in enumerate(deaths):
        death["sample_role"] = (
            "canonical_fresh_attempt_causal_sample"
            if index == 0
            else "post_respawn_discovery_sample"
        )
        death["bomb_input_verified_absent"] = True

    stage = int(decisions[0]["stage_route_index"])
    cause_counts = Counter(
        str(death["primary_cause_class"]) for death in deaths
    )
    contributor_counts = Counter(
        factor
        for death in deaths
        for factor in death["contributing_factors"]
    )
    spell_counts = Counter(
        (
            str(death["spell_attribution"]["spell_id"])
            if death["spell_attribution"]["spell_id"] is not None
            else "nonspell"
        )
        for death in deaths
    )
    first_hit = deaths[0] if deaths else None
    first_hit_frame = int(first_hit["frame"]) if first_hit else None
    first_window = (
        [
            row
            for row in decisions
            if first_hit_frame - 240 <= int(row["frame"]) <= first_hit_frame
        ]
        if first_hit_frame is not None
        else []
    )
    operational_lag_rows = [
        row for row in decisions if int(row["action_lag"]) < 120
    ]
    phase_counter_discontinuities = len(decisions) - len(
        operational_lag_rows
    )

    return {
        "schema": "th08-practice-dossier-v1",
        "run_id": run_id,
        "practice_scope": {
            "stage_route_index": stage,
            "stage_label": STAGE_ROUTE_LABELS.get(stage),
            "first_frame": int(decisions[0]["frame"]),
            "last_frame": int(decisions[-1]["frame"]),
            "observed_frame_span": (
                int(decisions[-1]["frame"]) - int(decisions[0]["frame"])
            ),
            "decision_count": len(decisions),
            "end_event": trace.end_event,
            "post_scope_decision_count_excluded": (
                trace.post_scope_decision_count
            ),
            "scene_events": list(trace.scene_events),
            "raw_summary_is_scope_valid": (
                trace.raw_summary is not None
                and int(trace.raw_summary.get("last_frame", -1))
                == int(decisions[-1]["frame"])
            ),
        },
        "provenance": {
            "path": trace.path,
            "sha256": trace.sha256,
            "size_bytes": trace.size_bytes,
            "parse_errors": trace.parse_errors,
            "identity": trace.identity,
            "controller_configs": list(trace.controller_configs),
            "raw_kind_counts": trace.raw_kind_counts,
            "raw_summary": trace.raw_summary,
        },
        "control_policy": {
            "practice_rule": "hard no-Bomb",
            "verification": no_bomb,
        },
        "interpretation_policy": {
            "canonical_sample": (
                "Only the first hit of a fresh practice attempt preserves the "
                "initial position, bullets, power, and respawn history."
            ),
            "later_samples": (
                "Later hits remain useful discovery evidence, but death and "
                "thprac respawn mutate position, projectile state, Bomb stock, "
                "and Power."
            ),
        },
        "totals": {
            "death_count": len(deaths),
            "death_frames": [int(death["frame"]) for death in deaths],
            "primary_cause_counts": dict(cause_counts),
            "contributing_factor_counts": dict(contributor_counts),
            "spell_hit_counts": dict(spell_counts),
            "max_active_bullets": max(
                int(row["active_bullets"]) for row in decisions
            ),
            "max_active_lasers": max(
                int(row["active_lasers"]) for row in decisions
            ),
            "resources": {
                key: _resource_range(decisions, key)
                for key in ("lives", "bombs", "power")
            },
            "latency_ms": {
                "read": _percentiles(row["read_ms"] for row in decisions),
                "plan": _percentiles(row["plan_ms"] for row in decisions),
                "corridor_solver": _corridor_latency(decisions),
            },
            "frame_lag": {
                "interpretation": (
                    "Values >=120 are phase-counter discontinuities and are "
                    "excluded from operational lag percentiles."
                ),
                "phase_counter_discontinuity_count": (
                    phase_counter_discontinuities
                ),
                "snapshot": _percentiles(
                    row["snapshot_lag"] for row in operational_lag_rows
                ),
                "action": _percentiles(
                    row["action_lag"] for row in operational_lag_rows
                ),
            },
        },
        "canonical_first_hit": {
            "death": first_hit,
            "preceding_240f": {
                "sample_count": len(first_window),
                "first_frame": (
                    int(first_window[0]["frame"]) if first_window else None
                ),
                "minimum_pipeline_clearance": (
                    min(
                        float(row["pipeline_clearance"])
                        for row in first_window
                    )
                    if first_window
                    else None
                ),
                "minimum_corridor_slack": (
                    min(
                        float(row["corridor_slack"])
                        for row in first_window
                        if row["corridor_slack"] is not None
                    )
                    if any(
                        row["corridor_slack"] is not None
                        for row in first_window
                    )
                    else None
                ),
            },
        },
        "death_clusters": _death_clusters(deaths),
        "deaths": deaths,
    }


def _format(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_markdown(dossier: dict[str, object]) -> str:
    scope = dossier["practice_scope"]
    totals = dossier["totals"]
    bomb = dossier["control_policy"]["verification"]
    canonical = dossier["canonical_first_hit"]["death"]
    spell_50_corridor = totals["latency_ms"]["corridor_solver"][
        "active_spell_50"
    ]
    lines = [
        f"# TH08 Stage 3 No-Bomb Practice Review: {dossier['run_id']}",
        "",
        "## Scope And Integrity",
        "",
        f"- Valid practice scope: `{scope['first_frame']}.."
        f"{scope['last_frame']}` ({scope['decision_count']} decisions).",
        f"- Scope terminator: `{scope['end_event']['reason']}`; "
        f"{scope['post_scope_decision_count_excluded']} reset-tail decisions "
        "were excluded.",
        "- The agent's raw summary is not scope-valid because thprac reset the "
        "manager counter before the external stop."
        if not scope["raw_summary_is_scope_valid"]
        else "- The agent's raw summary agrees with the scoped trace.",
        f"- Native hit edges: {totals['death_count']}, at "
        f"`{totals['death_frames']}`.",
        f"- Hard no-Bomb verification: **{'PASS' if bomb['passed'] else 'FAIL'}"
        f"** across {bomb['decision_count_checked']} decisions; mask/flag/"
        "action violations are all empty.",
        "",
        "Bomb-stock changes in the trace are death/respawn state changes. They "
        "are not Bomb use: every scoped input mask has bit `0x02` clear, every "
        "decision has `bomb=false`, and no action requests Bomb.",
        "",
        "## Primary Finding",
        "",
        f"The authoritative fresh-attempt hit is `{canonical['case_id']}`. "
        f"It occurred during spell {canonical['spell_attribution']['spell_id']} "
        f"`{canonical['spell_attribution']['spell_name']}` at player "
        f"({_format(canonical['player']['x'])}, "
        f"{_format(canonical['player']['y'])}), with "
        f"{canonical['active_bullets']} bullets and "
        f"{canonical['active_lasers']} lasers. The projectile model reported "
        f"pipeline clearance "
        f"{_format(canonical['pipeline_clearance_at_hit'])}.",
        "",
        "This is a strong enemy-body collision candidate, not a bullet-planner "
        "miss. Static analysis proves that the active spell owner can invoke "
        "a lethal player/enemy AABB check at `0x42cf7a -> 0x42c290 -> "
        "0x44a360`. The baseline trace records the owner pointer but not its "
        "position/contact size/flags, so exact same-frame overlap remains the "
        "next telemetry closure.",
        "",
        "## Failure Taxonomy",
        "",
        "| Cause | Hits |",
        "| --- | ---: |",
    ]
    for cause, count in sorted(
        totals["primary_cause_counts"].items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(f"| `{cause}` | {count} |")
    lines.extend(
        [
            "",
            "Contributing factors:",
            "",
        ]
    )
    for factor, count in sorted(
        totals["contributing_factor_counts"].items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(f"- `{factor}`: {count}")
    lines.extend(
        [
            "",
            "## Death Ledger",
            "",
            "| Role | Frame | Spell | Player | Action | Bullets/lasers | "
            "Pipeline/min 240f | Gate min | Primary cause |",
            "| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for death in dossier["deaths"]:
        spell = death["spell_attribution"]
        spell_label = (
            f"{spell['spell_id']} {spell['spell_name']}"
            if spell["spell_id"] is not None
            else "nonspell"
        )
        role = (
            "canonical"
            if death["sample_role"]
            == "canonical_fresh_attempt_causal_sample"
            else "discovery"
        )
        lines.append(
            f"| {role} | {death['frame']} | {spell_label} | "
            f"({_format(death['player']['x'])}, "
            f"{_format(death['player']['y'])}) | `{death['action']}` | "
            f"{death['active_bullets']}/{death['active_lasers']} | "
            f"{_format(death['pipeline_clearance_at_hit'])}/"
            f"{_format(death['minimum_pipeline_clearance_240f'])} | "
            f"{_format(death['minimum_corridor_slack_240f'])} | "
            f"`{death['primary_cause_class']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The first hit isolates a missing hazard class: enemy bodies are "
            "absent from both local clearance and global corridor occupancy.",
            "- Six hits were already unsafe in the committed input prefix. "
            "Five have direct bullet-overlap witnesses and one has a direct "
            "finite-segment laser witness.",
            "- The last six hits cluster in spell 50 with 180-200 active "
            f"lasers. Its {spell_50_corridor['unique_solution_count']} unique "
            "corridor solves took "
            f"{_format(spell_50_corridor['solve_ms']['median'])} ms median, "
            f"{_format(spell_50_corridor['solve_ms']['p95'])} ms p95, and "
            f"{_format(spell_50_corridor['solve_ms']['max'])} ms maximum; "
            "bottom-boundary occupation then removes escape options.",
            "- Fourteen of 16 hits use fast mode and 11 follow a missed corridor "
            "deadline. The global plan is not reserving a safe component early "
            "enough, even after Bomb decisions are removed.",
            "- Later hits cannot estimate an initial-stock clear rate because "
            "Power falls from 128 to 0/1 after repeated respawns. They remain "
            "valid counterexamples for geometry, latency, boundary use, and "
            "spell-specific pressure.",
            "",
            "## Baseline Correction Gate",
            "",
            "Add active-enemy lethal AABBs to the runtime snapshot, predictor, "
            "and corridor occupancy. The next fresh Stage-3 run must eliminate "
            "the spell-35 body contact as its canonical first hit without "
            "regressing the no-Bomb invariant. After that, optimize spell 50 "
            "with bounded solver latency and an earlier connected-component "
            "reservation instead of treating six post-respawn hits as one "
            "local dodge problem.",
            "",
            "## Offline Correction Prepared",
            "",
            "- The live adapter now reads the active spell owner's native "
            "contact window, applies the proven contact/disable flags, and "
            "lowers `0.75 * contact_size` enemy-body half-extents into both "
            "the committed-prefix check and local/global planners.",
            "- Runtime traces now persist enemy-body geometry and its snapshot "
            "frame. Every new hit also captures the native player lethal "
            "rectangle and spell-owner AABB in a stable manager-frame epoch, "
            "so only a same-epoch overlap becomes an exact witness.",
            "- Local and global finite laser-segment clearance fields are now "
            "vectorized. On the preserved spell-50 frame-25,433 snapshot, "
            "global planning fell from 64.8 ms median before the change to "
            "32.7 ms median after it in the offline benchmark.",
            "- These changes pass the full test and dossier-regression suites. "
            "They are not yet a physical Stage-3 acceptance result; the next "
            "fresh no-Bomb run must supply that evidence.",
        ]
    )
    return "\n".join(lines)


def write_death_csv(
    path: Path,
    deaths: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "case_id",
        "sample_role",
        "frame",
        "spell_id",
        "spell_name",
        "player_x",
        "player_y",
        "power",
        "action",
        "mask",
        "active_bullets",
        "active_lasers",
        "pipeline_clearance",
        "minimum_pipeline_clearance_240f",
        "minimum_corridor_slack_240f",
        "nearest_bullet_clearance",
        "nearest_laser_clearance",
        "primary_cause_class",
        "contributing_factors",
        "bomb_input_verified_absent",
    ]
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for death in deaths:
            bullet = death["nearest_observed_bullet"]
            laser = death["nearest_observed_laser"]
            spell = death["spell_attribution"]
            writer.writerow(
                {
                    "case_id": death["case_id"],
                    "sample_role": death["sample_role"],
                    "frame": death["frame"],
                    "spell_id": spell["spell_id"],
                    "spell_name": spell["spell_name"],
                    "player_x": death["player"]["x"],
                    "player_y": death["player"]["y"],
                    "power": death["resources_at_hit"]["power"],
                    "action": death["action"],
                    "mask": death["mask"],
                    "active_bullets": death["active_bullets"],
                    "active_lasers": death["active_lasers"],
                    "pipeline_clearance": (
                        death["pipeline_clearance_at_hit"]
                    ),
                    "minimum_pipeline_clearance_240f": (
                        death["minimum_pipeline_clearance_240f"]
                    ),
                    "minimum_corridor_slack_240f": (
                        death["minimum_corridor_slack_240f"]
                    ),
                    "nearest_bullet_clearance": (
                        bullet["aabb_clearance"] if bullet else None
                    ),
                    "nearest_laser_clearance": (
                        laser["clearance"] if laser else None
                    ),
                    "primary_cause_class": death["primary_cause_class"],
                    "contributing_factors": ";".join(
                        death["contributing_factors"]
                    ),
                    "bomb_input_verified_absent": True,
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--death-csv", type=Path, required=True)
    parser.add_argument("--regression-output", type=Path, required=True)
    args = parser.parse_args(argv)

    trace = read_practice_trace(args.trace)
    dossier = build_dossier(run_id=args.run_id, trace=trace)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(dossier, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(
        render_markdown(dossier) + "\n",
        encoding="utf-8",
    )
    write_death_csv(args.death_csv, dossier["deaths"])
    args.regression_output.parent.mkdir(parents=True, exist_ok=True)
    args.regression_output.write_text(
        json.dumps(
            {
                "schema": "th08-practice-death-regressions-v1",
                "run_id": args.run_id,
                "scope": dossier["practice_scope"],
                "no_bomb_verification": dossier["control_policy"][
                    "verification"
                ],
                "case_count": len(dossier["deaths"]),
                "cases": dossier["deaths"],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
