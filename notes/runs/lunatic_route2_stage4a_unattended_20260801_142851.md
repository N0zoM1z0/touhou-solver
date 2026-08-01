# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_142851

## Scope And Integrity

- Valid practice scope: `1..45180` (11591 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[833, 1265, 2278, 8812, 11606, 12156, 12606, 21061, 21609, 21974, 22640, 27713, 30504, 30903, 31670, 35594, 39280, 44846]`.
- Hard no-Bomb verification: **PASS** across 11591 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F833-T1`. It occurred during a nonspell phase at player (376.000, 417.742), with 218 bullets and 0 lasers. The projectile model reported pipeline clearance 6.171.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 7 |
| `modeled_committed_prefix_collision` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 4 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 14
- `fast_mode`: 12
- `corridor_deadline_miss`: 6
- `action_lag_over_model`: 5
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 833 | nonspell | (376.000, 417.742) | `up_right_fast` | 218/0 | 6.171/5.464 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1265 | nonspell | (376.000, 432.000) | `down_right` | 173/0 | 6.842/1.460 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2278 | nonspell | (312.000, 432.000) | `stay` | 298/0 | 0.496/0.496 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 8812 | nonspell | (376.000, 432.000) | `up_fast` | 769/0 | -16.729/-16.729 | 8f/10f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11606 | 57 夢境「二重大結界」 | (372.747, 432.000) | `up` | 508/0 | -2.220/-2.220 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12156 | 57 夢境「二重大結界」 | (8.000, 432.000) | `right_fast` | 629/0 | -3.593/-3.593 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12606 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 609/0 | -1.788/-1.788 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21061 | nonspell | (187.402, 430.928) | `down` | 350/0 | 32.321/20.142 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 21609 | nonspell | (189.787, 432.000) | `right_fast` | 169/0 | -3.151/-3.151 | 7f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 21974 | nonspell | (240.251, 432.000) | `stay` | 783/0 | -2.651/-2.651 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 22640 | nonspell | (8.000, 350.571) | `up_fast` | 903/0 | 0.198/-1.190 | 5f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 27713 | nonspell | (9.626, 419.326) | `up_right_fast` | 157/0 | 2.972/-0.242 | 2f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 30504 | 65 神技「八方龍殺陣」 | (259.794, 386.361) | `down_left_fast` | 1183/0 | -2.119/-2.119 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 30903 | 65 神技「八方龍殺陣」 | (84.561, 382.732) | `down_right` | 1047/0 | -3.534/-3.534 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31670 | 65 神技「八方龍殺陣」 | (153.879, 427.121) | `right_fast` | 1222/0 | -1.651/-5.283 | 4f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 35594 | nonspell | (8.000, 408.000) | `up_fast` | 105/0 | -1.730/-5.346 | 8f/15f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39280 | 69 回霊「夢想封印　侘」 | (376.000, 285.251) | `up_fast` | 619/0 | -4.730/-6.910 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44846 | 73 大結界「博麗弾幕結界」 | (65.645, 94.659) | `down_right_fast` | 1345/0 | -1.892/-1.892 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 6554 | 420 | 61 | 0 | 470 | 25 | 810.453 | 0.230 |
| 57 夢境「二重大結界」 | 3 | 1238 | 716 | 296 | 0 | 0 | 73 | 182.337 | 0.414 |
| 61 | 0 | 844 | 837 | 349 | 0 | 0 | 136 | 137.229 | 0.182 |
| 65 神技「八方龍殺陣」 | 3 | 975 | 426 | 337 | 0 | 0 | 24 | 68.596 | 0.347 |
| 69 回霊「夢想封印　侘」 | 1 | 1039 | 1033 | 649 | 0 | 0 | 179 | 102.243 | 0.163 |
| 73 大結界「博麗弾幕結界」 | 1 | 941 | 934 | 519 | 0 | 0 | 180 | 129.051 | 0.059 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 18.290 ms median and 33.806 ms p95.
- The full enemy sensor produced 6298 snapshots; capture read time was `{'median': 6.03160000173375, 'p95': 29.10729998257011, 'max': 492.98549999366514}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 104.0}` frames, and 10 phase-counter discontinuities were excluded; 11304 decisions retained at least one robust-union body (maximum 50); 5844 decisions contained latent contact-disabled geometry (maximum 50), and 4524 contained bounded inactive-slot memory (maximum 24). 299 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.99993896484375, 'p95': 3.999755859375, 'max': 7.810871124267578}` / `{'median': 2.411390781402588, 'p95': 3.9177112579345703, 'max': 67.39753723144531}` / `{'median': 0.018844544887542725, 'p95': 4.158191680908203, 'max': 67.39753723144531}`.
- The issue-time enemy guard retained 11591 observations, detected 4509 during-plan geometry changes, recertified 4509 decisions, and overrode 74 actions. Read/recertificate timing was `{'median': 1.6160999948624521, 'p95': 2.9273999971337616, 'max': 207.85350000369363}` / `{'median': 2.455099980579689, 'p95': 9.10300001851283, 'max': 454.4549999991432}` ms; 5845 issue captures contained latent bodies (maximum 50), and 4531 contained dormant bodies (maximum 25). Fresh/global transactions preserved 4433/4510 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9948 observations (9906 contact enabled, 42 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9948}`.
- The terminal-threat heuristic covered 11591 decisions with horizon counts `{'0': 23, '10': 11568}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 188, '3': 7528, '4': 2880, '5': 741, '6': 254}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 5, '2': 1717, '3': 7889, '4': 1821, '5': 151, '6': 8}`.
- Adaptive delay supports were `{'1,2': 5, '1,2,3': 1, '1,2,3,4': 4, '1,2,3,4,5': 24, '1,2,3,4,5,6': 17, '2,3': 753, '2,3,4': 3470, '2,3,4,5': 3612, '2,3,4,5,6': 2834, '3,4': 18, '3,4,5': 193, '3,4,5,6': 594, '4,5': 2, '4,5,6': 62, '6': 2}`; 104 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 23/166.
- Robust viability supplied 4366 available policy queries (0 had new delay support outside the cached policy), constrained 470 decisions, and exposed 2211 empty queried action sets. Recovery guidance was available/selected on 777/0 empty-kernel queries; distant-kernel guidance was available/selected on 1201/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 632, '1': 605, '2': 526, '3': 451, '4': 532, '5': 542, '6': 507, '7': 571}`.
- Global-horizon/local-prefix cross-tab covered 2574 decisions: 4 had a winning global state but unsafe selected prefix, 1237 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 192 selected actions were outside the reported winning set. 1034 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 617 unique policies with solve-time statistics `{'median': 125.46199999633245, 'p95': 223.60880000633188, 'max': 3008.663399989018}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1692.0}`. Policy status counts were `{'pending_future_epoch': 269, 'queryable': 4348, 'expired': 2784}`; 3035 robust-mode decisions had no query.
- Of 6425 unambiguous output transitions, 6069 (0.945) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 6, 'unresolved_planner_failure': 2, 'robust_action_set_exhausted_before_hit': 8, 'late_collision_after_positive_causal_margin': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[0, 0, 0, 10, 5, 8, 6, 0, 7, 0, 11, 6, 0, 7, 4, 15, 3, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.409 during the 60 frames preceding a hit versus 0.222 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
