# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_083433

## Scope And Integrity

- Valid practice scope: `1..43149` (13842 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[4166, 9514, 10679, 11397, 12301, 21123, 21989, 28481, 30075, 30617, 36538, 37647]`.
- Hard no-Bomb verification: **PASS** across 13842 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F4166-T1`. It occurred during a nonspell phase at player (368.000, 432.000), with 950 bullets and 0 lasers. The projectile model reported pipeline clearance -2.305.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 6 |
| `modeled_committed_prefix_collision` | 5 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 8
- `playfield_boundary`: 8
- `pool_density_over_1000`: 2
- `corridor_deadline_miss`: 1
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4166 | nonspell | (368.000, 432.000) | `down_fast` | 950/0 | -2.305/-6.733 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9514 | nonspell | (207.715, 412.686) | `up_left_fast` | 137/0 | -1.332/-28.219 | 0f/28f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10679 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 609/0 | -0.644/-0.644 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11397 | 57 夢境「二重大結界」 | (8.000, 415.266) | `right_fast` | 602/0 | -1.491/-1.491 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12301 | 57 夢境「二重大結界」 | (252.210, 287.818) | `down_right` | 600/0 | -0.197/-2.692 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21123 | nonspell | (13.657, 432.000) | `up_right_fast` | 625/0 | -2.478/-2.478 | 0f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21989 | nonspell | (376.000, 422.034) | `up_left` | 622/0 | -0.286/-2.304 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28481 | nonspell | (370.343, 422.690) | `up_left_fast` | 95/0 | -1.397/-4.081 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30075 | 65 神技「八方龍殺陣」 | (341.380, 432.000) | `left` | 1282/0 | -9.625/-9.625 | 0f/3f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30617 | 65 神技「八方龍殺陣」 | (176.660, 432.000) | `up_left_fast` | 1110/0 | -5.619/-17.461 | 14f/20f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36538 | 69 回霊「夢想封印　侘」 | (17.758, 414.285) | `up` | 578/0 | -5.913/-5.913 | 0f/20f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37647 | 69 回霊「夢想封印　侘」 | (8.000, 420.262) | `up_left_fast` | 636/0 | -4.724/-4.724 | 7f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 8136 | 7990 | 3396 | 0 | 4532 | 978 | 108.915 | 0.119 |
| 57 夢境「二重大結界」 | 3 | 1306 | 1296 | 318 | 0 | 957 | 183 | 159.690 | 0.199 |
| 61 | 0 | 1244 | 1236 | 281 | 0 | 944 | 158 | 124.929 | 0.125 |
| 65 神技「八方龍殺陣」 | 2 | 742 | 729 | 645 | 0 | 84 | 111 | 62.024 | 0.309 |
| 69 回霊「夢想封印　侘」 | 2 | 1334 | 1325 | 641 | 0 | 675 | 181 | 90.955 | 0.106 |
| 73 | 0 | 1080 | 1066 | 657 | 0 | 406 | 180 | 104.564 | 0.006 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.805 ms median and 17.632 ms p95.
- The full enemy sensor produced 6778 snapshots; capture read time was `{'median': 5.746850016294047, 'p95': 21.575699967797846, 'max': 38.854199985507876}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 6 phase-counter discontinuities were excluded; 13403 decisions retained at least one robust-union body (maximum 47); 2837 decisions contained latent contact-disabled geometry (maximum 47), and 6998 contained bounded inactive-slot memory (maximum 43). 213 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.4883270263671875, 'p95': 4.1908416748046875, 'max': 4.569671630859375}` / `{'median': 2.6335325241088867, 'p95': 3.975149393081665, 'max': 54.867340087890625}` / `{'median': 0.12967936197916669, 'p95': 2.2594499588012695, 'max': 54.867340087890625}`.
- The issue-time enemy guard retained 13842 observations, detected 2290 during-plan geometry changes, recertified 2290 decisions, and overrode 42 actions. Read/recertificate timing was `{'median': 1.712149998638779, 'p95': 3.5232999944128096, 'max': 12.80239998595789}` / `{'median': 1.8943000177387148, 'p95': 3.73070000205189, 'max': 12.96109997201711}` ms; 2836 issue captures contained latent bodies (maximum 47), and 7003 contained dormant bodies (maximum 45). Fresh/global transactions preserved 2248/2290 planned actions, relaxed 2 fresh/global empty intersections, inherited 14 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 10473 observations (10426 contact enabled, 47 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 10473}`.
- The terminal-threat heuristic covered 13842 decisions with horizon counts `{'0': 76, '10': 12993, '32': 773}`; it reported 32 collision and 147 sub-safety-clearance warnings, and relaxed 106 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2463, '3': 10375, '4': 1004}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 61, '2': 8626, '3': 4571, '4': 584}`.
- Adaptive delay supports were `{'1,2': 60, '1,2,3': 106, '1,2,3,4': 278, '1,2,3,4,5': 29, '2,3': 1811, '2,3,4': 6576, '2,3,4,5': 3853, '2,3,4,5,6': 1104, '3,4': 2, '3,4,5': 20, '4,5,6': 3}`; 58 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 16/126.
- Robust viability supplied 13642 available policy queries (0 had new delay support outside the cached policy), constrained 7598 decisions, and exposed 5938 empty queried action sets. Recovery guidance was available/selected on 1680/768 empty-kernel queries; distant-kernel guidance was available/selected on 3671/3564. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 17.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 93.29523031752481, 'p95': 286.2167011199731, 'max': 524.8390229394153}`, and `{'median': 0.0, 'p95': 16.0, 'max': 37.17157292366028}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2152, '1': 1669, '2': 1444, '3': 1690, '4': 1612, '5': 1695, '6': 1669, '7': 1711}`.
- Global-horizon/local-prefix cross-tab covered 9760 decisions: 3 had a winning global state but unsafe selected prefix, 4069 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 64 selected actions were outside the reported winning set. 2010 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1791 unique policies with solve-time statistics `{'median': 110.30320002464578, 'p95': 308.4682999760844, 'max': 401.36079996591434}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1789.0}`. Policy status counts were `{'pending_future_epoch': 80, 'queryable': 13643, 'expired': 13}`; 94 robust-mode decisions had no query.
- Of 6841 unambiguous output transitions, 6372 (0.931) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 12}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[8, 28, 4, 6, 9, 2, 7, 6, 3, 20, 20, 12]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.316 during the 60 frames preceding a hit versus 0.118 outside those windows.
- Mean selected control-reserve deficit was 8.500 during the 60 frames preceding a hit versus 3.211 outside those windows.
- Soft recovery was selected on 0.037 of alive decisions in the 60-frame pre-hit windows versus 0.058 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
