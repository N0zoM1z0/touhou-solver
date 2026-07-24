# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_181700

## Scope And Integrity

- Valid practice scope: `3..45310` (7950 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 21, at `[2548, 4133, 11721, 12327, 12687, 13093, 13637, 16588, 21501, 21960, 22744, 28830, 30590, 31170, 35022, 35349, 36920, 37910, 39579, 43631, 44675]`.
- Hard no-Bomb verification: **PASS** across 7950 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2548-T1`. It occurred during a nonspell phase at player (336.261, 432.000), with 321 bullets and 0 lasers. The projectile model reported pipeline clearance -1.499.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 14 |
| `observed_bullet_overlap` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 2 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 17
- `fast_mode`: 14
- `corridor_deadline_miss`: 8
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2548 | nonspell | (336.261, 432.000) | `stay` | 321/0 | -1.499/-1.837 | 10f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4133 | nonspell | (8.000, 427.590) | `down_right` | 1014/0 | -2.134/-2.134 | 4f/20f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11721 | 57 夢境「二重大結界」 | (8.000, 432.000) | `stay` | 633/0 | -0.020/-0.020 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12327 | 57 夢境「二重大結界」 | (8.000, 372.593) | `right_fast` | 588/0 | 0.271/-0.886 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 12687 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left` | 612/0 | -1.750/-1.750 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13093 | 57 夢境「二重大結界」 | (364.686, 420.686) | `up_left_fast` | 591/0 | 1.480/-1.548 | 6f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13637 | 57 夢境「二重大結界」 | (371.849, 432.000) | `up_fast` | 619/0 | -1.231/-1.231 | 4f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 16588 | nonspell | (364.570, 432.000) | `up_fast` | 432/0 | -2.199/-2.199 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21501 | nonspell | (8.000, 419.832) | `up_fast` | 280/0 | 0.559/0.559 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21960 | nonspell | (161.629, 432.000) | `right_fast` | 618/0 | -2.913/-12.091 | 0f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22744 | nonspell | (191.685, 432.000) | `up_left_fast` | 327/0 | -2.474/-12.236 | 0f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28830 | nonspell | (8.000, 178.264) | `up_fast` | 137/0 | 15.356/-16.703 | 0f/4f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 30590 | 65 神技「八方龍殺陣」 | (250.794, 432.000) | `up_left_fast` | 1271/0 | -2.843/-3.495 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31170 | 65 神技「八方龍殺陣」 | (104.199, 396.971) | `stay` | 1238/0 | -1.635/-28.750 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35022 | nonspell | (8.000, 432.000) | `up_left_fast` | 108/0 | -2.168/-6.762 | 5f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35349 | nonspell | (328.194, 432.000) | `left_fast` | 74/0 | -1.636/-14.155 | 16f/21f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36920 | nonspell | (288.781, 432.000) | `stay` | 121/0 | -0.556/-0.556 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37910 | 69 回霊「夢想封印　侘」 | (99.354, 432.000) | `stay` | 461/0 | -2.704/-2.704 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39579 | 69 回霊「夢想封印　侘」 | (376.000, 306.859) | `left_fast` | 629/0 | -4.962/-5.948 | 33f/47f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43631 | 73 大結界「博麗弾幕結界」 | (215.081, 384.650) | `left_fast` | 1292/0 | -1.774/-1.774 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44675 | 73 大結界「博麗弾幕結界」 | (126.924, 382.637) | `right_fast` | 1323/0 | 0.537/-0.352 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 4427 | 4332 | 1934 | 0 | 2320 | 947 | 171.563 | 0.163 |
| 57 夢境「二重大結界」 | 5 | 806 | 796 | 126 | 0 | 656 | 167 | 229.006 | 0.262 |
| 61 | 0 | 697 | 690 | 172 | 0 | 501 | 150 | 194.089 | 0.107 |
| 65 神技「八方龍殺陣」 | 2 | 577 | 570 | 463 | 0 | 107 | 142 | 66.090 | 0.311 |
| 69 回霊「夢想封印　侘」 | 2 | 740 | 734 | 383 | 0 | 345 | 165 | 134.733 | 0.108 |
| 73 大結界「博麗弾幕結界」 | 2 | 703 | 692 | 298 | 0 | 390 | 164 | 147.510 | 0.078 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 27.892 ms median and 50.410 ms p95.
- The full enemy sensor produced 6565 snapshots; capture read time was `{'median': 34.18079999391921, 'p95': 59.61939998087473, 'max': 100.77479999745265}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 14.0}` frames, and 7 phase-counter discontinuities were excluded; 7679 decisions retained at least one robust-union body (maximum 58); 1361 decisions contained latent contact-disabled geometry (maximum 58), and 3785 contained bounded inactive-slot memory (maximum 52). 0 body samples retained observed world-motion estimates; world/internal speed and disagreement were `None` / `None` / `None`.
- The issue-time enemy guard retained 7950 observations, detected 2841 during-plan geometry changes, recertified 2841 decisions, and overrode 1526 actions. Read/recertificate timing was `{'median': 2.2318499977700412, 'p95': 4.792600026121363, 'max': 26.630800013663247}` / `{'median': 10.755399998743087, 'p95': 19.604900007834658, 'max': 33.07400000630878}` ms; 1357 issue captures contained latent bodies (maximum 58), and 3778 contained dormant bodies (maximum 52).
- The synchronous spell-owner guard retained 3522 observations (3503 contact enabled, 19 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 1503, '0x00597600': 2019}`.
- The terminal-threat heuristic covered 7950 decisions with horizon counts `{'0': 42, '10': 7126, '32': 782}`; it reported 9 collision and 84 sub-safety-clearance warnings, and relaxed 119 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 44, '3': 129, '4': 821, '5': 4864, '6': 2092}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 50, '3': 220, '4': 1498, '5': 5138, '6': 1044}`.
- Adaptive delay supports were `{'2,3': 48, '2,3,4,5': 98, '2,3,4,5,6': 220, '3,4': 1, '3,4,5': 160, '3,4,5,6': 5451, '4,5,6': 1957, '5,6': 3, '6': 12}`; 1653 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 78/160.
- Robust viability supplied 7814 available policy queries (0 had new delay support outside the cached policy), constrained 4319 decisions, and exposed 3376 empty queried action sets. Recovery guidance was available/selected on 931/595 empty-kernel queries; distant-kernel guidance was available/selected on 1956/1897. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 24.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 113.13708498984761, 'p95': 304.0, 'max': 502.41019097944263}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1172, '1': 1120, '2': 1057, '3': 913, '4': 887, '5': 890, '6': 897, '7': 878}`.
- Global-horizon/local-prefix cross-tab covered 3791 decisions: 1 had a winning global state but unsafe selected prefix, 1361 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 34 selected actions were outside the reported winning set. 2222 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1735 unique policies with solve-time statistics `{'median': 167.16270000324585, 'p95': 376.4962999848649, 'max': 507.5979999965057}` and first-observed ages `{'median': 5.0, 'p95': 9.0, 'max': 1799.0}`. Policy status counts were `{'pending_future_epoch': 35, 'queryable': 7815, 'expired': 16}`; 52 robust-mode decisions had no query.
- Of 4783 unambiguous output transitions, 4023 (0.841) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 19, 'unresolved_planner_failure': 1, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[15, 20, 4, 0, 4, 10, 8, 0, 0, 22, 22, 4, 6, 6, 10, 21, 6, 5, 47, 5, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.378 during the 60 frames preceding a hit versus 0.152 outside those windows.
- Mean selected control-reserve deficit was 4.196 during the 60 frames preceding a hit versus 1.047 outside those windows.
- Soft recovery was selected on 0.067 of alive decisions in the 60-frame pre-hit windows versus 0.079 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
