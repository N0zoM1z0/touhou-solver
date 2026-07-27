# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_050305

## Scope And Integrity

- Valid practice scope: `2..44273` (14394 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[1743, 4261, 11456, 12075, 12924, 19000, 21350, 22433, 30479, 36975, 38631, 43525]`.
- Hard no-Bomb verification: **PASS** across 14394 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1743-T1`. It occurred during a nonspell phase at player (28.000, 432.000), with 395 bullets and 0 lasers. The projectile model reported pipeline clearance -0.047.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 9 |
| `modeled_committed_prefix_collision` | 3 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 8
- `pool_density_over_1000`: 3
- `corridor_deadline_miss`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1743 | nonspell | (28.000, 432.000) | `right_fast` | 395/0 | -0.047/-2.814 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4261 | nonspell | (370.343, 432.000) | `up` | 1070/0 | -1.738/-30.224 | 18f/21f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11456 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 610/0 | -1.455/-1.455 | 0f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12075 | 57 夢境「二重大結界」 | (370.343, 426.343) | `up_left_fast` | 582/0 | 2.497/-1.937 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12924 | 57 夢境「二重大結界」 | (16.000, 432.000) | `right_fast` | 605/0 | 1.123/-2.290 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19000 | 61 散霊「夢想封印　寂」 | (271.833, 432.000) | `left_fast` | 310/0 | 1.976/-7.313 | 11f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21350 | nonspell | (15.253, 432.000) | `up_left_fast` | 325/0 | -2.208/-2.208 | 0f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22433 | nonspell | (373.172, 416.018) | `down_left_fast` | 839/0 | -0.673/-0.673 | 2f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30479 | 65 神技「八方龍殺陣」 | (270.771, 429.700) | `up` | 1289/0 | -1.692/-6.932 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36975 | 69 回霊「夢想封印　侘」 | (368.000, 376.186) | `up_left_fast` | 500/0 | -0.467/-2.348 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38631 | 69 回霊「夢想封印　侘」 | (12.879, 383.944) | `up_right` | 655/0 | -1.505/-1.505 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43525 | 73 大結界「博麗弾幕結界」 | (180.657, 386.649) | `down_left_fast` | 1324/0 | -1.786/-3.501 | 3f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 8386 | 8244 | 3600 | 0 | 4557 | 1016 | 115.354 | 0.126 |
| 57 夢境「二重大結界」 | 3 | 1330 | 1321 | 294 | 0 | 1009 | 183 | 160.620 | 0.231 |
| 61 散霊「夢想封印　寂」 | 1 | 1328 | 1320 | 373 | 0 | 932 | 168 | 105.685 | 0.148 |
| 65 神技「八方龍殺陣」 | 1 | 868 | 859 | 703 | 0 | 129 | 136 | 56.713 | 0.420 |
| 69 回霊「夢想封印　侘」 | 2 | 1340 | 1333 | 629 | 0 | 698 | 182 | 91.510 | 0.122 |
| 73 大結界「博麗弾幕結界」 | 1 | 1142 | 1124 | 575 | 0 | 538 | 180 | 104.354 | 0.038 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.718 ms median and 17.598 ms p95.
- The full enemy sensor produced 7015 snapshots; capture read time was `{'median': 5.625899997539818, 'p95': 21.512399951461703, 'max': 37.510699999984354}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 9.0}` frames, and 7 phase-counter discontinuities were excluded; 13975 decisions retained at least one robust-union body (maximum 58); 2863 decisions contained latent contact-disabled geometry (maximum 58), and 7005 contained bounded inactive-slot memory (maximum 52). 170 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.2322654724121094, 'p95': 4.42529296875, 'max': 6.217256546020508}` / `{'median': 2.4954705238342285, 'p95': 3.9692413806915283, 'max': 5.070939064025879}` / `{'median': 0.5281205177307129, 'p95': 3.6666688919067383, 'max': 7.974594354629517}`.
- The issue-time enemy guard retained 14394 observations, detected 2314 during-plan geometry changes, recertified 2314 decisions, and overrode 31 actions. Read/recertificate timing was `{'median': 1.6832499823067337, 'p95': 3.423099988140166, 'max': 13.433200016152114}` / `{'median': 1.8632000137586147, 'p95': 3.752299991901964, 'max': 11.639000033028424}` ms; 2868 issue captures contained latent bodies (maximum 58), and 7024 contained dormant bodies (maximum 52). Fresh/global transactions preserved 2283/2314 planned actions, relaxed 1 fresh/global empty intersections, inherited 21 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11033 observations (10985 contact enabled, 48 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4783, '0x00587A90': 6250}`.
- The terminal-threat heuristic covered 14394 decisions with horizon counts `{'0': 76, '10': 13366, '32': 952}`; it reported 40 collision and 185 sub-safety-clearance warnings, and relaxed 164 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2685, '3': 10643, '4': 1066}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 12, '2': 9342, '3': 4764, '4': 276}`.
- Adaptive delay supports were `{'1,2': 37, '1,2,3': 168, '1,2,3,4': 219, '1,2,3,4,5': 49, '2,3': 2464, '2,3,4': 7493, '2,3,4,5': 3062, '2,3,4,5,6': 901, '3,4': 1}`; 59 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 48/294.
- Robust viability supplied 14201 available policy queries (0 had new delay support outside the cached policy), constrained 7863 decisions, and exposed 6174 empty queried action sets. Recovery guidance was available/selected on 1786/888 empty-kernel queries; distant-kernel guidance was available/selected on 3517/3385. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 16.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 101.19288512538814, 'p95': 326.3372488699382, 'max': 524.8390229394153}`, and `{'median': 0.0, 'p95': 16.0, 'max': 46.02010130882263}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2186, '1': 1795, '2': 1449, '3': 1774, '4': 1664, '5': 1789, '6': 1746, '7': 1798}`.
- Global-horizon/local-prefix cross-tab covered 10256 decisions: 1 had a winning global state but unsafe selected prefix, 4223 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 81 selected actions were outside the reported winning set. 2037 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1865 unique policies with solve-time statistics `{'median': 110.5297000030987, 'p95': 304.7738000168465, 'max': 398.4454999445006}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1803.0}`. Policy status counts were `{'pending_future_epoch': 85, 'queryable': 14201, 'expired': 37}`; 122 robust-mode decisions had no query.
- Of 7188 unambiguous output transitions, 6748 (0.939) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 12}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[8, 21, 2, 4, 7, 15, 2, 8, 9, 5, 8, 16]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.341 during the 60 frames preceding a hit versus 0.141 outside those windows.
- Mean selected control-reserve deficit was 8.699 during the 60 frames preceding a hit versus 3.570 outside those windows.
- Soft recovery was selected on 0.078 of alive decisions in the 60-frame pre-hit windows versus 0.064 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 15.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
