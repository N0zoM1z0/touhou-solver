# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260726_004142

## Scope And Integrity

- Valid practice scope: `2..75028` (12607 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 33, at `[8163, 9493, 12544, 12894, 13284, 13605, 19298, 20024, 20570, 21300, 21980, 22383, 23186, 24055, 27926, 30707, 31464, 36698, 38688, 40140, 42384, 48770, 50059, 50782, 51232, 51837, 52451, 55159, 55788, 56338, 57233, 58185, 65521]`.
- Hard no-Bomb verification: **PASS** across 12607 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F8163-T1`. It occurred during a nonspell phase at player (71.129, 427.801), with 702 bullets and 0 lasers. The projectile model reported pipeline clearance -2.240.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 20 |
| `observed_bullet_overlap` | 9 |
| `observed_laser_overlap` | 3 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 20
- `fast_mode`: 16
- `corridor_deadline_miss`: 11
- `action_lag_over_model`: 9
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 8163 | nonspell | (71.129, 427.801) | `down_left` | 702/0 | -2.240/-2.240 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9493 | nonspell | (8.000, 431.884) | `up_fast` | 640/0 | -3.200/-3.200 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12544 | 150 薬符「壺中の大銀河」 | (376.000, 432.000) | `stay` | 437/0 | -2.594/-24.043 | 5f/34f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12894 | 150 薬符「壺中の大銀河」 | (376.000, 432.000) | `down_left` | 647/0 | -2.063/-2.063 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13284 | 150 薬符「壺中の大銀河」 | (360.555, 432.000) | `right_fast` | 675/0 | -2.585/-18.054 | 20f/28f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13605 | 150 薬符「壺中の大銀河」 | (24.971, 415.029) | `up_right_fast` | 632/0 | -2.606/-22.519 | 19f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19298 | nonspell | (356.301, 432.000) | `down_fast` | 1092/0 | -2.594/-2.594 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20024 | nonspell | (339.799, 353.612) | `up_left` | 1136/0 | -2.936/-2.936 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20570 | nonspell | (199.415, 432.000) | `right_fast` | 1073/0 | -0.033/-2.272 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21300 | nonspell | (8.000, 432.000) | `up_fast` | 1065/0 | -3.178/-3.178 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21980 | 154 神宝「ブリリアントドラゴンバレッタ」 | (209.045, 432.000) | `left_fast` | 68/170 | -1.677/-4.828 | 4f/4f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22383 | 154 神宝「ブリリアントドラゴンバレッタ」 | (218.794, 418.206) | `stay` | 105/220 | -2.859/-2.859 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23186 | 154 神宝「ブリリアントドラゴンバレッタ」 | (44.446, 392.402) | `up_left_fast` | 122/220 | -3.775/-3.775 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24055 | 154 神宝「ブリリアントドラゴンバレッタ」 | (99.522, 432.000) | `down_right` | 110/210 | -4.512/-4.512 | 6f/6f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27926 | nonspell | (125.660, 403.769) | `up` | 418/0 | -2.786/-2.786 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30707 | 158 神宝「ブディストダイアモンド」 | (355.784, 432.000) | `up` | 240/33 | -2.687/-2.687 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31464 | 158 神宝「ブディストダイアモンド」 | (44.566, 432.000) | `up` | 239/33 | -1.801/-1.801 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36698 | nonspell | (376.000, 432.000) | `up_fast` | 692/0 | -3.280/-3.280 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38688 | nonspell | (168.799, 432.000) | `right_fast` | 717/0 | -26.953/-26.953 | 4f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40140 | 162 神宝「サラマンダーシールド」 | (8.000, 346.398) | `down_right_fast` | 564/28 | -4.148/-4.148 | 17f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42384 | 162 神宝「サラマンダーシールド」 | (107.144, 405.461) | `right_fast` | 566/28 | -4.430/-4.430 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 48770 | 166 神宝「ライフスプリングインフィニティ」 | (179.776, 374.269) | `down_left` | 288/52 | -1.717/-1.717 | 6f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50059 | 166 神宝「ライフスプリングインフィニティ」 | (8.789, 405.389) | `up_left` | 478/52 | -4.623/-4.623 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50782 | 166 神宝「ライフスプリングインフィニティ」 | (302.638, 405.186) | `stay` | 466/52 | -4.683/-4.683 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51232 | 166 神宝「ライフスプリングインフィニティ」 | (26.741, 406.158) | `up_fast` | 479/52 | 0.528/0.528 | 0f/0f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51837 | 166 神宝「ライフスプリングインフィニティ」 | (376.000, 432.000) | `up_right_fast` | 474/52 | -2.541/-2.541 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 52451 | 166 神宝「ライフスプリングインフィニティ」 | (79.311, 394.723) | `up_right` | 355/52 | -0.498/-14.035 | 44f/44f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55159 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (185.174, 432.000) | `up_left_fast` | 336/0 | -5.394/-5.394 | 8f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55788 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (18.465, 421.535) | `down_fast` | 564/0 | -1.821/-1.821 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56338 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 432.000) | `stay` | 572/0 | -1.960/-1.960 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57233 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 408.840) | `up_right` | 587/0 | -2.719/-2.719 | 9f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58185 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (36.813, 400.000) | `left` | 556/0 | 0.577/0.577 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 65521 | 178 「永夜返し  -子の四つ-」 | (376.000, 432.000) | `stay` | 1007/0 | -7.404/-7.404 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 5614 | 5389 | 2144 | 0 | 3184 | 1105 | 111.416 | 0.091 |
| 150 薬符「壺中の大銀河」 | 4 | 672 | 652 | 224 | 0 | 425 | 134 | 227.188 | 0.252 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 4 | 494 | 488 | 168 | 0 | 295 | 126 | 169.023 | 0.176 |
| 158 神宝「ブディストダイアモンド」 | 2 | 1069 | 1062 | 520 | 0 | 480 | 231 | 54.409 | 0.295 |
| 162 神宝「サラマンダーシールド」 | 2 | 865 | 857 | 451 | 0 | 397 | 206 | 92.531 | 0.115 |
| 166 神宝「ライフスプリングインフィニティ」 | 6 | 1090 | 1084 | 344 | 0 | 677 | 233 | 176.333 | 0.189 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 5 | 1455 | 1436 | 636 | 0 | 792 | 293 | 94.524 | 0.133 |
| 174 | 0 | 167 | 155 | 76 | 0 | 79 | 31 | 118.332 | 0.111 |
| 178 「永夜返し  -子の四つ-」 | 1 | 160 | 148 | 91 | 0 | 57 | 24 | 84.158 | 0.179 |
| 182 | 0 | 350 | 338 | 261 | 0 | 77 | 59 | 27.703 | 0.317 |
| 186 | 0 | 102 | 92 | 36 | 0 | 56 | 14 | 369.386 | 0.000 |
| 190 | 0 | 569 | 557 | 372 | 0 | 182 | 108 | 66.424 | 0.158 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 3 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 26.460 ms median and 51.934 ms p95.
- The full enemy sensor produced 9932 snapshots; capture read time was `{'median': 27.004200033843517, 'p95': 58.196600002702326, 'max': 147.84260001033545}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 17.0}` frames, and 13 phase-counter discontinuities were excluded; 12079 decisions retained at least one robust-union body (maximum 40); 3489 decisions contained latent contact-disabled geometry (maximum 40), and 4175 contained bounded inactive-slot memory (maximum 36). 268 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.8138656616210938, 'p95': 8.928390502929688, 'max': 10.078125}` / `{'median': 0.8175501227378845, 'p95': 8.95538330078125, 'max': 10.078125}` / `{'median': 0.0, 'p95': 0.1916961669921875, 'max': 3.0598068237304688}`.
- The issue-time enemy guard retained 12607 observations, detected 906 during-plan geometry changes, recertified 906 decisions, and overrode 479 actions. Read/recertificate timing was `{'median': 2.00009997934103, 'p95': 4.384699976071715, 'max': 26.911199965979904}` / `{'median': 12.284700031159446, 'p95': 23.602499975822866, 'max': 43.40079997200519}` ms; 1935 issue captures contained latent bodies (maximum 40), and 4168 contained dormant bodies (maximum 36).
- The synchronous spell-owner guard retained 11405 observations (9863 contact enabled, 1542 anticipatory, 0 errors). 11405 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 11405}`.
- The terminal-threat heuristic covered 12607 decisions with horizon counts `{'0': 79, '10': 11266, '32': 1262}`; it reported 19 collision and 202 sub-safety-clearance warnings, and relaxed 234 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 48, '3': 271, '4': 2773, '5': 6594, '6': 2921}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 14, '3': 256, '4': 4588, '5': 6678, '6': 1071}`.
- Adaptive delay supports were `{'1,2,3,4': 28, '2,3': 27, '2,3,4': 12, '2,3,4,5': 66, '2,3,4,5,6': 635, '3,4': 2, '3,4,5': 392, '3,4,5,6': 9850, '4,5,6': 1595}`; 692 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 106/253.
- Robust viability supplied 12258 available policy queries (0 had new delay support outside the cached policy), constrained 6701 decisions, and exposed 5323 empty queried action sets. Recovery guidance was available/selected on 1330/809 empty-kernel queries; distant-kernel guidance was available/selected on 3405/3275. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 22.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 112.0, 'p95': 329.460164511584, 'max': 510.2469990112632}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1894, '1': 1773, '2': 1586, '3': 1404, '4': 1377, '5': 1387, '6': 1442, '7': 1395}`.
- Global-horizon/local-prefix cross-tab covered 8689 decisions: 2 had a winning global state but unsafe selected prefix, 4098 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 73 selected actions were outside the reported winning set. 680 newer issue-time hazard versions and 16 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2564 unique policies with solve-time statistics `{'median': 110.4448499972932, 'p95': 453.7947999779135, 'max': 643.2893999735825}` and first-observed ages `{'median': 4.0, 'p95': 10.0, 'max': 1818.0}`. Policy status counts were `{'pending_future_epoch': 53, 'queryable': 12259, 'expired': 64}`; 118 robust-mode decisions had no query.
- Of 6686 unambiguous output transitions, 5806 (0.868) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 33}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 22 hit windows with a positive warning lead; those leads were `[0, 8, 34, 5, 28, 19, 0, 0, 8, 9, 4, 0, 0, 6, 0, 5, 5, 9, 8, 22, 0, 11, 0, 0, 0, 7, 44, 18, 5, 4, 13, 0, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.276 during the 60 frames preceding a hit versus 0.135 outside those windows.
- Mean selected control-reserve deficit was 10.394 during the 60 frames preceding a hit versus 6.331 outside those windows.
- Soft recovery was selected on 0.066 of alive decisions in the 60-frame pre-hit windows versus 0.063 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 14.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
