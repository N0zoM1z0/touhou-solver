# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_173718

## Scope And Integrity

- Valid practice scope: `3..43439` (7820 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 22, at `[4291, 9501, 9813, 11016, 11648, 12255, 13334, 20009, 20521, 25598, 28282, 29012, 29474, 30016, 32978, 33412, 34535, 36833, 37773, 41421, 41899, 42859]`.
- Hard no-Bomb verification: **PASS** across 7820 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F4291-T1`. It occurred during a nonspell phase at player (376.000, 430.665), with 897 bullets and 0 lasers. The projectile model reported pipeline clearance -4.167.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 7 |
| `observed_enemy_body_overlap` | 3 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 16
- `playfield_boundary`: 14
- `corridor_deadline_miss`: 9
- `pool_density_over_1000`: 7
- `enemy_body_absent_from_action_snapshot`: 3
- `action_lag_over_model`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4291 | nonspell | (376.000, 430.665) | `left_fast` | 897/0 | -4.167/-4.167 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9501 | nonspell | (153.817, 432.000) | `left_fast` | 148/0 | -1.124/-6.490 | 9f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9813 | nonspell | (137.518, 366.867) | `up_right_fast` | 585/0 | 81.918/29.882 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11016 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 537/0 | -1.456/-1.456 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11648 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 607/0 | -2.302/-2.302 | 5f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12255 | 57 夢境「二重大結界」 | (63.895, 360.357) | `stay` | 614/0 | -4.151/-4.151 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 13334 | 57 夢境「二重大結界」 | (30.948, 275.547) | `stay` | 595/0 | -1.375/-1.375 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 20009 | nonspell | (10.508, 432.000) | `right_fast` | 758/0 | -2.612/-2.612 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20521 | nonspell | (8.000, 403.084) | `down_fast` | 578/0 | -1.802/-1.802 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25598 | nonspell | (376.000, 411.887) | `up_left` | 174/0 | -2.904/-2.904 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28282 | 65 神技「八方龍殺陣」 | (191.422, 432.000) | `up` | 1222/0 | -1.272/-1.272 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29012 | 65 神技「八方龍殺陣」 | (291.088, 374.123) | `left_fast` | 1204/0 | 23.503/0.415 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29474 | 65 神技「八方龍殺陣」 | (292.814, 432.000) | `right_fast` | 1285/0 | 6.050/5.983 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30016 | 65 神技「八方龍殺陣」 | (213.819, 432.000) | `right_fast` | 1097/0 | 2.315/0.201 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32978 | nonspell | (364.686, 394.594) | `left_fast` | 79/0 | -12.806/-12.806 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33412 | nonspell | (356.000, 432.000) | `left_fast` | 125/0 | 0.638/-3.907 | 5f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34535 | nonspell | (98.522, 415.828) | `right_fast` | 133/0 | -1.753/-7.192 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36833 | 69 回霊「夢想封印　侘」 | (376.000, 432.000) | `up_fast` | 519/0 | -1.939/-1.939 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37773 | 69 回霊「夢想封印　侘」 | (376.000, 432.000) | `down` | 650/0 | -4.265/-4.265 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41421 | 73 大結界「博麗弾幕結界」 | (140.335, 421.306) | `down_right_fast` | 1272/0 | 0.278/0.278 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 41899 | 73 大結界「博麗弾幕結界」 | (194.910, 432.000) | `left` | 1288/0 | -1.940/-1.940 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42859 | 73 大結界「博麗弾幕結界」 | (171.117, 420.428) | `down_left_fast` | 1326/0 | -1.266/-4.050 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 4467 | 4377 | 1340 | 0 | 2986 | 842 | 224.640 | 0.116 |
| 57 夢境「二重大結界」 | 4 | 778 | 768 | 110 | 0 | 633 | 164 | 240.183 | 0.195 |
| 61 | 0 | 497 | 490 | 140 | 0 | 334 | 107 | 189.522 | 0.123 |
| 65 神技「八方龍殺陣」 | 4 | 646 | 638 | 506 | 0 | 132 | 151 | 80.610 | 0.247 |
| 69 回霊「夢想封印　侘」 | 2 | 718 | 712 | 306 | 0 | 400 | 165 | 149.311 | 0.144 |
| 73 大結界「博麗弾幕結界」 | 3 | 714 | 701 | 293 | 0 | 391 | 164 | 159.223 | 0.099 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 3 exact same-epoch enemy-body overlaps; 3 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 24.837 ms median and 47.857 ms p95.
- The full enemy sensor produced 6147 snapshots; capture read time was `{'median': 36.063099978491664, 'p95': 60.312199988402426, 'max': 93.01260000211187}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 18.0}` frames, and 4 phase-counter discontinuities were excluded; 5828 decisions retained at least one robust-union body (maximum 36); 0 decisions contained latent contact-disabled geometry (maximum 0), and 0 contained bounded inactive-slot memory (maximum 0). 0 body samples retained observed world-motion estimates; world/internal speed and disagreement were `None` / `None` / `None`.
- The issue-time enemy guard retained 7820 observations, detected 1531 during-plan geometry changes, recertified 1531 decisions, and overrode 790 actions. Read/recertificate timing was `{'median': 2.294349978910759, 'p95': 4.963699990184978, 'max': 24.592100002337247}` / `{'median': 11.441599985118955, 'p95': 20.13509999960661, 'max': 29.937699990114197}` ms; 0 issue captures contained latent bodies (maximum 0), and 0 contained dormant bodies (maximum 0).
- The synchronous spell-owner guard retained 3352 observations (3331 contact enabled, 21 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 1275, '0x00587A90': 2077}`.
- The terminal-threat heuristic covered 7820 decisions with horizon counts `{'0': 43, '10': 7037, '32': 740}`; it reported 12 collision and 58 sub-safety-clearance warnings, and relaxed 115 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 43, '3': 96, '4': 1614, '5': 4649, '6': 1418}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 28, '3': 267, '4': 2513, '5': 4430, '6': 582}`.
- Adaptive delay supports were `{'2,3': 21, '2,3,4': 39, '2,3,4,5': 201, '2,3,4,5,6': 114, '3,4': 101, '3,4,5': 243, '3,4,5,6': 6214, '4,5': 2, '4,5,6': 882, '5,6': 1, '6': 2}`; 877 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 56/161.
- Robust viability supplied 7686 available policy queries (0 had new delay support outside the cached policy), constrained 4876 decisions, and exposed 2695 empty queried action sets. Recovery guidance was available/selected on 926/553 empty-kernel queries; distant-kernel guidance was available/selected on 1504/1450. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 7.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 40.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 96.0, 'p95': 295.0254226333724, 'max': 453.1136722722015}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1135, '1': 1022, '2': 1047, '3': 898, '4': 902, '5': 883, '6': 856, '7': 943}`.
- Global-horizon/local-prefix cross-tab covered 4632 decisions: 3 had a winning global state but unsafe selected prefix, 1451 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 50 selected actions were outside the reported winning set. 1130 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1593 unique policies with solve-time statistics `{'median': 204.28960002027452, 'p95': 398.66409997921437, 'max': 478.25629997532815}` and first-observed ages `{'median': 5.0, 'p95': 10.0, 'max': 1804.0}`. Policy status counts were `{'pending_future_epoch': 34, 'queryable': 7688, 'expired': 17}`; 53 robust-mode decisions had no query.
- Of 4319 unambiguous output transitions, 3661 (0.848) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 19, 'late_collision_after_positive_causal_margin': 2, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[4, 13, 0, 5, 10, 0, 0, 8, 12, 5, 0, 0, 0, 0, 0, 15, 0, 6, 0, 0, 0, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.356 during the 60 frames preceding a hit versus 0.122 outside those windows.
- Mean selected control-reserve deficit was 6.099 during the 60 frames preceding a hit versus 0.670 outside those windows.
- Soft recovery was selected on 0.056 of alive decisions in the 60-frame pre-hit windows versus 0.081 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
