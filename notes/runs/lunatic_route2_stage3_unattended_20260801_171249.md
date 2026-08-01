# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260801_171249

## Scope And Integrity

- Valid practice scope: `1..27611` (7981 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 10, at `[594, 946, 2260, 3838, 7959, 8973, 14085, 15363, 23042, 26069]`.
- Hard no-Bomb verification: **PASS** across 7981 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F594-T1`. It occurred during a nonspell phase at player (182.242, 425.958), with 304 bullets and 0 lasers. The generated post-hit row reported pipeline clearance 39.825, but that row used the f566 hazard snapshot after a 28-frame synchronous issue gap.

The generated primary class `sensor_gap_or_unmodeled_hazard` is superseded by the retained causal reconstruction. Bullet slot 1 was already present at f566. With the unchanged focused `down_left` input, its signed AABB clearance is +1.972 at f586, -0.432 at f587, -1.742 at f588, and -2.553 at f589. The controller did not issue again until f594 because the constant-H80 delayed scan consumed 394.522 ms. This is a modeled computation-gap collision, not an absent hazard.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 3 |
| `sensor_gap_or_unmodeled_hazard` | 2 |

Contributing factors:

- `action_lag_over_model`: 6
- `fast_mode`: 5
- `corridor_deadline_miss`: 4
- `playfield_boundary`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 594 | nonspell | (182.242, 425.958) | `down_left` | 304/0 | 39.825/39.825 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 946 | nonspell | (173.264, 414.794) | `stay` | 425/0 | 37.614/2.461 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2260 | nonspell | (8.000, 432.000) | `stay` | 515/0 | -4.116/-4.116 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 3838 | nonspell | (33.456, 408.666) | `down_right_fast` | 199/0 | -1.705/-1.705 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 7959 | nonspell | (376.000, 432.000) | `down_right` | 478/0 | -5.155/-5.155 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 8973 | nonspell | (376.000, 427.121) | `down_left_fast` | 329/0 | -2.548/-2.548 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 14085 | nonspell | (86.927, 423.026) | `stay` | 277/0 | -1.839/-1.839 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 15363 | 38 始符「エフェメラリティ137」 | (11.253, 432.000) | `down_right_fast` | 192/0 | -2.304/-2.304 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23042 | nonspell | (259.692, 425.482) | `left_fast` | 90/0 | -1.799/-1.799 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 26069 | 50 虚史「幻想郷伝説」 | (223.304, 379.900) | `up_fast` | 297/200 | 1.068/1.068 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 3890 | 281 | 54 | 0 | 271 | 29 | 901.861 | 0.198 |
| 35 | 0 | 901 | 704 | 619 | 0 | 0 | 56 | 40.084 | 0.263 |
| 38 始符「エフェメラリティ137」 | 1 | 833 | 795 | 453 | 0 | 0 | 70 | 85.163 | 0.185 |
| 42 | 0 | 771 | 763 | 618 | 0 | 0 | 121 | 40.444 | 0.250 |
| 46 | 0 | 922 | 763 | 627 | 0 | 0 | 68 | 49.504 | 0.409 |
| 50 虚史「幻想郷伝説」 | 1 | 664 | 657 | 439 | 0 | 0 | 118 | 82.599 | 0.333 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 16.871 ms median and 31.811 ms p95.
- The full enemy sensor produced 4150 snapshots; capture read time was `{'median': 5.575050003244542, 'p95': 20.93189998413436, 'max': 303.8151999935508}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 86.0}` frames, and 10 phase-counter discontinuities were excluded; 7792 decisions retained at least one robust-union body (maximum 30); 7342 decisions contained latent contact-disabled geometry (maximum 30), and 2322 contained bounded inactive-slot memory (maximum 15). 136 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.35882568359375, 'p95': 3.0336456298828125, 'max': 10.278031137254503}` / `{'median': 1.0, 'p95': 2.6167943477630615, 'max': 4.3623576164245605}` / `{'median': 3.993511199951172e-06, 'p95': 2.3004798889160156, 'max': 12.015749123361376}`.
- The issue-time enemy guard retained 7981 observations, detected 1084 during-plan geometry changes, recertified 1084 decisions, and overrode 14 actions. Read/recertificate timing was `{'median': 1.5386999875772744, 'p95': 2.68470001174137, 'max': 83.79920001607388}` / `{'median': 2.21649999730289, 'p95': 8.432400005403906, 'max': 208.1117999914568}` ms; 7344 issue captures contained latent bodies (maximum 30), and 2332 contained dormant bodies (maximum 15). Fresh/global transactions preserved 1074/1089 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 6752 observations (6685 contact enabled, 67 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005A1DA0': 1707, '0x005D63C0': 5045}`.
- The terminal-threat heuristic covered 7981 decisions with horizon counts `{'0': 22, '10': 7959}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 51, '3': 6693, '4': 489, '5': 453, '6': 295}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 26, '2': 163, '3': 7462, '4': 189, '5': 139, '6': 2}`.
- Adaptive delay supports were `{'1,2': 25, '1,2,3': 5, '1,2,3,4': 52, '1,2,3,4,5': 31, '1,2,3,4,5,6': 32, '2,3': 437, '2,3,4': 2494, '2,3,4,5': 2397, '2,3,4,5,6': 2373, '3,4': 1, '3,4,5': 13, '3,4,5,6': 107, '4,5': 5, '4,5,6': 1, '5,6': 7, '6': 1}`; 21 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 25/122.
- Robust viability supplied 3963 available policy queries (0 had new delay support outside the cached policy), constrained 271 decisions, and exposed 2810 empty queried action sets. Recovery guidance was available/selected on 691/0 empty-kernel queries; distant-kernel guidance was available/selected on 1843/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 638, '1': 522, '2': 426, '3': 473, '4': 432, '5': 509, '6': 516, '7': 447}`.
- Global-horizon/local-prefix cross-tab covered 3006 decisions: 0 had a winning global state but unsafe selected prefix, 2189 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 81 selected actions were outside the reported winning set. 531 newer issue-time hazard versions and 4 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 462 unique policies with solve-time statistics `{'median': 58.5251500015147, 'p95': 181.15059999399818, 'max': 2342.756600002758}` and first-observed ages `{'median': 3.0, 'p95': 7.0, 'max': 143.0}`. Policy status counts were `{'pending_future_epoch': 149, 'queryable': 3938, 'expired': 1297}`; 1421 robust-mode decisions had no query.
- Of 4766 unambiguous output transitions, 4548 (0.954) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 2, 'missing_pre_hit_alive_decision': 1, 'late_collision_after_positive_causal_margin': 4, 'robust_action_set_exhausted_before_hit': 1, 'global_viability_kernel_exhausted_before_hit': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 3 hit windows with a positive warning lead; those leads were `[0, 0, 0, 0, 0, 6, 0, 7, 0, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.371 during the 60 frames preceding a hit versus 0.246 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 15.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Source delivery passed the canonical narrow gate: the f354..594 window contained 13 full-H268 roots and exact prepublication authority on 43/50 decisions. The next focused gate is causal computation safety. A long delayed scan may run only while an exact held-action certificate or compatible lease covers its complete issue-age support; otherwise it must not block input delivery. The bounded terminal probe should evaluate current-kernel high-repair alternatives before fixed compass defaults, but those candidates remain non-authoritative until their own prefix and terminal predecessor pass.
