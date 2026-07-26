# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260726_163501

## Scope And Integrity

- Valid practice scope: `1..73585` (15918 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 17, at `[2762, 9176, 11704, 13260, 18979, 19844, 20709, 30599, 35912, 39254, 53677, 54690, 55183, 56258, 57320, 61401, 63987]`.
- Hard no-Bomb verification: **PASS** across 15918 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F2762-T1`. It occurred during a nonspell phase at player (376.000, 362.560), with 367 bullets and 0 lasers. The projectile model reported pipeline clearance -3.140.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 14 |
| `sensor_gap_or_unmodeled_hazard` | 2 |
| `observed_laser_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 15
- `fast_mode`: 12
- `pool_density_over_1000`: 4
- `corridor_deadline_miss`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2762 | nonspell | (376.000, 362.560) | `down_left_fast` | 367/0 | -3.140/-3.140 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9176 | nonspell | (376.000, 425.495) | `up_right` | 313/0 | -3.373/-3.373 | 3f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11704 | 150 薬符「壺中の大銀河」 | (376.000, 432.000) | `right_fast` | 623/0 | 0.347/-3.404 | 4f/11f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13260 | 150 薬符「壺中の大銀河」 | (376.000, 416.000) | `up_right_fast` | 655/0 | 1.056/-31.826 | 7f/14f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18979 | nonspell | (13.482, 427.121) | `up` | 1109/0 | -1.436/-1.436 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19844 | nonspell | (361.858, 432.000) | `up_left_fast` | 1189/0 | -1.811/-1.906 | 6f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20709 | nonspell | (100.105, 432.000) | `down_left` | 1192/0 | -2.308/-2.308 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30599 | 158 神宝「ブディストダイアモンド」 | (8.000, 432.000) | `up_fast` | 241/33 | -1.874/-1.874 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35912 | nonspell | (67.214, 432.000) | `up_left_fast` | 625/0 | -7.367/-7.367 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39254 | 162 神宝「サラマンダーシールド」 | (376.000, 410.209) | `left_fast` | 564/32 | -4.590/-4.590 | 3f/12f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 53677 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (207.853, 432.000) | `up_right_fast` | 336/0 | -7.517/-7.517 | 6f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54690 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 366.300) | `left_fast` | 585/0 | -2.198/-2.198 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55183 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (371.121, 421.638) | `left_fast` | 576/0 | -2.580/-3.747 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56258 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 432.000) | `stay` | 531/0 | -0.586/-0.586 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57320 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (346.468, 432.000) | `left_fast` | 569/0 | -0.144/-1.178 | 3f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 61401 | 174 「永夜返し  -待宵-」 | (376.000, 432.000) | `stay` | 878/0 | -0.015/-1.027 | 3f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 63987 | 178 「永夜返し  -子の四つ-」 | (376.000, 432.000) | `up_fast` | 1043/0 | -4.782/-4.782 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 7236 | 7018 | 3145 | 0 | 3809 | 1156 | 98.040 | 0.089 |
| 150 薬符「壺中の大銀河」 | 2 | 784 | 762 | 287 | 0 | 469 | 128 | 200.660 | 0.125 |
| 154 | 0 | 766 | 759 | 342 | 0 | 390 | 147 | 128.949 | 0.192 |
| 158 神宝「ブディストダイアモンド」 | 1 | 1066 | 1057 | 619 | 0 | 433 | 172 | 57.734 | 0.209 |
| 162 神宝「サラマンダーシールド」 | 1 | 1204 | 1194 | 686 | 0 | 506 | 214 | 81.619 | 0.121 |
| 166 | 0 | 1330 | 1324 | 556 | 0 | 691 | 238 | 154.289 | 0.242 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 5 | 1821 | 1803 | 835 | 0 | 954 | 299 | 89.232 | 0.249 |
| 174 「永夜返し  -待宵-」 | 1 | 230 | 218 | 85 | 0 | 114 | 32 | 97.133 | 0.084 |
| 178 「永夜返し  -子の四つ-」 | 1 | 210 | 190 | 137 | 0 | 53 | 26 | 65.402 | 0.238 |
| 182 | 0 | 415 | 395 | 333 | 0 | 62 | 59 | 27.477 | 0.263 |
| 186 | 0 | 148 | 139 | 74 | 0 | 64 | 18 | 334.795 | 0.099 |
| 190 | 0 | 708 | 686 | 420 | 0 | 261 | 109 | 64.542 | 0.086 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 1 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 15.555 ms median and 26.616 ms p95.
- The full enemy sensor produced 8781 snapshots; capture read time was `{'median': 19.35119996778667, 'p95': 39.8879999993369, 'max': 86.66109998011962}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 12 phase-counter discontinuities were excluded; 15373 decisions retained at least one robust-union body (maximum 34); 4438 decisions contained latent contact-disabled geometry (maximum 33), and 5328 contained bounded inactive-slot memory (maximum 33). 139 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 9.11346435546875, 'max': 9.415674546185661}` / `{'median': 0.0, 'p95': 9.573974609375, 'max': 10.168914794921875}` / `{'median': 0.0, 'p95': 3.862670000861673, 'max': 4.115363625919118}`.
- The issue-time enemy guard retained 15918 observations, detected 822 during-plan geometry changes, recertified 822 decisions, and overrode 465 actions. Read/recertificate timing was `{'median': 1.7941500118467957, 'p95': 3.6954000242985785, 'max': 20.852499990724027}` / `{'median': 3.568749991245568, 'p95': 7.994999992661178, 'max': 17.068800050765276}` ms; 2498 issue captures contained latent bodies (maximum 33), and 5324 contained dormant bodies (maximum 33).
- The synchronous spell-owner guard retained 14442 observations (12511 contact enabled, 1931 anticipatory, 0 errors). 12858 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 12858, '0x0059C9D0': 1584}`.
- The terminal-threat heuristic covered 15918 decisions with horizon counts `{'0': 75, '10': 14732, '32': 1111}`; it reported 14 collision and 192 sub-safety-clearance warnings, and relaxed 220 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 39, '3': 4447, '4': 10877, '5': 477, '6': 78}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 54, '3': 11084, '4': 4770, '5': 10}`.
- Adaptive delay supports were `{'1,2,3': 26, '1,2,3,4': 1, '2,3': 48, '2,3,4': 485, '2,3,4,5': 1888, '2,3,4,5,6': 2303, '3': 20, '3,4': 627, '3,4,5': 4656, '3,4,5,6': 5857, '4,5,6': 2, '5,6': 5}`; 517 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 81/495.
- Robust viability supplied 15545 available policy queries (0 had new delay support outside the cached policy), constrained 7806 decisions, and exposed 7519 empty queried action sets. Recovery guidance was available/selected on 1772/959 empty-kernel queries; distant-kernel guidance was available/selected on 4930/4779. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 9.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 107.33126291998991, 'p95': 320.3997503120126, 'max': 489.76729168044693}`, and `{'median': 0.0, 'p95': 20.7473087310791, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2439, '1': 2150, '2': 1926, '3': 1704, '4': 1891, '5': 1806, '6': 1775, '7': 1854}`.
- Global-horizon/local-prefix cross-tab covered 12807 decisions: 1 had a winning global state but unsafe selected prefix, 6452 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 83 selected actions were outside the reported winning set. 729 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2598 unique policies with solve-time statistics `{'median': 101.0934000078123, 'p95': 432.7437999891117, 'max': 559.1256999759935}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1809.0}`. Policy status counts were `{'pending_future_epoch': 59, 'queryable': 15549, 'expired': 74}`; 137 robust-mode decisions had no query.
- Of 8228 unambiguous output transitions, 7092 (0.862) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 17}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 17 hit windows with a positive warning lead; those leads were `[5, 11, 11, 14, 11, 12, 4, 6, 9, 12, 15, 11, 6, 7, 18, 10, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.363 during the 60 frames preceding a hit versus 0.138 outside those windows.
- Mean selected control-reserve deficit was 12.701 during the 60 frames preceding a hit versus 5.809 outside those windows.
- Soft recovery was selected on 0.024 of alive decisions in the 60-frame pre-hit windows versus 0.064 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 6.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
