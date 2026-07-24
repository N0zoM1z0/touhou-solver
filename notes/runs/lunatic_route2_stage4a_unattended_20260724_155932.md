# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_155932

## Scope And Integrity

- Valid practice scope: `2..45110` (8293 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 19, at `[1632, 2609, 4023, 4330, 9430, 9859, 11460, 12203, 12512, 12881, 13262, 20910, 22041, 22862, 31415, 35419, 36008, 37260, 45012]`.
- Hard no-Bomb verification: **PASS** across 8293 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1632-T1`. It occurred during a nonspell phase at player (22.345, 432.000), with 431 bullets and 0 lasers. The projectile model reported pipeline clearance 0.484.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 5 |
| `sensor_gap_or_unmodeled_hazard` | 4 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 12
- `playfield_boundary`: 12
- `corridor_deadline_miss`: 6
- `pool_density_over_1000`: 2
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1632 | nonspell | (22.345, 432.000) | `left_fast` | 431/0 | 0.484/-1.622 | 0f/4f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2609 | nonspell | (299.429, 432.000) | `up` | 363/0 | -3.215/-3.215 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4023 | nonspell | (8.000, 432.000) | `left_fast` | 999/0 | -2.201/-2.201 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4330 | nonspell | (111.732, 410.584) | `down_left_fast` | 894/0 | -1.857/-1.857 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 9430 | nonspell | (20.676, 432.000) | `right_fast` | 270/0 | -10.205/-14.781 | 7f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 9859 | nonspell | (92.932, 384.965) | `down_right_fast` | 474/0 | 19.973/-15.405 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11460 | 57 夢境「二重大結界」 | (8.000, 378.383) | `up_right_fast` | 608/0 | 0.534/-0.744 | 5f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12203 | 57 夢境「二重大結界」 | (8.000, 432.000) | `stay` | 601/0 | -2.324/-2.324 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12512 | 57 夢境「二重大結界」 | (193.988, 432.000) | `left` | 547/0 | -2.772/-2.772 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12881 | 57 夢境「二重大結界」 | (8.000, 407.369) | `up_right` | 575/0 | -1.301/-1.301 | 4f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13262 | 57 夢境「二重大結界」 | (8.000, 387.582) | `up_left_fast` | 593/0 | -0.908/-3.196 | 3f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 20910 | 61 散霊「夢想封印　寂」 | (29.238, 432.000) | `up` | 424/0 | -15.483/-15.483 | 5f/12f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22041 | nonspell | (8.000, 417.885) | `stay` | 647/0 | -1.921/-1.921 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22862 | nonspell | (24.601, 432.000) | `up_fast` | 620/0 | -0.622/-2.538 | 8f/30f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31415 | 65 神技「八方龍殺陣」 | (56.081, 413.786) | `left_fast` | 1034/0 | 0.540/-1.216 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35419 | nonspell | (317.827, 136.404) | `up_right_fast` | 118/0 | -22.780/-22.780 | 0f/0f | `observed_enemy_body_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 36008 | nonspell | (360.000, 423.171) | `stay` | 100/0 | 14.381/6.865 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37260 | nonspell | (102.099, 415.919) | `down_left_fast` | 114/0 | -10.916/-10.916 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45012 | 73 大結界「博麗弾幕結界」 | (170.341, 384.298) | `down_left_fast` | 1342/0 | -1.989/-1.989 | 6f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 11 | 4898 | 4787 | 1474 | 0 | 3207 | 892 | 272.457 | 0.113 |
| 57 夢境「二重大結界」 | 5 | 790 | 782 | 127 | 0 | 653 | 135 | 348.027 | 0.266 |
| 61 散霊「夢想封印　寂」 | 1 | 725 | 712 | 175 | 0 | 520 | 142 | 276.860 | 0.163 |
| 65 神技「八方龍殺陣」 | 1 | 569 | 559 | 456 | 0 | 97 | 110 | 364.470 | 0.237 |
| 69 | 0 | 727 | 718 | 391 | 0 | 319 | 154 | 271.838 | 0.115 |
| 73 大結界「博麗弾幕結界」 | 1 | 584 | 577 | 336 | 0 | 238 | 100 | 432.307 | 0.020 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 29.094 ms median and 48.377 ms p95.
- The full enemy sensor produced 6532 snapshots; capture read time was `{'median': 34.18430000601802, 'p95': 56.5649000054691, 'max': 92.08839997882023}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 12.0}` frames, and 5 phase-counter discontinuities were excluded; 6393 decisions retained at least one contact-enabled body (maximum 37).
- No issue-time enemy-geometry guard telemetry was present.
- The synchronous spell-owner guard retained 3395 observations (3381 contact enabled, 14 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3395}`.
- The terminal-threat heuristic covered 8293 decisions with horizon counts `{'0': 44, '10': 7197, '32': 1052}`; it reported 16 collision and 124 sub-safety-clearance warnings, and relaxed 142 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 45, '3': 156, '4': 1904, '5': 5269, '6': 919}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 28, '3': 213, '4': 4490, '5': 2884, '6': 678}`.
- Adaptive delay supports were `{'1,2,3,4,5,6': 13, '2,3': 7, '2,3,4': 3, '2,3,4,5': 110, '2,3,4,5,6': 616, '3,4': 1, '3,4,5': 27, '3,4,5,6': 6468, '4,5,6': 921, '5,6': 122, '6': 5}`; 140 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 62/175.
- Robust viability supplied 8135 available policy queries (0 had new delay support outside the cached policy), constrained 5034 decisions, and exposed 2959 empty queried action sets. Recovery guidance was available/selected on 1049/635 empty-kernel queries; distant-kernel guidance was available/selected on 1611/1542. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 5.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 29.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 80.0, 'p95': 252.98221281347034, 'max': 417.22895393296955}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1074, '1': 1038, '2': 1080, '3': 1044, '4': 1004, '5': 936, '6': 986, '7': 973}`.
- Global-horizon/local-prefix cross-tab covered 6613 decisions: 32 had a winning global state but unsafe selected prefix, 2395 had a losing global state but safe short prefix, 30 selected globally certified actions contradicted the fresh local prefix checker, and 99 selected actions were outside the reported winning set.
- The rolling worker produced 1533 unique policies with solve-time statistics `{'median': 290.2024000068195, 'p95': 437.1617999859154, 'max': 519.6632999868598}` and first-observed ages `{'median': 6.0, 'p95': 13.0, 'max': 1799.0}`. Policy status counts were `{'pending_future_epoch': 28, 'queryable': 8134, 'expired': 11}`; 38 robust-mode decisions had no query.
- Of 4843 unambiguous output transitions, 4052 (0.837) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 12, 'missing_pre_hit_alive_decision': 1, 'robust_action_set_exhausted_before_hit': 5, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[4, 7, 8, 0, 7, 0, 10, 8, 4, 12, 7, 12, 9, 30, 0, 0, 0, 0, 12]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.251 during the 60 frames preceding a hit versus 0.124 outside those windows.
- Mean selected control-reserve deficit was 3.832 during the 60 frames preceding a hit versus 0.607 outside those windows.
- Soft recovery was selected on 0.108 of alive decisions in the 60-frame pre-hit windows versus 0.074 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 8.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
