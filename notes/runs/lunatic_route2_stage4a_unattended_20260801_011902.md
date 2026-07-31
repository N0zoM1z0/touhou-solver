# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_011902

## Scope And Integrity

- Valid practice scope: `1..45682` (12261 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 26, at `[796, 1233, 2158, 2627, 2948, 3608, 4206, 9319, 9818, 10448, 11610, 12061, 12882, 13723, 18720, 19854, 20584, 21732, 22301, 22906, 31652, 32103, 35449, 36070, 43270, 45395]`.
- Hard no-Bomb verification: **PASS** across 12261 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F796-T1`. It occurred during a nonspell phase at player (191.280, 425.489), with 293 bullets and 0 lasers. The projectile model reported pipeline clearance 20.159.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 9 |
| `sensor_gap_or_unmodeled_hazard` | 5 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 16
- `playfield_boundary`: 16
- `corridor_deadline_miss`: 9
- `action_lag_over_model`: 5
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 796 | nonspell | (191.280, 425.489) | `down` | 293/0 | 20.159/12.450 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 1233 | nonspell | (376.000, 386.109) | `up_right` | 182/0 | 3.959/3.959 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2158 | nonspell | (21.011, 428.747) | `left` | 366/0 | -0.023/-1.517 | 2f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 2627 | nonspell | (8.000, 432.000) | `up_right` | 564/0 | -3.201/-3.201 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 2948 | nonspell | (307.673, 426.632) | `right` | 630/0 | 5.756/1.430 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3608 | nonspell | (376.000, 432.000) | `down_right_fast` | 417/0 | 19.954/3.083 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4206 | nonspell | (364.982, 432.000) | `down` | 928/0 | -1.824/-1.824 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 9319 | nonspell | (376.000, 403.001) | `up_fast` | 702/0 | 0.299/-19.594 | 3f/19f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 9818 | nonspell | (376.000, 432.000) | `down` | 711/0 | -14.747/-14.747 | 11f/16f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 10448 | nonspell | (70.218, 432.000) | `left_fast` | 199/0 | 1.480/-5.679 | 2f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11610 | 57 夢境「二重大結界」 | (12.000, 432.000) | `right_fast` | 635/0 | -3.097/-3.097 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12061 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 607/0 | -1.787/-1.787 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12882 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 583/0 | -1.405/-1.405 | 3f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13723 | 57 夢境「二重大結界」 | (34.889, 346.017) | `up_fast` | 590/0 | 0.729/-0.115 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 18720 | 61 散霊「夢想封印　寂」 | (196.528, 426.447) | `up_left_fast` | 249/0 | -2.402/-2.402 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19854 | 61 散霊「夢想封印　寂」 | (109.441, 432.000) | `left_fast` | 274/0 | -2.444/-2.444 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20584 | 61 散霊「夢想封印　寂」 | (370.343, 422.343) | `up_fast` | 388/0 | -2.424/-11.726 | 9f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21732 | nonspell | (114.348, 420.552) | `stay` | 271/0 | 17.178/7.521 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 22301 | nonspell | (25.012, 414.703) | `up_right` | 688/0 | -2.071/-2.071 | 0f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22906 | nonspell | (376.000, 419.780) | `up_right` | 634/0 | -2.620/-2.620 | 0f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 31652 | 65 神技「八方龍殺陣」 | (305.366, 427.400) | `up_fast` | 1022/0 | 1.491/-5.930 | 4f/22f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32103 | 65 神技「八方龍殺陣」 | (10.828, 429.949) | `down_right_fast` | 1211/0 | -3.541/-3.541 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35449 | nonspell | (376.000, 424.000) | `up_fast` | 77/0 | 5.715/-1.988 | 2f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36070 | nonspell | (140.634, 432.000) | `left_fast` | 143/0 | -1.396/-1.396 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 43270 | 73 大結界「博麗弾幕結界」 | (210.161, 374.350) | `down_left_fast` | 1000/0 | -1.169/-1.169 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45395 | 73 大結界「博麗弾幕結界」 | (14.505, 132.243) | `up_right_fast` | 1344/0 | -2.530/-2.530 | 4f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 15 | 7162 | 481 | 105 | 0 | 422 | 31 | 367.345 | 0.225 |
| 57 夢境「二重大結界」 | 4 | 1147 | 1116 | 253 | 0 | 0 | 158 | 192.388 | 0.353 |
| 61 散霊「夢想封印　寂」 | 3 | 1042 | 1035 | 472 | 0 | 0 | 155 | 131.542 | 0.216 |
| 65 神技「八方龍殺陣」 | 2 | 925 | 745 | 601 | 0 | 0 | 85 | 63.905 | 0.352 |
| 69 | 0 | 1028 | 1022 | 705 | 0 | 0 | 172 | 93.297 | 0.234 |
| 73 大結界「博麗弾幕結界」 | 2 | 957 | 949 | 491 | 0 | 0 | 172 | 120.600 | 0.017 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.701 ms median and 30.803 ms p95.
- The full enemy sensor produced 6560 snapshots; capture read time was `{'median': 5.376249995606486, 'p95': 21.372000002884306, 'max': 193.04749999719206}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 87.0}` frames, and 5 phase-counter discontinuities were excluded; 11980 decisions retained at least one robust-union body (maximum 51); 6747 decisions contained latent contact-disabled geometry (maximum 51), and 4883 contained bounded inactive-slot memory (maximum 27). 499 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.8670997619628906, 'p95': 4.59869384765625, 'max': 7.766805013020833}` / `{'median': 2.8829078674316406, 'p95': 4.5351386070251465, 'max': 18.448631286621094}` / `{'median': 0.0005836673080921173, 'p95': 2.6799964904785156, 'max': 18.448631286621094}`.
- The issue-time enemy guard retained 12261 observations, detected 4340 during-plan geometry changes, recertified 4340 decisions, and overrode 103 actions. Read/recertificate timing was `{'median': 1.6048999968916178, 'p95': 2.862200009985827, 'max': 38.275099999736995}` / `{'median': 2.4799000020720996, 'p95': 5.148999989614822, 'max': 169.8130000004312}` ms; 6746 issue captures contained latent bodies (maximum 51), and 4876 contained dormant bodies (maximum 37). Fresh/global transactions preserved 4237/4340 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9922 observations (9880 contact enabled, 42 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9922}`.
- The terminal-threat heuristic covered 12261 decisions with horizon counts `{'0': 25, '10': 12236}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 21, '3': 8115, '4': 3108, '5': 629, '6': 388}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 15, '2': 260, '3': 10972, '4': 1008, '5': 6}`.
- Adaptive delay supports were `{'1,2': 15, '1,2,3': 1, '1,2,3,4,5,6': 27, '2,3': 416, '2,3,4': 3635, '2,3,4,5': 4377, '2,3,4,5,6': 2966, '3,4': 107, '3,4,5': 223, '3,4,5,6': 491, '4,5,6': 3}`; 134 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 27/156.
- Robust viability supplied 5348 available policy queries (0 had new delay support outside the cached policy), constrained 422 decisions, and exposed 2627 empty queried action sets. Recovery guidance was available/selected on 774/0 empty-kernel queries; distant-kernel guidance was available/selected on 1447/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 793, '1': 740, '2': 607, '3': 600, '4': 643, '5': 657, '6': 633, '7': 675}`.
- Global-horizon/local-prefix cross-tab covered 2799 decisions: 0 had a winning global state but unsafe selected prefix, 1279 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 166 selected actions were outside the reported winning set. 1123 newer issue-time hazard versions and 6 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 773 unique policies with solve-time statistics `{'median': 121.61470000864938, 'p95': 394.44689999800175, 'max': 3049.866399989696}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1760.0}`. Policy status counts were `{'pending_future_epoch': 86, 'queryable': 5332, 'expired': 2838}`; 2908 robust-mode decisions had no query.
- Of 6892 unambiguous output transitions, 6566 (0.953) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 4, 'robust_action_set_exhausted_before_hit': 10, 'global_viability_kernel_exhausted_before_hit': 11, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 20 hit windows with a positive warning lead; those leads were `[0, 0, 7, 5, 0, 0, 8, 19, 16, 9, 3, 7, 7, 0, 5, 6, 14, 0, 10, 9, 22, 7, 4, 6, 10, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.528 during the 60 frames preceding a hit versus 0.211 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Exact Ordinary Authority Audit

- **Observed:** 1,947 future-source projections completed 140 times and carried
  at most 900 sector trajectories. Across 7,162 nonspell decisions, exact
  authority was eligible/applicable/effective on 452/422/399 decisions; 149
  effective decisions used a completed pending policy. The 80-frame windows
  before 15 nonspell hits contained 380 decisions and zero applicable or
  effective authority: 366 were source-unavailable, eight had an empty exact
  set, and six were player transitions.
- **Observed:** the 31 unique complete nonspell policies had solve-time
  median/p95/max 367/1,848/3,050 ms. Exact clearance was 18/600/993 ms and
  Boolean viability was 211/1,664/3,026 ms. This validates the sector-volume
  acceleration and moves the remaining complete-root latency into recurrence.
- **Observed canonical chain:** source 639 took 1,415 ms, split 478 ms
  clearance and 918 ms viability. The corridor's last nonnegative gate was
  frame 714 and its first negative gate was frame 716, before the frame-796
  hit; the late exact predecessor was empty.
- **Observed aggregate coverage:** the largest projection failure class was
  1,195 armed phase transitions without an integrated successor. This remains
  fail closed, but does not replace the canonical first-hit latency finding.
- **Inference:** a faster exact recurrence is the next smallest physical
  falsifier. Hostile-birth uncertainty and local action ranking remain later.
