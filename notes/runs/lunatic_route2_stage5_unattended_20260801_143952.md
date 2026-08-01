# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_143952

## Scope And Integrity

- Valid practice scope: `1..44024` (10903 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[1888, 2625, 3809, 12975, 13629, 13975, 22860, 24153, 29090, 29598, 32010, 35599, 36038, 36835, 37619, 39740, 41838, 42878]`.
- Hard no-Bomb verification: **PASS** across 10903 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1888-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 312 bullets and 0 lasers. The projectile model reported pipeline clearance 9.210.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 3 |

Contributing factors:

- `playfield_boundary`: 14
- `fast_mode`: 11
- `action_lag_over_model`: 5
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1888 | nonspell | (376.000, 432.000) | `down_right` | 312/0 | 9.210/9.210 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2625 | nonspell | (332.909, 418.180) | `stay` | 274/0 | 11.160/4.485 | 0f/43f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 3809 | nonspell | (376.000, 373.800) | `up_left_fast` | 698/0 | 10.905/2.139 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 12975 | nonspell | (376.000, 432.000) | `down_right` | 28/0 | -2.241/-16.448 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 13629 | nonspell | (192.000, 384.000) | `stay` | 343/0 | -6.210/-29.041 | 231f/231f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13975 | nonspell | (376.000, 428.981) | `up_fast` | 336/0 | -4.282/-4.282 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22860 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 890/0 | -2.702/-2.702 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 24153 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 1070/0 | -2.076/-2.076 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 29090 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (206.122, 389.491) | `up_fast` | 1003/0 | -7.035/-7.035 | 11f/63f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29598 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (279.052, 432.000) | `right` | 993/0 | -6.972/-7.610 | 11f/26f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32010 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (35.090, 432.000) | `up` | 1020/0 | -5.726/-5.726 | 4f/37f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35599 | nonspell | (357.653, 428.747) | `left_fast` | 471/0 | -0.370/-0.370 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 36038 | nonspell | (376.000, 407.969) | `down_left_fast` | 453/0 | -2.840/-2.840 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 36835 | nonspell | (376.000, 385.389) | `left_fast` | 367/0 | -2.376/-2.376 | 5f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 37619 | nonspell | (23.168, 432.000) | `up` | 455/0 | -0.433/-0.433 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39740 | 111 懶惰「生神停止(マインドストッパー)」 | (207.971, 187.178) | `up_fast` | 339/0 | -0.033/-2.334 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41838 | 115 散符「真実の月(インビジブルフルムーン)」 | (368.000, 432.000) | `left_fast` | 1285/0 | 0.844/-1.719 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42878 | 115 散符「真実の月(インビジブルフルムーン)」 | (255.609, 429.172) | `up_left_fast` | 1090/0 | -0.544/-1.073 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 6879 | 20 | 10 | 0 | 22 | 5 | 1810.343 | 0.365 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 829 | 474 | 290 | 0 | 0 | 38 | 110.375 | 0.360 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 3 | 1126 | 1119 | 933 | 0 | 0 | 254 | 80.057 | 0.278 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1022 | 1015 | 566 | 0 | 0 | 177 | 71.442 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1047 | 1040 | 714 | 0 | 0 | 185 | 67.316 | 0.425 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 19.098 ms median and 32.559 ms p95.
- The full enemy sensor produced 6030 snapshots; capture read time was `{'median': 5.609400002867915, 'p95': 27.470900007756427, 'max': 291.8181999993976}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 112.0}` frames, and 18 phase-counter discontinuities were excluded; 10269 decisions retained at least one robust-union body (maximum 48); 7821 decisions contained latent contact-disabled geometry (maximum 48), and 3920 contained bounded inactive-slot memory (maximum 37). 381 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.649589538574219, 'max': 9.460580008370536}` / `{'median': 0.0, 'p95': 4.581655502319336, 'max': 4.707549571990967}` / `{'median': 0.0, 'p95': 3.834167957305908, 'max': 5.566324506487165}`.
- The issue-time enemy guard retained 10903 observations, detected 3161 during-plan geometry changes, recertified 3161 decisions, and overrode 54 actions. Read/recertificate timing was `{'median': 1.55570000060834, 'p95': 2.5889000098686665, 'max': 101.02010000264272}` / `{'median': 3.2223000016529113, 'p95': 6.937899976037443, 'max': 257.4542000074871}` ms; 7802 issue captures contained latent bodies (maximum 48), and 3927 contained dormant bodies (maximum 37). Fresh/global transactions preserved 3112/3166 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8608 observations (8582 contact enabled, 26 anticipatory, 0 errors). 8608 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8608}`.
- The terminal-threat heuristic covered 10903 decisions with horizon counts `{'0': 526, '10': 10377}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 687, '3': 6743, '4': 2463, '5': 903, '6': 107}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 469, '2': 1896, '3': 6142, '4': 2055, '5': 310, '6': 31}`.
- Adaptive delay supports were `{'1': 31, '1,2': 254, '1,2,3': 140, '1,2,3,4': 334, '1,2,3,4,5': 96, '1,2,3,4,5,6': 32, '2,3': 463, '2,3,4': 3088, '2,3,4,5': 2701, '2,3,4,5,6': 2311, '3,4': 5, '3,4,5': 10, '3,4,5,6': 1234, '4,5,6': 184, '6': 20}`; 294 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 44/180.
- Robust viability supplied 3668 available policy queries (0 had new delay support outside the cached policy), constrained 22 decisions, and exposed 2513 empty queried action sets. Recovery guidance was available/selected on 255/0 empty-kernel queries; distant-kernel guidance was available/selected on 1516/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 583, '1': 547, '2': 435, '3': 370, '4': 394, '5': 475, '6': 465, '7': 399}`.
- Global-horizon/local-prefix cross-tab covered 1306 decisions: 1 had a winning global state but unsafe selected prefix, 644 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 20 selected actions were outside the reported winning set. 1524 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 659 unique policies with solve-time statistics `{'median': 75.98910000524484, 'p95': 179.6920000051614, 'max': 1968.7115999986418}` and first-observed ages `{'median': 4.0, 'p95': 6.0, 'max': 94.0}`. Policy status counts were `{'queryable': 3658, 'expired': 337, 'pending_future_epoch': 88}`; 415 robust-mode decisions had no query.
- Of 5404 unambiguous output transitions, 5019 (0.929) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 2, 'robust_action_set_exhausted_before_hit': 9, 'late_collision_after_positive_causal_margin': 1, 'global_viability_kernel_exhausted_before_hit': 6}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 15 hit windows with a positive warning lead; those leads were `[0, 43, 0, 0, 231, 5, 3, 8, 63, 26, 37, 5, 5, 5, 8, 6, 10, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.502 during the 60 frames preceding a hit versus 0.320 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
