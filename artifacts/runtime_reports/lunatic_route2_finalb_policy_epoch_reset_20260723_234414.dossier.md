# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_finalb_policy_epoch_reset_20260723_234414

## Scope And Integrity

- Valid practice scope: `1..70295` (17723 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 37, at `[1441, 2891, 12000, 12832, 13204, 18413, 18996, 19577, 20253, 20813, 21199, 28834, 32563, 36322, 37079, 37380, 37909, 38281, 38854, 39158, 44874, 45268, 45644, 46304, 46930, 47228, 50867, 51281, 52989, 53594, 54020, 54495, 54962, 58300, 60870, 66806, 69692]`.
- Hard no-Bomb verification: **PASS** across 17723 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F1441-T1`. It occurred during a nonspell phase at player (335.307, 414.343), with 316 bullets and 0 lasers. The projectile model reported pipeline clearance 1.786.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 14 |
| `modeled_committed_prefix_collision` | 13 |
| `observed_laser_overlap` | 9 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 24
- `playfield_boundary`: 18
- `corridor_deadline_miss`: 13
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1441 | nonspell | (335.307, 414.343) | `stay` | 316/0 | 1.786/1.703 | 0f/3f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2891 | nonspell | (295.462, 380.260) | `right_fast` | 407/0 | -1.424/-1.424 | 0f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12000 | 150 薬符「壺中の大銀河」 | (372.506, 425.831) | `stay` | 662/0 | -2.841/-2.905 | 2f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12832 | 150 薬符「壺中の大銀河」 | (371.361, 427.345) | `left_fast` | 301/0 | -2.509/-2.509 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13204 | 150 薬符「壺中の大銀河」 | (373.604, 400.553) | `down_fast` | 494/0 | -2.156/-2.156 | 0f/23f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 18413 | nonspell | (11.485, 428.942) | `up_fast` | 1144/0 | -1.120/-1.120 | 3f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18996 | nonspell | (10.241, 427.400) | `up_right` | 1115/0 | -1.721/-1.721 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19577 | nonspell | (372.431, 431.414) | `left_fast` | 1135/0 | -0.599/-0.745 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20253 | 154 神宝「ブリリアントドラゴンバレッタ」 | (63.631, 429.569) | `left_fast` | 106/230 | -8.050/-8.050 | 0f/25f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 20813 | 154 神宝「ブリリアントドラゴンバレッタ」 | (38.935, 426.066) | `up` | 120/220 | -5.179/-7.604 | 4f/7f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 21199 | 154 神宝「ブリリアントドラゴンバレッタ」 | (115.565, 431.052) | `right_fast` | 107/220 | -7.775/-7.775 | 0f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 28834 | 158 神宝「ブディストダイアモンド」 | (271.206, 427.847) | `right_fast` | 225/66 | -3.378/-7.977 | 6f/188f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32563 | nonspell | (368.693, 426.050) | `up_right` | 650/0 | -2.455/-2.455 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36322 | 162 神宝「サラマンダーシールド」 | (44.705, 429.841) | `up_fast` | 566/28 | -7.781/-8.200 | 10f/10f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37079 | 162 神宝「サラマンダーシールド」 | (364.000, 401.402) | `left_fast` | 546/28 | -3.972/-7.629 | 6f/6f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37380 | 162 神宝「サラマンダーシールド」 | (43.490, 330.932) | `up_right_fast` | 440/32 | -2.826/-8.200 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 37909 | 162 神宝「サラマンダーシールド」 | (12.316, 374.544) | `stay` | 524/28 | -6.109/-7.943 | 17f/19f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38281 | 162 神宝「サラマンダーシールド」 | (36.444, 373.759) | `right_fast` | 524/32 | -5.743/-8.200 | 12f/42f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38854 | 162 神宝「サラマンダーシールド」 | (74.460, 432.000) | `left_fast` | 568/28 | -2.305/-7.659 | 3f/3f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39158 | 162 神宝「サラマンダーシールド」 | (349.508, 389.632) | `down_fast` | 380/32 | -2.902/-7.441 | 3f/3f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44874 | 166 神宝「ライフスプリングインフィニティ」 | (21.421, 97.795) | `up_left_fast` | 136/52 | -4.537/-6.714 | 8f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 45268 | 166 神宝「ライフスプリングインフィニティ」 | (166.374, 315.603) | `down` | 405/52 | -4.953/-7.974 | 9f/9f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45644 | 166 神宝「ライフスプリングインフィニティ」 | (236.750, 427.650) | `up_fast` | 311/52 | -0.491/-1.924 | 4f/18f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 46304 | 166 神宝「ライフスプリングインフィニティ」 | (160.817, 427.962) | `up_right_fast` | 476/52 | -3.077/-5.853 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 46930 | 166 神宝「ライフスプリングインフィニティ」 | (158.389, 430.211) | `stay` | 447/52 | -3.187/-6.223 | 4f/239f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 47228 | 166 神宝「ライフスプリングインフィニティ」 | (233.980, 431.080) | `up` | 394/52 | -1.834/-7.177 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 50867 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (372.843, 421.760) | `up_left_fast` | 538/0 | -2.852/-2.852 | 3f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 51281 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (41.763, 429.524) | `stay` | 602/0 | -1.263/-2.145 | 2f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 52989 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (13.136, 427.182) | `up` | 562/0 | -1.263/-1.263 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 53594 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 402.853) | `stay` | 552/0 | -1.080/-1.477 | 2f/13f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 54020 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (12.042, 426.522) | `stay` | 558/0 | -1.509/-1.655 | 2f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54495 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (24.303, 423.893) | `right_fast` | 565/0 | -0.784/-3.084 | 7f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54962 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (11.429, 420.465) | `right_fast` | 572/0 | -2.317/-2.317 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58300 | 174 「永夜返し  -待宵-」 | (366.175, 431.869) | `left_fast` | 1145/0 | -4.087/-4.087 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 60870 | 178 「永夜返し  -子の四つ-」 | (288.964, 369.546) | `up_left_fast` | 997/0 | -5.141/-5.141 | 6f/34f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 66806 | 186 「永夜返し  -寅の四つ-」 | (345.864, 431.582) | `up_right_fast` | 1015/0 | -3.367/-3.367 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 69692 | 190 「永夜返し  -世明け-」 | (11.727, 420.816) | `up_fast` | 402/0 | -1.043/-2.079 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 8588 | 8049 | 3298 | 470 | 4553 | 409 | 237.401 | 0.152 |
| 150 薬符「壺中の大銀河」 | 3 | 878 | 840 | 68 | 28 | 744 | 48 | 299.512 | 0.141 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 3 | 748 | 731 | 504 | 0 | 227 | 53 | 208.136 | 0.264 |
| 158 神宝「ブディストダイアモンド」 | 1 | 716 | 701 | 590 | 50 | 111 | 42 | 90.041 | 0.525 |
| 162 神宝「サラマンダーシールド」 | 7 | 1381 | 1351 | 783 | 47 | 528 | 79 | 150.205 | 0.321 |
| 166 神宝「ライフスプリングインフィニティ」 | 6 | 1153 | 1131 | 1043 | 22 | 83 | 67 | 99.519 | 0.604 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 7 | 2140 | 2124 | 873 | 118 | 1196 | 115 | 207.825 | 0.287 |
| 174 「永夜返し  -待宵-」 | 1 | 385 | 343 | 197 | 10 | 144 | 19 | 281.771 | 0.302 |
| 178 「永夜返し  -子の四つ-」 | 1 | 277 | 231 | 137 | 26 | 80 | 13 | 288.059 | 0.042 |
| 182 | 0 | 488 | 438 | 348 | 15 | 90 | 24 | 126.434 | 0.275 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 386 | 335 | 169 | 15 | 151 | 18 | 371.678 | 0.230 |
| 190 「永夜返し  -世明け-」 | 1 | 583 | 539 | 282 | 12 | 257 | 24 | 193.953 | 0.096 |

## Interpretation

- Retained witnesses classify 14 bullet overlaps, 9 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 16.013 ms median and 34.396 ms p95.
- Modeled action hold counts were `{'2': 836, '3': 11959, '4': 4671, '5': 257}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 1, '2': 1907, '3': 14372, '4': 1443}`.
- Adaptive delay supports were `{'1,2': 1, '1,2,3': 140, '1,2,3,4': 62, '1,2,3,4,5,6': 15, '2,3': 503, '2,3,4': 4556, '2,3,4,5': 6836, '2,3,4,5,6': 4133, '3,4': 94, '3,4,5': 314, '3,4,5,6': 1069}`; 526 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 108/942.
- Robust viability supplied 16813 available policy queries (813 had new delay support outside the cached policy), constrained 8164 decisions, and exposed 8292 empty queried action sets. Safe-action count and selected repair-volume statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 911 unique policies with solve-time statistics `{'median': 208.13579999958165, 'p95': 369.28769999940414, 'max': 609.3216000008397}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1797.0}`. Policy status counts were `{'pending_future_epoch': 421, 'queryable': 16817, 'expired': 255}`; 680 robust-mode decisions had no query.
- Of 8488 unambiguous output transitions, 7290 (0.859) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 26, 'robust_action_set_exhausted_before_hit': 9, 'missing_pre_hit_alive_decision': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 35 hit windows with a positive warning lead; those leads were `[3, 2, 9, 4, 23, 8, 8, 9, 25, 7, 9, 188, 4, 10, 6, 0, 19, 42, 3, 3, 8, 9, 18, 7, 239, 0, 5, 8, 5, 13, 6, 9, 9, 7, 34, 9, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.473 during the 60 frames preceding a hit versus 0.202 outside those windows.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 15.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
