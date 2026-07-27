# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260727_210928

## Scope And Integrity

- Valid practice scope: `2..45549` (15110 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 22, at `[1174, 1553, 4081, 4492, 8984, 9506, 11484, 11899, 12648, 13429, 20747, 22408, 22882, 30100, 30586, 31340, 31754, 32519, 36073, 38423, 39649, 40468]`.
- Hard no-Bomb verification: **PASS** across 15110 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1174-T1`. It occurred during a nonspell phase at player (365.919, 415.075), with 332 bullets and 0 lasers. The projectile model reported pipeline clearance 2.126.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 9 |
| `observed_enemy_body_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 15
- `playfield_boundary`: 15
- `corridor_deadline_miss`: 6
- `pool_density_over_1000`: 5
- `action_lag_over_model`: 1
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1174 | nonspell | (365.919, 415.075) | `right_fast` | 332/0 | 2.126/2.126 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1553 | nonspell | (8.000, 224.175) | `up_right_fast` | 283/0 | -6.807/-16.766 | 6f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4081 | nonspell | (348.069, 420.686) | `up_left_fast` | 731/0 | -1.551/-3.480 | 4f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4492 | nonspell | (15.515, 419.515) | `up_right` | 1528/0 | -1.828/-7.064 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8984 | nonspell | (44.208, 428.000) | `stay` | 192/0 | -25.729/-25.729 | 6f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9506 | nonspell | (211.910, 432.000) | `up_left` | 148/0 | -15.032/-21.543 | 9f/13f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11484 | 57 夢境「二重大結界」 | (20.135, 432.000) | `up_right_fast` | 602/0 | -1.602/-1.602 | 2f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11899 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 611/0 | -1.795/-1.795 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12648 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 601/0 | -1.797/-1.797 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13429 | 57 夢境「二重大結界」 | (19.842, 428.000) | `up_left_fast` | 573/0 | 0.113/-0.654 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20747 | 61 散霊「夢想封印　寂」 | (376.000, 432.000) | `right` | 186/0 | -2.159/-2.159 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22408 | nonspell | (361.143, 432.000) | `up_left_fast` | 878/0 | -3.493/-27.461 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22882 | nonspell | (376.000, 431.824) | `down_left` | 752/0 | -1.939/-1.939 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30100 | 65 神技「八方龍殺陣」 | (18.229, 97.290) | `left_fast` | 451/0 | -2.884/-3.086 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30586 | 65 神技「八方龍殺陣」 | (166.301, 432.000) | `up_fast` | 1112/0 | -1.439/-1.439 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31340 | 65 神技「八方龍殺陣」 | (51.082, 416.541) | `down_right_fast` | 1159/0 | 18.215/2.196 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31754 | 65 神技「八方龍殺陣」 | (197.967, 428.747) | `right` | 1300/0 | -2.842/-17.937 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32519 | 65 神技「八方龍殺陣」 | (155.503, 406.343) | `up_left_fast` | 1190/0 | 14.334/-0.447 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36073 | nonspell | (313.208, 372.138) | `right_fast` | 133/0 | -15.930/-15.930 | 0f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38423 | 69 回霊「夢想封印　侘」 | (8.000, 432.000) | `up_fast` | 493/0 | -2.799/-2.799 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39649 | 69 回霊「夢想封印　侘」 | (8.000, 432.000) | `up_right` | 676/0 | -2.292/-2.292 | 8f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40468 | 69 回霊「夢想封印　侘」 | (10.636, 378.559) | `up_right_fast` | 689/0 | -5.438/-5.438 | 2f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 8681 | 8531 | 3664 | 0 | 4802 | 1050 | 116.163 | 0.160 |
| 57 夢境「二重大結界」 | 4 | 1351 | 1342 | 267 | 0 | 1051 | 184 | 161.150 | 0.303 |
| 61 散霊「夢想封印　寂」 | 1 | 1355 | 1345 | 447 | 0 | 883 | 167 | 122.851 | 0.140 |
| 65 神技「八方龍殺陣」 | 5 | 1267 | 1255 | 1107 | 0 | 147 | 170 | 60.081 | 0.483 |
| 69 回霊「夢想封印　侘」 | 3 | 1375 | 1364 | 663 | 0 | 691 | 184 | 86.567 | 0.063 |
| 73 | 0 | 1081 | 1066 | 647 | 0 | 413 | 176 | 104.617 | 0.005 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.894 ms median and 17.846 ms p95.
- The full enemy sensor produced 7393 snapshots; capture read time was `{'median': 5.828699970152229, 'p95': 23.049900017213076, 'max': 55.26930000633001}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 11.0}` frames, and 7 phase-counter discontinuities were excluded; 14679 decisions retained at least one robust-union body (maximum 50); 2864 decisions contained latent contact-disabled geometry (maximum 50), and 7725 contained bounded inactive-slot memory (maximum 37). 319 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.5270309448242188, 'p95': 4.166656494140625, 'max': 7.8333740234375}` / `{'median': 2.549922466278076, 'p95': 3.9676663875579834, 'max': 25.000802993774414}` / `{'median': 0.014567496048079609, 'p95': 4.666669845581055, 'max': 25.000802993774414}`.
- The issue-time enemy guard retained 15110 observations, detected 2431 during-plan geometry changes, recertified 2431 decisions, and overrode 59 actions. Read/recertificate timing was `{'median': 1.7751999839674681, 'p95': 3.57960001565516, 'max': 24.124599993228912}` / `{'median': 1.929999969433993, 'p95': 3.683999995701015, 'max': 13.572099967859685}` ms; 2864 issue captures contained latent bodies (maximum 50), and 7723 contained dormant bodies (maximum 37). Fresh/global transactions preserved 2372/2431 planned actions, relaxed 1 fresh/global empty intersections, inherited 11 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11769 observations (11719 contact enabled, 50 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 11769}`.
- The terminal-threat heuristic covered 15110 decisions with horizon counts `{'0': 74, '10': 14247, '32': 789}`; it reported 9 collision and 133 sub-safety-clearance warnings, and relaxed 121 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2584, '3': 11812, '4': 714}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 11, '2': 10481, '3': 4231, '4': 384, '5': 3}`.
- Adaptive delay supports were `{'1,2': 47, '1,2,3': 169, '1,2,3,4': 144, '1,2,3,4,5': 10, '2,3': 2021, '2,3,4': 8445, '2,3,4,5': 2673, '2,3,4,5,6': 1481, '3,4': 14, '3,4,5': 75, '3,4,5,6': 31}`; 85 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 20/136.
- Robust viability supplied 14903 available policy queries (0 had new delay support outside the cached policy), constrained 7987 decisions, and exposed 6795 empty queried action sets. Recovery guidance was available/selected on 1914/828 empty-kernel queries; distant-kernel guidance was available/selected on 3850/3757. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 14.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 101.19288512538814, 'p95': 323.9753077010654, 'max': 512.2499389946279}`, and `{'median': 0.0, 'p95': 16.0, 'max': 42.37659025192261}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2387, '1': 1795, '2': 1640, '3': 1759, '4': 1841, '5': 1744, '6': 1950, '7': 1787}`.
- Global-horizon/local-prefix cross-tab covered 9785 decisions: 4 had a winning global state but unsafe selected prefix, 4193 had a losing global state but safe short prefix, 4 selected globally certified actions contradicted the fresh local prefix checker, and 71 selected actions were outside the reported winning set. 1927 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1931 unique policies with solve-time statistics `{'median': 111.2178000039421, 'p95': 314.3667000113055, 'max': 399.2102000047453}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1789.0}`. Policy status counts were `{'pending_future_epoch': 70, 'queryable': 14902, 'expired': 10}`; 79 robust-mode decisions had no query.
- Of 7267 unambiguous output transitions, 6716 (0.924) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 22}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 17 hit windows with a positive warning lead; those leads were `[0, 11, 11, 6, 12, 13, 6, 3, 4, 6, 6, 13, 6, 0, 5, 0, 0, 0, 2, 5, 11, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.409 during the 60 frames preceding a hit versus 0.152 outside those windows.
- Mean selected control-reserve deficit was 6.462 during the 60 frames preceding a hit versus 3.535 outside those windows.
- Soft recovery was selected on 0.037 of alive decisions in the 60-frame pre-hit windows versus 0.060 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 5.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
