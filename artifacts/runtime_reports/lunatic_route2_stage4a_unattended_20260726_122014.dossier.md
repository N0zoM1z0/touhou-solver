# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260726_122014

## Scope And Integrity

- Valid practice scope: `2..44817` (8914 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 17, at `[3996, 10913, 11324, 11932, 12435, 21810, 22647, 27182, 30582, 31255, 34562, 35021, 36012, 36334, 37504, 38214, 39249]`.
- Hard no-Bomb verification: **PASS** across 8914 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F3996-T1`. It occurred during a nonspell phase at player (363.618, 427.718), with 878 bullets and 0 lasers. The projectile model reported pipeline clearance 0.566.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 2 |

Contributing factors:

- `fast_mode`: 10
- `playfield_boundary`: 10
- `action_lag_over_model`: 3
- `corridor_deadline_miss`: 2
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3996 | nonspell | (363.618, 427.718) | `left` | 878/0 | 0.566/-29.036 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10913 | 57 夢境「二重大結界」 | (8.000, 432.000) | `stay` | 456/0 | -1.460/-1.460 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11324 | 57 夢境「二重大結界」 | (300.301, 420.000) | `left_fast` | 615/0 | 2.304/-2.758 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11932 | 57 夢境「二重大結界」 | (38.696, 348.867) | `up_fast` | 597/0 | -1.108/-1.108 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 12435 | 57 夢境「二重大結界」 | (9.905, 432.000) | `down_left_fast` | 593/0 | -1.628/-1.628 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21810 | nonspell | (16.132, 341.180) | `up_left_fast` | 654/0 | -2.702/-7.021 | 4f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22647 | nonspell | (115.216, 393.506) | `up` | 705/0 | -0.935/-0.935 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27182 | nonspell | (373.081, 168.225) | `up_fast` | 140/0 | -20.661/-20.661 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30582 | 65 神技「八方龍殺陣」 | (212.979, 432.000) | `down` | 1198/0 | -1.517/-1.517 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31255 | 65 神技「八方龍殺陣」 | (181.595, 432.000) | `left_fast` | 1171/0 | -6.906/-8.906 | 7f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34562 | nonspell | (8.000, 424.000) | `up_fast` | 103/0 | -14.137/-14.137 | 8f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35021 | nonspell | (8.000, 432.000) | `up_fast` | 102/0 | -1.470/-2.102 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36012 | nonspell | (68.100, 432.000) | `left` | 83/0 | -2.408/-16.404 | 20f/25f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36334 | nonspell | (356.000, 432.000) | `left_fast` | 95/0 | -0.076/-14.293 | 12f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37504 | 69 回霊「夢想封印　侘」 | (67.086, 335.538) | `down_right_fast` | 473/0 | 1.529/1.529 | 0f/3f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38214 | 69 回霊「夢想封印　侘」 | (8.000, 407.094) | `down_left` | 590/0 | -1.522/-1.522 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39249 | 69 回霊「夢想封印　侘」 | (92.232, 410.800) | `up` | 650/0 | -3.860/-3.860 | 12f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 5026 | 4914 | 2328 | 0 | 2537 | 901 | 144.432 | 0.162 |
| 57 夢境「二重大結界」 | 4 | 874 | 865 | 164 | 0 | 682 | 163 | 209.527 | 0.291 |
| 61 | 0 | 821 | 813 | 198 | 0 | 595 | 153 | 153.730 | 0.118 |
| 65 神技「八方龍殺陣」 | 2 | 535 | 524 | 442 | 0 | 82 | 121 | 65.453 | 0.358 |
| 69 回霊「夢想封印　侘」 | 3 | 849 | 844 | 360 | 0 | 478 | 164 | 115.850 | 0.092 |
| 73 | 0 | 809 | 799 | 477 | 0 | 315 | 159 | 107.363 | 0.024 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 21.992 ms median and 42.813 ms p95.
- The full enemy sensor produced 6266 snapshots; capture read time was `{'median': 25.42300001368858, 'p95': 55.35260000033304, 'max': 211.46219997899607}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 21.0}` frames, and 5 phase-counter discontinuities were excluded; 8588 decisions retained at least one robust-union body (maximum 58); 1702 decisions contained latent contact-disabled geometry (maximum 58), and 4400 contained bounded inactive-slot memory (maximum 52). 275 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.69586181640625, 'p95': 4.1827748616536455, 'max': 7.793496268136161}` / `{'median': 2.782097101211548, 'p95': 3.922954797744751, 'max': 119.4684066772461}` / `{'median': 0.01930514971415187, 'p95': 3.068565845489502, 'max': 119.4684066772461}`.
- The issue-time enemy guard retained 8914 observations, detected 2774 during-plan geometry changes, recertified 2774 decisions, and overrode 1480 actions. Read/recertificate timing was `{'median': 1.947249984368682, 'p95': 4.373900010250509, 'max': 30.412100022658706}` / `{'median': 8.219650015234947, 'p95': 17.93019997421652, 'max': 40.78519996255636}` ms; 1697 issue captures contained latent bodies (maximum 58), and 4399 contained dormant bodies (maximum 52).
- The synchronous spell-owner guard retained 6850 observations (6823 contact enabled, 27 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 2996, '0x00597600': 3854}`.
- The terminal-threat heuristic covered 8914 decisions with horizon counts `{'0': 46, '10': 8146, '32': 722}`; it reported 3 collision and 71 sub-safety-clearance warnings, and relaxed 101 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 47, '3': 253, '4': 4406, '5': 3420, '6': 788}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 53, '3': 556, '4': 6724, '5': 1348, '6': 233}`.
- Adaptive delay supports were `{'1,2,3': 26, '1,2,3,4,5,6': 1, '2,3': 25, '2,3,4': 58, '2,3,4,5': 154, '2,3,4,5,6': 634, '3,4': 49, '3,4,5': 485, '3,4,5,6': 7294, '4,5,6': 186, '5,6': 1, '6': 1}`; 1579 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 45/166.
- Robust viability supplied 8759 available policy queries (0 had new delay support outside the cached policy), constrained 4689 decisions, and exposed 3969 empty queried action sets. Recovery guidance was available/selected on 1150/645 empty-kernel queries; distant-kernel guidance was available/selected on 2313/2188. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 16.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 97.32420048477151, 'p95': 314.350123270216, 'max': 497.80317395532944}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1311, '1': 1245, '2': 1101, '3': 1014, '4': 1010, '5': 1022, '6': 1047, '7': 1009}`.
- Global-horizon/local-prefix cross-tab covered 4877 decisions: 3 had a winning global state but unsafe selected prefix, 1841 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 43 selected actions were outside the reported winning set. 2318 newer issue-time hazard versions and 3 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1661 unique policies with solve-time statistics `{'median': 138.19929998135194, 'p95': 442.46049999492243, 'max': 574.8733999789692}` and first-observed ages `{'median': 4.0, 'p95': 10.0, 'max': 1817.0}`. Policy status counts were `{'pending_future_epoch': 40, 'queryable': 8760, 'expired': 30}`; 71 robust-mode decisions had no query.
- Of 5281 unambiguous output transitions, 4578 (0.867) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 16, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 11 hit windows with a positive warning lead; those leads were `[0, 6, 10, 0, 10, 9, 0, 0, 0, 15, 14, 7, 25, 19, 3, 0, 15]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.379 during the 60 frames preceding a hit versus 0.149 outside those windows.
- Mean selected control-reserve deficit was 11.429 during the 60 frames preceding a hit versus 7.296 outside those windows.
- Soft recovery was selected on 0.085 of alive decisions in the 60-frame pre-hit windows versus 0.073 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
