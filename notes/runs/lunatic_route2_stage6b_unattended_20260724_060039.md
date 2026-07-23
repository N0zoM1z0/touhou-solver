# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260724_060039

## Scope And Integrity

- Valid practice scope: `2..77112` (15582 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 30, at `[7333, 11630, 12355, 12904, 13568, 18780, 19165, 20831, 21592, 21985, 22745, 23312, 23705, 25386, 33408, 34588, 41780, 50900, 51747, 52187, 52637, 53908, 56841, 57383, 57963, 59607, 60830, 64725, 67278, 73036]`.
- Hard no-Bomb verification: **PASS** across 15582 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F7333-T1`. It occurred during a nonspell phase at player (362.943, 422.714), with 202 bullets and 0 lasers. The projectile model reported pipeline clearance -3.527.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 17 |
| `observed_bullet_overlap` | 7 |
| `observed_laser_overlap` | 5 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 17
- `playfield_boundary`: 11
- `pool_density_over_1000`: 7
- `corridor_deadline_miss`: 6
- `action_lag_over_model`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 7333 | nonspell | (362.943, 422.714) | `up_right_fast` | 202/0 | -3.527/-3.527 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11630 | 150 薬符「壺中の大銀河」 | (129.786, 409.006) | `up_right_fast` | 351/0 | 1.022/1.022 | 0f/4f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 12355 | 150 薬符「壺中の大銀河」 | (374.825, 407.235) | `down_fast` | 613/0 | -2.376/-2.376 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12904 | 150 薬符「壺中の大銀河」 | (158.618, 20.953) | `down_left` | 382/0 | -0.048/-0.048 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13568 | 150 薬符「壺中の大銀河」 | (368.016, 30.423) | `up` | 608/0 | -0.462/-1.615 | 0f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18780 | nonspell | (372.423, 429.381) | `up_fast` | 1199/0 | -3.561/-3.561 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19165 | nonspell | (47.769, 385.626) | `up_left_fast` | 1053/0 | -3.336/-3.336 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20831 | nonspell | (33.108, 425.409) | `up_left_fast` | 1122/0 | -0.072/-1.178 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21592 | nonspell | (365.238, 421.751) | `up` | 1182/0 | -2.984/-2.984 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21985 | 154 神宝「ブリリアントドラゴンバレッタ」 | (270.348, 344.584) | `down_right` | 72/170 | -1.325/-1.325 | 0f/7f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 22745 | 154 神宝「ブリリアントドラゴンバレッタ」 | (30.345, 410.184) | `up_right` | 107/210 | -1.199/-1.841 | 7f/20f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23312 | 154 神宝「ブリリアントドラゴンバレッタ」 | (221.770, 418.831) | `down_right` | 113/215 | -3.462/-3.462 | 6f/6f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23705 | 154 神宝「ブリリアントドラゴンバレッタ」 | (272.417, 432.000) | `right_fast` | 103/230 | -3.995/-3.995 | 0f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 25386 | 154 神宝「ブリリアントドラゴンバレッタ」 | (27.359, 385.135) | `down_fast` | 125/250 | -0.859/-0.859 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33408 | 158 神宝「ブディストダイアモンド」 | (327.261, 428.434) | `up_left` | 261/33 | -1.457/-1.457 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34588 | 158 神宝「ブディストダイアモンド」 | (62.071, 428.688) | `up` | 253/33 | -0.582/-0.582 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41780 | 162 神宝「サラマンダーシールド」 | (18.596, 427.669) | `up_right_fast` | 554/28 | -4.589/-4.589 | 6f/12f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50900 | 166 神宝「ライフスプリングインフィニティ」 | (12.879, 118.929) | `up_right_fast` | 354/104 | -1.562/-1.944 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51747 | 166 神宝「ライフスプリングインフィニティ」 | (373.347, 417.294) | `up` | 456/52 | -2.890/-2.890 | 5f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 52187 | 166 神宝「ライフスプリングインフィニティ」 | (298.613, 22.306) | `down_right_fast` | 432/52 | -4.735/-4.735 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 52637 | 166 神宝「ライフスプリングインフィニティ」 | (347.184, 425.267) | `right_fast` | 440/52 | -4.709/-4.709 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 53908 | 166 神宝「ライフスプリングインフィニティ」 | (314.915, 403.949) | `stay` | 478/52 | -2.631/-2.631 | 0f/12f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56841 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (13.862, 427.066) | `stay` | 284/0 | -2.505/-3.208 | 3f/25f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57383 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (369.542, 423.057) | `up_left_fast` | 536/0 | -2.301/-2.301 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57963 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (10.766, 421.508) | `up_fast` | 558/0 | -1.297/-2.433 | 4f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 59607 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (372.854, 428.312) | `up_fast` | 556/0 | -2.697/-2.697 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 60830 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (13.891, 430.796) | `right` | 554/0 | -0.887/-1.326 | 4f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 64725 | 174 「永夜返し  -待宵-」 | (10.715, 427.845) | `stay` | 1143/0 | -6.221/-6.221 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 67278 | 178 「永夜返し  -子の四つ-」 | (374.633, 431.303) | `up_fast` | 1003/0 | -5.494/-5.494 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 73036 | 186 「永夜返し  -寅の四つ-」 | (365.613, 423.285) | `up_left_fast` | 1256/0 | -2.890/-4.312 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 7199 | 6912 | 2835 | 118 | 3310 | 820 | 254.685 | 0.115 |
| 150 薬符「壺中の大銀河」 | 4 | 860 | 824 | 251 | 0 | 504 | 103 | 342.008 | 0.026 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 5 | 637 | 596 | 339 | 0 | 217 | 53 | 936.425 | 0.266 |
| 158 神宝「ブディストダイアモンド」 | 2 | 1228 | 1209 | 670 | 0 | 430 | 178 | 290.905 | 0.234 |
| 162 神宝「サラマンダーシールド」 | 1 | 874 | 862 | 523 | 0 | 287 | 134 | 378.851 | 0.263 |
| 166 神宝「ライフスプリングインフィニティ」 | 5 | 1227 | 1209 | 442 | 0 | 606 | 165 | 352.707 | 0.148 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 5 | 1706 | 1695 | 870 | 6 | 736 | 220 | 242.525 | 0.310 |
| 174 「永夜返し  -待宵-」 | 1 | 296 | 282 | 122 | 16 | 118 | 37 | 309.018 | 0.210 |
| 178 「永夜返し  -子の四つ-」 | 1 | 203 | 182 | 116 | 6 | 66 | 24 | 338.450 | 0.113 |
| 182 | 0 | 398 | 379 | 295 | 5 | 84 | 47 | 140.410 | 0.219 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 236 | 217 | 143 | 9 | 68 | 26 | 382.329 | 0.117 |
| 190 | 0 | 718 | 697 | 487 | 7 | 185 | 80 | 174.718 | 0.213 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 5 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 21.154 ms median and 55.153 ms p95.
- The full enemy sensor produced 10028 snapshots; capture read time was `{'median': 27.284799987683073, 'p95': 65.80919999396428, 'max': 170.88350001722574}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 17.0}` frames, and 16 phase-counter discontinuities were excluded; 456 decisions retained at least one contact-enabled body (maximum 27).
- The terminal-threat heuristic covered 15582 decisions with horizon counts `{'0': 344, '10': 14001, '32': 1237}`; it reported 10 collision and 211 sub-safety-clearance warnings, and relaxed 1237 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 52, '3': 2435, '4': 9161, '5': 2375, '6': 1559}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 57, '3': 3758, '4': 8503, '5': 2490, '6': 774}`.
- Adaptive delay supports were `{'1,2,3': 27, '1,2,3,4': 1, '1,2,3,4,5': 21, '1,2,3,4,5,6': 7, '2,3': 23, '2,3,4': 799, '2,3,4,5': 3649, '2,3,4,5,6': 4705, '3,4': 35, '3,4,5': 1511, '3,4,5,6': 3882, '4,5,6': 557, '5,6': 365}`; 337 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 285/884.
- Robust viability supplied 15064 available policy queries (167 had new delay support outside the cached policy), constrained 6611 decisions, and exposed 7093 empty queried action sets. Recovery guidance was available/selected on 1643/1027 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 9.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 1887 unique policies with solve-time statistics `{'median': 284.45690000080504, 'p95': 462.09559999988414, 'max': 1485.951999988174}` and first-observed ages `{'median': 4.0, 'p95': 14.0, 'max': 1807.0}`. Policy status counts were `{'pending_future_epoch': 67, 'queryable': 15046, 'expired': 164}`; 213 robust-mode decisions had no query.
- Of 8804 unambiguous output transitions, 7682 (0.873) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 27, 'robust_action_set_exhausted_before_hit': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 28 hit windows with a positive warning lead; those leads were `[0, 4, 6, 3, 24, 6, 3, 7, 3, 7, 20, 6, 10, 0, 4, 4, 12, 4, 10, 11, 8, 12, 25, 12, 10, 6, 21, 7, 8, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.304 during the 60 frames preceding a hit versus 0.160 outside those windows.
- Soft recovery was selected on 0.069 of alive decisions in the 60-frame pre-hit windows versus 0.068 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 6.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Experiment Decision

This is an **accepted complete physical checkpoint**, not a no-hit clear.
The run reached `route_complete` at frame 77,112, used no Bomb input, selected
the no-save exit, and closed without a runtime exception.

Against complete Stage-6B baseline `20260724_014545`, total hit edges fell
from 42 to 30. The strongest phase improvement was spell 162, from six hits
to one. The aggregate is still discovery evidence after the first respawn:
later phases run with altered Power and cannot estimate an initial-stock clear
probability.

Against the matched dense-laser portion of failed pre-cache run
`20260724_053742`, spell 154 fell from ten to five hits and corridor solve
median/p95 fell from 1340/1863 to 936/1345 ms. Overall local-plan p95 improved
from 97.31 to 55.15 ms and cadence p95 from eight to five frames. This
physically accepts exact lifecycle-template reuse and the nonfatal rollout
fallback, while rejecting any claim that dense lasers are solved: five
spell-154 laser contacts and near-second solves remain.

The 1,237 coarse-constraint downgrades preserved 3/5-frame cadence, satisfying
the performance gate for CE-0071. This run is not an ablation, so its survival
improvement is not attributed to that change.
