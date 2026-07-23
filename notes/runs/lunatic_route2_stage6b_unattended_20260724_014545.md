# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260724_014545

## Scope And Integrity

- Valid practice scope: `2..74588` (16696 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 42, at `[3368, 7314, 8646, 12016, 13517, 18447, 19111, 20100, 20844, 21462, 21998, 22590, 23148, 23707, 24099, 30237, 31762, 32808, 35710, 39447, 40032, 40742, 41077, 41376, 42184, 48391, 49046, 49629, 50047, 50492, 50948, 51287, 54178, 54579, 55972, 57131, 57515, 57979, 58804, 61677, 64439, 70511]`.
- Hard no-Bomb verification: **PASS** across 16696 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F3368-T1`. It occurred during a nonspell phase at player (328.798, 414.062), with 304 bullets and 0 lasers. The projectile model reported pipeline clearance -1.276.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 20 |
| `observed_bullet_overlap` | 13 |
| `observed_laser_overlap` | 7 |
| `active_laser_without_observed_overlap` | 1 |
| `observed_multiple_hazard_overlap` | 1 |

Contributing factors:

- `fast_mode`: 19
- `playfield_boundary`: 18
- `corridor_deadline_miss`: 11
- `pool_density_over_1000`: 6
- `action_lag_over_model`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3368 | nonspell | (328.798, 414.062) | `right_fast` | 304/0 | -1.276/-1.747 | 9f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7314 | nonspell | (371.631, 29.256) | `down_left_fast` | 293/0 | -1.296/-1.296 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8646 | nonspell | (366.178, 425.125) | `down_left_fast` | 360/0 | -4.992/-4.992 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12016 | 150 薬符「壺中の大銀河」 | (267.639, 425.709) | `stay` | 574/0 | -2.617/-2.617 | 5f/18f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13517 | 150 薬符「壺中の大銀河」 | (366.416, 186.471) | `up_fast` | 471/0 | 2.070/0.187 | 0f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18447 | nonspell | (12.372, 423.664) | `up_right_fast` | 1141/0 | 0.146/-0.270 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19111 | nonspell | (372.713, 417.280) | `up_fast` | 1151/0 | -1.793/-3.101 | 4f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20100 | nonspell | (12.783, 421.782) | `down_fast` | 1140/0 | -2.718/-2.718 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20844 | nonspell | (376.000, 426.532) | `up_left` | 1130/0 | -1.813/-1.813 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21462 | 154 神宝「ブリリアントドラゴンバレッタ」 | (307.468, 416.068) | `stay` | 93/215 | 0.026/-2.403 | 0f/50f | `active_laser_without_observed_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21998 | 154 神宝「ブリリアントドラゴンバレッタ」 | (112.422, 427.296) | `up_right` | 96/205 | -3.622/-6.780 | 9f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22590 | 154 神宝「ブリリアントドラゴンバレッタ」 | (219.778, 429.652) | `up_fast` | 130/230 | -2.662/-4.951 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23148 | 154 神宝「ブリリアントドラゴンバレッタ」 | (207.669, 429.523) | `up_fast` | 123/230 | -3.499/-6.657 | 3f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23707 | 154 神宝「ブリリアントドラゴンバレッタ」 | (139.266, 428.277) | `up_fast` | 97/220 | -3.620/-5.774 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24099 | 154 神宝「ブリリアントドラゴンバレッタ」 | (200.776, 428.446) | `right_fast` | 110/205 | -6.290/-6.290 | 8f/11f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 30237 | 158 神宝「ブディストダイアモンド」 | (247.134, 424.895) | `stay` | 159/33 | -2.379/-5.174 | 0f/161f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31762 | 158 神宝「ブディストダイアモンド」 | (189.373, 431.519) | `up` | 231/33 | -2.634/-5.482 | 37f/37f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32808 | 158 神宝「ブディストダイアモンド」 | (277.026, 426.437) | `up_left` | 235/33 | -3.575/-4.962 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35710 | nonspell | (373.479, 427.721) | `up_left_fast` | 710/0 | -6.998/-6.998 | 3f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39447 | 162 神宝「サラマンダーシールド」 | (51.404, 353.584) | `down_left` | 554/28 | -7.206/-7.806 | 4f/8f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40032 | 162 神宝「サラマンダーシールド」 | (373.922, 405.490) | `left_fast` | 568/28 | -6.570/-8.389 | 12f/12f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40742 | 162 神宝「サラマンダーシールド」 | (277.773, 418.102) | `down` | 570/28 | -2.763/-7.994 | 15f/18f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41077 | 162 神宝「サラマンダーシールド」 | (57.724, 298.215) | `right` | 414/32 | -6.924/-7.718 | 9f/16f | `observed_multiple_hazard_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41376 | 162 神宝「サラマンダーシールド」 | (359.361, 425.507) | `up` | 404/28 | -7.401/-8.548 | 0f/0f | `observed_laser_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 42184 | 162 神宝「サラマンダーシールド」 | (40.408, 412.977) | `right` | 530/32 | -4.237/-8.426 | 7f/17f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 48391 | 166 神宝「ライフスプリングインフィニティ」 | (290.473, 222.604) | `stay` | 416/52 | -0.704/-7.013 | 50f/230f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 49046 | 166 神宝「ライフスプリングインフィニティ」 | (11.602, 386.489) | `up_fast` | 337/52 | -1.359/-7.325 | 0f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 49629 | 166 神宝「ライフスプリングインフィニティ」 | (228.753, 429.452) | `up_left` | 328/52 | -2.394/-6.383 | 0f/154f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50047 | 166 神宝「ライフスプリングインフィニティ」 | (152.435, 428.164) | `stay` | 378/52 | -2.525/-4.953 | 116f/116f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50492 | 166 神宝「ライフスプリングインフィニティ」 | (158.988, 429.728) | `stay` | 475/52 | -1.957/-7.363 | 139f/139f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50948 | 166 神宝「ライフスプリングインフィニティ」 | (234.463, 421.818) | `up_right` | 382/52 | -6.076/-7.182 | 6f/153f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51287 | 166 神宝「ライフスプリングインフィニティ」 | (171.121, 430.079) | `up` | 320/52 | -3.304/-3.304 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54178 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.777, 411.079) | `up_right_fast` | 365/0 | -2.810/-3.566 | 6f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54579 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (329.415, 385.242) | `up_fast` | 545/0 | -3.280/-3.398 | 2f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 55972 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (308.388, 425.964) | `stay` | 589/0 | -2.101/-2.101 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57131 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 387.265) | `up` | 552/0 | -1.675/-1.675 | 0f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 57515 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (159.369, 417.788) | `up_left_fast` | 580/0 | -3.002/-3.002 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57979 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (10.229, 396.517) | `up` | 555/0 | -3.027/-3.027 | 2f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 58804 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (357.577, 427.651) | `left` | 554/0 | -3.139/-3.139 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 61677 | 174 「永夜返し  -待宵-」 | (14.293, 428.236) | `right_fast` | 893/0 | -4.197/-4.197 | 3f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 64439 | 178 「永夜返し  -子の四つ-」 | (13.814, 417.978) | `right_fast` | 1001/0 | -4.285/-4.285 | 3f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 70511 | 186 「永夜返し  -寅の四つ-」 | (370.485, 393.366) | `stay` | 1009/0 | -4.264/-4.264 | 2f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 7661 | 7224 | 2943 | 202 | 4161 | 430 | 261.783 | 0.148 |
| 150 薬符「壺中の大銀河」 | 2 | 847 | 795 | 29 | 46 | 720 | 49 | 287.146 | 0.108 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 6 | 813 | 797 | 448 | 0 | 349 | 61 | 219.134 | 0.286 |
| 158 神宝「ブディストダイアモンド」 | 3 | 1050 | 1032 | 940 | 39 | 74 | 69 | 100.189 | 0.583 |
| 162 神宝「サラマンダーシールド」 | 6 | 1218 | 1198 | 745 | 0 | 453 | 79 | 158.601 | 0.374 |
| 166 神宝「ライフスプリングインフィニティ」 | 7 | 1090 | 1072 | 996 | 0 | 76 | 75 | 120.125 | 0.337 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 7 | 1864 | 1848 | 749 | 25 | 1096 | 115 | 217.932 | 0.299 |
| 174 「永夜返し  -待宵-」 | 1 | 296 | 257 | 144 | 9 | 113 | 15 | 302.559 | 0.229 |
| 178 「永夜返し  -子の四つ-」 | 1 | 315 | 278 | 204 | 30 | 44 | 17 | 308.973 | 0.391 |
| 182 | 0 | 430 | 395 | 319 | 23 | 76 | 24 | 148.054 | 0.233 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 383 | 342 | 161 | 25 | 156 | 22 | 435.359 | 0.177 |
| 190 | 0 | 729 | 691 | 441 | 0 | 250 | 41 | 190.131 | 0.253 |

## Interpretation

- Retained witnesses classify 13 bullet overlaps, 7 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.729 ms median and 38.423 ms p95.
- Modeled action hold counts were `{'2': 80, '3': 5611, '4': 9686, '5': 1319}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 51, '3': 9835, '4': 6657, '5': 153}`.
- Adaptive delay supports were `{'1,2,3': 32, '1,2,3,4': 54, '1,2,3,4,5,6': 21, '2,3': 67, '2,3,4': 1732, '2,3,4,5': 5475, '2,3,4,5,6': 5299, '3,4,5': 767, '3,4,5,6': 3249}`; 656 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 133/779.
- Robust viability supplied 15929 available policy queries (399 had new delay support outside the cached policy), constrained 7568 decisions, and exposed 8119 empty queried action sets. Recovery guidance was available/selected on 1371/810 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 6.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 997 unique policies with solve-time statistics `{'median': 218.2228000019677, 'p95': 378.838500007987, 'max': 770.8549000089988}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1788.0}`. Policy status counts were `{'pending_future_epoch': 324, 'queryable': 15933, 'expired': 202}`; 530 robust-mode decisions had no query.
- Of 8476 unambiguous output transitions, 7437 (0.877) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 35, 'robust_action_set_exhausted_before_hit': 6, 'missing_pre_hit_alive_decision': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 41 hit windows with a positive warning lead; those leads were `[9, 5, 5, 18, 11, 5, 6, 7, 3, 50, 9, 6, 15, 13, 11, 161, 37, 9, 8, 8, 12, 18, 16, 0, 17, 230, 13, 154, 116, 139, 153, 7, 8, 6, 8, 9, 11, 6, 3, 12, 8, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.399 during the 60 frames preceding a hit versus 0.215 outside those windows.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 18.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Causal Review

- Baseline `20260723_234414` had 37 hits; this run had 42. The aggregate
  recovery experiment therefore did not pass an improvement gate.
- Recovery was selected on 810 decisions, but only 2.17 percent of alive
  pre-hit-window decisions versus 5.24 percent outside. The extra hits cannot
  be causally assigned to recovery from this run.
- The trace still used the known-invalid static laser capsule: every allocated
  warning/fading record was full-length and its active transverse half-extent
  was doubled. Spells 154/158/162/166 account for 22 of 42 hits.
- The subsequent general correction retains complete native laser lifecycle
  state and lowers per-frame lethal boxes into `SegmentTrajectoryHazard`.
  Physical acceptance will compare the same phase metrics on a fresh run.
