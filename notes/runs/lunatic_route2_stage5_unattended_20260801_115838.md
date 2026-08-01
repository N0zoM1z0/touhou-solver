# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_115838

## Scope And Integrity

- Valid practice scope: `2..45606` (11128 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[1728, 2051, 2546, 3798, 6978, 11220, 11685, 12903, 13742, 23985, 25065, 31237, 33503, 36546, 41452, 43210, 43837, 44493]`.
- Hard no-Bomb verification: **PASS** across 11128 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1728-T1`. It occurred during a nonspell phase at player (113.504, 429.742), with 328 bullets and 0 lasers. The projectile model reported pipeline clearance 36.303.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `sensor_gap_or_unmodeled_hazard` | 4 |
| `observed_bullet_overlap` | 3 |

Contributing factors:

- `playfield_boundary`: 14
- `fast_mode`: 12
- `pool_density_over_1000`: 6
- `action_lag_over_model`: 5
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1728 | nonspell | (113.504, 429.742) | `down_right` | 328/0 | 36.303/11.915 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2051 | nonspell | (192.000, 384.000) | `stay` | 527/0 | -1.385/-1.385 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 2546 | nonspell | (192.000, 432.000) | `down_fast` | 298/0 | 8.645/8.645 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3798 | nonspell | (366.459, 432.000) | `down_right` | 554/0 | 5.705/2.171 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 6978 | nonspell | (359.342, 427.121) | `up_left_fast` | 599/0 | -2.217/-7.519 | 12f/22f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11220 | nonspell | (8.000, 432.000) | `up_fast` | 924/0 | -2.076/-7.544 | 0f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11685 | nonspell | (153.423, 432.000) | `up_fast` | 872/0 | -3.552/-4.070 | 25f/33f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12903 | nonspell | (376.000, 245.771) | `up_right_fast` | 327/0 | -2.004/-2.004 | 3f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13742 | nonspell | (65.496, 402.260) | `stay` | 398/0 | 12.183/3.614 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 23985 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 428.000) | `up_fast` | 1113/0 | -3.068/-3.068 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25065 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `down_fast` | 1035/0 | -0.784/-2.365 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31237 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (178.784, 432.000) | `up_right_fast` | 967/0 | -6.370/-6.370 | 13f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33503 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (89.720, 429.172) | `up_left_fast` | 1015/0 | -8.837/-8.837 | 22f/31f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36546 | nonspell | (8.000, 432.000) | `right_fast` | 370/0 | -2.184/-2.184 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 41452 | 111 懶惰「生神停止(マインドストッパー)」 | (216.188, 16.000) | `up_right` | 482/0 | -1.522/-1.522 | 12f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43210 | 115 散符「真実の月(インビジブルフルムーン)」 | (107.268, 429.700) | `up` | 1156/0 | -1.566/-2.340 | 0f/18f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43837 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 428.000) | `up_fast` | 1156/0 | -1.650/-1.650 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44493 | 115 散符「真実の月(インビジブルフルムーン)」 | (369.114, 429.172) | `up_right_fast` | 1151/0 | -2.498/-8.605 | 3f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 7141 | 25 | 14 | 0 | 23 | 6 | 1221.823 | 0.435 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 971 | 440 | 250 | 0 | 0 | 34 | 142.903 | 0.409 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 931 | 925 | 734 | 0 | 0 | 210 | 78.052 | 0.340 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1015 | 1009 | 651 | 0 | 0 | 178 | 70.574 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 1070 | 1062 | 712 | 0 | 0 | 186 | 68.275 | 0.349 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.711 ms median and 32.289 ms p95.
- The full enemy sensor produced 6186 snapshots; capture read time was `{'median': 5.21155001479201, 'p95': 27.0586000115145, 'max': 451.3341000129003}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 72.0}` frames, and 17 phase-counter discontinuities were excluded; 10628 decisions retained at least one robust-union body (maximum 42); 8138 decisions contained latent contact-disabled geometry (maximum 41), and 3871 contained bounded inactive-slot memory (maximum 36). 368 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.9400472640991211, 'p95': 4.2528076171875, 'max': 9.022945924238725}` / `{'median': 0.9673951268196106, 'p95': 3.7578277587890625, 'max': 5.050006866455078}` / `{'median': 3.732740879058838e-06, 'p95': 2.0090556144714355, 'max': 13.356428839943625}`.
- The issue-time enemy guard retained 11128 observations, detected 2964 during-plan geometry changes, recertified 2964 decisions, and overrode 50 actions. Read/recertificate timing was `{'median': 1.320450013736263, 'p95': 2.3951999901328236, 'max': 159.15880000102334}` / `{'median': 3.2631499925628304, 'p95': 6.907900009537116, 'max': 285.4877000208944}` ms; 8112 issue captures contained latent bodies (maximum 41), and 3875 contained dormant bodies (maximum 37). Fresh/global transactions preserved 2915/2966 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9084 observations (9058 contact enabled, 26 anticipatory, 0 errors). 9084 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9084}`.
- The terminal-threat heuristic covered 11128 decisions with horizon counts `{'0': 387, '10': 10741}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 430, '3': 7103, '4': 2674, '5': 788, '6': 133}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 287, '2': 1400, '3': 7444, '4': 1404, '5': 588, '6': 5}`.
- Adaptive delay supports were `{'1,2': 167, '1,2,3': 80, '1,2,3,4': 47, '1,2,3,4,5': 181, '1,2,3,4,5,6': 53, '2,3': 519, '2,3,4': 2797, '2,3,4,5': 3264, '2,3,4,5,6': 2659, '3,4': 43, '3,4,5': 31, '3,4,5,6': 1057, '4,5': 24, '4,5,6': 201, '6': 5}`; 250 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 27/115.
- Robust viability supplied 3461 available policy queries (0 had new delay support outside the cached policy), constrained 23 decisions, and exposed 2361 empty queried action sets. Recovery guidance was available/selected on 176/0 empty-kernel queries; distant-kernel guidance was available/selected on 1425/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 577, '1': 498, '2': 377, '3': 334, '4': 410, '5': 448, '6': 399, '7': 418}`.
- Global-horizon/local-prefix cross-tab covered 1293 decisions: 2 had a winning global state but unsafe selected prefix, 665 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 10 selected actions were outside the reported winning set. 1356 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 614 unique policies with solve-time statistics `{'median': 74.66595001460519, 'p95': 185.74099999386817, 'max': 3237.281100009568}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 86.0}`. Policy status counts were `{'queryable': 3450, 'expired': 500, 'pending_future_epoch': 116}`; 605 robust-mode decisions had no query.
- Of 5778 unambiguous output transitions, 5498 (0.952) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 3, 'missing_pre_hit_alive_decision': 1, 'global_viability_kernel_exhausted_before_hit': 9, 'robust_action_set_exhausted_before_hit': 5}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[0, 0, 0, 0, 22, 10, 33, 8, 0, 8, 7, 21, 31, 6, 19, 18, 7, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.612 during the 60 frames preceding a hit versus 0.368 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 3.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
