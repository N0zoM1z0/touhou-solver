# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_092619

## Scope And Integrity

- Valid practice scope: `2..44999` (14649 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[1299, 2813, 4131, 10002, 11743, 12143, 12790, 13828, 20516, 21812, 22489, 27127, 30019, 30928, 36974, 37765, 39139, 44569]`.
- Hard no-Bomb verification: **PASS** across 14649 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1299-T1`. It occurred during a nonspell phase at player (357.100, 416.976), with 101 bullets and 0 lasers. The projectile model reported pipeline clearance -2.442.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 8 |
| `observed_enemy_body_overlap` | 1 |
| `observed_multiple_hazard_overlap` | 1 |

Contributing factors:

- `fast_mode`: 14
- `playfield_boundary`: 12
- `corridor_deadline_miss`: 5
- `pool_density_over_1000`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1299 | nonspell | (357.100, 416.976) | `right_fast` | 101/0 | -2.442/-2.442 | 0f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2813 | nonspell | (8.000, 432.000) | `up_right_fast` | 538/0 | -1.301/-1.301 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4131 | nonspell | (376.000, 432.000) | `up_fast` | 921/0 | -3.807/-13.558 | 0f/27f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10002 | nonspell | (245.289, 432.000) | `up` | 138/0 | -14.301/-23.581 | 2f/29f | `observed_multiple_hazard_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11743 | 57 夢境「二重大結界」 | (10.828, 429.172) | `up_right_fast` | 622/0 | 1.427/-0.908 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12143 | 57 夢境「二重大結界」 | (376.000, 420.076) | `up_right_fast` | 606/0 | -1.847/-1.847 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12790 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 614/0 | -1.451/-1.451 | 0f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13828 | 57 夢境「二重大結界」 | (371.400, 432.000) | `up_fast` | 590/0 | -1.496/-2.327 | 2f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20516 | 61 散霊「夢想封印　寂」 | (165.714, 432.000) | `right_fast` | 268/0 | -2.666/-2.666 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21812 | nonspell | (315.155, 426.343) | `up_right_fast` | 786/0 | -0.047/-1.442 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22489 | nonspell | (12.600, 432.000) | `right` | 570/0 | -0.125/-1.333 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27127 | nonspell | (366.898, 130.296) | `down_fast` | 181/0 | -16.277/-16.277 | 0f/2f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30019 | 65 神技「八方龍殺陣」 | (99.326, 417.858) | `right` | 1207/0 | -1.643/-1.643 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30928 | 65 神技「八方龍殺陣」 | (104.574, 432.000) | `right_fast` | 1269/0 | -1.805/-1.805 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36974 | nonspell | (369.785, 156.719) | `up_fast` | 176/0 | 4.398/-1.960 | 5f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37765 | 69 回霊「夢想封印　侘」 | (371.400, 432.000) | `down_left_fast` | 410/0 | -0.662/-1.735 | 5f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39139 | 69 回霊「夢想封印　侘」 | (8.000, 416.271) | `up_right` | 696/0 | -0.202/-1.991 | 5f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44569 | 73 大結界「博麗弾幕結界」 | (148.274, 348.175) | `up_left_fast` | 1313/0 | 0.802/0.158 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 8846 | 8702 | 3858 | 0 | 4755 | 1075 | 117.710 | 0.151 |
| 57 夢境「二重大結界」 | 4 | 1345 | 1336 | 255 | 0 | 1069 | 184 | 166.828 | 0.268 |
| 61 散霊「夢想封印　寂」 | 1 | 998 | 987 | 302 | 0 | 672 | 125 | 107.813 | 0.151 |
| 65 神技「八方龍殺陣」 | 2 | 1035 | 1026 | 892 | 0 | 113 | 162 | 58.124 | 0.484 |
| 69 回霊「夢想封印　侘」 | 2 | 1346 | 1328 | 691 | 0 | 634 | 179 | 88.018 | 0.051 |
| 73 大結界「博麗弾幕結界」 | 1 | 1079 | 1062 | 524 | 0 | 527 | 175 | 107.084 | 0.072 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.850 ms median and 18.000 ms p95.
- The full enemy sensor produced 7188 snapshots; capture read time was `{'median': 5.628199985949323, 'p95': 21.961399994324893, 'max': 39.33380002854392}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 7 phase-counter discontinuities were excluded; 14252 decisions retained at least one robust-union body (maximum 55); 2914 decisions contained latent contact-disabled geometry (maximum 55), and 7314 contained bounded inactive-slot memory (maximum 49). 279 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.5053863525390625, 'p95': 4.569671630859375, 'max': 15.077199300130209}` / `{'median': 2.5738425254821777, 'p95': 3.922955274581909, 'max': 14.90289306640625}` / `{'median': 0.01083385944366455, 'p95': 5.326102256774902, 'max': 11.0}`.
- The issue-time enemy guard retained 14649 observations, detected 2463 during-plan geometry changes, recertified 2463 decisions, and overrode 35 actions. Read/recertificate timing was `{'median': 1.7041000537574291, 'p95': 3.4071000409312546, 'max': 12.423800013493747}` / `{'median': 1.8871999927796423, 'p95': 3.6841999972239137, 'max': 11.539399973116815}` ms; 2914 issue captures contained latent bodies (maximum 55), and 7303 contained dormant bodies (maximum 49). Fresh/global transactions preserved 2428/2463 planned actions, relaxed 4 fresh/global empty intersections, inherited 10 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11294 observations (11257 contact enabled, 37 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 11294}`.
- The terminal-threat heuristic covered 14649 decisions with horizon counts `{'0': 73, '10': 13619, '32': 957}`; it reported 19 collision and 134 sub-safety-clearance warnings, and relaxed 149 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2275, '3': 11145, '4': 1229}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 9236, '3': 4937, '4': 463}`.
- Adaptive delay supports were `{'1,2': 39, '1,2,3': 68, '1,2,3,4': 309, '1,2,3,4,5': 21, '1,2,3,4,5,6': 8, '2,3': 1580, '2,3,4': 8243, '2,3,4,5': 3306, '2,3,4,5,6': 961, '3,4,5': 80, '3,4,5,6': 34}`; 59 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 50/335.
- Robust viability supplied 14441 available policy queries (0 had new delay support outside the cached policy), constrained 7770 decisions, and exposed 6522 empty queried action sets. Recovery guidance was available/selected on 1740/893 empty-kernel queries; distant-kernel guidance was available/selected on 3802/3679. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 14.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 97.32420048477151, 'p95': 304.0, 'max': 502.41019097944263}`, and `{'median': 0.0, 'p95': 16.0, 'max': 38.37365436553955}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2260, '1': 1790, '2': 1584, '3': 1709, '4': 1736, '5': 1763, '6': 1833, '7': 1766}`.
- Global-horizon/local-prefix cross-tab covered 9819 decisions: 9 had a winning global state but unsafe selected prefix, 4256 had a losing global state but safe short prefix, 3 selected globally certified actions contradicted the fresh local prefix checker, and 93 selected actions were outside the reported winning set. 2024 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1900 unique policies with solve-time statistics `{'median': 111.41904999385588, 'p95': 302.3067999747582, 'max': 407.8457000432536}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1803.0}`. Policy status counts were `{'pending_future_epoch': 86, 'queryable': 14440, 'expired': 36}`; 121 robust-mode decisions had no query.
- Of 7181 unambiguous output transitions, 6720 (0.936) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 18}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[9, 4, 27, 29, 5, 9, 2, 6, 7, 9, 7, 2, 5, 6, 9, 7, 15, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.392 during the 60 frames preceding a hit versus 0.158 outside those windows.
- Mean selected control-reserve deficit was 10.000 during the 60 frames preceding a hit versus 3.547 outside those windows.
- Soft recovery was selected on 0.084 of alive decisions in the 60-frame pre-hit windows versus 0.061 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Hoc ECL Control Replay

The later CE-0154 correction replays 5,788/5,803 callback rows against the
retained decoded Stage-4A image. No unknown row becomes complete. It finds
1,996 old complete-horizon rows that crossed unsupported loop/call control
(997 spell 61, 999 spell 65), and changes all spell-57/spell-73 incomplete
rows to the earlier exact unsupported-control boundary. Total inspected
instructions fall `563,466 -> 58,204`; spell 57 falls
`344,320 -> 3,155`.

Fifteen late spell-73 transition rows are not byte-mappable to the retained
decoded file. The deterministic audit therefore fails its all-rows gate and
does not infer them. Report SHA-256 is
`99f17fbc0a98a5bb9c2711c98e52bef00f3703566d97a26a0e59cfbb10f1edd1`.
