# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_075455

## Scope And Integrity

- Valid practice scope: `1..45499` (14903 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 16, at `[1189, 1832, 2666, 3941, 9406, 9982, 12301, 12890, 13491, 22307, 22846, 32111, 36685, 39484, 40287, 44579]`.
- Hard no-Bomb verification: **PASS** across 14903 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1189-T1`. It occurred during a nonspell phase at player (358.791, 429.802), with 261 bullets and 0 lasers. The projectile model reported pipeline clearance -2.296.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 6 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 16
- `playfield_boundary`: 14
- `corridor_deadline_miss`: 6
- `pool_density_over_1000`: 2
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1189 | nonspell | (358.791, 429.802) | `down_fast` | 261/0 | -2.296/-2.296 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1832 | nonspell | (65.657, 432.000) | `right_fast` | 323/0 | -4.459/-28.810 | 21f/29f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2666 | nonspell | (321.387, 432.000) | `left_fast` | 455/0 | 0.433/-1.619 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3941 | nonspell | (20.732, 429.026) | `up_right_fast` | 805/0 | -12.603/-25.995 | 21f/25f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9406 | nonspell | (46.295, 432.000) | `right_fast` | 332/0 | -0.302/-5.643 | 5f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9982 | nonspell | (8.000, 424.000) | `up_fast` | 160/0 | -10.446/-23.270 | 11f/20f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12301 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 630/0 | -1.455/-1.455 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12890 | 57 夢境「二重大結界」 | (372.000, 432.000) | `left_fast` | 590/0 | -3.136/-3.218 | 2f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13491 | 57 夢境「二重大結界」 | (373.172, 429.172) | `up_left_fast` | 607/0 | 2.096/-1.414 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22307 | nonspell | (376.000, 423.090) | `up_fast` | 788/0 | -1.385/-1.385 | 0f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22846 | nonspell | (30.564, 426.343) | `up_right_fast` | 626/0 | 0.000/-13.279 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32111 | 65 神技「八方龍殺陣」 | (68.758, 432.000) | `left_fast` | 1191/0 | 5.658/0.747 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36685 | nonspell | (369.495, 428.747) | `left_fast` | 108/0 | -13.497/-17.574 | 6f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39484 | 69 回霊「夢想封印　侘」 | (8.000, 432.000) | `up_right_fast` | 693/0 | -2.772/-2.772 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40287 | 69 回霊「夢想封印　侘」 | (20.000, 432.000) | `up_fast` | 649/0 | -3.939/-3.939 | 3f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44579 | 73 大結界「博麗弾幕結界」 | (286.956, 357.754) | `down_fast` | 1344/0 | -3.125/-3.125 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 8814 | 8677 | 4206 | 0 | 4405 | 1066 | 106.885 | 0.152 |
| 57 夢境「二重大結界」 | 3 | 1313 | 1305 | 324 | 0 | 953 | 183 | 161.050 | 0.280 |
| 61 | 0 | 1301 | 1292 | 457 | 0 | 813 | 167 | 110.163 | 0.122 |
| 65 神技「八方龍殺陣」 | 1 | 989 | 979 | 827 | 0 | 118 | 157 | 58.752 | 0.434 |
| 69 回霊「夢想封印　侘」 | 2 | 1348 | 1340 | 736 | 0 | 601 | 180 | 83.829 | 0.145 |
| 73 大結界「博麗弾幕結界」 | 1 | 1138 | 1120 | 611 | 0 | 501 | 178 | 103.307 | 0.027 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.723 ms median and 17.853 ms p95.
- The full enemy sensor produced 7289 snapshots; capture read time was `{'median': 5.671299993991852, 'p95': 21.580700005870312, 'max': 40.80459999386221}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 7 phase-counter discontinuities were excluded; 14504 decisions retained at least one robust-union body (maximum 57); 2929 decisions contained latent contact-disabled geometry (maximum 57), and 7519 contained bounded inactive-slot memory (maximum 52). 226 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 3.0254693031311035, 'p95': 4.1105092366536455, 'max': 10.842856952122279}` / `{'median': 3.042462944984436, 'p95': 3.922957181930542, 'max': 19.217205047607422}` / `{'median': 0.01554042100906372, 'p95': 1.293428897857666, 'max': 22.442858287266322}`.
- The issue-time enemy guard retained 14903 observations, detected 2745 during-plan geometry changes, recertified 2745 decisions, and overrode 64 actions. Read/recertificate timing was `{'median': 1.6898000030778348, 'p95': 3.4390000510029495, 'max': 12.566200050059706}` / `{'median': 1.8580000032670796, 'p95': 3.523699997458607, 'max': 13.650399981997907}` ms; 2930 issue captures contained latent bodies (maximum 57), and 7500 contained dormant bodies (maximum 52). Fresh/global transactions preserved 2681/2745 planned actions, relaxed 4 fresh/global empty intersections, inherited 15 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11521 observations (11472 contact enabled, 49 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 11521}`.
- The terminal-threat heuristic covered 14903 decisions with horizon counts `{'0': 76, '10': 14032, '32': 795}`; it reported 15 collision and 152 sub-safety-clearance warnings, and relaxed 161 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2493, '3': 11242, '4': 1168}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 16, '2': 9987, '3': 4788, '4': 112}`.
- Adaptive delay supports were `{'1,2': 70, '1,2,3': 183, '1,2,3,4': 206, '1,2,3,4,5': 16, '2': 14, '2,3': 1953, '2,3,4': 8067, '2,3,4,5': 3524, '2,3,4,5,6': 870}`; 96 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 52/363.
- Robust viability supplied 14713 available policy queries (0 had new delay support outside the cached policy), constrained 7391 decisions, and exposed 7161 empty queried action sets. Recovery guidance was available/selected on 2033/967 empty-kernel queries; distant-kernel guidance was available/selected on 4263/4109. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 9.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 112.0, 'p95': 294.15642097360376, 'max': 488.4588007191599}`, and `{'median': 0.0, 'p95': 19.514718770980835, 'max': 43.154051065444946}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2295, '1': 1869, '2': 1569, '3': 1729, '4': 1780, '5': 1796, '6': 1855, '7': 1820}`.
- Global-horizon/local-prefix cross-tab covered 10058 decisions: 3 had a winning global state but unsafe selected prefix, 4554 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 77 selected actions were outside the reported winning set. 2147 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1931 unique policies with solve-time statistics `{'median': 105.31499999342486, 'p95': 307.02870001550764, 'max': 400.5622999975458}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1804.0}`. Policy status counts were `{'pending_future_epoch': 79, 'queryable': 14717, 'expired': 30}`; 113 robust-mode decisions had no query.
- Of 7671 unambiguous output transitions, 7177 (0.936) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 16}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 15 hit windows with a positive warning lead; those leads were `[5, 29, 11, 25, 11, 20, 5, 15, 10, 15, 4, 0, 10, 9, 7, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.461 during the 60 frames preceding a hit versus 0.157 outside those windows.
- Mean selected control-reserve deficit was 10.802 during the 60 frames preceding a hit versus 3.841 outside those windows.
- Soft recovery was selected on 0.050 of alive decisions in the 60-frame pre-hit windows versus 0.067 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 8.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
