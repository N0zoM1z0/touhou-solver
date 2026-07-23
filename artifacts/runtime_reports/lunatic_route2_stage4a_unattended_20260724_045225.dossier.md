# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_045225

## Scope And Integrity

- Valid practice scope: `2..45974` (9439 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 27, at `[2572, 4238, 9330, 10057, 10839, 11952, 12527, 12956, 13355, 13771, 16268, 17524, 19295, 22581, 28282, 30556, 31499, 32001, 35948, 36266, 37308, 38474, 40210, 44382, 44695, 44999, 45589]`.
- Hard no-Bomb verification: **PASS** across 9439 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2572-T1`. It occurred during a nonspell phase at player (342.895, 426.405), with 577 bullets and 0 lasers. The projectile model reported pipeline clearance 0.034.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 12 |
| `modeled_committed_prefix_collision` | 8 |
| `observed_enemy_body_overlap` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 3 |

Contributing factors:

- `fast_mode`: 18
- `corridor_deadline_miss`: 9
- `playfield_boundary`: 7
- `pool_density_over_1000`: 4
- `enemy_body_absent_from_action_snapshot`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2572 | nonspell | (342.895, 426.405) | `left_fast` | 577/0 | 0.034/0.034 | 0f/4f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4238 | nonspell | (343.883, 423.453) | `stay` | 999/0 | -1.031/-1.566 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9330 | nonspell | (56.000, 425.565) | `right_fast` | 684/0 | -16.346/-16.346 | 0f/0f | `observed_enemy_body_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 10057 | nonspell | (143.654, 427.648) | `stay` | 104/0 | -1.824/-1.824 | 5f/12f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 10839 | nonspell | (26.970, 420.431) | `stay` | 436/0 | 9.545/-0.051 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11952 | 57 夢境「二重大結界」 | (370.226, 421.158) | `up_fast` | 618/0 | -2.690/-2.690 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12527 | 57 夢境「二重大結界」 | (352.487, 425.129) | `left_fast` | 610/0 | 1.110/-2.493 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12956 | 57 夢境「二重大結界」 | (334.558, 364.309) | `down` | 610/0 | -3.440/-3.440 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 13355 | 57 夢境「二重大結界」 | (349.713, 348.704) | `left_fast` | 600/0 | -1.986/-1.986 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 13771 | 57 夢境「二重大結界」 | (14.636, 429.267) | `up_right_fast` | 601/0 | -1.964/-1.964 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 16268 | nonspell | (370.370, 390.636) | `stay` | 445/0 | -2.404/-2.404 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 17524 | nonspell | (17.292, 421.676) | `stay` | 198/0 | -2.659/-2.659 | 0f/24f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 19295 | 61 散霊「夢想封印　寂」 | (52.663, 425.450) | `stay` | 186/0 | 0.223/-17.109 | 2f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 22581 | nonspell | (8.118, 409.602) | `up_fast` | 810/0 | -2.633/-2.633 | 4f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28282 | nonspell | (363.792, 28.829) | `down_fast` | 118/0 | -1.888/-1.888 | 4f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30556 | 65 神技「八方龍殺陣」 | (376.000, 292.923) | `left_fast` | 803/0 | -2.449/-2.449 | 0f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 31499 | 65 神技「八方龍殺陣」 | (70.739, 431.869) | `up_fast` | 1328/0 | 3.329/-0.199 | 0f/5f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32001 | 65 神技「八方龍殺陣」 | (342.918, 421.757) | `down_right` | 1307/0 | 13.318/-13.874 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35948 | nonspell | (195.955, 415.029) | `up_right_fast` | 112/0 | 21.006/0.110 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 36266 | nonspell | (273.847, 427.559) | `left_fast` | 71/0 | 7.676/-18.876 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37308 | nonspell | (194.000, 431.147) | `up_right_fast` | 175/0 | 1.508/-1.521 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38474 | 69 回霊「夢想封印　侘」 | (22.998, 418.646) | `right_fast` | 427/0 | -1.678/-1.678 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40210 | 69 回霊「夢想封印　侘」 | (10.714, 320.857) | `up` | 718/0 | -6.710/-6.710 | 0f/25f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44382 | 73 大結界「博麗弾幕結界」 | (200.657, 430.625) | `down_left_fast` | 1310/0 | -0.195/-1.453 | 4f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 44695 | 73 大結界「博麗弾幕結界」 | (261.985, 419.973) | `left_fast` | 880/0 | -3.352/-3.599 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44999 | 73 大結界「博麗弾幕結界」 | (183.247, 425.883) | `left_fast` | 808/0 | -1.129/-2.296 | 3f/3f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 45589 | 73 大結界「博麗弾幕結界」 | (175.185, 380.036) | `left_fast` | 1320/0 | -0.070/-0.070 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 12 | 5398 | 5297 | 1618 | 62 | 3623 | 719 | 237.202 | 0.187 |
| 57 夢境「二重大結界」 | 5 | 859 | 850 | 77 | 0 | 773 | 124 | 290.869 | 0.229 |
| 61 散霊「夢想封印　寂」 | 1 | 812 | 798 | 216 | 6 | 576 | 110 | 227.892 | 0.198 |
| 65 神技「八方龍殺陣」 | 3 | 699 | 682 | 546 | 8 | 136 | 107 | 314.567 | 0.262 |
| 69 回霊「夢想封印　侘」 | 2 | 855 | 843 | 395 | 0 | 448 | 119 | 232.719 | 0.205 |
| 73 大結界「博麗弾幕結界」 | 4 | 816 | 810 | 296 | 0 | 514 | 123 | 315.695 | 0.046 |

## Interpretation

- Retained witnesses classify 12 bullet overlaps, 0 laser overlaps, and 4 exact same-epoch enemy-body overlaps; 3 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 27.192 ms median and 45.322 ms p95.
- The full enemy sensor produced 6604 snapshots; capture read time was `{'median': 24.85935000004247, 'p95': 47.800400003325194, 'max': 123.72350000077859}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 12.0}` frames, and 10 phase-counter discontinuities were excluded; 7335 decisions retained at least one contact-enabled body (maximum 37).
- The terminal-threat heuristic covered 9439 decisions with horizon counts `{'0': 48, '32': 9391}`; it reported 273 collision and 1804 sub-safety-clearance warnings.
- Modeled action hold counts were `{'2': 46, '3': 170, '4': 6210, '5': 2802, '6': 211}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 74, '3': 181, '4': 8310, '5': 874}`.
- Adaptive delay supports were `{'2,3': 85, '2,3,4': 60, '2,3,4,5': 93, '2,3,4,5,6': 575, '3,4': 6, '3,4,5': 456, '3,4,5,6': 8147, '4,5,6': 17}`; 202 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 143/557.
- Robust viability supplied 9280 available policy queries (76 had new delay support outside the cached policy), constrained 6070 decisions, and exposed 3148 empty queried action sets. Recovery guidance was available/selected on 1025/583 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 7.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 33.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 1302 unique policies with solve-time statistics `{'median': 253.2414500019513, 'p95': 362.91259998688474, 'max': 461.1177999759093}` and first-observed ages `{'median': 4.0, 'p95': 10.0, 'max': 1806.0}`. Policy status counts were `{'pending_future_epoch': 33, 'queryable': 9276, 'expired': 32}`; 61 robust-mode decisions had no query.
- Of 5611 unambiguous output transitions, 4879 (0.870) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 15, 'late_collision_after_positive_causal_margin': 3, 'robust_action_set_exhausted_before_hit': 8, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[4, 9, 0, 12, 0, 5, 9, 0, 0, 8, 7, 24, 8, 12, 11, 10, 5, 0, 0, 0, 9, 0, 25, 7, 8, 3, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.405 during the 60 frames preceding a hit versus 0.174 outside those windows.
- Soft recovery was selected on 0.061 of alive decisions in the 60-frame pre-hit windows versus 0.060 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
