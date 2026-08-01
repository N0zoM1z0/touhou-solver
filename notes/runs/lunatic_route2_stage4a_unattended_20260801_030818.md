# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_030818

## Scope And Integrity

- Valid practice scope: `1..45167` (11459 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 21, at `[827, 1186, 1665, 2134, 2494, 3011, 3397, 4327, 8881, 9912, 12931, 21252, 21727, 22044, 27606, 30320, 31252, 31988, 37793, 39859, 43067]`.
- Hard no-Bomb verification: **PASS** across 11459 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F827-T1`. It occurred during a nonspell phase at player (50.601, 390.768), with 235 bullets and 0 lasers. The projectile model reported pipeline clearance 5.700.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 12 |
| `sensor_gap_or_unmodeled_hazard` | 5 |
| `modeled_committed_prefix_collision` | 4 |

Contributing factors:

- `fast_mode`: 17
- `playfield_boundary`: 10
- `action_lag_over_model`: 8
- `pool_density_over_1000`: 5
- `corridor_deadline_miss`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 827 | nonspell | (50.601, 390.768) | `up_right` | 235/0 | 5.700/5.700 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 1186 | nonspell | (141.382, 400.887) | `up_right_fast` | 251/0 | -1.012/-1.012 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 1665 | nonspell | (53.200, 431.490) | `right_fast` | 444/0 | 0.094/-0.345 | 0f/17f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 2134 | nonspell | (16.485, 422.587) | `up_right_fast` | 114/0 | -0.033/-1.752 | 2f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 2494 | nonspell | (187.121, 395.779) | `stay` | 438/0 | 26.554/25.450 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3011 | nonspell | (373.412, 432.000) | `down` | 511/0 | 0.703/0.703 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3397 | nonspell | (113.214, 432.000) | `down_left_fast` | 360/0 | -18.996/-18.996 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 4327 | nonspell | (16.835, 429.172) | `up_right_fast` | 1103/0 | 2.133/-16.978 | 0f/3f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 8881 | nonspell | (107.640, 432.000) | `right_fast` | 505/0 | -2.309/-7.760 | 6f/13f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 9912 | nonspell | (36.000, 432.000) | `right_fast` | 317/0 | 0.437/-9.106 | 10f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12931 | 57 夢境「二重大結界」 | (16.485, 419.515) | `up_right_fast` | 598/0 | 1.637/-2.020 | 2f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21252 | nonspell | (368.138, 432.000) | `left_fast` | 425/0 | 9.300/5.416 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 21727 | nonspell | (8.000, 294.949) | `up_left_fast` | 466/0 | -1.896/-26.673 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 22044 | nonspell | (166.886, 420.614) | `stay` | 802/0 | -4.074/-4.074 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 27606 | nonspell | (21.789, 423.090) | `up_fast` | 168/0 | 4.559/-1.348 | 4f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 30320 | 65 神技「八方龍殺陣」 | (376.000, 419.294) | `left_fast` | 1224/0 | -2.783/-18.540 | 16f/28f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31252 | 65 神技「八方龍殺陣」 | (324.115, 428.000) | `up_fast` | 1302/0 | -0.958/-6.688 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31988 | 65 神技「八方龍殺陣」 | (203.405, 422.957) | `right_fast` | 1264/0 | 0.443/-4.576 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 37793 | 69 回霊「夢想封印　侘」 | (74.388, 388.630) | `up_left_fast` | 445/0 | -4.323/-4.323 | 16f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39859 | 69 回霊「夢想封印　侘」 | (12.879, 420.616) | `down_left_fast` | 755/0 | -3.126/-3.126 | 14f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43067 | 73 大結界「博麗弾幕結界」 | (159.274, 384.834) | `right_fast` | 1240/0 | -0.042/-1.896 | 6f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 14 | 6372 | 348 | 89 | 0 | 345 | 28 | 722.452 | 0.256 |
| 57 夢境「二重大結界」 | 1 | 1145 | 701 | 317 | 0 | 0 | 78 | 174.979 | 0.376 |
| 61 | 0 | 997 | 991 | 419 | 0 | 0 | 165 | 134.145 | 0.150 |
| 65 神技「八方龍殺陣」 | 3 | 941 | 376 | 293 | 0 | 0 | 14 | 58.003 | 0.377 |
| 69 回霊「夢想封印　侘」 | 2 | 1064 | 1058 | 614 | 0 | 0 | 181 | 102.489 | 0.242 |
| 73 大結界「博麗弾幕結界」 | 1 | 940 | 933 | 523 | 0 | 0 | 181 | 123.331 | 0.020 |

## Interpretation

- Retained witnesses classify 12 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.653 ms median and 33.792 ms p95.
- The full enemy sensor produced 6285 snapshots; capture read time was `{'median': 5.607899991446175, 'p95': 27.26059999258723, 'max': 466.8835000047693}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 84.0}` frames, and 7 phase-counter discontinuities were excluded; 11230 decisions retained at least one robust-union body (maximum 59); 5990 decisions contained latent contact-disabled geometry (maximum 59), and 4545 contained bounded inactive-slot memory (maximum 35). 441 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.99993896484375, 'p95': 4.0, 'max': 6.689430236816406}` / `{'median': 2.4403953552246094, 'p95': 3.92295503616333, 'max': 7.733334541320801}` / `{'median': 0.4965839385986328, 'p95': 3.9229540824890137, 'max': 10.5999755859375}`.
- The issue-time enemy guard retained 11459 observations, detected 4268 during-plan geometry changes, recertified 4268 decisions, and overrode 88 actions. Read/recertificate timing was `{'median': 1.577299990458414, 'p95': 2.8993000014452264, 'max': 181.71479999728035}` / `{'median': 2.5194499976350926, 'p95': 9.024300001328811, 'max': 259.72770000225864}` ms; 5989 issue captures contained latent bodies (maximum 59), and 4534 contained dormant bodies (maximum 43). Fresh/global transactions preserved 4180/4268 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9695 observations (9653 contact enabled, 42 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9695}`.
- The terminal-threat heuristic covered 11459 decisions with horizon counts `{'0': 41, '10': 11418}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 24, '3': 6730, '4': 3232, '5': 709, '6': 764}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 27, '2': 568, '3': 8710, '4': 1818, '5': 335, '6': 1}`.
- Adaptive delay supports were `{'1,2': 26, '1,2,3,4,5': 51, '1,2,3,4,5,6': 42, '2,3': 407, '2,3,4': 3883, '2,3,4,5': 3159, '2,3,4,5,6': 3030, '3,4': 51, '3,4,5': 420, '3,4,5,6': 375, '4,5,6': 14, '6': 1}`; 131 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 45/124.
- Robust viability supplied 4407 available policy queries (0 had new delay support outside the cached policy), constrained 345 decisions, and exposed 2255 empty queried action sets. Recovery guidance was available/selected on 761/0 empty-kernel queries; distant-kernel guidance was available/selected on 1233/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 701, '1': 593, '2': 499, '3': 502, '4': 522, '5': 537, '6': 543, '7': 510}`.
- Global-horizon/local-prefix cross-tab covered 2619 decisions: 1 had a winning global state but unsafe selected prefix, 1316 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 173 selected actions were outside the reported winning set. 947 newer issue-time hazard versions and 7 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 647 unique policies with solve-time statistics `{'median': 122.0718999975361, 'p95': 226.81760000705253, 'max': 8036.0706000064965}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 2160.0}`. Policy status counts were `{'pending_future_epoch': 181, 'queryable': 4387, 'expired': 4398}`; 4559 robust-mode decisions had no query.
- Of 6546 unambiguous output transitions, 6261 (0.956) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 4, 'late_collision_after_positive_causal_margin': 4, 'robust_action_set_exhausted_before_hit': 6, 'global_viability_kernel_exhausted_before_hit': 6, 'missing_pre_hit_alive_decision': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[0, 0, 17, 5, 0, 0, 0, 3, 13, 15, 9, 0, 0, 0, 6, 28, 10, 0, 16, 18, 15]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.541 during the 60 frames preceding a hit versus 0.234 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 8.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
