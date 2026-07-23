# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_033341

## Scope And Integrity

- Valid practice scope: `2..46032` (10431 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 27, at `[4318, 11459, 12026, 12398, 12983, 13722, 19141, 19457, 20405, 21393, 21954, 22665, 23313, 28020, 28524, 29993, 31476, 32005, 32976, 36776, 37257, 37927, 39560, 40070, 43711, 44996, 45925]`.
- Hard no-Bomb verification: **PASS** across 10431 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F4318-T1`. It occurred during a nonspell phase at player (27.985, 414.656), with 877 bullets and 0 lasers. The projectile model reported pipeline clearance -2.079.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 14 |
| `observed_bullet_overlap` | 10 |
| `sensor_gap_or_unmodeled_hazard` | 2 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 19
- `corridor_deadline_miss`: 14
- `playfield_boundary`: 10
- `pool_density_over_1000`: 6

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4318 | nonspell | (27.985, 414.656) | `up_left` | 877/0 | -2.079/-4.133 | 6f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11459 | 57 夢境「二重大結界」 | (8.090, 423.114) | `right_fast` | 446/0 | -2.022/-2.022 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12026 | 57 夢境「二重大結界」 | (40.336, 430.213) | `left_fast` | 594/0 | -2.914/-2.914 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12398 | 57 夢境「二重大結界」 | (9.029, 377.141) | `up_fast` | 581/0 | -2.572/-2.572 | 2f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12983 | 57 夢境「二重大結界」 | (20.453, 429.219) | `down_left_fast` | 597/0 | -3.498/-3.498 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13722 | 57 夢境「二重大結界」 | (40.047, 327.406) | `down_left_fast` | 582/0 | 0.237/-1.425 | 6f/12f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 19141 | 61 散霊「夢想封印　寂」 | (51.045, 426.762) | `right_fast` | 129/0 | 1.752/-1.116 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19457 | 61 散霊「夢想封印　寂」 | (111.131, 428.258) | `stay` | 396/0 | -3.105/-9.888 | 3f/16f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 20405 | 61 散霊「夢想封印　寂」 | (367.763, 421.207) | `up_fast` | 433/0 | -2.048/-2.435 | 3f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 21393 | 61 散霊「夢想封印　寂」 | (211.384, 426.823) | `up_left_fast` | 300/0 | -0.439/-0.439 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21954 | nonspell | (372.840, 372.992) | `up` | 385/0 | -3.704/-3.704 | 2f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22665 | nonspell | (9.572, 414.198) | `up_fast` | 821/0 | -2.175/-2.175 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23313 | nonspell | (11.562, 422.859) | `down` | 638/0 | 2.052/-2.893 | 0f/4f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28020 | nonspell | (372.222, 384.818) | `stay` | 192/0 | -1.945/-2.009 | 2f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 28524 | nonspell | (180.179, 424.231) | `up_right` | 195/0 | -2.038/-2.038 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 29993 | nonspell | (135.768, 424.437) | `up_fast` | 145/0 | -1.009/-3.538 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31476 | 65 神技「八方龍殺陣」 | (370.624, 424.825) | `stay` | 1215/0 | -2.130/-13.578 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32005 | 65 神技「八方龍殺陣」 | (308.719, 378.857) | `down_left` | 1062/0 | -1.293/-15.838 | 15f/15f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 32976 | 65 神技「八方龍殺陣」 | (36.733, 410.921) | `right_fast` | 1056/0 | 10.561/2.561 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36776 | nonspell | (162.246, 355.019) | `right_fast` | 176/0 | -18.649/-18.649 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37257 | nonspell | (367.018, 236.340) | `up_fast` | 176/0 | -16.388/-16.388 | 3f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 37927 | nonspell | (366.553, 394.970) | `down_left_fast` | 149/0 | 1.069/-13.352 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39560 | 69 回霊「夢想封印　侘」 | (369.903, 192.228) | `down_left_fast` | 533/0 | -3.163/-3.163 | 4f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40070 | 69 回霊「夢想封印　侘」 | (372.204, 417.686) | `down_left_fast` | 651/0 | -2.545/-2.545 | 5f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43711 | 73 大結界「博麗弾幕結界」 | (55.079, 355.571) | `down_fast` | 1096/0 | -2.821/-2.821 | 4f/11f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 44996 | 73 大結界「博麗弾幕結界」 | (62.004, 350.839) | `down_left_fast` | 1320/0 | 1.283/-2.954 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45925 | 73 大結界「博麗弾幕結界」 | (78.367, 368.165) | `down_fast` | 1315/0 | -3.552/-3.552 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 5945 | 5779 | 1755 | 121 | 3930 | 371 | 254.497 | 0.128 |
| 57 夢境「二重大結界」 | 5 | 951 | 932 | 74 | 19 | 839 | 63 | 275.656 | 0.295 |
| 61 散霊「夢想封印　寂」 | 4 | 918 | 894 | 223 | 10 | 668 | 58 | 262.730 | 0.121 |
| 65 神技「八方龍殺陣」 | 3 | 805 | 784 | 547 | 0 | 237 | 56 | 333.206 | 0.229 |
| 69 回霊「夢想封印　侘」 | 2 | 916 | 899 | 527 | 0 | 372 | 61 | 214.136 | 0.141 |
| 73 大結界「博麗弾幕結界」 | 3 | 896 | 882 | 441 | 0 | 441 | 63 | 335.710 | 0.013 |

## Interpretation

- Retained witnesses classify 10 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 19.764 ms median and 36.102 ms p95.
- The full enemy sensor produced 1955 snapshots; capture read time was `{'median': 17.70690002012998, 'p95': 28.042899997672066, 'max': 62.30999997933395}`, snapshot age was `{'median': 11.0, 'p95': 20.0, 'max': 24.0}` frames, and 9 phase-counter discontinuities were excluded; 8231 decisions retained at least one contact-enabled body (maximum 36).
- Modeled action hold counts were `{'2': 45, '3': 327, '4': 9051, '5': 1008}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 10, '2': 50, '3': 1321, '4': 9022, '5': 28}`.
- Adaptive delay supports were `{'1,2': 10, '1,2,3': 55, '1,2,3,4': 7, '2,3': 24, '2,3,4': 350, '2,3,4,5': 1121, '2,3,4,5,6': 4661, '3,4': 1, '3,4,5': 179, '3,4,5,6': 4023}`; 163 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 126/637.
- Robust viability supplied 10170 available policy queries (150 had new delay support outside the cached policy), constrained 6487 decisions, and exposed 3567 empty queried action sets. Recovery guidance was available/selected on 1376/815 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 5.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 31.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 672 unique policies with solve-time statistics `{'median': 266.30599999043625, 'p95': 397.12839998537675, 'max': 476.94560000672936}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1787.0}`. Policy status counts were `{'pending_future_epoch': 122, 'queryable': 10171, 'expired': 60}`; 183 robust-mode decisions had no query.
- Of 5826 unambiguous output transitions, 4981 (0.855) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 13, 'robust_action_set_exhausted_before_hit': 13, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 23 hit windows with a positive warning lead; those leads were `[11, 5, 6, 6, 5, 12, 6, 16, 7, 4, 7, 9, 4, 7, 0, 6, 7, 15, 0, 0, 10, 0, 11, 11, 11, 3, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.192 during the 60 frames preceding a hit versus 0.133 outside those windows.
- Soft recovery was selected on 0.096 of alive decisions in the 60-frame pre-hit windows versus 0.075 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Causal Review

- This first original-game Stage-4A baseline completed frames `2..46032`
  with 10,431 decisions, 27 hits, and zero Bomb input. Auto-confirm,
  post-stage no-save, and exact-process termination all passed.
- Twenty-four hits already have bullet overlap or committed-prefix evidence.
  Two are sensor gaps and frame 32,976 is an exact helper-body overlap with
  slot 34 (`0x00634860`). The action snapshot was seven frames old and
  retained only the boss; the stable hit epoch contained 35 enabled bodies,
  including the overlapping helper.
- The full enemy pool matters much more here than in Stage 5: 8,231 decisions
  retained at least one body and the maximum was 36. The old contiguous sensor
  cost 17.71/28.04 ms at median/p95 and produced 11/20-frame snapshot age.
- A same-process differential replaced the 9.8 MiB contiguous read with 480
  flag probes plus active 1,500-byte body windows. In a paused eight-body
  regime, all 30 pointer sets matched while capture median fell 14.06 to
  3.34 ms. The sensor now uses this sparse reader every four manager frames.
- Thirteen hit windows had globally exhausted viability and another thirteen
  exhausted the local robust set. Fast-mode occupancy was 35.7 percent in the
  preceding 60-frame windows versus 29.5 percent outside, but this correlation
  is not yet enough to add a blanket fast-action penalty.
- The next Stage-4A differential must verify that sparse/four-frame sensing
  restores current helper visibility without degrading decision cadence. ECL
  future activation remains necessary for a true same-frame guarantee.
