# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_005108

## Scope And Integrity

- Valid practice scope: `2..44411` (14804 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 10, at `[4259, 11726, 12357, 13405, 19017, 21215, 22063, 31161, 31625, 42033]`.
- Hard no-Bomb verification: **PASS** across 14804 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F4259-T1`. It occurred during a nonspell phase at player (370.343, 432.000), with 1093 bullets and 0 lasers. The projectile model reported pipeline clearance -1.424.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 6 |
| `modeled_committed_prefix_collision` | 3 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 8
- `pool_density_over_1000`: 3
- `corridor_deadline_miss`: 2
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4259 | nonspell | (370.343, 432.000) | `down_left_fast` | 1093/0 | -1.424/-1.424 | 0f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11726 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 634/0 | -3.429/-3.429 | 0f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12357 | 57 夢境「二重大結界」 | (8.000, 428.000) | `up_fast` | 611/0 | 1.335/-1.295 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13405 | 57 夢境「二重大結界」 | (16.000, 432.000) | `right_fast` | 630/0 | 0.016/-3.600 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19017 | 61 散霊「夢想封印　寂」 | (221.542, 428.000) | `up_right_fast` | 146/0 | -2.157/-2.157 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21215 | nonspell | (13.347, 432.000) | `up_right_fast` | 198/0 | 0.132/-2.028 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22063 | nonspell | (376.000, 406.916) | `up_right` | 905/0 | 0.501/-2.830 | 2f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31161 | 65 神技「八方龍殺陣」 | (99.769, 418.343) | `up_fast` | 1120/0 | -8.032/-26.530 | 23f/25f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31625 | 65 神技「八方龍殺陣」 | (91.308, 432.000) | `up_fast` | 1074/0 | -13.336/-13.336 | 0f/2f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42033 | 73 大結界「博麗弾幕結界」 | (216.766, 388.329) | `down_left_fast` | 992/0 | 1.390/-2.308 | 6f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 8596 | 8450 | 3672 | 0 | 4711 | 1033 | 117.576 | 0.136 |
| 57 夢境「二重大結界」 | 3 | 1356 | 1346 | 282 | 0 | 1044 | 184 | 155.773 | 0.290 |
| 61 散霊「夢想封印　寂」 | 1 | 1178 | 1167 | 368 | 0 | 788 | 144 | 114.667 | 0.123 |
| 65 神技「八方龍殺陣」 | 2 | 1196 | 1184 | 1085 | 0 | 99 | 154 | 53.994 | 0.421 |
| 69 | 0 | 1315 | 1304 | 716 | 0 | 583 | 177 | 78.224 | 0.068 |
| 73 大結界「博麗弾幕結界」 | 1 | 1163 | 1148 | 601 | 0 | 532 | 179 | 100.746 | 0.069 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.981 ms median and 17.662 ms p95.
- The full enemy sensor produced 7191 snapshots; capture read time was `{'median': 6.1175000155344605, 'p95': 21.49649994680658, 'max': 41.54140001628548}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 6 phase-counter discontinuities were excluded; 14381 decisions retained at least one robust-union body (maximum 49); 2891 decisions contained latent contact-disabled geometry (maximum 49), and 7513 contained bounded inactive-slot memory (maximum 45). 106 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.9738006591796875, 'p95': 4.6742401123046875, 'max': 7.810832977294922}` / `{'median': 1.9796435236930847, 'p95': 3.3345139026641846, 'max': 5.252639293670654}` / `{'median': 7.092952728271484e-06, 'p95': 3.5999984741210938, 'max': 7.810832977294922}`.
- The issue-time enemy guard retained 14804 observations, detected 2766 during-plan geometry changes, recertified 2766 decisions, and overrode 34 actions. Read/recertificate timing was `{'median': 1.654049992794171, 'p95': 3.3091999939642847, 'max': 13.342799968086183}` / `{'median': 1.8235499737784266, 'p95': 3.4040999598801136, 'max': 12.721500010229647}` ms; 2888 issue captures contained latent bodies (maximum 49), and 7515 contained dormant bodies (maximum 45). Fresh/global transactions preserved 2732/2766 planned actions, relaxed 1 fresh/global empty intersections, inherited 18 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11407 observations (11360 contact enabled, 47 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4924, '0x0059C9D0': 6483}`.
- The terminal-threat heuristic covered 14804 decisions with horizon counts `{'0': 76, '10': 13807, '32': 921}`; it reported 14 collision and 138 sub-safety-clearance warnings, and relaxed 118 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 4372, '3': 9833, '4': 599}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 10465, '3': 4321, '4': 5}`.
- Adaptive delay supports were `{'1,2': 46, '1,2,3': 113, '1,2,3,4': 279, '1,2,3,4,5,6': 19, '2,3': 2542, '2,3,4': 8602, '2,3,4,5': 2473, '2,3,4,5,6': 727, '3,4': 3}`; 55 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 32/229.
- Robust viability supplied 14599 available policy queries (0 had new delay support outside the cached policy), constrained 7757 decisions, and exposed 6724 empty queried action sets. Recovery guidance was available/selected on 1794/821 empty-kernel queries; distant-kernel guidance was available/selected on 3941/3811. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 13.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 96.0, 'p95': 289.77232442039735, 'max': 544.9403637096449}`, and `{'median': 0.0, 'p95': 13.171572923660278, 'max': 45.17157292366028}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2254, '1': 1802, '2': 1589, '3': 1688, '4': 1809, '5': 1808, '6': 1790, '7': 1859}`.
- Global-horizon/local-prefix cross-tab covered 10414 decisions: 0 had a winning global state but unsafe selected prefix, 4382 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 70 selected actions were outside the reported winning set. 2487 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1871 unique policies with solve-time statistics `{'median': 106.84520000359043, 'p95': 303.6168999969959, 'max': 416.3748000282794}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1788.0}`. Policy status counts were `{'pending_future_epoch': 78, 'queryable': 14599, 'expired': 12}`; 90 robust-mode decisions had no query.
- Of 7332 unambiguous output transitions, 6823 (0.931) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[15, 2, 9, 5, 0, 4, 16, 25, 2, 12]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.585 during the 60 frames preceding a hit versus 0.145 outside those windows.
- Mean selected control-reserve deficit was 10.107 during the 60 frames preceding a hit versus 3.226 outside those windows.
- Soft recovery was selected on 0.098 of alive decisions in the 60-frame pre-hit windows versus 0.055 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 32.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
