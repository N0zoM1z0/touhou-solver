# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_084835

## Scope And Integrity

- Valid practice scope: `2..43356` (8885 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 19, at `[4270, 9287, 9854, 10984, 11611, 12046, 12637, 20463, 21086, 27456, 28694, 29106, 30112, 33649, 35256, 38266, 40918, 41592, 42974]`.
- Hard no-Bomb verification: **PASS** across 8885 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F4270-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 1107 bullets and 0 lasers. The projectile model reported pipeline clearance -1.846.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 4 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 15
- `playfield_boundary`: 11
- `pool_density_over_1000`: 7
- `corridor_deadline_miss`: 6
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4270 | nonspell | (376.000, 432.000) | `up_left` | 1107/0 | -1.846/-1.846 | 0f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9287 | nonspell | (234.571, 424.239) | `up_fast` | 788/0 | 12.750/1.219 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 9854 | nonspell | (110.162, 432.000) | `down_right_fast` | 541/0 | -17.218/-17.218 | 9f/13f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 10984 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 437/0 | -1.360/-1.360 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11611 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_fast` | 603/0 | 0.519/-2.437 | 4f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12046 | 57 夢境「二重大結界」 | (8.000, 390.072) | `up_right_fast` | 600/0 | 0.681/-2.348 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12637 | 57 夢境「二重大結界」 | (8.000, 432.000) | `right_fast` | 632/0 | -1.926/-1.926 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20463 | nonspell | (19.314, 416.686) | `right` | 536/0 | -2.742/-3.592 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21086 | nonspell | (35.843, 432.000) | `left_fast` | 565/0 | 1.275/0.238 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27456 | nonspell | (236.179, 432.000) | `right_fast` | 118/0 | -2.101/-2.101 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28694 | 65 神技「八方龍殺陣」 | (108.803, 372.876) | `left_fast` | 1199/0 | 29.380/3.077 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29106 | 65 神技「八方龍殺陣」 | (305.420, 372.206) | `right_fast` | 1052/0 | 20.984/9.148 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30112 | 65 神技「八方龍殺陣」 | (241.407, 432.000) | `right` | 1271/0 | -1.581/-5.196 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33649 | nonspell | (305.758, 391.714) | `left_fast` | 148/0 | -15.999/-15.999 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35256 | nonspell | (123.096, 415.581) | `right_fast` | 178/0 | 31.900/6.269 | 0f/0f | `observed_enemy_body_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 38266 | 69 回霊「夢想封印　侘」 | (376.000, 409.795) | `down_left_fast` | 715/0 | -0.460/-0.460 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40918 | 73 大結界「博麗弾幕結界」 | (226.736, 432.000) | `down_fast` | 1000/0 | 0.938/-1.904 | 0f/27f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41592 | 73 大結界「博麗弾幕結界」 | (141.320, 382.261) | `up_right_fast` | 1273/0 | 0.085/0.085 | 0f/13f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42974 | 73 大結界「博麗弾幕結界」 | (173.743, 384.100) | `stay` | 1341/0 | -0.212/-0.212 | 5f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 5043 | 4944 | 1430 | 42 | 3411 | 665 | 244.774 | 0.112 |
| 57 夢境「二重大結界」 | 4 | 883 | 875 | 128 | 0 | 742 | 123 | 291.537 | 0.174 |
| 61 | 0 | 639 | 632 | 136 | 14 | 473 | 83 | 229.196 | 0.134 |
| 65 神技「八方龍殺陣」 | 3 | 635 | 617 | 534 | 0 | 83 | 92 | 302.701 | 0.147 |
| 69 回霊「夢想封印　侘」 | 1 | 852 | 842 | 446 | 0 | 380 | 119 | 231.714 | 0.145 |
| 73 大結界「博麗弾幕結界」 | 3 | 833 | 824 | 360 | 0 | 462 | 120 | 337.858 | 0.041 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 25.515 ms median and 41.648 ms p95.
- The full enemy sensor produced 6119 snapshots; capture read time was `{'median': 27.86740000010468, 'p95': 50.53790000965819, 'max': 76.4783000049647}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 10 phase-counter discontinuities were excluded; 6837 decisions retained at least one contact-enabled body (maximum 36).
- The terminal-threat heuristic covered 8885 decisions with horizon counts `{'0': 48, '10': 7938, '32': 899}`; it reported 9 collision and 136 sub-safety-clearance warnings, and relaxed 100 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 51, '3': 197, '4': 6419, '5': 2218}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 62, '3': 447, '4': 8085, '5': 291}`.
- Adaptive delay supports were `{'1,2,3': 26, '1,2,3,4': 7, '2,3': 60, '2,3,4': 228, '2,3,4,5': 492, '2,3,4,5,6': 548, '3,4': 116, '3,4,5': 742, '3,4,5,6': 6571, '4,5,6': 95}`; 185 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 122/536.
- Robust viability supplied 8734 available policy queries (56 had new delay support outside the cached policy), constrained 5551 decisions, and exposed 3034 empty queried action sets. Recovery guidance was available/selected on 1186/654 empty-kernel queries; distant-kernel guidance was available/selected on 1588/1534. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 7.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 34.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 80.0, 'p95': 222.8542124349459, 'max': 555.409758646713}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- The rolling worker produced 1202 unique policies with solve-time statistics `{'median': 257.9369000013685, 'p95': 368.9328000182286, 'max': 448.68569998652674}` and first-observed ages `{'median': 4.0, 'p95': 11.0, 'max': 1808.0}`. Policy status counts were `{'pending_future_epoch': 35, 'queryable': 8731, 'expired': 29}`; 61 robust-mode decisions had no query.
- Of 5422 unambiguous output transitions, 4718 (0.870) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 16, 'unresolved_planner_failure': 1, 'robust_action_set_exhausted_before_hit': 1, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[14, 0, 13, 3, 12, 9, 8, 9, 8, 4, 0, 0, 0, 0, 0, 9, 27, 13, 14]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.232 during the 60 frames preceding a hit versus 0.114 outside those windows.
- Mean selected control-reserve deficit was 3.654 during the 60 frames preceding a hit versus 0.581 outside those windows.
- Soft recovery was selected on 0.096 of alive decisions in the 60-frame pre-hit windows versus 0.075 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
