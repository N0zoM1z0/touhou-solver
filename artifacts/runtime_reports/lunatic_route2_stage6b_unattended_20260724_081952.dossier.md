# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260724_081952

## Scope And Integrity

- Valid practice scope: `2..75091` (14484 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[18494, 19288, 20771, 21239, 21941, 31067, 40489, 41803, 48086, 49103, 51158, 54979, 55718, 56264, 56788, 57551, 58149, 71015]`.
- Hard no-Bomb verification: **PASS** across 14484 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F18494-T1`. It occurred during a nonspell phase at player (8.000, 428.747), with 1165 bullets and 0 lasers. The projectile model reported pipeline clearance -1.402.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 5 |
| `observed_laser_overlap` | 3 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 12
- `fast_mode`: 8
- `pool_density_over_1000`: 5
- `corridor_deadline_miss`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 18494 | nonspell | (8.000, 428.747) | `up_right_fast` | 1165/0 | -1.402/-1.402 | 5f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19288 | nonspell | (12.879, 427.121) | `down_right_fast` | 1057/0 | -2.520/-2.520 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20771 | nonspell | (8.000, 428.747) | `down_left` | 1160/0 | -1.793/-1.793 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21239 | nonspell | (41.462, 432.000) | `down_left` | 1183/0 | 0.071/0.071 | 0f/7f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21941 | 154 神宝「ブリリアントドラゴンバレッタ」 | (36.850, 403.273) | `down_right_fast` | 125/220 | -4.057/-4.057 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31067 | 158 神宝「ブディストダイアモンド」 | (117.678, 432.000) | `left` | 253/33 | -2.712/-2.712 | 0f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40489 | 162 神宝「サラマンダーシールド」 | (12.808, 387.281) | `up_left_fast` | 564/32 | -4.689/-4.689 | 4f/12f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41803 | 162 神宝「サラマンダーシールド」 | (8.000, 367.754) | `stay` | 560/24 | -4.784/-4.784 | 0f/9f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 48086 | 166 神宝「ライフスプリングインフィニティ」 | (363.226, 360.234) | `up` | 417/52 | 0.786/0.080 | 0f/5f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 49103 | 166 神宝「ライフスプリングインフィニティ」 | (315.646, 432.000) | `stay` | 446/52 | -1.650/-3.241 | 0f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51158 | 166 神宝「ライフスプリングインフィニティ」 | (16.000, 432.000) | `up_right_fast` | 282/52 | 1.243/-1.117 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54979 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (219.749, 427.121) | `left` | 571/0 | -0.725/-2.096 | 6f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55718 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (361.495, 432.000) | `stay` | 587/0 | -4.234/-4.234 | 0f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56264 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (349.244, 432.000) | `left_fast` | 558/0 | -2.904/-2.904 | 8f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56788 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (371.121, 432.000) | `right` | 554/0 | -2.633/-2.633 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57551 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (233.617, 432.000) | `right` | 556/0 | -1.071/-1.071 | 3f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58149 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (19.215, 422.800) | `down_fast` | 569/0 | 1.567/0.014 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 71015 | 186 「永夜返し  -寅の四つ-」 | (321.876, 430.164) | `up_left_fast` | 1351/0 | -0.008/-0.008 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 6549 | 6303 | 2544 | 33 | 3648 | 827 | 256.158 | 0.127 |
| 150 | 0 | 761 | 738 | 308 | 0 | 429 | 99 | 305.396 | 0.019 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 1 | 348 | 333 | 77 | 0 | 243 | 71 | 246.444 | 0.324 |
| 158 神宝「ブディストダイアモンド」 | 1 | 1229 | 1221 | 661 | 16 | 505 | 183 | 134.288 | 0.405 |
| 162 神宝「サラマンダーシールド」 | 2 | 967 | 961 | 471 | 0 | 485 | 148 | 218.820 | 0.147 |
| 166 神宝「ライフスプリングインフィニティ」 | 3 | 1210 | 1202 | 403 | 0 | 711 | 169 | 257.128 | 0.277 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 6 | 1624 | 1608 | 661 | 0 | 928 | 222 | 249.175 | 0.350 |
| 174 | 0 | 355 | 344 | 214 | 0 | 119 | 49 | 315.114 | 0.350 |
| 178 | 0 | 253 | 236 | 168 | 0 | 68 | 32 | 336.814 | 0.358 |
| 182 | 0 | 362 | 341 | 265 | 0 | 76 | 46 | 143.913 | 0.229 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 228 | 210 | 136 | 0 | 74 | 26 | 405.069 | 0.170 |
| 190 | 0 | 598 | 572 | 361 | 0 | 208 | 79 | 177.743 | 0.174 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 3 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 22.991 ms median and 45.213 ms p95.
- The full enemy sensor produced 9774 snapshots; capture read time was `{'median': 27.172300004167482, 'p95': 53.16320000565611, 'max': 225.18720000516623}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 18.0}` frames, and 16 phase-counter discontinuities were excluded; 458 decisions retained at least one contact-enabled body (maximum 25).
- The terminal-threat heuristic covered 14484 decisions with horizon counts `{'0': 249, '10': 12925, '32': 1310}`; it reported 9 collision and 258 sub-safety-clearance warnings, and relaxed 263 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 46, '3': 916, '4': 8376, '5': 4721, '6': 425}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 62, '3': 515, '4': 12010, '5': 1613, '6': 284}`.
- Adaptive delay supports were `{'1,2,3': 36, '1,2,3,4': 1, '2,3': 106, '2,3,4': 226, '2,3,4,5': 1474, '2,3,4,5,6': 2950, '3,4': 79, '3,4,5': 1254, '3,4,5,6': 8223, '4,5,6': 135}`; 388 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 237/765.
- Robust viability supplied 14069 available policy queries (49 had new delay support outside the cached policy), constrained 7494 decisions, and exposed 6269 empty queried action sets. Recovery guidance was available/selected on 1736/1027 empty-kernel queries; distant-kernel guidance was available/selected on 4376/4298. Safe-action count, selected repair-volume, and selected recovery-distance statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}` `{'median': 15.0, 'p95': 153.0, 'max': 153.0}`, and `{'median': 101.19288512538814, 'p95': 279.42798714516766, 'max': 509.24257481086556}`.
- The rolling worker produced 1951 unique policies with solve-time statistics `{'median': 246.00339998141862, 'p95': 389.4758000096772, 'max': 559.8116999899503}` and first-observed ages `{'median': 4.0, 'p95': 11.0, 'max': 1807.0}`. Policy status counts were `{'pending_future_epoch': 44, 'queryable': 14065, 'expired': 107}`; 147 robust-mode decisions had no query.
- Of 8026 unambiguous output transitions, 7012 (0.874) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 18}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 17 hit windows with a positive warning lead; those leads were `[8, 6, 3, 7, 0, 15, 12, 9, 5, 21, 9, 15, 17, 13, 10, 16, 8, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.517 during the 60 frames preceding a hit versus 0.188 outside those windows.
- Soft recovery was selected on 0.059 of alive decisions in the 60-frame pre-hit windows versus 0.073 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 17.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
