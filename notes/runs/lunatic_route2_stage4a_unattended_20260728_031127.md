# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_031127

## Scope And Integrity

- Valid practice scope: `1..43931` (14411 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 11, at `[3968, 4490, 8993, 9528, 12848, 13180, 14005, 22117, 22686, 36678, 42817]`.
- Hard no-Bomb verification: **PASS** across 14411 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F3968-T1`. It occurred during a nonspell phase at player (357.349, 432.000), with 731 bullets and 0 lasers. The projectile model reported pipeline clearance -18.892.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 6 |
| `modeled_committed_prefix_collision` | 3 |
| `observed_enemy_body_overlap` | 1 |
| `observed_multiple_hazard_overlap` | 1 |

Contributing factors:

- `fast_mode`: 11
- `playfield_boundary`: 6
- `corridor_deadline_miss`: 3
- `enemy_body_absent_from_action_snapshot`: 2
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3968 | nonspell | (357.349, 432.000) | `left_fast` | 731/0 | -18.892/-18.892 | 2f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4490 | nonspell | (11.253, 428.747) | `down_left_fast` | 1056/0 | -1.491/-5.034 | 2f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8993 | nonspell | (127.055, 426.343) | `up_fast` | 177/0 | -19.065/-19.065 | 13f/19f | `observed_multiple_hazard_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9528 | nonspell | (86.178, 399.601) | `up_fast` | 127/0 | 11.336/7.501 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12848 | 57 夢境「二重大結界」 | (8.000, 424.000) | `right_fast` | 642/0 | -3.192/-3.192 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13180 | 57 夢境「二重大結界」 | (370.343, 421.350) | `down_left_fast` | 576/0 | 2.181/-2.021 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14005 | 57 夢境「二重大結界」 | (372.747, 432.000) | `up_fast` | 590/0 | -1.382/-1.382 | 3f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22117 | nonspell | (8.000, 400.000) | `right_fast` | 473/0 | -0.112/-3.817 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22686 | nonspell | (14.226, 426.343) | `up_right_fast` | 602/0 | 0.959/-1.907 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36678 | 69 回霊「夢想封印　侘」 | (376.000, 425.006) | `up_fast` | 494/0 | -2.142/-2.142 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42817 | 73 大結界「博麗弾幕結界」 | (189.495, 395.019) | `down_left_fast` | 1354/0 | -0.757/-2.187 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 8579 | 8440 | 3771 | 0 | 4608 | 1034 | 109.394 | 0.137 |
| 57 夢境「二重大結界」 | 3 | 1312 | 1304 | 358 | 0 | 924 | 183 | 154.040 | 0.263 |
| 61 | 0 | 1221 | 1210 | 369 | 0 | 811 | 150 | 103.690 | 0.168 |
| 65 | 0 | 866 | 853 | 713 | 0 | 140 | 115 | 58.613 | 0.343 |
| 69 回霊「夢想封印　侘」 | 1 | 1307 | 1300 | 743 | 0 | 553 | 181 | 85.357 | 0.113 |
| 73 大結界「博麗弾幕結界」 | 1 | 1126 | 1110 | 529 | 0 | 571 | 181 | 106.032 | 0.022 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 2 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.567 ms median and 17.416 ms p95.
- The full enemy sensor produced 7004 snapshots; capture read time was `{'median': 4.705399973317981, 'p95': 20.394799998030066, 'max': 34.90379999857396}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 6 phase-counter discontinuities were excluded; 13995 decisions retained at least one robust-union body (maximum 41); 2846 decisions contained latent contact-disabled geometry (maximum 38), and 6935 contained bounded inactive-slot memory (maximum 36). 143 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.414459228515625, 'p95': 4.046478271484375, 'max': 4.569671630859375}` / `{'median': 2.882915496826172, 'p95': 3.8987677097320557, 'max': 4.100006103515625}` / `{'median': 0.6467175483703613, 'p95': 3.190864086151123, 'max': 8.20001220703125}`.
- The issue-time enemy guard retained 14411 observations, detected 2187 during-plan geometry changes, recertified 2187 decisions, and overrode 50 actions. Read/recertificate timing was `{'median': 1.7029999871738255, 'p95': 3.4768999903462827, 'max': 14.053300023078918}` / `{'median': 1.867300015874207, 'p95': 3.4960999619215727, 'max': 11.805699963588268}` ms; 2842 issue captures contained latent bodies (maximum 38), and 6935 contained dormant bodies (maximum 36). Fresh/global transactions preserved 2137/2187 planned actions, relaxed 4 fresh/global empty intersections, inherited 18 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11029 observations (10981 contact enabled, 48 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4995, '0x00597600': 6034}`.
- The terminal-threat heuristic covered 14411 decisions with horizon counts `{'0': 75, '10': 13456, '32': 880}`; it reported 15 collision and 149 sub-safety-clearance warnings, and relaxed 127 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2831, '3': 10945, '4': 635}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 9753, '3': 4288, '4': 357}`.
- Adaptive delay supports were `{'1,2': 44, '1,2,3': 106, '1,2,3,4': 238, '1,2,3,4,5': 57, '2,3': 1723, '2,3,4': 8650, '2,3,4,5': 2553, '2,3,4,5,6': 996, '3,4': 17, '3,4,5': 18, '3,4,5,6': 9}`; 72 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 25/137.
- Robust viability supplied 14217 available policy queries (0 had new delay support outside the cached policy), constrained 7607 decisions, and exposed 6483 empty queried action sets. Recovery guidance was available/selected on 1952/939 empty-kernel queries; distant-kernel guidance was available/selected on 3748/3648. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 14.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 101.19288512538814, 'p95': 307.34996339677673, 'max': 512.2499389946279}`, and `{'median': 0.0, 'p95': 16.913495540618896, 'max': 38.65269136428833}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2243, '1': 1755, '2': 1470, '3': 1717, '4': 1760, '5': 1734, '6': 1781, '7': 1757}`.
- Global-horizon/local-prefix cross-tab covered 10497 decisions: 2 had a winning global state but unsafe selected prefix, 4598 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 85 selected actions were outside the reported winning set. 1922 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1844 unique policies with solve-time statistics `{'median': 107.86049996386282, 'p95': 304.7919000382535, 'max': 404.6153000090271}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1798.0}`. Policy status counts were `{'pending_future_epoch': 69, 'queryable': 14217, 'expired': 23}`; 92 robust-mode decisions had no query.
- Of 7102 unambiguous output transitions, 6619 (0.932) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 11}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[9, 9, 19, 0, 5, 6, 4, 6, 5, 7, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.359 during the 60 frames preceding a hit versus 0.148 outside those windows.
- Mean selected control-reserve deficit was 11.224 during the 60 frames preceding a hit versus 3.715 outside those windows.
- Soft recovery was selected on 0.109 of alive decisions in the 60-frame pre-hit windows versus 0.066 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
