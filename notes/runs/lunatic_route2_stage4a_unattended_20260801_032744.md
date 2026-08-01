# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_032744

## Scope And Integrity

- Valid practice scope: `2..45771` (11657 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 22, at `[792, 1207, 1819, 2242, 2565, 2896, 4314, 8813, 9311, 9882, 11948, 12934, 13775, 19632, 21808, 22142, 22977, 25213, 39662, 40169, 44556, 45212]`.
- Hard no-Bomb verification: **PASS** across 11657 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F792-T1`. It occurred during a nonspell phase at player (63.522, 432.000), with 242 bullets and 0 lasers. The projectile model reported pipeline clearance -2.431.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `sensor_gap_or_unmodeled_hazard` | 8 |
| `modeled_committed_prefix_collision` | 6 |
| `observed_bullet_overlap` | 6 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 16
- `fast_mode`: 13
- `action_lag_over_model`: 11
- `corridor_deadline_miss`: 7
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 792 | nonspell | (63.522, 432.000) | `down` | 242/0 | -2.431/-2.431 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1207 | nonspell | (8.000, 415.805) | `right_fast` | 364/0 | 3.871/3.082 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 1819 | nonspell | (79.973, 432.000) | `down_right` | 282/0 | -0.765/-0.765 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 2242 | nonspell | (303.584, 432.000) | `down_left` | 301/0 | -2.695/-2.695 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 2565 | nonspell | (303.480, 432.000) | `stay` | 503/0 | 14.610/-2.754 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 2896 | nonspell | (146.243, 412.484) | `up_left` | 670/0 | 8.251/2.307 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 4314 | nonspell | (8.000, 412.284) | `stay` | 968/0 | 4.704/1.811 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 8813 | nonspell | (352.000, 424.000) | `up_right_fast` | 765/0 | -14.965/-20.714 | 13f/18f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 9311 | nonspell | (336.624, 432.000) | `right_fast` | 752/0 | -13.028/-14.617 | 5f/14f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 9882 | nonspell | (8.000, 432.000) | `stay` | 421/0 | -1.185/-1.185 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11948 | 57 夢境「二重大結界」 | (111.687, 282.997) | `up_left_fast` | 627/0 | -1.319/-1.319 | 7f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12934 | 57 夢境「二重大結界」 | (56.307, 426.343) | `up_left_fast` | 616/0 | 0.395/-1.470 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13775 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 578/0 | -1.781/-1.781 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19632 | 61 散霊「夢想封印　寂」 | (374.359, 432.000) | `left_fast` | 143/0 | -4.536/-4.536 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21808 | nonspell | (190.174, 432.000) | `left` | 271/0 | 12.320/6.966 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 22142 | nonspell | (53.794, 432.000) | `right_fast` | 309/0 | 16.429/14.980 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 22977 | nonspell | (376.000, 380.000) | `up_fast` | 545/0 | 8.828/-34.011 | 69f/79f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 25213 | nonspell | (376.000, 415.029) | `stay` | 0/0 | 407.360/407.360 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 39662 | 69 回霊「夢想封印　侘」 | (10.828, 429.172) | `up_right_fast` | 677/0 | -2.524/-2.524 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40169 | 69 回霊「夢想封印　侘」 | (12.000, 432.000) | `right_fast` | 638/0 | -2.772/-2.772 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44556 | 73 大結界「博麗弾幕結界」 | (269.024, 355.528) | `left_fast` | 1305/0 | -1.234/-3.022 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45212 | 73 大結界「博麗弾幕結界」 | (185.405, 377.895) | `down_right_fast` | 1345/0 | -1.304/-1.304 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 14 | 6524 | 289 | 70 | 0 | 306 | 23 | 845.176 | 0.239 |
| 57 夢境「二重大結界」 | 3 | 1188 | 699 | 255 | 0 | 0 | 72 | 180.171 | 0.344 |
| 61 散霊「夢想封印　寂」 | 1 | 1029 | 1022 | 382 | 0 | 0 | 167 | 127.485 | 0.190 |
| 65 | 0 | 872 | 347 | 265 | 0 | 0 | 14 | 58.598 | 0.495 |
| 69 回霊「夢想封印　侘」 | 2 | 1084 | 1079 | 608 | 0 | 0 | 182 | 95.614 | 0.229 |
| 73 大結界「博麗弾幕結界」 | 2 | 960 | 953 | 507 | 0 | 0 | 183 | 126.862 | 0.075 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.570 ms median and 33.821 ms p95.
- The full enemy sensor produced 6373 snapshots; capture read time was `{'median': 5.6677999964449555, 'p95': 29.42250001069624, 'max': 529.180900004576}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 98.0}` frames, and 5 phase-counter discontinuities were excluded; 11447 decisions retained at least one robust-union body (maximum 56); 5977 decisions contained latent contact-disabled geometry (maximum 56), and 4495 contained bounded inactive-slot memory (maximum 33). 348 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.6991195678710938, 'p95': 4.068111419677734, 'max': 5.20050048828125}` / `{'median': 2.918061137199402, 'p95': 3.9891040325164795, 'max': 5.2004852294921875}` / `{'median': 0.3424518257379532, 'p95': 3.904379305632218, 'max': 8.20001220703125}`.
- The issue-time enemy guard retained 11657 observations, detected 3922 during-plan geometry changes, recertified 3922 decisions, and overrode 66 actions. Read/recertificate timing was `{'median': 1.5645999956177548, 'p95': 2.958299999590963, 'max': 278.7238000018988}` / `{'median': 2.516799999284558, 'p95': 8.935799996834248, 'max': 435.8680000004824}` ms; 5992 issue captures contained latent bodies (maximum 56), and 4483 contained dormant bodies (maximum 33). Fresh/global transactions preserved 3856/3922 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9967 observations (9927 contact enabled, 40 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9967}`.
- The terminal-threat heuristic covered 11657 decisions with horizon counts `{'0': 34, '10': 11623}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 31, '3': 7185, '4': 3212, '5': 757, '6': 472}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 924, '3': 9020, '4': 1499, '5': 155, '6': 59}`.
- Adaptive delay supports were `{'1,2,3': 6, '1,2,3,4': 39, '1,2,3,4,5': 23, '2,3': 824, '2,3,4': 3134, '2,3,4,5': 3821, '2,3,4,5,6': 2489, '3,4': 160, '3,4,5': 361, '3,4,5,6': 745, '4,5': 1, '4,5,6': 25, '5,6': 22, '6': 7}`; 105 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 22/113.
- Robust viability supplied 4389 available policy queries (0 had new delay support outside the cached policy), constrained 306 decisions, and exposed 2087 empty queried action sets. Recovery guidance was available/selected on 776/0 empty-kernel queries; distant-kernel guidance was available/selected on 1093/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 674, '1': 601, '2': 482, '3': 490, '4': 529, '5': 531, '6': 520, '7': 562}`.
- Global-horizon/local-prefix cross-tab covered 2371 decisions: 0 had a winning global state but unsafe selected prefix, 1150 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 178 selected actions were outside the reported winning set. 1007 newer issue-time hazard versions and 3 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 641 unique policies with solve-time statistics `{'median': 123.07469999359455, 'p95': 220.41389999503735, 'max': 3128.968699995312}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1772.0}`. Policy status counts were `{'pending_future_epoch': 225, 'queryable': 4373, 'expired': 2555}`; 2764 robust-mode decisions had no query.
- Of 6571 unambiguous output transitions, 6283 (0.956) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 8, 'unresolved_planner_failure': 4, 'late_collision_after_positive_causal_margin': 2, 'missing_pre_hit_alive_decision': 3, 'robust_action_set_exhausted_before_hit': 5}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[0, 0, 0, 0, 0, 0, 0, 18, 14, 5, 19, 8, 5, 4, 0, 0, 79, 0, 7, 7, 10, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.486 during the 60 frames preceding a hit versus 0.247 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
