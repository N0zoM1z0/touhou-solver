# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_101804

## Scope And Integrity

- Valid practice scope: `1..43865` (14126 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 13, at `[3919, 4271, 9854, 11602, 12243, 13162, 20611, 21058, 21383, 29548, 30483, 34070, 38026]`.
- Hard no-Bomb verification: **PASS** across 14126 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F3919-T1`. It occurred during a nonspell phase at player (324.804, 432.000), with 645 bullets and 0 lasers. The projectile model reported pipeline clearance 0.975.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 7 |
| `modeled_committed_prefix_collision` | 4 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 12
- `playfield_boundary`: 9
- `pool_density_over_1000`: 3
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3919 | nonspell | (324.804, 432.000) | `left_fast` | 645/0 | 0.975/-3.564 | 3f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4271 | nonspell | (376.000, 426.250) | `down_left_fast` | 1097/0 | -3.231/-10.565 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9854 | nonspell | (66.837, 420.659) | `up` | 519/0 | 0.082/-2.941 | 3f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11602 | 57 夢境「二重大結界」 | (8.000, 400.654) | `up_right_fast` | 599/0 | -1.945/-1.945 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12243 | 57 夢境「二重大結界」 | (376.000, 430.005) | `up_left_fast` | 582/0 | -1.416/-1.416 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13162 | 57 夢境「二重大結界」 | (376.000, 412.893) | `up_fast` | 594/0 | -0.270/-3.343 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20611 | nonspell | (369.027, 432.000) | `up_left_fast` | 284/0 | 2.881/-3.786 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21058 | nonspell | (350.269, 432.000) | `right_fast` | 800/0 | 0.023/-2.352 | 0f/5f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21383 | nonspell | (190.940, 420.000) | `right_fast` | 545/0 | -1.529/-14.047 | 7f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29548 | 65 神技「八方龍殺陣」 | (16.000, 432.000) | `right_fast` | 1202/0 | -2.008/-20.709 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30483 | 65 神技「八方龍殺陣」 | (332.686, 404.000) | `up_fast` | 1300/0 | 0.369/-10.071 | 15f/28f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34070 | nonspell | (21.690, 339.188) | `up_fast` | 147/0 | -8.390/-8.390 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38026 | 69 回霊「夢想封印　侘」 | (376.000, 347.505) | `left_fast` | 715/0 | -6.166/-6.166 | 10f/22f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 8377 | 8240 | 3683 | 0 | 4505 | 1004 | 116.128 | 0.149 |
| 57 夢境「二重大結界」 | 3 | 1308 | 1300 | 277 | 0 | 991 | 183 | 158.255 | 0.247 |
| 61 | 0 | 1117 | 1106 | 299 | 0 | 791 | 142 | 106.037 | 0.184 |
| 65 神技「八方龍殺陣」 | 2 | 942 | 933 | 766 | 0 | 167 | 143 | 61.598 | 0.329 |
| 69 回霊「夢想封印　侘」 | 1 | 1310 | 1299 | 698 | 0 | 597 | 179 | 82.989 | 0.066 |
| 73 | 0 | 1072 | 1057 | 629 | 0 | 410 | 177 | 105.228 | 0.036 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.753 ms median and 17.719 ms p95.
- The full enemy sensor produced 6921 snapshots; capture read time was `{'median': 5.903499957639724, 'p95': 22.45829999446869, 'max': 39.71689997706562}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 6 phase-counter discontinuities were excluded; 13733 decisions retained at least one robust-union body (maximum 57); 2934 decisions contained latent contact-disabled geometry (maximum 57), and 7045 contained bounded inactive-slot memory (maximum 51). 236 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.407911268147555, 'p95': 3.991586685180664, 'max': 7.746488571166992}` / `{'median': 2.4195791482925415, 'p95': 3.7785749435424805, 'max': 3.9229559898376465}` / `{'median': 0.009130358695983887, 'p95': 4.891898155212402, 'max': 7.79998779296875}`.
- The issue-time enemy guard retained 14126 observations, detected 2183 during-plan geometry changes, recertified 2183 decisions, and overrode 55 actions. Read/recertificate timing was `{'median': 1.7240999732166529, 'p95': 3.501200000755489, 'max': 16.411199991125613}` / `{'median': 1.8842999706976116, 'p95': 3.617800015490502, 'max': 12.02780002495274}` ms; 2935 issue captures contained latent bodies (maximum 57), and 7030 contained dormant bodies (maximum 51). Fresh/global transactions preserved 2128/2183 planned actions, relaxed 0 fresh/global empty intersections, inherited 8 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 10734 observations (10688 contact enabled, 46 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4379, '0x0059C9D0': 6355}`.
- The terminal-threat heuristic covered 14126 decisions with horizon counts `{'0': 73, '10': 13238, '32': 815}`; it reported 9 collision and 134 sub-safety-clearance warnings, and relaxed 122 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2125, '3': 10985, '4': 1016}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 46, '2': 9326, '3': 4149, '4': 605}`.
- Adaptive delay supports were `{'1,2': 37, '1,2,3': 121, '1,2,3,4': 264, '1,2,3,4,5': 9, '2,3': 1397, '2,3,4': 8263, '2,3,4,5': 2906, '2,3,4,5,6': 1114, '3,4': 12, '3,4,5,6': 2, '4,5,6': 1}`; 75 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 19/122.
- Robust viability supplied 13935 available policy queries (0 had new delay support outside the cached policy), constrained 7461 decisions, and exposed 6352 empty queried action sets. Recovery guidance was available/selected on 1798/851 empty-kernel queries; distant-kernel guidance was available/selected on 3833/3726. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 13.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 97.32420048477151, 'p95': 294.15642097360376, 'max': 475.1757569573599}`, and `{'median': 0.0, 'p95': 16.0, 'max': 38.46975231170654}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2155, '1': 1774, '2': 1455, '3': 1689, '4': 1661, '5': 1745, '6': 1718, '7': 1738}`.
- Global-horizon/local-prefix cross-tab covered 10098 decisions: 2 had a winning global state but unsafe selected prefix, 4263 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 89 selected actions were outside the reported winning set. 1783 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1828 unique policies with solve-time statistics `{'median': 109.53484996571206, 'p95': 307.1312999818474, 'max': 422.8829000494443}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1792.0}`. Policy status counts were `{'pending_future_epoch': 75, 'queryable': 13937, 'expired': 13}`; 90 robust-mode decisions had no query.
- Of 7084 unambiguous output transitions, 6613 (0.934) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 13}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[11, 4, 13, 4, 10, 5, 5, 5, 13, 6, 28, 0, 22]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.300 during the 60 frames preceding a hit versus 0.149 outside those windows.
- Mean selected control-reserve deficit was 7.683 during the 60 frames preceding a hit versus 3.507 outside those windows.
- Soft recovery was selected on 0.058 of alive decisions in the 60-frame pre-hit windows versus 0.065 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
