# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_175647

## Scope And Integrity

- Valid practice scope: `2..45711` (7802 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 25, at `[1047, 2156, 2726, 4092, 8816, 9845, 10478, 13035, 13599, 20452, 22510, 23079, 29457, 30835, 31543, 32358, 35354, 36180, 37298, 38985, 39657, 43695, 44329, 44678, 45071]`.
- Hard no-Bomb verification: **PASS** across 7802 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1047-T1`. It occurred during a nonspell phase at player (76.164, 430.451), with 220 bullets and 0 lasers. The projectile model reported pipeline clearance 0.612.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 15 |
| `observed_bullet_overlap` | 8 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 19
- `playfield_boundary`: 13
- `corridor_deadline_miss`: 12
- `pool_density_over_1000`: 8
- `action_lag_over_model`: 1
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1047 | nonspell | (76.164, 430.451) | `down_right` | 220/0 | 0.612/-0.652 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2156 | nonspell | (19.314, 432.000) | `down_right_fast` | 363/0 | -1.365/-1.365 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2726 | nonspell | (8.000, 432.000) | `right` | 513/0 | -2.232/-2.232 | 6f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4092 | nonspell | (17.334, 432.000) | `down_right_fast` | 1003/0 | -1.526/-1.526 | 6f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8816 | nonspell | (349.617, 421.668) | `left_fast` | 767/0 | -14.094/-14.094 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 9845 | nonspell | (134.391, 412.344) | `left_fast` | 547/0 | -5.004/-5.004 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10478 | nonspell | (216.086, 397.958) | `up_fast` | 157/0 | -15.955/-15.955 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13035 | 57 夢境「二重大結界」 | (30.274, 339.677) | `down_fast` | 635/0 | -3.214/-3.214 | 0f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13599 | 57 夢境「二重大結界」 | (8.000, 432.000) | `stay` | 626/0 | -0.636/-0.636 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20452 | 61 散霊「夢想封印　寂」 | (311.815, 404.988) | `left_fast` | 439/0 | 1.781/-5.810 | 6f/6f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22510 | nonspell | (8.000, 430.742) | `up_fast` | 854/0 | -1.743/-1.743 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23079 | nonspell | (8.000, 353.375) | `up` | 755/0 | -1.725/-1.725 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29457 | nonspell | (30.088, 16.000) | `left_fast` | 143/0 | -0.680/-1.601 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30835 | 65 神技「八方龍殺陣」 | (8.000, 416.000) | `stay` | 1032/0 | -1.039/-4.524 | 18f/26f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31543 | 65 神技「八方龍殺陣」 | (51.464, 432.000) | `down_fast` | 1050/0 | -1.448/-2.627 | 0f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32358 | 65 神技「八方龍殺陣」 | (8.000, 401.858) | `up_fast` | 1212/0 | -12.651/-12.651 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35354 | nonspell | (328.384, 432.000) | `left_fast` | 84/0 | -13.038/-13.038 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36180 | nonspell | (163.880, 420.686) | `up_left_fast` | 83/0 | 9.609/3.510 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37298 | nonspell | (16.485, 394.488) | `up_fast` | 101/0 | -13.079/-13.079 | 5f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 38985 | 69 回霊「夢想封印　侘」 | (8.000, 425.990) | `down_left` | 583/0 | -2.386/-2.386 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39657 | 69 回霊「夢想封印　侘」 | (21.126, 338.316) | `down_fast` | 723/0 | -3.677/-3.677 | 5f/28f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43695 | 73 大結界「博麗弾幕結界」 | (289.916, 417.504) | `up_fast` | 1274/0 | 1.594/-2.688 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44329 | 73 大結界「博麗弾幕結界」 | (194.146, 432.000) | `left_fast` | 1307/0 | -0.955/-1.883 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 44678 | 73 大結界「博麗弾幕結界」 | (118.906, 357.701) | `up_right_fast` | 1020/0 | -3.968/-3.968 | 5f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45071 | 73 大結界「博麗弾幕結界」 | (109.069, 385.507) | `down_right_fast` | 1216/0 | -1.774/-1.774 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 13 | 4379 | 4283 | 1567 | 0 | 2650 | 928 | 204.594 | 0.148 |
| 57 夢境「二重大結界」 | 2 | 749 | 742 | 172 | 0 | 548 | 163 | 229.468 | 0.330 |
| 61 散霊「夢想封印　寂」 | 1 | 647 | 638 | 162 | 0 | 458 | 143 | 198.614 | 0.153 |
| 65 神技「八方龍殺陣」 | 3 | 611 | 603 | 472 | 0 | 130 | 149 | 82.035 | 0.231 |
| 69 回霊「夢想封印　侘」 | 2 | 699 | 694 | 287 | 0 | 400 | 163 | 145.094 | 0.115 |
| 73 大結界「博麗弾幕結界」 | 4 | 717 | 705 | 262 | 0 | 431 | 163 | 164.208 | 0.042 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 29.186 ms median and 54.457 ms p95.
- The full enemy sensor produced 6541 snapshots; capture read time was `{'median': 37.36300001037307, 'p95': 65.04570000106469, 'max': 110.3956000006292}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 14.0}` frames, and 5 phase-counter discontinuities were excluded; 7484 decisions retained at least one robust-union body (maximum 49); 1294 decisions contained latent contact-disabled geometry (maximum 49), and 0 contained bounded inactive-slot memory (maximum 0). 0 body samples retained observed world-motion estimates; world/internal speed and disagreement were `None` / `None` / `None`.
- The issue-time enemy guard retained 7802 observations, detected 2806 during-plan geometry changes, recertified 2806 decisions, and overrode 1406 actions. Read/recertificate timing was `{'median': 2.34019999334123, 'p95': 4.923200001940131, 'max': 28.135400003520772}` / `{'median': 11.808049996034242, 'p95': 20.739899977343157, 'max': 44.91890000645071}` ms; 1295 issue captures contained latent bodies (maximum 49), and 0 contained dormant bodies (maximum 0).
- The synchronous spell-owner guard retained 3422 observations (3402 contact enabled, 20 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 1396, '0x00587A90': 2026}`.
- The terminal-threat heuristic covered 7802 decisions with horizon counts `{'0': 44, '10': 6788, '32': 970}`; it reported 15 collision and 98 sub-safety-clearance warnings, and relaxed 126 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 43, '3': 112, '4': 742, '5': 3533, '6': 3372}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 38, '3': 296, '4': 798, '5': 4597, '6': 2073}`.
- Adaptive delay supports were `{'2,3': 19, '2,3,4': 174, '2,3,4,5': 5, '2,3,4,5,6': 334, '3,4': 19, '3,4,5': 138, '3,4,5,6': 5222, '4,5,6': 1850, '5,6': 41}`; 1521 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 77/194.
- Robust viability supplied 7665 available policy queries (0 had new delay support outside the cached policy), constrained 4617 decisions, and exposed 2922 empty queried action sets. Recovery guidance was available/selected on 1043/668 empty-kernel queries; distant-kernel guidance was available/selected on 1546/1506. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 6.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 34.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 93.29523031752481, 'p95': 288.44410203711914, 'max': 524.8390229394153}`, and `{'median': 0.0, 'p95': 23.46647596359253, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1132, '1': 1065, '2': 1008, '3': 915, '4': 931, '5': 852, '6': 886, '7': 876}`.
- Global-horizon/local-prefix cross-tab covered 3633 decisions: 3 had a winning global state but unsafe selected prefix, 1168 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 48 selected actions were outside the reported winning set. 1978 newer issue-time hazard versions and 2 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1709 unique policies with solve-time statistics `{'median': 191.1608999944292, 'p95': 397.59009997942485, 'max': 515.6367000017781}` and first-observed ages `{'median': 5.0, 'p95': 10.0, 'max': 1782.0}`. Policy status counts were `{'pending_future_epoch': 34, 'queryable': 7668, 'expired': 10}`; 47 robust-mode decisions had no query.
- Of 4643 unambiguous output transitions, 3914 (0.843) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 21, 'robust_action_set_exhausted_before_hit': 3, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 20 hit windows with a positive warning lead; those leads were `[0, 9, 12, 10, 6, 5, 0, 7, 5, 6, 6, 6, 8, 26, 19, 6, 0, 0, 5, 11, 28, 5, 0, 9, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.316 during the 60 frames preceding a hit versus 0.153 outside those windows.
- Mean selected control-reserve deficit was 4.793 during the 60 frames preceding a hit versus 0.578 outside those windows.
- Soft recovery was selected on 0.088 of alive decisions in the 60-frame pre-hit windows versus 0.097 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
