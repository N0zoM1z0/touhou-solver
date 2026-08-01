# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_040011

## Scope And Integrity

- Valid practice scope: `2..45781` (12035 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[2140, 2625, 3493, 10862, 11546, 12450, 13755, 14089, 23777, 25275, 31844, 33688, 34105, 36759, 38598, 40766, 42036, 43371]`.
- Hard no-Bomb verification: **PASS** across 12035 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2140-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 488 bullets and 0 lasers. The projectile model reported pipeline clearance -0.901.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 12 |
| `observed_bullet_overlap` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 2 |

Contributing factors:

- `fast_mode`: 14
- `playfield_boundary`: 14
- `pool_density_over_1000`: 4
- `action_lag_over_model`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2140 | nonspell | (376.000, 432.000) | `down_right` | 488/0 | -0.901/-0.901 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 2625 | nonspell | (376.000, 348.681) | `up_right` | 416/0 | 3.352/0.873 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3493 | nonspell | (8.000, 432.000) | `up_fast` | 983/0 | -2.457/-2.457 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 10862 | nonspell | (361.847, 432.000) | `up_right_fast` | 872/0 | -2.590/-4.045 | 4f/12f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11546 | nonspell | (348.004, 420.262) | `up_left_fast` | 880/0 | 0.493/-4.307 | 14f/16f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12450 | nonspell | (376.000, 432.000) | `up_fast` | 222/0 | -1.739/-1.739 | 0f/19f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13755 | nonspell | (327.917, 364.412) | `up_left_fast` | 389/0 | 12.521/2.670 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 14089 | nonspell | (8.000, 432.000) | `right` | 501/0 | -1.427/-1.427 | 0f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 23777 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_left_fast` | 1088/0 | -3.002/-3.002 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25275 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 1109/0 | -2.001/-2.001 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31844 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (242.480, 432.000) | `up_fast` | 1023/0 | -5.765/-5.765 | 8f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33688 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (10.695, 432.000) | `up_left_fast` | 994/0 | -6.086/-6.086 | 17f/51f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34105 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (208.148, 432.000) | `left_fast` | 1011/0 | -7.267/-7.267 | 4f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36759 | nonspell | (376.000, 432.000) | `up_left_fast` | 551/0 | -2.834/-2.834 | 2f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 38598 | nonspell | (376.000, 432.000) | `left_fast` | 457/0 | -2.774/-2.774 | 2f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 40766 | 111 懶惰「生神停止(マインドストッパー)」 | (229.785, 188.218) | `right_fast` | 346/0 | -1.620/-1.620 | 0f/24f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42036 | 111 懶惰「生神停止(マインドストッパー)」 | (191.779, 20.879) | `right_fast` | 501/0 | -1.340/-1.340 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43371 | 115 散符「真実の月(インビジブルフルムーン)」 | (160.179, 430.374) | `up_left` | 883/0 | -2.143/-2.143 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 8092 | 0 | 0 | 0 | 0 | 0 | - | 0.384 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 896 | 860 | 508 | 0 | 0 | 163 | 109.300 | 0.441 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 3 | 999 | 993 | 795 | 0 | 0 | 220 | 76.148 | 0.320 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1042 | 1036 | 517 | 0 | 0 | 180 | 78.739 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1006 | 999 | 722 | 0 | 0 | 183 | 64.656 | 0.521 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.662 ms median and 32.582 ms p95.
- The full enemy sensor produced 6654 snapshots; capture read time was `{'median': 5.382049996114802, 'p95': 26.479899999685585, 'max': 118.15730000671465}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 24.0}` frames, and 7 phase-counter discontinuities were excluded; 11404 decisions retained at least one robust-union body (maximum 49); 8927 decisions contained latent contact-disabled geometry (maximum 49), and 4215 contained bounded inactive-slot memory (maximum 36). 423 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.81353759765625, 'p95': 4.278419494628906, 'max': 9.311904907226562}` / `{'median': 0.8135315775871277, 'p95': 4.278415679931641, 'max': 5.061916351318359}` / `{'median': 4.371138828673793e-08, 'p95': 1.0000123977661133, 'max': 7.1535584926605225}`.
- The issue-time enemy guard retained 12035 observations, detected 3606 during-plan geometry changes, recertified 3606 decisions, and overrode 44 actions. Read/recertificate timing was `{'median': 1.6560999938519672, 'p95': 3.187099995557219, 'max': 66.91139999020379}` / `{'median': 3.123299997241702, 'p95': 6.4199999906122684, 'max': 99.67260000121314}` ms; 8901 issue captures contained latent bodies (maximum 49), and 4214 contained dormant bodies (maximum 37). Fresh/global transactions preserved 3562/3606 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9000 observations (8974 contact enabled, 26 anticipatory, 0 errors). 9000 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9000}`.
- The terminal-threat heuristic covered 12035 decisions with horizon counts `{'0': 536, '10': 11499}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 455, '3': 6956, '4': 2492, '5': 1549, '6': 583}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 132, '2': 381, '3': 8778, '4': 2188, '5': 556}`.
- Adaptive delay supports were `{'1,2': 154, '1,2,3': 69, '1,2,3,4': 152, '1,2,3,4,5': 156, '1,2,3,4,5,6': 243, '2,3': 379, '2,3,4': 2986, '2,3,4,5': 2662, '2,3,4,5,6': 3700, '3,4': 41, '3,4,5': 196, '3,4,5,6': 1242, '4,5,6': 55}`; 270 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 43/212.
- Robust viability supplied 3888 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 2542 empty queried action sets. Recovery guidance was available/selected on 211/0 empty-kernel queries; distant-kernel guidance was available/selected on 1514/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 659, '1': 556, '2': 429, '3': 376, '4': 466, '5': 463, '6': 494, '7': 445}`.
- Global-horizon/local-prefix cross-tab covered 1431 decisions: 1 had a winning global state but unsafe selected prefix, 721 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 19 selected actions were outside the reported winning set. 1663 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 746 unique policies with solve-time statistics `{'median': 78.16759999695932, 'p95': 175.80300000554416, 'max': 209.25060000445228}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 8.0}`. Policy status counts were `{'pending_future_epoch': 41, 'queryable': 3888, 'expired': 3}`; 44 robust-mode decisions had no query.
- Of 6274 unambiguous output transitions, 5864 (0.935) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'late_collision_after_positive_causal_margin': 1, 'unresolved_planner_failure': 2, 'robust_action_set_exhausted_before_hit': 7, 'global_viability_kernel_exhausted_before_hit': 8}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 15 hit windows with a positive warning lead; those leads were `[0, 0, 5, 12, 16, 19, 0, 9, 9, 8, 24, 51, 13, 4, 5, 24, 11, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.529 during the 60 frames preceding a hit versus 0.358 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
