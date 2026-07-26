# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260726_100451

## Scope And Integrity

- Valid practice scope: `1..45836` (9222 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 21, at `[2581, 4276, 8815, 9512, 11779, 12397, 12998, 13477, 19154, 19614, 19992, 21611, 22613, 23014, 28226, 28874, 31597, 38481, 39627, 40513, 45181]`.
- Hard no-Bomb verification: **PASS** across 9222 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2581-T1`. It occurred during a nonspell phase at player (8.000, 431.887), with 543 bullets and 0 lasers. The projectile model reported pipeline clearance -2.729.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 16 |
| `observed_bullet_overlap` | 2 |
| `observed_enemy_body_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 17
- `playfield_boundary`: 14
- `corridor_deadline_miss`: 8
- `pool_density_over_1000`: 3
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2581 | nonspell | (8.000, 431.887) | `down_right` | 543/0 | -2.729/-2.729 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4276 | nonspell | (284.852, 432.000) | `down_right_fast` | 1000/0 | -2.524/-2.524 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8815 | nonspell | (376.000, 432.000) | `up_fast` | 766/0 | -13.807/-13.807 | 4f/17f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9512 | nonspell | (169.106, 424.000) | `up_fast` | 144/0 | -9.365/-9.365 | 7f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11779 | 57 夢境「二重大結界」 | (8.000, 379.413) | `down_right_fast` | 607/0 | -2.263/-2.263 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12397 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 610/0 | -0.895/-0.895 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12998 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_fast` | 583/0 | -3.153/-3.153 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13477 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_fast` | 613/0 | -0.656/-0.656 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19154 | 61 散霊「夢想封印　寂」 | (161.839, 409.649) | `up_fast` | 380/0 | -12.310/-12.310 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19614 | 61 散霊「夢想封印　寂」 | (360.000, 422.800) | `up_fast` | 195/0 | -5.860/-8.992 | 0f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19992 | 61 散霊「夢想封印　寂」 | (268.660, 432.000) | `left_fast` | 283/0 | -8.386/-8.386 | 0f/5f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21611 | nonspell | (361.858, 22.505) | `up_left_fast` | 201/0 | -0.907/-2.304 | 6f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22613 | nonspell | (281.373, 432.000) | `left_fast` | 823/0 | -2.792/-29.291 | 0f/84f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23014 | nonspell | (10.991, 432.000) | `right_fast` | 569/0 | -1.771/-1.771 | 4f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28226 | nonspell | (365.910, 16.000) | `left` | 186/0 | -1.900/-1.900 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28874 | nonspell | (376.000, 91.869) | `stay` | 176/0 | -2.793/-2.793 | 0f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31597 | 65 神技「八方龍殺陣」 | (153.971, 427.814) | `right_fast` | 1239/0 | -2.728/-6.375 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38481 | 69 回霊「夢想封印　侘」 | (376.000, 432.000) | `left_fast` | 458/0 | -3.891/-3.891 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39627 | 69 回霊「夢想封印　侘」 | (376.000, 415.737) | `up_right_fast` | 698/0 | -2.262/-2.262 | 9f/26f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40513 | 69 回霊「夢想封印　侘」 | (364.616, 432.000) | `down_left` | 716/0 | -2.673/-2.673 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45181 | 73 大結界「博麗弾幕結界」 | (255.894, 403.115) | `down_left_fast` | 1322/0 | 0.548/-0.651 | 6f/6f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 5154 | 5056 | 2405 | 0 | 2599 | 947 | 142.159 | 0.189 |
| 57 夢境「二重大結界」 | 4 | 882 | 875 | 145 | 0 | 714 | 166 | 203.495 | 0.205 |
| 61 散霊「夢想封印　寂」 | 3 | 843 | 837 | 289 | 0 | 529 | 153 | 147.771 | 0.162 |
| 65 神技「八方龍殺陣」 | 1 | 676 | 664 | 546 | 0 | 118 | 149 | 57.350 | 0.348 |
| 69 回霊「夢想封印　侘」 | 3 | 885 | 879 | 399 | 0 | 472 | 171 | 105.790 | 0.089 |
| 73 大結界「博麗弾幕結界」 | 1 | 782 | 762 | 403 | 0 | 350 | 162 | 110.052 | 0.027 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 5.000 frames p95. The local plan took 23.398 ms median and 41.340 ms p95.
- The full enemy sensor produced 6671 snapshots; capture read time was `{'median': 21.385899977758527, 'p95': 46.111400006338954, 'max': 106.68999998597428}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 15.0}` frames, and 4 phase-counter discontinuities were excluded; 8930 decisions retained at least one robust-union body (maximum 51); 1663 decisions contained latent contact-disabled geometry (maximum 51), and 4684 contained bounded inactive-slot memory (maximum 46). 271 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.8797098795572915, 'p95': 4.4893544514973955, 'max': 15.253564453125}` / `{'median': 3.001739501953125, 'p95': 4.308481216430664, 'max': 15.251350402832031}` / `{'median': 0.09999847412109375, 'p95': 0.9581314623355865, 'max': 15.251350402832031}`.
- The issue-time enemy guard retained 9222 observations, detected 2944 during-plan geometry changes, recertified 2944 decisions, and overrode 1497 actions. Read/recertificate timing was `{'median': 1.8806500011123717, 'p95': 4.01370000327006, 'max': 21.57500002067536}` / `{'median': 8.101950021227822, 'p95': 15.97320003202185, 'max': 39.718100044410676}` ms; 1665 issue captures contained latent bodies (maximum 51), and 4677 contained dormant bodies (maximum 46).
- The synchronous spell-owner guard retained 7255 observations (7224 contact enabled, 31 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 7255}`.
- The terminal-threat heuristic covered 9222 decisions with horizon counts `{'0': 45, '10': 8490, '32': 687}`; it reported 17 collision and 102 sub-safety-clearance warnings, and relaxed 104 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 46, '3': 298, '4': 4466, '5': 4272, '6': 140}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 1, '2': 32, '3': 521, '4': 7065, '5': 1603}`.
- Adaptive delay supports were `{'1,2': 1, '1,2,3,4': 36, '2,3': 31, '2,3,4': 48, '2,3,4,5': 171, '2,3,4,5,6': 421, '3,4': 37, '3,4,5': 510, '3,4,5,6': 7479, '4,5': 1, '4,5,6': 486, '5,6': 1}`; 1619 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 59/187.
- Robust viability supplied 9073 available policy queries (0 had new delay support outside the cached policy), constrained 4782 decisions, and exposed 4187 empty queried action sets. Recovery guidance was available/selected on 1151/672 empty-kernel queries; distant-kernel guidance was available/selected on 2430/2334. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 16.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 115.37764081484765, 'p95': 310.6638054231616, 'max': 522.3944869540643}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1360, '1': 1304, '2': 1143, '3': 1063, '4': 1012, '5': 1073, '6': 1100, '7': 1018}`.
- Global-horizon/local-prefix cross-tab covered 4690 decisions: 2 had a winning global state but unsafe selected prefix, 1955 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 55 selected actions were outside the reported winning set. 2304 newer issue-time hazard versions and 1 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1748 unique policies with solve-time statistics `{'median': 133.1216500257142, 'p95': 421.7196999816224, 'max': 546.4084999985062}` and first-observed ages `{'median': 4.0, 'p95': 9.0, 'max': 1800.0}`. Policy status counts were `{'pending_future_epoch': 42, 'queryable': 9073, 'expired': 13}`; 55 robust-mode decisions had no query.
- Of 5337 unambiguous output transitions, 4567 (0.856) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 21}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 21 hit windows with a positive warning lead; those leads were `[6, 5, 17, 18, 13, 4, 8, 8, 4, 21, 5, 11, 84, 7, 4, 13, 5, 6, 26, 7, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.386 during the 60 frames preceding a hit versus 0.167 outside those windows.
- Mean selected control-reserve deficit was 14.764 during the 60 frames preceding a hit versus 6.770 outside those windows.
- Soft recovery was selected on 0.108 of alive decisions in the 60-frame pre-hit windows versus 0.074 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
