# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260724_135201

## Scope And Integrity

- Valid practice scope: `3..75073` (12818 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 27, at `[11720, 12346, 18671, 19431, 20323, 21571, 21975, 22359, 22768, 36391, 40258, 42564, 48451, 48896, 49205, 49867, 50253, 50928, 52421, 55463, 56164, 56993, 57930, 58437, 59084, 65562, 70966]`.
- Hard no-Bomb verification: **PASS** across 12818 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F11720-T1`. It occurred during spell 150 `薬符「壺中の大銀河」` at player (31.342, 417.858), with 428 bullets and 0 lasers. The projectile model reported pipeline clearance 1.781.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 8 |
| `observed_laser_overlap` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 2 |
| `active_laser_without_observed_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 17
- `fast_mode`: 14
- `corridor_deadline_miss`: 7
- `pool_density_over_1000`: 5
- `action_lag_over_model`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 11720 | 150 薬符「壺中の大銀河」 | (31.342, 417.858) | `right_fast` | 428/0 | 1.781/0.003 | 0f/22f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12346 | 150 薬符「壺中の大銀河」 | (364.686, 30.235) | `down_left_fast` | 366/0 | -1.094/-1.237 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 18671 | nonspell | (11.029, 432.000) | `up_left_fast` | 1205/0 | -1.646/-1.646 | 0f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19431 | nonspell | (8.000, 432.000) | `up_right` | 1222/0 | -3.402/-3.402 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20323 | nonspell | (376.000, 432.000) | `left_fast` | 1174/0 | -3.093/-3.093 | 0f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21571 | 154 神宝「ブリリアントドラゴンバレッタ」 | (205.221, 409.000) | `up` | 99/230 | -2.664/-2.664 | 0f/0f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21975 | 154 神宝「ブリリアントドラゴンバレッタ」 | (148.284, 410.716) | `right_fast` | 107/205 | 0.868/-5.636 | 4f/4f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22359 | 154 神宝「ブリリアントドラゴンバレッタ」 | (246.229, 432.000) | `up_left` | 103/210 | 0.739/0.739 | 0f/11f | `active_laser_without_observed_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22768 | 154 神宝「ブリリアントドラゴンバレッタ」 | (218.849, 432.000) | `up_left_fast` | 110/225 | -4.155/-4.155 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36391 | nonspell | (359.893, 432.000) | `up_right_fast` | 711/0 | -2.574/-2.574 | 4f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40258 | 162 神宝「サラマンダーシールド」 | (21.218, 432.000) | `right` | 528/28 | -2.616/-2.616 | 20f/25f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42564 | 162 神宝「サラマンダーシールド」 | (376.000, 363.262) | `down` | 546/28 | -4.248/-4.248 | 7f/12f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 48451 | 166 神宝「ライフスプリングインフィニティ」 | (199.642, 342.836) | `stay` | 288/52 | -4.655/-8.436 | 11f/11f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 48896 | 166 神宝「ライフスプリングインフィニティ」 | (9.678, 279.986) | `left` | 467/52 | -2.911/-2.911 | 0f/12f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 49205 | 166 神宝「ライフスプリングインフィニティ」 | (184.537, 328.363) | `stay` | 411/52 | -8.227/-8.227 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 49867 | 166 神宝「ライフスプリングインフィニティ」 | (376.000, 432.000) | `up_fast` | 274/52 | -3.071/-3.071 | 0f/4f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50253 | 166 神宝「ライフスプリングインフィニティ」 | (181.223, 321.970) | `down` | 406/52 | -8.052/-8.052 | 16f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50928 | 166 神宝「ライフスプリングインフィニティ」 | (376.000, 420.000) | `up_left_fast` | 253/52 | -0.879/-2.376 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 52421 | 166 神宝「ライフスプリングインフィニティ」 | (367.416, 398.453) | `stay` | 452/52 | -1.666/-1.666 | 11f/29f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55463 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (367.868, 411.868) | `right_fast` | 562/0 | -1.544/-1.544 | 0f/28f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56164 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 432.000) | `up_right_fast` | 564/0 | -1.782/-1.782 | 14f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56993 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 423.868) | `up_left` | 558/0 | -2.339/-2.339 | 9f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57930 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 406.783) | `down_fast` | 550/0 | -0.540/-0.540 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58437 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (56.617, 432.000) | `right_fast` | 563/0 | -1.408/-1.408 | 0f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 59084 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 432.000) | `stay` | 558/0 | -1.924/-1.924 | 0f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 65562 | 178 「永夜返し  -子の四つ-」 | (8.000, 432.000) | `stay` | 1003/0 | -3.197/-7.272 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 70966 | 186 「永夜返し  -寅の四つ-」 | (202.066, 419.303) | `down_fast` | 1536/0 | 0.854/0.854 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 5753 | 5492 | 2381 | 0 | 3033 | 988 | 276.567 | 0.094 |
| 150 薬符「壺中の大銀河」 | 2 | 704 | 678 | 193 | 0 | 454 | 103 | 363.791 | 0.107 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 4 | 476 | 461 | 136 | 0 | 296 | 105 | 290.605 | 0.207 |
| 158 | 0 | 1091 | 1085 | 620 | 0 | 426 | 254 | 143.786 | 0.248 |
| 162 神宝「サラマンダーシールド」 | 2 | 804 | 800 | 427 | 0 | 372 | 201 | 235.088 | 0.172 |
| 166 神宝「ライフスプリングインフィニティ」 | 7 | 1107 | 1100 | 417 | 0 | 622 | 211 | 278.778 | 0.194 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 6 | 1453 | 1440 | 545 | 0 | 864 | 275 | 283.940 | 0.223 |
| 174 | 0 | 257 | 234 | 135 | 0 | 89 | 44 | 355.758 | 0.134 |
| 178 「永夜返し  -子の四つ-」 | 1 | 171 | 149 | 80 | 0 | 69 | 23 | 400.007 | 0.224 |
| 182 | 0 | 332 | 311 | 237 | 0 | 74 | 61 | 158.374 | 0.172 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 118 | 96 | 20 | 0 | 70 | 12 | 445.917 | 0.000 |
| 190 | 0 | 552 | 528 | 327 | 0 | 194 | 105 | 183.979 | 0.071 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 6 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 24.485 ms median and 46.689 ms p95.
- The full enemy sensor produced 9961 snapshots; capture read time was `{'median': 36.11129999626428, 'p95': 61.08410001615994, 'max': 214.97790000285022}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 18.0}` frames, and 10 phase-counter discontinuities were excluded; 402 decisions retained at least one contact-enabled body (maximum 28).
- The terminal-threat heuristic covered 12818 decisions with horizon counts `{'0': 284, '10': 11305, '32': 1229}`; it reported 24 collision and 274 sub-safety-clearance warnings, and relaxed 293 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 47, '3': 637, '4': 2988, '5': 6332, '6': 2814}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 54, '3': 305, '4': 5683, '5': 5927, '6': 849}`.
- Adaptive delay supports were `{'1,2,3': 15, '1,2,3,4': 1, '2,3': 41, '2,3,4': 23, '2,3,4,5': 528, '2,3,4,5,6': 2330, '3,4': 20, '3,4,5': 205, '3,4,5,6': 8547, '4,5': 1, '4,5,6': 1094, '5,6': 13}`; 503 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 104/291.
- Robust viability supplied 12374 available policy queries (0 had new delay support outside the cached policy), constrained 6563 decisions, and exposed 5518 empty queried action sets. Recovery guidance was available/selected on 1562/887 empty-kernel queries; distant-kernel guidance was available/selected on 3801/3672. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 12.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 113.13708498984761, 'p95': 310.6638054231616, 'max': 465.1021393199563}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1673, '1': 1692, '2': 1577, '3': 1549, '4': 1505, '5': 1440, '6': 1466, '7': 1472}`.
- The rolling worker produced 2382 unique policies with solve-time statistics `{'median': 266.79675000195857, 'p95': 431.74299999373034, 'max': 671.5388000011444}` and first-observed ages `{'median': 6.0, 'p95': 13.0, 'max': 1809.0}`. Policy status counts were `{'pending_future_epoch': 34, 'queryable': 12374, 'expired': 99}`; 133 robust-mode decisions had no query.
- Of 7332 unambiguous output transitions, 6177 (0.842) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 24, 'robust_action_set_exhausted_before_hit': 2, 'missing_pre_hit_alive_decision': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 24 hit windows with a positive warning lead; those leads were `[22, 8, 22, 10, 11, 0, 4, 11, 3, 11, 25, 12, 11, 12, 0, 4, 16, 7, 29, 28, 24, 15, 8, 11, 17, 12, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.307 during the 60 frames preceding a hit versus 0.132 outside those windows.
- Mean selected control-reserve deficit was 10.043 during the 60 frames preceding a hit versus 1.422 outside those windows.
- Soft recovery was selected on 0.080 of alive decisions in the 60-frame pre-hit windows versus 0.070 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 6.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
