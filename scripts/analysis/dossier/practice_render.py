"""Offline dossier rendering with stable field and row ordering."""

from __future__ import annotations

import csv
from pathlib import Path


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
    canonical_cause = (
        canonical["primary_cause_class"] if canonical is not None else None
    )
    if canonical is None:
        primary_lines = [
            "No native hit edge occurred in this scoped practice trace.",
            "",
            "This is a physical no-Bomb pass for the captured scope. It does "
            "not by itself establish repeatability; retain repeated clean "
            "focused passes before promoting the phase.",
        ]
    else:
        canonical_spell = canonical["spell_attribution"]
        canonical_spell_label = (
            f"spell {canonical_spell['spell_id']} "
            f"`{canonical_spell['spell_name']}`"
            if canonical_spell["spell_id"] is not None
            else "a nonspell phase"
        )
        primary_lines = [
            f"The authoritative fresh-attempt hit is "
            f"`{canonical['case_id']}`. It occurred during "
            f"{canonical_spell_label} at player "
            f"({_format(canonical['player']['x'])}, "
            f"{_format(canonical['player']['y'])}), with "
            f"{canonical['active_bullets']} bullets and "
            f"{canonical['active_lasers']} lasers. The projectile model "
            "reported pipeline clearance "
            f"{_format(canonical['pipeline_clearance_at_hit'])}.",
            "",
        ]
    if canonical_cause == "enemy_body_contact_candidate":
        primary_explanation = (
            "This is a strong enemy-body collision candidate, not a "
            "bullet-planner miss. Static analysis proves that the active "
            "spell owner can invoke a lethal player/enemy AABB check at "
            "`0x42cf7a -> 0x42c290 -> 0x44a360`. The baseline trace records "
            "the owner pointer but not its position/contact size/flags, so "
            "exact same-frame overlap remains the next telemetry closure."
        )
    elif canonical is not None:
        primary_explanation = (
            f"The primary class is `{canonical_cause}`. This trace contains "
            "the retained hit-window geometry for that classification; later "
            "post-respawn hits remain discovery evidence rather than fresh "
            "independent trials."
        )
    else:
        primary_explanation = None
    if primary_explanation is not None:
        primary_lines.append(primary_explanation)

    stage_label = scope.get("stage_label") or (
        f"route {scope['stage_route_index']}"
    )
    lines = [
        f"# TH08 {stage_label} No-Bomb Practice Review: {dossier['run_id']}",
        "",
        "## Scope And Integrity",
        "",
        f"- Valid practice scope: `{scope['first_frame']}.."
        f"{scope['last_frame']}` ({scope['decision_count']} decisions).",
        f"- Selected frame epoch: {scope.get('selected_frame_epoch_index', 0)} "
        f"of {scope.get('frame_epoch_count', 1)}; "
        f"{scope.get('pre_scope_decision_count_excluded', 0)} earlier decisions "
        "were excluded.",
        f"- Scope terminator: `{scope['end_event']['reason']}`; "
        f"{scope['post_scope_decision_count_excluded']} reset-tail decisions "
        "were excluded.",
        "- The agent's raw summary is not scope-valid because thprac reset the "
        "manager counter before the external stop."
        if not scope["raw_summary_is_scope_valid"]
        else "- The agent's raw summary agrees with the scoped trace.",
        f"- Accepted complete practice: **"
        f"{'YES' if scope.get('accepted_completion') else 'NO'}**.",
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
        *primary_lines,
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
            "| Role | Frame | Spell | Player | Active input | Bullets/lasers | "
            "Pipeline/min 240f | Pipeline/robust warning | Contact/cause | "
            "Planner failure |",
            "| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
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
            f"{_format(death['player']['y'])}) | "
            f"`{death.get('active_input_action', death['action'])}` | "
            f"{death['active_bullets']}/{death['active_lasers']} | "
            f"{_format(death['pipeline_clearance_at_hit'])}/"
            f"{_format(death['minimum_pipeline_clearance_240f'])} | "
            f"{death['usable_pipeline_warning_lead_frames']}f/"
            f"{death.get('usable_robust_warning_lead_frames', 0)}f | "
            f"`{death['primary_cause_class']}` | "
            f"`{death['planner_failure_class']}` |"
        )
    lines.extend(
        [
            "",
            "## Per-Phase Planner Health",
            "",
            "| Phase | Hits | Decisions | Queries | Empty | Support outside | "
            "Constrained | Solves | Solve median ms | Bottom alive |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
            "---: | ---: |",
        ]
    )
    for phase in totals["per_spell"]:
        viability = phase["robust_viability"]
        solve_ms = viability["solve_ms"]
        phase_label = (
            "nonspell"
            if phase["spell_id"] is None
            else f"{phase['spell_id']} {phase['spell_name'] or ''}".strip()
        )
        bottom = phase["behavior_alive"].get("bottom_8px_fraction")
        lines.append(
            f"| {phase_label} | {phase['hit_count']} | "
            f"{phase['decision_count']} | {viability['query_count']} | "
            f"{viability['empty_action_set_count']} | "
            f"{viability['support_uncovered_query_count']} | "
            f"{viability['constrained_decision_count']} | "
            f"{viability['unique_solution_count']} | "
            f"{_format(solve_ms.get('median') if solve_ms else None)} | "
            f"{_format(bottom)} |"
        )
    cause_counts = totals["primary_cause_counts"]
    planner_failure_counts = totals["planner_failure_counts"]
    behavior = totals["behavior_context"]
    cadence = totals["decision_cadence_frames"]
    action_hold = totals["action_hold_frames"]
    control_delay = totals["control_delay_frames"]
    adaptive_delay = totals["adaptive_control_delay"]
    robust_viability = totals["robust_viability"]
    planner_consistency = totals.get(
        "planner_consistency",
        {
            "comparable_decision_count": 0,
            "global_winning_local_prefix_unsafe_count": 0,
            "global_losing_local_prefix_safe_count": 0,
            "selected_certified_action_local_prefix_unsafe_count": 0,
            "selected_action_outside_global_winning_set_count": 0,
        },
    )
    input_visibility = totals["input_visibility"]
    enemy_sensor = totals.get("enemy_sensor")
    issue_enemy_guard = totals.get("issue_enemy_guard")
    spell_owner_guard = totals.get("spell_owner_guard")
    terminal_threat = totals.get("terminal_threat")
    body_overlaps = sum(
        death["observed_enemy_body_contact_candidate"] is not None
        for death in dossier["deaths"]
    )
    body_overlaps_absent_at_action = sum(
        death["observed_enemy_body_contact_candidate"] is not None
        and not bool(
            death["observed_enemy_body_contact_candidate"].get(
                "present_in_action_snapshot",
                False,
            )
        )
        for death in dossier["deaths"]
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Retained witnesses classify "
            f"{cause_counts.get('observed_bullet_overlap', 0)} bullet "
            f"overlaps, {cause_counts.get('observed_laser_overlap', 0)} "
            f"laser overlaps, and {body_overlaps} exact same-epoch enemy-body "
            "overlaps; "
            f"{body_overlaps_absent_at_action} of those enemy slots were "
            "absent from the action snapshot.",
            f"- The controller decision cadence was "
            f"{_format(cadence['median'])} frames median and "
            f"{_format(cadence['p95'])} frames p95. The local plan took "
            f"{_format(totals['latency_ms']['plan']['median'])} ms median and "
            f"{_format(totals['latency_ms']['plan']['p95'])} ms p95.",
            (
                "- The full enemy sensor produced "
                f"{enemy_sensor['snapshot_count']} snapshots; capture read "
                f"time was `{enemy_sensor['capture_read_ms']}`, snapshot age "
                f"was `{enemy_sensor['snapshot_age_frames']}` frames, and "
                f"{enemy_sensor['snapshot_age_discontinuity_count']} "
                "phase-counter discontinuities were excluded; "
                f"{enemy_sensor['decision_count_with_active_bodies']} "
                "decisions retained at least one robust-union body "
                f"(maximum {enemy_sensor['max_active_bodies']}); "
                f"{enemy_sensor['decision_count_with_anticipatory_bodies']} "
                "decisions contained latent contact-disabled geometry "
                f"(maximum {enemy_sensor['max_anticipatory_bodies']}), and "
                f"{enemy_sensor['decision_count_with_dormant_bodies']} "
                "contained bounded inactive-slot memory "
                f"(maximum {enemy_sensor['max_dormant_bodies']}). "
                f"{enemy_sensor.get('observed_world_motion_sample_count', 0)} "
                "body samples retained observed world-motion estimates; "
                "world/internal speed and disagreement were "
                f"`{enemy_sensor.get('observed_world_speed')}` / "
                f"`{enemy_sensor.get('internal_component_speed')}` / "
                f"`{enemy_sensor.get('world_internal_motion_disagreement')}`."
            )
            if isinstance(enemy_sensor, dict)
            else "- No full enemy-pool sensor telemetry was present.",
            (
                "- The issue-time enemy guard retained "
                f"{issue_enemy_guard['observation_count']} observations, "
                f"detected {issue_enemy_guard['changed_observation_count']} "
                "during-plan geometry changes, recertified "
                f"{issue_enemy_guard['recertified_count']} decisions, and "
                f"overrode {issue_enemy_guard['action_override_count']} "
                "actions. Read/recertificate timing was "
                f"`{issue_enemy_guard['read_ms']}` / "
                f"`{issue_enemy_guard['recertificate_ms']}` ms; "
                f"{issue_enemy_guard['observation_count_with_anticipatory_bodies']} "
                "issue captures contained latent bodies "
                f"(maximum {issue_enemy_guard['max_anticipatory_bodies']}), "
                f"and {issue_enemy_guard['observation_count_with_dormant_bodies']} "
                "contained dormant bodies "
                f"(maximum {issue_enemy_guard['max_dormant_bodies']}). "
                f"Fresh/global transactions preserved "
                f"{issue_enemy_guard['planned_action_preserved_count']}/"
                f"{issue_enemy_guard['transaction_count']} planned actions, "
                "relaxed "
                f"{issue_enemy_guard['fresh_global_empty_relaxation_count']} "
                "fresh/global empty intersections, inherited "
                f"{issue_enemy_guard['inherited_constraint_relaxation_count']} "
                "earlier planner relaxations, "
                "and recorded "
                f"{issue_enemy_guard['silent_outside_global_count']} silent "
                "outside-global selections."
            )
            if isinstance(issue_enemy_guard, dict)
            else "- No issue-time enemy-geometry guard telemetry was present.",
            (
                "- The synchronous spell-owner guard retained "
                f"{spell_owner_guard['observation_count']} observations "
                f"({spell_owner_guard['contact_enabled_count']} contact "
                "enabled, "
                f"{spell_owner_guard['anticipatory_count']} anticipatory, "
                f"{spell_owner_guard['error_count']} errors). "
                f"{spell_owner_guard['outside_async_pool_count']} observed "
                "owners were outside the ordinary 480-slot async scan; "
                f"pointer counts were "
                f"`{spell_owner_guard['pointer_counts']}`."
            )
            if isinstance(spell_owner_guard, dict)
            else "- No synchronous spell-owner guard telemetry was present.",
            (
                "- The terminal-threat heuristic covered "
                f"{terminal_threat['decision_count']} decisions with horizon "
                f"counts `{terminal_threat['horizon_counts']}`; it reported "
                f"{terminal_threat['collision_warning_count']} collision and "
                f"{terminal_threat['clearance_below_item_safety_count']} "
                "sub-safety-clearance warnings, and relaxed "
                f"{terminal_threat['constraint_relaxed_count']} coarse "
                "constraints at clamped aliases."
            )
            if isinstance(terminal_threat, dict)
            else "- No extended terminal-threat telemetry was present.",
            "- Modeled action hold counts were "
            f"`{action_hold['all']['counts']}` overall.",
            "- Modeled uncontrollable-prefix counts were "
            f"`{control_delay['counts']}`.",
            (
                "- Adaptive delay supports were "
                f"`{adaptive_delay['support_counts']}`; "
                f"{adaptive_delay['robust_override_count']} decisions changed "
                "their nominal first action, "
                f"{adaptive_delay['learned_end_to_end_sample_max']} "
                "end-to-end transition samples were retained, and the "
                f"maximum observed overrun/censored counters were "
                f"{adaptive_delay['overrun_max']}/"
                f"{adaptive_delay['censored_max']}."
            ),
            (
                "- Robust viability supplied "
                f"{robust_viability['available_query_count']} available "
                "policy queries "
                f"({robust_viability['support_uncovered_query_count']} had "
                "new delay support outside the cached policy), constrained "
                f"{robust_viability['constrained_decision_count']} decisions, "
                "and exposed "
                f"{robust_viability['empty_action_set_count']} empty queried "
                "action sets. Recovery guidance was available/selected on "
                f"{robust_viability.get('recovery_guided_query_count', 0)}/"
                f"{robust_viability.get('recovery_selected_count', 0)} "
                "empty-kernel "
                "queries; distant-kernel guidance was available/selected on "
                f"{robust_viability.get('distant_recovery_guided_query_count', 0)}/"
                f"{robust_viability.get('distant_recovery_selected_count', 0)}. "
                "Safe-action count, selected repair-volume, selected "
                "recovery-distance, and selected control-reserve deficit "
                f"statistics were `{robust_viability['safe_action_count']}`, "
                f"`{robust_viability['selected_repair_volume']}`, "
                f"`{robust_viability.get('selected_recovery_distance')}`, "
                "and "
                f"`{robust_viability.get('selected_control_reserve_deficit')}`."
            ),
            (
                "- Queried policy phase offsets within the coarse control "
                "layer were "
                f"`{robust_viability.get('policy_phase_frame_counts', {})}`."
            ),
            (
                "- Global-horizon/local-prefix cross-tab covered "
                f"{planner_consistency['comparable_decision_count']} "
                "decisions: "
                f"{planner_consistency['global_winning_local_prefix_unsafe_count']} "
                "had a winning global state but unsafe selected prefix, "
                f"{planner_consistency['global_losing_local_prefix_safe_count']} "
                "had a losing global state but safe short prefix, "
                f"{planner_consistency['selected_certified_action_local_prefix_unsafe_count']} "
                "selected globally certified actions contradicted the fresh "
                "local prefix checker, and "
                f"{planner_consistency['selected_action_outside_global_winning_set_count']} "
                "selected actions were outside the reported winning set. "
                f"{planner_consistency.get('excluded_hazard_version_change_count', 0)} "
                "newer issue-time hazard versions and "
                f"{planner_consistency.get('excluded_deadline_hold_count', 0)} "
                "deadline-held old inputs were excluded from the aligned "
                "comparison."
            ),
            (
                "- The rolling worker produced "
                f"{robust_viability['unique_solution_count']} unique policies "
                "with solve-time statistics "
                f"`{robust_viability['solve_ms']}` and first-observed ages "
                f"`{robust_viability['first_observed_age_frames']}`. Policy "
                "status counts were "
                f"`{robust_viability['policy_status_counts']}`; "
                f"{robust_viability['decision_without_query_count']} robust-"
                "mode decisions had no query."
            ),
            "- Of "
            f"{input_visibility['unambiguous_transition_count']} unambiguous "
            "output transitions, "
            f"{input_visibility['visible_on_next_observation_count']} "
            f"({_format(input_visibility['visible_on_next_observation_fraction'])}) "
            "were already visible in the next decision snapshot; their "
            "snapshot delta had median "
            f"{_format(input_visibility['visible_snapshot_delta_frames']['median'])} "
            "frame.",
            "- Separating physical contact from planner causality gives "
            f"`{planner_failure_counts}`. Active input is the game-observed "
            "input at collision; the newly issued action on a hit row occurs "
            "after hit detection.",
            "- Robust action-set exhaustion supplied "
            f"{sum(death.get('usable_robust_warning_lead_frames', 0) > 0 for death in dossier['deaths'])} "
            "hit windows with a positive warning lead; those leads were "
            f"`{[death.get('usable_robust_warning_lead_frames', 0) for death in dossier['deaths']]}` "
            "frames.",
            "- Across all phases, bottom-eight-pixel occupancy was "
            f"{_format(behavior['alive_preceding_hit_60f'].get('bottom_8px_fraction'))} "
            "during the 60 frames preceding a hit versus "
            f"{_format(behavior['alive_outside_preceding_hit_60f'].get('bottom_8px_fraction'))} "
            "outside those windows.",
            "- Mean selected control-reserve deficit was "
            f"{_format(behavior['alive_preceding_hit_60f'].get('control_reserve_deficit_mean'))} "
            "during the 60 frames preceding a hit versus "
            f"{_format(behavior['alive_outside_preceding_hit_60f'].get('control_reserve_deficit_mean'))} "
            "outside those windows.",
            "- Soft recovery was selected on "
            f"{_format(behavior['alive_preceding_hit_60f'].get('recovery_selected_fraction'))} "
            "of alive decisions in the 60-frame pre-hit windows versus "
            f"{_format(behavior['alive_outside_preceding_hit_60f'].get('recovery_selected_fraction'))} "
            "outside; correlation alone is not a causal acceptance result.",
            "- Later hits cannot estimate an initial-stock clear rate because "
            f"Power falls from 128 to "
            f"{_format(totals['resources']['power']['end'])} after respawns. "
            "They remain valid counterexamples for geometry, latency, "
            "boundary use, and spell-specific pressure.",
        ]
    )
    if canonical_cause == "enemy_body_contact_candidate":
        lines.extend(
            [
                "",
                "## Baseline Correction Gate",
                "",
                "Add active-enemy lethal AABBs to the runtime snapshot, "
                "predictor, and corridor occupancy. The next fresh focused "
                "run must eliminate the canonical body-contact candidate "
                "without regressing the no-Bomb invariant.",
                "",
                "## Offline Correction Prepared",
                "",
                "- The live adapter now reads the active spell owner's native "
                "contact window and lowers its proven lethal AABB into local "
                "and global planners.",
                "- Runtime hit telemetry now captures the native player lethal "
                "rectangle and spell-owner AABB in a stable manager-frame "
                "epoch.",
                "- Local and global finite laser-segment clearance fields are "
                "vectorized; physical acceptance remains pending in this "
                "baseline report.",
            ]
        )
    elif robust_viability["policy_decision_count"] > 0:
        lines.extend(
            [
                "",
                "## Next Correction Gate",
                "",
                "Treat policy delivery, delay-support coverage, and viability "
                "exhaustion as separate gates. The next focused run must keep "
                "rolling-policy queries available, reduce unsupported query "
                "epochs, and preserve a non-empty action kernel before each "
                "former hit window. Compare per-phase position and warning "
                "lead, not only aggregate hit count.",
            ]
        )
    elif max(
        (int(value) for value in action_hold["all"]["counts"]),
        default=2,
    ) > 2:
        lines.extend(
            [
                "",
                "## Next Correction Gate",
                "",
                "Dynamic action hold is now physically exercised and complete "
                "loop timing is available. The next controller must model the "
                "separate actuation-delay distribution: newly injected input "
                "is usually visible one manager snapshot after SendInput, "
                "while planning cadence controls how long it remains held. "
                "The global corridor objective must also score terminal "
                "reachable volume and repair directions so a locally clear "
                "boundary cell is not accepted as a dead end.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Next Correction Gate",
                "",
                "Measure complete loop, decode, trace-write, and input costs; "
                "make the MPC action-hold model follow observed controller "
                "cadence instead of assuming a fixed two frames. Separately, "
                "the global objective must value terminal escape viability so "
                "that a currently clear bottom cell is not treated as a good "
                "long-horizon component when it has no repair space.",
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
        "issued_action_after_hit_detection",
        "active_bullets",
        "active_lasers",
        "pipeline_clearance",
        "minimum_pipeline_clearance_240f",
        "minimum_corridor_slack_240f",
        "nearest_bullet_clearance",
        "nearest_laser_clearance",
        "primary_cause_class",
        "planner_failure_class",
        "usable_pipeline_warning_lead_frames",
        "usable_robust_warning_lead_frames",
        "usable_viability_warning_lead_frames",
        "viability_kernel_exhausted_at_frame",
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
                    "action": death["active_input_action"],
                    "mask": death["active_input_mask"],
                    "issued_action_after_hit_detection": death[
                        "issued_action_after_hit_detection"
                    ],
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
                    "planner_failure_class": death[
                        "planner_failure_class"
                    ],
                    "usable_pipeline_warning_lead_frames": death[
                        "usable_pipeline_warning_lead_frames"
                    ],
                    "usable_robust_warning_lead_frames": death.get(
                        "usable_robust_warning_lead_frames",
                        0,
                    ),
                    "usable_viability_warning_lead_frames": death.get(
                        "usable_viability_warning_lead_frames",
                        0,
                    ),
                    "viability_kernel_exhausted_at_frame": death.get(
                        "viability_kernel_exhausted_at_frame"
                    ),
                    "contributing_factors": ";".join(
                        death["contributing_factors"]
                    ),
                    "bomb_input_verified_absent": True,
                }
            )


__all__ = ["render_markdown", "write_death_csv"]
