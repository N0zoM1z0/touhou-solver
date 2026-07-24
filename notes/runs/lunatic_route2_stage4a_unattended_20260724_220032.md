# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_220032

## Scope And Integrity

- Valid practice scope: `2..46090` (7255 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 40, at `[673, 1210, 1875, 2311, 2756, 4024, 4454, 8868, 9354, 9801, 10296, 11734, 12132, 12737, 13181, 13777, 19628, 22001, 22396, 23285, 28960, 30088, 31230, 31858, 32173, 32866, 35663, 35974, 36493, 36968, 37724, 39537, 40063, 40659, 43825, 44356, 44823, 45128, 45589, 45938]`.
- Hard no-Bomb verification: **PASS** across 7255 decisions; mask/flag/action violations are all empty.

This is a completed but **rejected algorithm experiment**, not an acceptance
baseline. Full-horizon 8-pixel refinement reduced empty queries but increased
solve median/p95 from `170.77/380.59` to `532.04/1174.21` ms, cut delivered
unique policies from 1,728 to 630, and raised expired decisions from 34 to
178. CE-0102 and
`notes/DELIVERY_AWARE_STRATEGY_REASSESSMENT_20260724.md` record the rollback.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F673-T1`. It occurred during a nonspell phase at player (376.000, 397.311), with 177 bullets and 0 lasers. The projectile model reported pipeline clearance -2.037.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 20 |
| `observed_bullet_overlap` | 14 |
| `sensor_gap_or_unmodeled_hazard` | 5 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 29
- `playfield_boundary`: 28
- `corridor_deadline_miss`: 18
- `action_lag_over_model`: 11
- `pool_density_over_1000`: 10

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 673 | nonspell | (376.000, 397.311) | `left_fast` | 177/0 | -2.037/-2.037 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1210 | nonspell | (376.000, 392.201) | `up_fast` | 300/0 | -1.293/-1.583 | 7f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1875 | nonspell | (376.000, 345.628) | `down_left_fast` | 174/0 | -4.550/-4.550 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2311 | nonspell | (356.201, 432.000) | `up_right_fast` | 229/0 | -2.147/-23.856 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2756 | nonspell | (13.800, 432.000) | `left_fast` | 466/0 | -4.008/-26.671 | 30f/34f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4024 | nonspell | (40.485, 432.000) | `right_fast` | 924/0 | -4.122/-4.122 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4454 | nonspell | (376.000, 385.920) | `up_right` | 1051/0 | 0.393/0.393 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8868 | nonspell | (81.214, 432.000) | `down_right` | 602/0 | -3.766/-3.766 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9354 | nonspell | (8.000, 431.285) | `left_fast` | 562/0 | -1.913/-7.052 | 10f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9801 | nonspell | (307.566, 432.000) | `right_fast` | 755/0 | -15.540/-15.540 | 16f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10296 | nonspell | (376.000, 432.000) | `right_fast` | 740/0 | -18.797/-18.797 | 0f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11734 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_fast` | 580/0 | -2.057/-2.057 | 0f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12132 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 588/0 | 1.298/-1.936 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12737 | 57 夢境「二重大結界」 | (106.141, 432.000) | `up_right_fast` | 609/0 | -2.102/-2.102 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13181 | 57 夢境「二重大結界」 | (8.000, 432.000) | `stay` | 605/0 | 0.530/-1.103 | 5f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13777 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 606/0 | -0.636/-0.636 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19628 | 61 散霊「夢想封印　寂」 | (317.900, 432.000) | `right_fast` | 306/0 | 0.893/0.893 | 0f/5f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 22001 | nonspell | (376.000, 432.000) | `up_fast` | 104/0 | 0.967/0.967 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22396 | nonspell | (376.000, 432.000) | `up_fast` | 624/0 | -2.815/-10.592 | 0f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23285 | nonspell | (367.868, 309.011) | `down_left` | 836/0 | -2.014/-4.648 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28960 | nonspell | (367.515, 423.515) | `up_fast` | 90/0 | 2.525/-2.671 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30088 | nonspell | (28.700, 419.912) | `right` | 95/0 | -2.594/-2.594 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31230 | 65 神技「八方龍殺陣」 | (275.581, 432.000) | `down_fast` | 1251/0 | -1.742/-14.146 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 31858 | 65 神技「八方龍殺陣」 | (178.170, 410.858) | `down_right_fast` | 1284/0 | -0.181/-1.805 | 7f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32173 | 65 神技「八方龍殺陣」 | (328.387, 432.000) | `stay` | 1026/0 | -2.075/-21.265 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32866 | 65 神技「八方龍殺陣」 | (267.109, 416.689) | `right_fast` | 1253/0 | 1.420/-2.114 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35663 | nonspell | (240.846, 432.000) | `down_left_fast` | 72/0 | -2.680/-14.521 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35974 | nonspell | (262.954, 432.000) | `left_fast` | 106/0 | -3.720/-3.720 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 36493 | nonspell | (202.375, 432.000) | `down_fast` | 64/0 | -18.544/-18.544 | 7f/15f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 36968 | nonspell | (27.799, 412.201) | `right_fast` | 62/0 | 20.710/2.244 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37724 | nonspell | (373.142, 430.853) | `stay` | 143/0 | -2.430/-9.938 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39537 | 69 回霊「夢想封印　侘」 | (339.200, 353.622) | `up_fast` | 616/0 | -4.004/-4.004 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40063 | 69 回霊「夢想封印　侘」 | (8.000, 260.477) | `stay` | 529/0 | -7.928/-7.928 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40659 | 69 回霊「夢想封印　侘」 | (104.931, 432.000) | `up_left` | 733/0 | -5.798/-5.798 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43825 | 73 大結界「博麗弾幕結界」 | (281.943, 308.244) | `down_left_fast` | 1239/0 | -2.911/-2.911 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44356 | 73 大結界「博麗弾幕結界」 | (69.708, 383.230) | `up_fast` | 1273/0 | 2.040/-2.954 | 7f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44823 | 73 大結界「博麗弾幕結界」 | (268.200, 389.730) | `stay` | 1323/0 | -1.671/-1.671 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45128 | 73 大結界「博麗弾幕結界」 | (8.000, 407.122) | `down_fast` | 864/0 | 0.922/0.922 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45589 | 73 大結界「博麗弾幕結界」 | (352.163, 330.082) | `down_fast` | 1309/0 | -1.919/-2.018 | 7f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45938 | 73 大結界「博麗弾幕結界」 | (302.601, 358.730) | `stay` | 1040/0 | -3.815/-3.815 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 21 | 3987 | 3750 | 1392 | 0 | 2282 | 341 | 553.886 | 0.193 |
| 57 夢境「二重大結界」 | 5 | 757 | 721 | 81 | 0 | 612 | 63 | 229.911 | 0.303 |
| 61 散霊「夢想封印　寂」 | 1 | 600 | 576 | 90 | 0 | 467 | 46 | 782.550 | 0.183 |
| 65 神技「八方龍殺陣」 | 4 | 539 | 511 | 385 | 0 | 109 | 43 | 556.226 | 0.245 |
| 69 回霊「夢想封印　侘」 | 3 | 666 | 633 | 291 | 0 | 334 | 59 | 636.783 | 0.183 |
| 73 大結界「博麗弾幕結界」 | 6 | 706 | 691 | 195 | 0 | 481 | 78 | 307.198 | 0.028 |

## Interpretation

- Retained witnesses classify 14 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 7.000 frames p95. The local plan took 31.060 ms median and 63.111 ms p95.
- The full enemy sensor produced 6300 snapshots; capture read time was `{'median': 39.640099988901056, 'p95': 75.49090002430603, 'max': 189.66240002191626}`, snapshot age was `{'median': 6.0, 'p95': 10.0, 'max': 17.0}` frames, and 5 phase-counter discontinuities were excluded; 7001 decisions retained at least one robust-union body (maximum 57); 1253 decisions contained latent contact-disabled geometry (maximum 57), and 3329 contained bounded inactive-slot memory (maximum 51). 631 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.5983047485351562, 'p95': 3.9915771484375, 'max': 8.95136242821103}` / `{'median': 2.6335296630859375, 'p95': 3.8987743854522705, 'max': 144.8713836669922}` / `{'median': 0.010132193565368652, 'p95': 1.2312797546386718, 'max': 144.8713836669922}`.
- The issue-time enemy guard retained 7255 observations, detected 2397 during-plan geometry changes, recertified 2397 decisions, and overrode 1190 actions. Read/recertificate timing was `{'median': 2.4919999996200204, 'p95': 5.6025999947451055, 'max': 29.81119998730719}` / `{'median': 12.950400006957352, 'p95': 25.587800017092377, 'max': 56.27400000230409}` ms; 1255 issue captures contained latent bodies (maximum 57), and 3341 contained dormant bodies (maximum 51).
- The synchronous spell-owner guard retained 3268 observations (3252 contact enabled, 16 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3268}`.
- The terminal-threat heuristic covered 7255 decisions with horizon counts `{'0': 40, '10': 6052, '32': 1163}`; it reported 42 collision and 254 sub-safety-clearance warnings, and relaxed 163 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 5, '3': 72, '4': 510, '5': 626, '6': 6042}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 33, '3': 156, '4': 464, '5': 1908, '6': 4694}`.
- Adaptive delay supports were `{'2,3': 15, '2,3,4': 176, '2,3,4,5': 21, '2,3,4,5,6': 229, '3,4': 16, '3,4,5': 75, '3,4,5,6': 4832, '4,5': 13, '4,5,6': 1871, '5,6': 2, '6': 5}`; 1321 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 128/142.
- Robust viability supplied 6882 available policy queries (0 had new delay support outside the cached policy), constrained 4285 decisions, and exposed 2434 empty queried action sets. Recovery guidance was available/selected on 847/621 empty-kernel queries; distant-kernel guidance was available/selected on 1463/1444. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 9.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 56.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 82.365041127896, 'p95': 257.9922479455536, 'max': 402.8697059844535}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 915, '1': 901, '2': 867, '3': 877, '4': 828, '5': 872, '6': 808, '7': 814}`.
- Global-horizon/local-prefix cross-tab covered 2822 decisions: 12 had a winning global state but unsafe selected prefix, 757 had a losing global state but safe short prefix, 8 selected globally certified actions contradicted the fresh local prefix checker, and 51 selected actions were outside the reported winning set. 1413 newer issue-time hazard versions and 15 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 630 unique policies with solve-time statistics `{'median': 532.0405499951448, 'p95': 1174.2137999972329, 'max': 1605.936300009489}` and first-observed ages `{'median': 5.0, 'p95': 23.0, 'max': 1777.0}`. Policy status counts were `{'pending_future_epoch': 141, 'queryable': 6837, 'expired': 178}`; 274 robust-mode decisions had no query.
- Of 4218 unambiguous output transitions, 3583 (0.849) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 32, 'robust_action_set_exhausted_before_hit': 5, 'late_collision_after_positive_causal_margin': 2, 'missing_pre_hit_alive_decision': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 28 hit windows with a positive warning lead; those leads were `[0, 12, 6, 6, 34, 4, 0, 13, 15, 16, 16, 4, 8, 4, 11, 6, 5, 0, 11, 7, 11, 0, 0, 7, 6, 0, 6, 0, 15, 0, 0, 7, 5, 6, 0, 7, 7, 0, 7, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.404 during the 60 frames preceding a hit versus 0.170 outside those windows.
- Mean selected control-reserve deficit was 5.519 during the 60 frames preceding a hit versus 0.982 outside those windows.
- Soft recovery was selected on 0.092 of alive decisions in the 60-frame pre-hit windows versus 0.082 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Do not tune this live strategy further. Keep fine refinement and fused
survival labels shadow/offline, restore the coarse Boolean live path, and
redesign around issue-time validity and bounded policy service.
