# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260731_231944

## Scope And Integrity

- Valid practice scope: `2..44854` (10069 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 35, at `[498, 989, 3996, 4309, 9003, 9348, 9798, 10493, 11353, 11837, 13303, 16488, 17049, 17366, 18011, 20651, 21510, 22362, 22676, 27403, 27740, 28172, 28646, 29144, 30517, 34161, 34810, 35290, 36393, 37705, 39061, 39578, 42412, 43089, 44094]`.
- Hard no-Bomb verification: **PASS** across 10069 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F498-T1`. It occurred during a nonspell phase at player (192.000, 384.000), with 114 bullets and 0 lasers. The projectile model reported pipeline clearance 16.572.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 17 |
| `observed_bullet_overlap` | 10 |
| `sensor_gap_or_unmodeled_hazard` | 8 |

Contributing factors:

- `fast_mode`: 24
- `corridor_deadline_miss`: 21
- `action_lag_over_model`: 20
- `playfield_boundary`: 19
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 498 | nonspell | (192.000, 384.000) | `stay` | 114/0 | 16.572/16.572 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 989 | nonspell | (52.839, 424.939) | `right_fast` | 310/0 | -0.550/-0.550 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 3996 | nonspell | (360.689, 432.000) | `stay` | 913/0 | -1.771/-2.018 | 13f/17f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4309 | nonspell | (16.485, 432.000) | `down_right_fast` | 1057/0 | -2.380/-2.380 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9003 | nonspell | (348.352, 432.000) | `down_left` | 172/0 | -3.286/-11.429 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9348 | nonspell | (66.835, 432.000) | `down_fast` | 597/0 | -2.804/-2.804 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 9798 | nonspell | (19.891, 348.033) | `up_fast` | 756/0 | 0.308/0.308 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 10493 | nonspell | (8.000, 395.605) | `up_right_fast` | 137/0 | -14.087/-14.087 | 4f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11353 | 57 夢境「二重大結界」 | (13.657, 422.343) | `up_right_fast` | 574/0 | 0.780/-3.206 | 3f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11837 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 610/0 | -3.844/-3.844 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13303 | 57 夢境「二重大結界」 | (12.000, 432.000) | `right_fast` | 609/0 | -3.306/-3.306 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 16488 | nonspell | (8.000, 411.163) | `stay` | 129/0 | 0.360/0.360 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 17049 | nonspell | (118.266, 393.250) | `up_right_fast` | 297/0 | -1.428/-1.428 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 17366 | nonspell | (8.000, 323.908) | `left_fast` | 354/0 | -0.447/-0.447 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 18011 | nonspell | (235.115, 406.831) | `up_left` | 327/0 | -3.951/-3.951 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20651 | 61 散霊「夢想封印　寂」 | (376.000, 424.293) | `up` | 402/0 | 2.835/-1.301 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21510 | nonspell | (376.000, 418.745) | `down_fast` | 153/0 | 1.167/1.167 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22362 | nonspell | (376.000, 348.991) | `up_fast` | 905/0 | -2.442/-2.442 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22676 | nonspell | (78.488, 410.658) | `up_left_fast` | 577/0 | -2.104/-2.104 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27403 | nonspell | (359.260, 432.000) | `right_fast` | 113/0 | 1.828/1.828 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 27740 | nonspell | (236.000, 384.953) | `left_fast` | 78/0 | -1.332/-1.332 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 28172 | nonspell | (336.402, 411.300) | `up` | 138/0 | -0.843/-0.843 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28646 | nonspell | (19.681, 413.126) | `stay` | 164/0 | 2.414/-0.578 | 9f/9f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 29144 | nonspell | (33.456, 406.544) | `up_right_fast` | 126/0 | 0.458/0.458 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30517 | 65 神技「八方龍殺陣」 | (128.477, 432.000) | `right_fast` | 1107/0 | -2.616/-2.616 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34161 | nonspell | (277.005, 432.000) | `down` | 110/0 | -2.633/-2.633 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34810 | nonspell | (361.284, 310.378) | `up_right_fast` | 120/0 | -4.035/-8.264 | 8f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 35290 | nonspell | (373.700, 432.000) | `left` | 149/0 | 0.183/-2.494 | 0f/10f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36393 | nonspell | (214.191, 381.088) | `up_right_fast` | 168/0 | 4.089/0.812 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37705 | 69 回霊「夢想封印　侘」 | (8.000, 428.000) | `up_fast` | 565/0 | -2.325/-2.325 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39061 | 69 回霊「夢想封印　侘」 | (364.000, 432.000) | `up` | 640/0 | 0.624/-2.814 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39578 | 69 回霊「夢想封印　侘」 | (8.000, 386.695) | `up_right_fast` | 628/0 | -2.822/-2.822 | 9f/17f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42412 | 73 大結界「博麗弾幕結界」 | (208.764, 377.471) | `down_left_fast` | 1000/0 | 0.227/0.156 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43089 | 73 大結界「博麗弾幕結界」 | (147.308, 377.758) | `up_right_fast` | 1276/0 | -2.244/-2.897 | 4f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44094 | 73 大結界「博麗弾幕結界」 | (168.672, 369.346) | `left_fast` | 1355/0 | -2.207/-2.207 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 24 | 4975 | 3113 | 1481 | 0 | 0 | 255 | 284.346 | 0.201 |
| 57 夢境「二重大結界」 | 3 | 1153 | 927 | 304 | 0 | 0 | 101 | 165.487 | 0.340 |
| 61 散霊「夢想封印　寂」 | 1 | 1044 | 1013 | 482 | 0 | 0 | 132 | 120.487 | 0.190 |
| 65 神技「八方龍殺陣」 | 1 | 712 | 433 | 348 | 0 | 0 | 30 | 65.682 | 0.384 |
| 69 回霊「夢想封印　侘」 | 3 | 1164 | 834 | 505 | 0 | 0 | 84 | 94.936 | 0.239 |
| 73 大結界「博麗弾幕結界」 | 3 | 1021 | 954 | 501 | 0 | 0 | 130 | 115.004 | 0.077 |

## Interpretation

- Retained witnesses classify 10 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 7.000 frames p95. The local plan took 17.002 ms median and 78.493 ms p95.
- The full enemy sensor produced 6075 snapshots; capture read time was `{'median': 6.267000004299916, 'p95': 69.82190000417177, 'max': 151.5886999986833}`, snapshot age was `{'median': 5.0, 'p95': 10.0, 'max': 20.0}` frames, and 6 phase-counter discontinuities were excluded; 9536 decisions retained at least one robust-union body (maximum 59); 5308 decisions contained latent contact-disabled geometry (maximum 59), and 3604 contained bounded inactive-slot memory (maximum 31). 482 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.866383870442708, 'p95': 4.377655029296875, 'max': 11.495724487304688}` / `{'median': 2.931610107421875, 'p95': 3.922954797744751, 'max': 92.662109375}` / `{'median': 0.006684422492980957, 'p95': 0.7840652465820312, 'max': 92.662109375}`.
- The issue-time enemy guard retained 10069 observations, detected 3787 during-plan geometry changes, recertified 3787 decisions, and overrode 47 actions. Read/recertificate timing was `{'median': 1.5601000050082803, 'p95': 3.575399998226203, 'max': 49.31329999817535}` / `{'median': 3.2888999994611368, 'p95': 13.503700000001118, 'max': 54.44100000022445}` ms; 5310 issue captures contained latent bodies (maximum 59), and 3589 contained dormant bodies (maximum 31). Fresh/global transactions preserved 3740/3787 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 7784 observations (7744 contact enabled, 40 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 7784}`.
- The terminal-threat heuristic covered 10069 decisions with horizon counts `{'0': 533, '10': 9536}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 427, '3': 2328, '4': 2718, '5': 1105, '6': 3491}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 281, '2': 145, '3': 3567, '4': 3770, '5': 1454, '6': 852}`.
- Adaptive delay supports were `{'1,2': 191, '1,2,3': 66, '1,2,3,4': 70, '1,2,3,4,5': 44, '1,2,3,4,5,6': 542, '2,3': 68, '2,3,4': 623, '2,3,4,5': 2005, '2,3,4,5,6': 5635, '3,4': 11, '3,4,5': 245, '3,4,5,6': 509, '4,5': 1, '4,5,6': 51, '5,6': 3, '6': 5}`; 132 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 73/113.
- Robust viability supplied 7274 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 3621 empty queried action sets. Recovery guidance was available/selected on 1071/0 empty-kernel queries; distant-kernel guidance was available/selected on 1968/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 997, '1': 1015, '2': 775, '3': 929, '4': 891, '5': 888, '6': 880, '7': 899}`.
- Global-horizon/local-prefix cross-tab covered 2960 decisions: 9 had a winning global state but unsafe selected prefix, 1263 had a losing global state but safe short prefix, 4 selected globally certified actions contradicted the fresh local prefix checker, and 202 selected actions were outside the reported winning set. 1912 newer issue-time hazard versions and 8 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 732 unique policies with solve-time statistics `{'median': 144.9267999996664, 'p95': 1390.3320000099484, 'max': 2842.766899993876}` and first-observed ages `{'median': 3.0, 'p95': 11.0, 'max': 1794.0}`. Policy status counts were `{'pending_future_epoch': 266, 'queryable': 7198, 'expired': 2365}`; 2555 robust-mode decisions had no query.
- Of 5171 unambiguous output transitions, 5022 (0.971) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 2, 'late_collision_after_positive_causal_margin': 5, 'global_viability_kernel_exhausted_before_hit': 25, 'robust_action_set_exhausted_before_hit': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[0, 0, 17, 5, 0, 0, 0, 6, 6, 6, 5, 0, 0, 0, 0, 4, 0, 3, 11, 0, 0, 0, 9, 0, 7, 0, 8, 10, 0, 3, 7, 17, 6, 7, 11]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.333 during the 60 frames preceding a hit versus 0.215 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Causal Diagnosis

This is the valid source-v3 physical gate: the Stage-4A ECL image and SHA-256
were present and runtime identity passed. The run completed with 35 hits,
first hit 498, zero Bombs, an accepted replay, and full cleanup. Different-RNG
hits are observational; exact activation is decisive.

Of 1,859 future-source projections, only one completed. 1,836 crossed
`enemy_manager_frame`; 13 exposed impossible auxiliary depth from torn roots,
five reached unsupported dynamic float variable 10069, and four reached
separate auxiliary-timer/phase-successor residuals. The only complete root was
frame 4676, captured in 16.118 ms during a freeze and not consumed by a hard
policy. All 4,499 state-eligible nonspell records remained
`future_policy_unavailable`; first hit 498 was preceded by 332 such records.

The contiguous topology therefore removed sparse-call overhead but not the
observer allocations/copies inside the bracket. Windows local timing shows a
10.32 MiB ctypes allocation, `.raw` copy, and bytes slice cost about
3.74/3.43/3.40 ms respectively. The next implementation retains one
worker-local destination, uses `ReadProcessMemory` directly into it, and
exposes manager/pool memoryviews without copies. No coverage rule is relaxed.
