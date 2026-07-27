# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_070838

## Scope And Integrity

- Valid practice scope: `2..45454` (15011 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 15, at `[2384, 3999, 9479, 11859, 12896, 13281, 13661, 21957, 22371, 23186, 30730, 39497, 40100, 44244, 44932]`.
- Hard no-Bomb verification: **PASS** across 15011 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2384-T1`. It occurred during a nonspell phase at player (376.000, 47.853), with 418 bullets and 0 lasers. The projectile model reported pipeline clearance -13.038.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 7 |
| `modeled_committed_prefix_collision` | 6 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 13
- `fast_mode`: 11
- `pool_density_over_1000`: 3
- `corridor_deadline_miss`: 2
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2384 | nonspell | (376.000, 47.853) | `down_fast` | 418/0 | -13.038/-34.499 | 19f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3999 | nonspell | (376.000, 432.000) | `up_left_fast` | 836/0 | -2.651/-2.651 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9479 | nonspell | (9.579, 412.262) | `right` | 179/0 | -18.433/-18.433 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11859 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 603/0 | -1.456/-1.456 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12896 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 582/0 | -1.797/-1.797 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13281 | 57 夢境「二重大結界」 | (371.400, 428.000) | `up_fast` | 597/0 | -3.116/-3.116 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13661 | 57 夢境「二重大結界」 | (376.000, 424.818) | `left_fast` | 614/0 | -1.738/-1.738 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21957 | nonspell | (60.193, 432.000) | `up_right_fast` | 231/0 | -0.395/-1.555 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22371 | nonspell | (372.747, 432.000) | `up` | 835/0 | 0.125/-0.323 | 0f/5f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23186 | nonspell | (368.996, 432.000) | `down_right` | 427/0 | -1.811/-1.811 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30730 | 65 神技「八方龍殺陣」 | (70.358, 432.000) | `stay` | 1080/0 | -4.966/-4.966 | 2f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39497 | 69 回霊「夢想封印　侘」 | (373.172, 432.000) | `down_left_fast` | 738/0 | -3.504/-3.504 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40100 | 69 回霊「夢想封印　侘」 | (376.000, 432.000) | `up_fast` | 718/0 | -3.267/-3.267 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44244 | 73 大結界「博麗弾幕結界」 | (262.083, 383.890) | `down_left_fast` | 1307/0 | 0.475/-0.053 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44932 | 73 大結界「博麗弾幕結界」 | (53.327, 351.335) | `up_right_fast` | 1324/0 | 1.357/-1.226 | 4f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 8883 | 8736 | 3830 | 0 | 4831 | 1072 | 115.906 | 0.145 |
| 57 夢境「二重大結界」 | 4 | 1350 | 1342 | 228 | 0 | 1093 | 185 | 165.224 | 0.202 |
| 61 | 0 | 1311 | 1302 | 489 | 0 | 792 | 167 | 101.824 | 0.113 |
| 65 神技「八方龍殺陣」 | 1 | 927 | 914 | 823 | 0 | 91 | 145 | 58.411 | 0.381 |
| 69 回霊「夢想封印　侘」 | 2 | 1363 | 1356 | 635 | 0 | 711 | 181 | 83.468 | 0.065 |
| 73 大結界「博麗弾幕結界」 | 2 | 1177 | 1159 | 594 | 0 | 560 | 180 | 106.646 | 0.006 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.772 ms median and 17.585 ms p95.
- The full enemy sensor produced 7308 snapshots; capture read time was `{'median': 5.630300001939759, 'p95': 22.264499973971397, 'max': 48.78730000928044}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 6 phase-counter discontinuities were excluded; 14609 decisions retained at least one robust-union body (maximum 51); 2943 decisions contained latent contact-disabled geometry (maximum 51), and 7747 contained bounded inactive-slot memory (maximum 46). 193 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.993743896484375, 'p95': 3.9988327026367188, 'max': 5.299989700317383}` / `{'median': 2.522418737411499, 'p95': 3.85054349899292, 'max': 5.299989700317383}` / `{'median': 0.5001258850097656, 'p95': 3.072075366973877, 'max': 7.100006103515625}`.
- The issue-time enemy guard retained 15011 observations, detected 2249 during-plan geometry changes, recertified 2249 decisions, and overrode 38 actions. Read/recertificate timing was `{'median': 1.6976000042632222, 'p95': 3.4182999515905976, 'max': 15.12120000552386}` / `{'median': 1.9022999913431704, 'p95': 3.6194000276736915, 'max': 11.970999999903142}` ms; 2943 issue captures contained latent bodies (maximum 51), and 7753 contained dormant bodies (maximum 46). Fresh/global transactions preserved 2211/2249 planned actions, relaxed 0 fresh/global empty intersections, inherited 17 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11632 observations (11585 contact enabled, 47 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 11632}`.
- The terminal-threat heuristic covered 15011 decisions with horizon counts `{'0': 75, '10': 14137, '32': 799}`; it reported 15 collision and 103 sub-safety-clearance warnings, and relaxed 132 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2261, '3': 11767, '4': 983}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 10331, '3': 4445, '4': 222}`.
- Adaptive delay supports were `{'1,2': 12, '1,2,3': 286, '1,2,3,4': 159, '1,2,3,4,5': 18, '2,3': 1795, '2,3,4': 8868, '2,3,4,5': 2826, '2,3,4,5,6': 1030, '3,4': 16, '3,4,5': 1}`; 61 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 34/246.
- Robust viability supplied 14809 available policy queries (0 had new delay support outside the cached policy), constrained 8078 decisions, and exposed 6599 empty queried action sets. Recovery guidance was available/selected on 1896/864 empty-kernel queries; distant-kernel guidance was available/selected on 3824/3708. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 16.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 90.50966799187809, 'p95': 289.77232442039735, 'max': 524.8390229394153}`, and `{'median': 0.0, 'p95': 16.0, 'max': 40.29253602027893}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2368, '1': 1787, '2': 1599, '3': 1783, '4': 1799, '5': 1813, '6': 1866, '7': 1794}`.
- Global-horizon/local-prefix cross-tab covered 10492 decisions: 1 had a winning global state but unsafe selected prefix, 4516 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 62 selected actions were outside the reported winning set. 1983 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1930 unique policies with solve-time statistics `{'median': 111.06894997647032, 'p95': 304.4364000088535, 'max': 403.70439999969676}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1803.0}`. Policy status counts were `{'pending_future_epoch': 77, 'queryable': 14811, 'expired': 25}`; 104 robust-mode decisions had no query.
- Of 7682 unambiguous output transitions, 7182 (0.935) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 15}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[23, 5, 0, 4, 4, 7, 4, 6, 5, 0, 14, 6, 6, 10, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.322 during the 60 frames preceding a hit versus 0.138 outside those windows.
- Mean selected control-reserve deficit was 10.493 during the 60 frames preceding a hit versus 3.296 outside those windows.
- Soft recovery was selected on 0.070 of alive decisions in the 60-frame pre-hit windows versus 0.059 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
