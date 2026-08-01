# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_034804

## Scope And Integrity

- Valid practice scope: `2..45410` (11583 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 19, at `[931, 1284, 2320, 2681, 9306, 9861, 12934, 13503, 21418, 21711, 22037, 22371, 30755, 31861, 35082, 38046, 39680, 42997, 44053]`.
- Hard no-Bomb verification: **PASS** across 11583 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F931-T1`. It occurred during a nonspell phase at player (337.808, 425.100), with 70 bullets and 0 lasers. The projectile model reported pipeline clearance 11.646.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `sensor_gap_or_unmodeled_hazard` | 5 |
| `observed_bullet_overlap` | 4 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 10
- `playfield_boundary`: 10
- `corridor_deadline_miss`: 8
- `action_lag_over_model`: 7
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 931 | nonspell | (337.808, 425.100) | `up_right` | 70/0 | 11.646/1.083 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 1284 | nonspell | (257.789, 432.000) | `down` | 71/0 | 1.252/-3.255 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2320 | nonspell | (316.783, 392.900) | `stay` | 229/0 | -3.010/-3.010 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 2681 | nonspell | (8.000, 415.192) | `left_fast` | 250/0 | 16.275/16.275 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 9306 | nonspell | (363.646, 432.000) | `left_fast` | 760/0 | -12.835/-12.835 | 6f/11f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 9861 | nonspell | (281.365, 432.000) | `left_fast` | 495/0 | -1.051/-11.999 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12934 | 57 夢境「二重大結界」 | (12.000, 432.000) | `right_fast` | 621/0 | -3.106/-3.106 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13503 | 57 夢境「二重大結界」 | (8.000, 424.000) | `up_right` | 624/0 | -2.590/-2.590 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21418 | nonspell | (376.000, 313.044) | `up_fast` | 350/0 | 0.216/0.216 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 21711 | nonspell | (253.388, 352.482) | `up_right_fast` | 287/0 | 28.832/3.952 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 22037 | nonspell | (249.829, 432.000) | `up` | 820/0 | -2.571/-2.571 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22371 | nonspell | (273.367, 180.621) | `stay` | 1191/0 | -2.746/-2.746 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 30755 | 65 神技「八方龍殺陣」 | (212.545, 427.679) | `up` | 1283/0 | -2.568/-2.568 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 31861 | 65 神技「八方龍殺陣」 | (181.453, 417.744) | `up_fast` | 1248/0 | -2.294/-2.294 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35082 | nonspell | (226.339, 432.000) | `up_right` | 151/0 | -1.775/-1.775 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 38046 | 69 回霊「夢想封印　侘」 | (376.000, 414.329) | `down` | 450/0 | -3.588/-3.588 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39680 | 69 回霊「夢想封印　侘」 | (19.054, 340.070) | `left_fast` | 703/0 | -7.226/-7.226 | 3f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42997 | 73 大結界「博麗弾幕結界」 | (217.837, 379.774) | `left_fast` | 1000/0 | -3.756/-3.756 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44053 | 73 大結界「博麗弾幕結界」 | (81.313, 354.629) | `down_fast` | 1287/0 | -1.542/-1.542 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 11 | 6433 | 357 | 59 | 0 | 391 | 28 | 767.086 | 0.223 |
| 57 夢境「二重大結界」 | 2 | 1159 | 721 | 248 | 0 | 0 | 79 | 186.046 | 0.351 |
| 61 | 0 | 1009 | 1003 | 356 | 0 | 0 | 165 | 130.155 | 0.146 |
| 65 神技「八方龍殺陣」 | 2 | 941 | 377 | 289 | 0 | 0 | 17 | 60.445 | 0.388 |
| 69 回霊「夢想封印　侘」 | 2 | 1074 | 1068 | 688 | 0 | 0 | 181 | 103.136 | 0.180 |
| 73 大結界「博麗弾幕結界」 | 2 | 967 | 960 | 466 | 0 | 0 | 183 | 128.153 | 0.077 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.391 ms median and 33.037 ms p95.
- The full enemy sensor produced 6280 snapshots; capture read time was `{'median': 5.5637499972363, 'p95': 28.45779999915976, 'max': 655.6603000062751}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 108.0}` frames, and 6 phase-counter discontinuities were excluded; 11306 decisions retained at least one robust-union body (maximum 51); 5994 decisions contained latent contact-disabled geometry (maximum 51), and 4554 contained bounded inactive-slot memory (maximum 34). 364 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.450389099121094, 'p95': 4.099995930989583, 'max': 10.798599243164062}` / `{'median': 2.4908435344696045, 'p95': 3.8580856323242188, 'max': 36.73600769042969}` / `{'median': 0.016925066709518433, 'p95': 3.489715576171875, 'max': 36.73600769042969}`.
- The issue-time enemy guard retained 11583 observations, detected 3736 during-plan geometry changes, recertified 3736 decisions, and overrode 67 actions. Read/recertificate timing was `{'median': 1.5941000019665807, 'p95': 2.8517000027932227, 'max': 261.0144000063883}` / `{'median': 2.5911500051734038, 'p95': 8.543900010408834, 'max': 517.5588999991305}` ms; 5986 issue captures contained latent bodies (maximum 51), and 4570 contained dormant bodies (maximum 34). Fresh/global transactions preserved 3669/3736 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9813 observations (9770 contact enabled, 43 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9813}`.
- The terminal-threat heuristic covered 11583 decisions with horizon counts `{'0': 21, '10': 11562}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 25, '3': 6965, '4': 3483, '5': 761, '6': 349}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1092, '3': 8724, '4': 1697, '5': 39, '6': 31}`.
- Adaptive delay supports were `{'1,2,3': 6, '1,2,3,4,5,6': 20, '2,3': 234, '2,3,4': 4047, '2,3,4,5': 3567, '2,3,4,5,6': 2680, '3,4': 44, '3,4,5': 386, '3,4,5,6': 516, '4,5,6': 56, '5,6': 20, '6': 7}`; 89 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 27/140.
- Robust viability supplied 4486 available policy queries (0 had new delay support outside the cached policy), constrained 391 decisions, and exposed 2106 empty queried action sets. Recovery guidance was available/selected on 619/0 empty-kernel queries; distant-kernel guidance was available/selected on 1293/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 707, '1': 582, '2': 524, '3': 504, '4': 530, '5': 543, '6': 540, '7': 556}`.
- Global-horizon/local-prefix cross-tab covered 2507 decisions: 0 had a winning global state but unsafe selected prefix, 1186 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 166 selected actions were outside the reported winning set. 974 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 653 unique policies with solve-time statistics `{'median': 124.8250999924494, 'p95': 226.30340000614524, 'max': 4789.500099999714}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1658.0}`. Policy status counts were `{'pending_future_epoch': 256, 'queryable': 4466, 'expired': 2518}`; 2754 robust-mode decisions had no query.
- Of 6491 unambiguous output transitions, 6221 (0.958) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 3, 'global_viability_kernel_exhausted_before_hit': 8, 'late_collision_after_positive_causal_margin': 2, 'robust_action_set_exhausted_before_hit': 4, 'missing_pre_hit_alive_decision': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 11 hit windows with a positive warning lead; those leads were `[0, 0, 0, 0, 11, 6, 6, 5, 0, 0, 6, 0, 0, 7, 4, 6, 14, 7, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.443 during the 60 frames preceding a hit versus 0.218 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
