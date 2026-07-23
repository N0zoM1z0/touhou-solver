# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_finalb_practice_rolling_epoch_20260723_213126

## Scope And Integrity

- Valid practice scope: `1..70642` (19289 decisions).
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 25, at `[8494, 12581, 13284, 19897, 20922, 22435, 27042, 29182, 30244, 32726, 37050, 37761, 39109, 45592, 45998, 46432, 47323, 47897, 50160, 51349, 51845, 53425, 58104, 60468, 66565]`.
- Hard no-Bomb verification: **PASS** across 19289 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F8494-T1`. It occurred during a nonspell phase at player (273.712, 302.037), with 634 bullets and 0 lasers. The projectile model reported pipeline clearance 2.764.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 8 |
| `observed_laser_overlap` | 3 |
| `sensor_gap_or_unmodeled_hazard` | 3 |

Contributing factors:

- `fast_mode`: 18
- `playfield_boundary`: 11
- `corridor_deadline_miss`: 8
- `pool_density_over_1000`: 3
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 8494 | nonspell | (273.712, 302.037) | `left_fast` | 634/0 | 2.764/0.251 | 0f/3f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 12581 | 150 薬符「壺中の大銀河」 | (24.971, 151.328) | `right_fast` | 672/0 | -1.382/-1.382 | 2f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13284 | 150 薬符「壺中の大銀河」 | (8.142, 256.338) | `right_fast` | 509/0 | -1.508/-1.508 | 0f/17f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 19897 | nonspell | (12.127, 426.223) | `up_fast` | 1153/0 | -1.295/-1.295 | 2f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 20922 | nonspell | (373.385, 421.329) | `up_fast` | 1067/0 | 1.020/-2.846 | 2f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 22435 | 154 神宝「ブリリアントドラゴンバレッタ」 | (312.720, 425.039) | `up_left_fast` | 111/190 | -2.044/-5.825 | 15f/33f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27042 | nonspell | (367.348, 431.339) | `stay` | 422/0 | -1.991/-1.991 | 2f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 29182 | 158 神宝「ブディストダイアモンド」 | (261.345, 426.639) | `up` | 210/33 | -1.653/-2.593 | 0f/119f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30244 | 158 神宝「ブディストダイアモンド」 | (105.318, 427.207) | `stay` | 243/33 | -2.247/-2.558 | 0f/11f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 32726 | nonspell | (216.263, 133.037) | `left_fast` | 0/0 | 9999.000/2.639 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 37050 | 162 神宝「サラマンダーシールド」 | (321.909, 426.286) | `stay` | 530/32 | -0.457/-8.200 | 6f/6f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 37761 | 162 神宝「サラマンダーシールド」 | (376.000, 427.125) | `left_fast` | 532/28 | -6.966/-8.200 | 6f/6f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39109 | 162 神宝「サラマンダーシールド」 | (374.783, 427.446) | `stay` | 534/28 | -5.393/-7.015 | 6f/6f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 45592 | 166 神宝「ライフスプリングインフィニティ」 | (8.000, 16.000) | `down_fast` | 98/52 | -2.158/-2.158 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 45998 | 166 神宝「ライフスプリングインフィニティ」 | (223.799, 420.899) | `up_left_fast` | 416/52 | 1.603/-3.284 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 46432 | 166 神宝「ライフスプリングインフィニティ」 | (177.858, 421.748) | `up_fast` | 476/52 | -0.085/-6.258 | 0f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 47323 | 166 神宝「ライフスプリングインフィニティ」 | (189.941, 431.813) | `up_fast` | 453/52 | -1.530/-1.818 | 0f/239f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 47897 | 166 神宝「ライフスプリングインフィニティ」 | (189.172, 424.113) | `up_fast` | 471/52 | -4.132/-6.332 | 0f/240f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50160 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (212.630, 197.326) | `up_right_fast` | 336/0 | -2.374/-2.374 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51349 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (45.473, 416.405) | `stay` | 578/0 | -2.664/-2.664 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 51845 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (10.371, 395.904) | `up_fast` | 557/0 | -3.059/-3.059 | 4f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 53425 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (9.022, 379.507) | `stay` | 567/0 | -2.575/-2.575 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 58104 | 174 「永夜返し  -待宵-」 | (372.949, 420.508) | `left_fast` | 889/0 | -1.901/-1.901 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 60468 | 178 「永夜返し  -子の四つ-」 | (109.545, 378.628) | `up_right_fast` | 964/0 | -1.128/-4.295 | 13f/36f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 66565 | 186 「永夜返し  -寅の四つ-」 | (264.783, 431.377) | `up_fast` | 1169/0 | 0.172/-1.010 | 0f/3f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 9775 | 4292 | 2022 | 1217 | 1679 | 138 | 1925.245 | 0.144 |
| 150 薬符「壺中の大銀河」 | 2 | 993 | 533 | 56 | 171 | 341 | 18 | 1650.086 | 0.043 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 1 | 575 | 205 | 163 | 21 | 21 | 10 | 2773.890 | 0.314 |
| 158 神宝「ブディストダイアモンド」 | 2 | 856 | 367 | 308 | 105 | 35 | 14 | 2117.136 | 0.470 |
| 162 神宝「サラマンダーシールド」 | 3 | 1376 | 552 | 518 | 164 | 34 | 21 | 2450.890 | 0.418 |
| 166 神宝「ライフスプリングインフィニティ」 | 5 | 946 | 452 | 357 | 144 | 24 | 19 | 2251.386 | 0.653 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 4 | 2175 | 1126 | 445 | 248 | 538 | 39 | 1797.721 | 0.280 |
| 174 「永夜返し  -待宵-」 | 1 | 378 | 138 | 34 | 36 | 72 | 6 | 1928.348 | 0.184 |
| 178 「永夜返し  -子の四つ-」 | 1 | 259 | 61 | 0 | 25 | 36 | 2 | 1393.568 | 0.078 |
| 182 | 0 | 550 | 203 | 136 | 65 | 67 | 7 | 2136.171 | 0.162 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 517 | 172 | 23 | 68 | 81 | 6 | 2386.185 | 0.470 |
| 190 | 0 | 889 | 353 | 198 | 145 | 89 | 12 | 2193.120 | 0.133 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 3 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 16.473 ms median and 33.725 ms p95.
- Modeled action hold counts were `{'2': 4441, '3': 12594, '4': 2254}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 100, '2': 4964, '3': 13687, '4': 538}`.
- Adaptive delay supports were `{'1,2': 185, '1,2,3': 202, '1,2,3,4': 1709, '1,2,3,4,5': 491, '1,2,3,4,5,6': 338, '2,3': 674, '2,3,4': 5235, '2,3,4,5': 6268, '2,3,4,5,6': 3308, '3,4': 104, '3,4,5': 297, '3,4,5,6': 478}`; 502 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 115/1004.
- Robust viability supplied 8454 available policy queries (2409 had new delay support outside the cached policy), constrained 3017 decisions, and exposed 4260 empty queried action sets. Safe-action count and selected repair-volume statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 292 unique policies with solve-time statistics `{'median': 1957.0642500038957, 'p95': 2914.8480000003474, 'max': 3267.7537999989}` and first-observed ages `{'median': 2.0, 'p95': 33.0, 'max': 1787.0}`. Policy status counts were `{'pending_future_epoch': 771, 'queryable': 8309, 'expired': 8834}`; 9460 robust-mode decisions had no query.
- Of 9748 unambiguous output transitions, 8463 (0.868) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 18, 'global_viability_kernel_exhausted_before_hit': 6, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 24 hit windows with a positive warning lead; those leads were `[3, 6, 17, 5, 4, 33, 6, 119, 11, 0, 6, 6, 6, 6, 11, 8, 239, 240, 3, 6, 6, 8, 6, 36, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.410 during the 60 frames preceding a hit versus 0.204 outside those windows.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 7.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Root Cause

- **Observed:** Future policy epochs increased queries from 80 in the prior
  complete-run Final B scope to 8,454 here. They did not provide continuous
  control: 8,834 robust-mode decisions reported an expired policy.
- **Observed:** Solver median/p95 was 1,957/2,915 ms, approximately 117/175
  frames at 60 FPS, while the finite policy horizon is 80 frames. A serial
  worker cannot continuously cover this timing regime.
- **Observed:** Of 25 hits, 18 followed local robust action-set exhaustion and
  six followed global viability-kernel exhaustion. Twenty-four hit windows
  had a positive robust warning lead.
- **Observed:** Bottom-eight-pixel occupancy was 41.0% in the 60 frames before
  a hit versus 20.4% elsewhere. Negative corridor slack was 71.3% before hits.
  This is long-horizon positioning loss, not primarily SendInput latency;
  86.8% of unambiguous input transitions were visible in the next snapshot.
- **Observed:** Spell 162 had 518 empty sets in 552 queries. Spell 166 had 357
  in 452, five hits, and 65.3% bottom occupancy. Spell 178 had zero empty sets
  in 61 queries and one hit. The failure is phase-dependent hazard/viability
  pressure rather than a universal input failure.

## Offline Correction Prepared

- Added a game-neutral native backend for time-expanded AABB/segment clearance
  and robust backward DP. NumPy remains the executable reference fallback.
- Windows stress warm median fell from 1,501.9 ms to 540.2 ms. With full delay
  support `1..6`, median/max was 511.4/561.4 ms, approximately 31/34 physical
  frames and below the 80-frame horizon.
- Added explicit p90 solve-frame, serial coverage-margin, backend, and
  per-kernel timing telemetry.
- Policy submission now pads the current bounded delay support by one frame on
  each side. This is a game-neutral hedge against estimator drift while the
  asynchronous solve is running.
- Physical acceptance remains pending. This trace exercised the NumPy
  rolling-epoch controller, not the native correction.
