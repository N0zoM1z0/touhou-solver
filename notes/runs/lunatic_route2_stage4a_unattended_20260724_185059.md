# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_185059

## Scope And Integrity

- Valid practice scope: `2..45451` (8002 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 26, at `[3907, 4295, 9012, 9369, 9790, 10313, 11279, 11984, 12613, 13070, 13479, 18753, 19189, 21283, 21762, 22140, 22837, 30354, 30765, 31148, 31707, 32307, 34863, 35538, 39805, 44476]`.
- Hard no-Bomb verification: **PASS** across 8002 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F3907-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 653 bullets and 0 lasers. The projectile model reported pipeline clearance -19.614.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 17 |
| `observed_bullet_overlap` | 6 |
| `observed_enemy_body_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 19
- `fast_mode`: 15
- `corridor_deadline_miss`: 9
- `pool_density_over_1000`: 7
- `enemy_body_absent_from_action_snapshot`: 2
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3907 | nonspell | (376.000, 432.000) | `up_fast` | 653/0 | -19.614/-19.614 | 4f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4295 | nonspell | (376.000, 432.000) | `down_left` | 1097/0 | -11.666/-11.666 | 5f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9012 | nonspell | (8.000, 432.000) | `up_fast` | 147/0 | -22.812/-34.298 | 17f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9369 | nonspell | (85.500, 432.000) | `down_left` | 442/0 | -0.448/-0.448 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9790 | nonspell | (228.749, 420.811) | `right_fast` | 762/0 | 20.541/5.044 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 10313 | nonspell | (25.745, 432.000) | `up_fast` | 686/0 | -2.117/-13.067 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11279 | 57 夢境「二重大結界」 | (8.000, 432.000) | `right_fast` | 625/0 | -1.003/-1.003 | 0f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11984 | 57 夢境「二重大結界」 | (376.000, 432.000) | `left_fast` | 588/0 | -2.524/-2.524 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12613 | 57 夢境「二重大結界」 | (376.000, 432.000) | `down_right` | 582/0 | -2.336/-2.336 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13070 | 57 夢境「二重大結界」 | (8.000, 423.195) | `up_right_fast` | 605/0 | -1.391/-1.391 | 9f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13479 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left` | 605/0 | -1.409/-1.409 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18753 | 61 散霊「夢想封印　寂」 | (214.065, 418.302) | `stay` | 437/0 | -15.424/-15.424 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19189 | 61 散霊「夢想封印　寂」 | (260.211, 432.000) | `up_left_fast` | 230/0 | -5.774/-5.774 | 5f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21283 | nonspell | (22.142, 432.000) | `down_right_fast` | 366/0 | -1.294/-1.294 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21762 | nonspell | (361.858, 432.000) | `up_fast` | 336/0 | 0.383/-26.142 | 5f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22140 | nonspell | (376.000, 432.000) | `stay` | 846/0 | -24.761/-24.761 | 72f/72f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22837 | nonspell | (24.971, 415.029) | `right_fast` | 684/0 | -0.686/-0.686 | 6f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30354 | 65 神技「八方龍殺陣」 | (301.713, 404.818) | `down_right_fast` | 1193/0 | 0.365/0.365 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30765 | 65 神技「八方龍殺陣」 | (233.623, 420.500) | `up` | 1072/0 | -2.768/-2.768 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31148 | 65 神技「八方龍殺陣」 | (181.964, 395.230) | `up_right_fast` | 1038/0 | -1.662/-7.358 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31707 | 65 神技「八方龍殺陣」 | (213.670, 432.000) | `stay` | 1253/0 | -2.018/-11.755 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32307 | 65 神技「八方龍殺陣」 | (376.000, 386.200) | `down_fast` | 1248/0 | -18.634/-18.634 | 21f/27f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34863 | nonspell | (286.873, 432.000) | `down_right` | 132/0 | -1.766/-1.766 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35538 | nonspell | (367.515, 384.873) | `up_fast` | 90/0 | -14.673/-14.673 | 0f/0f | `observed_enemy_body_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 39805 | 69 回霊「夢想封印　侘」 | (8.000, 417.854) | `right` | 703/0 | -1.870/-1.870 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44476 | 73 大結界「博麗弾幕結界」 | (212.916, 430.244) | `down_right` | 1342/0 | -3.373/-3.373 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 12 | 4515 | 4419 | 1787 | 0 | 2581 | 927 | 186.225 | 0.125 |
| 57 夢境「二重大結界」 | 5 | 792 | 785 | 167 | 0 | 602 | 164 | 240.922 | 0.344 |
| 61 散霊「夢想封印　寂」 | 2 | 715 | 710 | 220 | 0 | 469 | 156 | 176.293 | 0.194 |
| 65 神技「八方龍殺陣」 | 5 | 606 | 597 | 500 | 0 | 96 | 152 | 74.667 | 0.192 |
| 69 回霊「夢想封印　侘」 | 1 | 716 | 710 | 396 | 0 | 308 | 167 | 124.535 | 0.096 |
| 73 大結界「博麗弾幕結界」 | 1 | 658 | 646 | 321 | 0 | 315 | 162 | 151.221 | 0.048 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 2 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 27.054 ms median and 49.963 ms p95.
- The full enemy sensor produced 6549 snapshots; capture read time was `{'median': 36.44299998995848, 'p95': 61.38990001636557, 'max': 110.28619998251088}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 13.0}` frames, and 5 phase-counter discontinuities were excluded; 7728 decisions retained at least one robust-union body (maximum 54); 1412 decisions contained latent contact-disabled geometry (maximum 54), and 3642 contained bounded inactive-slot memory (maximum 45). 508 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.3652687072753906, 'p95': 3.9883956909179688, 'max': 10.435516357421875}` / `{'median': 2.50203275680542, 'p95': 3.898771047592163, 'max': 123.99569702148438}` / `{'median': 0.006226092576980591, 'p95': 3.041013240814209, 'max': 123.99569702148438}`.
- The issue-time enemy guard retained 8002 observations, detected 1258 during-plan geometry changes, recertified 1258 decisions, and overrode 707 actions. Read/recertificate timing was `{'median': 2.316049998626113, 'p95': 4.946800007019192, 'max': 25.727100000949576}` / `{'median': 12.378349987557158, 'p95': 21.9941999821458, 'max': 37.44929999811575}` ms; 1415 issue captures contained latent bodies (maximum 53), and 3625 contained dormant bodies (maximum 45).
- The synchronous spell-owner guard retained 3487 observations (3470 contact enabled, 17 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3487}`.
- The terminal-threat heuristic covered 8002 decisions with horizon counts `{'0': 41, '10': 7160, '32': 801}`; it reported 8 collision and 77 sub-safety-clearance warnings, and relaxed 105 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 26, '3': 184, '4': 911, '5': 4623, '6': 2258}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 6, '3': 137, '4': 1845, '5': 5254, '6': 760}`.
- Adaptive delay supports were `{'2,3': 5, '2,3,4,5': 65, '2,3,4,5,6': 503, '3,4,5': 80, '3,4,5,6': 5834, '4,5,6': 1504, '5,6': 11}`; 857 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 88/234.
- Robust viability supplied 7867 available policy queries (0 had new delay support outside the cached policy), constrained 4371 decisions, and exposed 3391 empty queried action sets. Recovery guidance was available/selected on 954/618 empty-kernel queries; distant-kernel guidance was available/selected on 2092/2008. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 22.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 102.44998779892558, 'p95': 321.99378875996973, 'max': 520.9222590751906}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1207, '1': 1094, '2': 996, '3': 960, '4': 935, '5': 921, '6': 870, '7': 884}`.
- Global-horizon/local-prefix cross-tab covered 4912 decisions: 3 had a winning global state but unsafe selected prefix, 1868 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 67 selected actions were outside the reported winning set. 855 newer issue-time hazard versions and 3 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1728 unique policies with solve-time statistics `{'median': 170.7713500072714, 'p95': 380.59029998839833, 'max': 489.9603000085335}` and first-observed ages `{'median': 5.0, 'p95': 10.0, 'max': 1812.0}`. Policy status counts were `{'pending_future_epoch': 34, 'queryable': 7867, 'expired': 34}`; 68 robust-mode decisions had no query.
- Of 4776 unambiguous output transitions, 4046 (0.847) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 23, 'unresolved_planner_failure': 1, 'late_collision_after_positive_causal_margin': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 20 hit windows with a positive warning lead; those leads were `[14, 5, 22, 9, 0, 5, 9, 4, 4, 14, 4, 0, 11, 0, 9, 72, 12, 5, 11, 4, 0, 27, 8, 0, 9, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.448 during the 60 frames preceding a hit versus 0.120 outside those windows.
- Mean selected control-reserve deficit was 5.228 during the 60 frames preceding a hit versus 0.606 outside those windows.
- Soft recovery was selected on 0.083 of alive decisions in the 60-frame pre-hit windows versus 0.082 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
