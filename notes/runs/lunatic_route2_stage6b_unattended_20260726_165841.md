# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260726_165841

## Scope And Integrity

- Valid practice scope: `2..75142` (19156 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 20, at `[748, 8121, 8963, 12134, 12883, 20189, 21015, 37829, 40196, 48815, 50136, 50716, 51767, 54824, 55514, 56121, 58771, 59482, 62606, 71035]`.
- Hard no-Bomb verification: **PASS** across 19156 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F748-T1`. It occurred during a nonspell phase at player (255.417, 432.000), with 535 bullets and 0 lasers. The projectile model reported pipeline clearance -2.022.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 7 |
| `observed_laser_overlap` | 4 |

Contributing factors:

- `playfield_boundary`: 17
- `fast_mode`: 15
- `corridor_deadline_miss`: 4
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 748 | nonspell | (255.417, 432.000) | `up_fast` | 535/0 | -2.022/-20.764 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8121 | nonspell | (376.000, 423.515) | `up_fast` | 348/0 | -1.658/-1.658 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8963 | nonspell | (8.000, 386.049) | `up_right_fast` | 686/0 | -3.632/-3.632 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12134 | 150 薬符「壺中の大銀河」 | (335.400, 16.000) | `up_left_fast` | 119/0 | -2.243/-29.516 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12883 | 150 薬符「壺中の大銀河」 | (372.468, 432.000) | `right` | 505/0 | 0.030/-2.603 | 2f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20189 | nonspell | (73.485, 432.000) | `up_left_fast` | 1186/0 | -0.170/-1.662 | 4f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21015 | nonspell | (175.823, 432.000) | `up_fast` | 1146/0 | -1.359/-1.359 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37829 | nonspell | (370.343, 432.000) | `up_fast` | 627/0 | -2.293/-2.293 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40196 | 162 神宝「サラマンダーシールド」 | (8.000, 431.035) | `up_right` | 528/32 | -1.336/-1.336 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 48815 | 166 神宝「ライフスプリングインフィニティ」 | (8.000, 16.000) | `down_right_fast` | 361/52 | -3.488/-3.488 | 0f/3f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50136 | 166 神宝「ライフスプリングインフィニティ」 | (17.758, 432.000) | `right_fast` | 285/52 | -2.481/-2.481 | 2f/4f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50716 | 166 神宝「ライフスプリングインフィニティ」 | (369.100, 432.000) | `up_left_fast` | 303/52 | -2.123/-2.123 | 0f/9f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51767 | 166 神宝「ライフスプリングインフィニティ」 | (376.000, 432.000) | `left_fast` | 263/52 | -1.410/-1.410 | 3f/8f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54824 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (177.926, 432.000) | `up_fast` | 336/0 | -5.228/-5.228 | 5f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55514 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (365.453, 424.395) | `up_left` | 575/0 | 1.909/-1.302 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56121 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 384.516) | `down` | 573/0 | -1.569/-1.715 | 2f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58771 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (371.121, 425.100) | `up` | 560/0 | -1.254/-1.537 | 10f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 59482 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 422.440) | `right_fast` | 560/0 | -1.899/-1.899 | 3f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 62606 | 174 「永夜返し  -待宵-」 | (8.000, 432.000) | `up_fast` | 878/0 | -2.519/-2.519 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 71035 | 186 「永夜返し  -寅の四つ-」 | (348.763, 432.000) | `down_right_fast` | 822/0 | -4.977/-4.977 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 8456 | 8160 | 3855 | 0 | 4250 | 1158 | 94.287 | 0.091 |
| 150 薬符「壺中の大銀河」 | 2 | 958 | 937 | 424 | 0 | 506 | 141 | 192.423 | 0.138 |
| 154 | 0 | 655 | 645 | 286 | 0 | 342 | 109 | 122.831 | 0.171 |
| 158 | 0 | 1847 | 1840 | 1170 | 0 | 622 | 267 | 51.593 | 0.251 |
| 162 神宝「サラマンダーシールド」 | 1 | 1367 | 1361 | 728 | 0 | 633 | 219 | 81.701 | 0.113 |
| 166 神宝「ライフスプリングインフィニティ」 | 4 | 1578 | 1568 | 644 | 0 | 793 | 245 | 170.083 | 0.214 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 5 | 2082 | 2061 | 987 | 0 | 1066 | 307 | 88.369 | 0.207 |
| 174 「永夜返し  -待宵-」 | 1 | 284 | 269 | 137 | 0 | 132 | 36 | 90.586 | 0.259 |
| 178 | 0 | 319 | 293 | 224 | 0 | 69 | 39 | 60.068 | 0.245 |
| 182 | 0 | 514 | 500 | 412 | 0 | 88 | 62 | 26.930 | 0.212 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 244 | 232 | 155 | 0 | 76 | 29 | 277.541 | 0.182 |
| 190 | 0 | 852 | 828 | 539 | 0 | 284 | 112 | 58.754 | 0.156 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 4 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.025 ms median and 28.105 ms p95.
- The full enemy sensor produced 9853 snapshots; capture read time was `{'median': 8.209799998439848, 'p95': 29.431000002659857, 'max': 60.2091999608092}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 14.0}` frames, and 14 phase-counter discontinuities were excluded; 18449 decisions retained at least one robust-union body (maximum 35); 5371 decisions contained latent contact-disabled geometry (maximum 35), and 6082 contained bounded inactive-slot memory (maximum 33). 129 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.8887939453125, 'p95': 5.729454040527344, 'max': 6.837337493896484}` / `{'median': 0.8887949585914612, 'p95': 5.863142013549805, 'max': 6.2717132568359375}` / `{'median': 0.0, 'p95': 0.5656514167785645, 'max': 0.9286861419677734}`.
- The issue-time enemy guard retained 19156 observations, detected 709 during-plan geometry changes, recertified 709 decisions, and overrode 398 actions. Read/recertificate timing was `{'median': 1.7941500118467957, 'p95': 3.5817999741993845, 'max': 21.824800001922995}` / `{'median': 3.480200015474111, 'p95': 8.208699990063906, 'max': 23.974200012162328}` ms; 2915 issue captures contained latent bodies (maximum 35), and 6070 contained dormant bodies (maximum 33).
- The synchronous spell-owner guard retained 17372 observations (14925 contact enabled, 2447 anticipatory, 0 errors). 17372 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 17372}`.
- The terminal-threat heuristic covered 19156 decisions with horizon counts `{'0': 100, '10': 17917, '32': 1139}`; it reported 13 collision and 210 sub-safety-clearance warnings, and relaxed 272 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 103, '3': 16705, '4': 2228, '5': 111, '6': 9}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 15, '2': 157, '3': 18336, '4': 648}`.
- Adaptive delay supports were `{'1,2,3': 194, '1,2,3,4': 11, '1,2,3,4,5': 17, '1,2,3,4,5,6': 23, '2,3': 276, '2,3,4': 2632, '2,3,4,5': 6645, '2,3,4,5,6': 8783, '3,4': 8, '3,4,5': 254, '3,4,5,6': 310, '4,5,6': 3}`; 466 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 70/538.
- Robust viability supplied 18694 available policy queries (0 had new delay support outside the cached policy), constrained 8861 decisions, and exposed 9561 empty queried action sets. Recovery guidance was available/selected on 2118/1067 empty-kernel queries; distant-kernel guidance was available/selected on 6404/6209. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 5.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 107.33126291998991, 'p95': 329.84845004941286, 'max': 499.85597925802585}`, and `{'median': 0.0, 'p95': 23.214994192123413, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2918, '1': 2545, '2': 2104, '3': 2288, '4': 2247, '5': 2108, '6': 2252, '7': 2232}`.
- Global-horizon/local-prefix cross-tab covered 15405 decisions: 3 had a winning global state but unsafe selected prefix, 8124 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 92 selected actions were outside the reported winning set. 621 newer issue-time hazard versions and 1 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2724 unique policies with solve-time statistics `{'median': 93.94805002375506, 'p95': 435.36550004500896, 'max': 567.1140999766067}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1810.0}`. Policy status counts were `{'pending_future_epoch': 81, 'queryable': 18699, 'expired': 103}`; 189 robust-mode decisions had no query.
- Of 9307 unambiguous output transitions, 7854 (0.844) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 20}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 20 hit windows with a positive warning lead; those leads were `[5, 5, 9, 6, 13, 4, 9, 5, 7, 3, 4, 9, 8, 16, 8, 14, 15, 11, 6, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.435 during the 60 frames preceding a hit versus 0.140 outside those windows.
- Mean selected control-reserve deficit was 16.008 during the 60 frames preceding a hit versus 5.289 outside those windows.
- Soft recovery was selected on 0.040 of alive decisions in the 60-frame pre-hit windows versus 0.054 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 6.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
