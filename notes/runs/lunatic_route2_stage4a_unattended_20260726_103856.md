# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260726_103856

## Experiment Disposition

- **Rejected live change:** the 50-ms repeated-manager-frame input guard.
- This was the latest live Boolean/local controller with candidate
  verification kept shadow-only; it was not a weakened-planner ablation.
- The guard fired 2,780 times in 7,925 decisions although only 72 actual wall
  pulses occurred. Its epoch invalidations reduced available viability
  queries from the pre-guard run's 9,073 to 691. Live behavior was therefore
  rolled back to `1ce5b44`; CE-0120 remains unresolved.
- The original supervisor accepted the complete physical run and terminated
  the game, then failed during artifact generation on an explicit null enemy
  snapshot. The repaired parser generated this note without changing the
  original failed postprocessing provenance.
- Compact causal audit:
  `artifacts/viability_audit/stage4a_20260726_103856_frozen_guard_rejection.json`.

## Scope And Integrity

- Valid practice scope: `2..46325` (7925 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 64, at `[895, 1870, 2658, 4016, 4351, 8833, 9361, 9895, 10354, 10896, 11651, 12024, 12605, 12974, 13527, 13929, 16999, 17567, 18200, 18874, 19466, 19935, 20328, 20649, 21059, 21870, 22337, 22789, 23269, 23610, 27630, 28440, 28789, 29109, 29478, 30081, 30793, 31196, 31499, 31879, 32252, 32603, 32984, 35236, 35577, 35903, 36404, 36708, 37162, 37654, 38000, 38755, 39249, 39566, 40259, 40592, 41085, 43769, 44067, 44467, 44825, 45136, 45778, 46129]`.
- Hard no-Bomb verification: **PASS** across 7925 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F895-T1`. It occurred during a nonspell phase at player (226.780, 432.000), with 151 bullets and 0 lasers. The projectile model reported pipeline clearance -0.683.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 29 |
| `observed_bullet_overlap` | 19 |
| `sensor_gap_or_unmodeled_hazard` | 16 |

Contributing factors:

- `action_lag_over_model`: 46
- `playfield_boundary`: 26
- `fast_mode`: 12
- `pool_density_over_1000`: 11
- `corridor_deadline_miss`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 895 | nonspell | (226.780, 432.000) | `down_left_fast` | 151/0 | -0.683/-1.558 | 4f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 1870 | nonspell | (8.000, 411.866) | `stay` | 295/0 | -1.488/-1.488 | 6f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 2658 | nonspell | (252.999, 430.932) | `down_right_fast` | 125/0 | -1.779/-1.779 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 4016 | nonspell | (376.000, 322.220) | `stay` | 735/0 | 0.058/0.058 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 4351 | nonspell | (52.678, 432.000) | `stay` | 883/0 | -1.928/-1.928 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 8833 | nonspell | (263.013, 432.000) | `stay` | 757/0 | -22.305/-22.305 | 25f/31f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 9361 | nonspell | (96.430, 411.118) | `stay` | 553/0 | -16.286/-16.286 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 9895 | nonspell | (8.000, 419.060) | `stay` | 351/0 | -11.103/-11.103 | 0f/11f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 10354 | nonspell | (65.136, 432.000) | `left_fast` | 521/0 | -1.100/-1.100 | 0f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10896 | nonspell | (136.862, 418.327) | `stay` | 289/0 | -0.674/-10.125 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 11651 | 57 夢境「二重大結界」 | (8.000, 432.000) | `stay` | 585/0 | -0.967/-0.967 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12024 | 57 夢境「二重大結界」 | (30.851, 432.000) | `stay` | 593/0 | 0.250/0.250 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 12605 | 57 夢境「二重大結界」 | (8.000, 428.971) | `stay` | 609/0 | -0.315/-1.087 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 12974 | 57 夢境「二重大結界」 | (299.756, 373.574) | `stay` | 580/0 | -1.932/-1.932 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 13527 | 57 夢境「二重大結界」 | (376.000, 432.000) | `stay` | 585/0 | -1.896/-1.896 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13929 | 57 夢境「二重大結界」 | (287.256, 375.431) | `stay` | 592/0 | -1.118/-1.731 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 16999 | nonspell | (376.000, 392.461) | `stay` | 424/0 | -2.044/-2.044 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 17567 | nonspell | (268.857, 432.000) | `stay` | 182/0 | -1.440/-1.440 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 18200 | nonspell | (170.853, 425.771) | `up_left_fast` | 452/0 | 1.461/-1.614 | 4f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 18874 | 61 散霊「夢想封印　寂」 | (175.585, 407.454) | `stay` | 618/0 | 5.572/5.572 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 19466 | 61 散霊「夢想封印　寂」 | (300.109, 415.177) | `stay` | 569/0 | 13.577/1.177 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 19935 | 61 散霊「夢想封印　寂」 | (18.470, 426.302) | `stay` | 213/0 | -0.202/-1.886 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 20328 | 61 散霊「夢想封印　寂」 | (321.503, 428.206) | `left_fast` | 189/0 | -9.634/-9.634 | 5f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 20649 | 61 散霊「夢想封印　寂」 | (183.355, 398.482) | `stay` | 720/0 | -3.039/-3.039 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 21059 | 61 散霊「夢想封印　寂」 | (146.419, 427.192) | `stay` | 593/0 | 8.856/-3.005 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 21870 | nonspell | (187.278, 420.348) | `stay` | 389/0 | -3.152/-3.152 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 22337 | nonspell | (163.886, 425.521) | `stay` | 298/0 | -4.201/-4.201 | 5f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 22789 | nonspell | (317.272, 373.885) | `up_fast` | 771/0 | -1.411/-4.485 | 5f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 23269 | nonspell | (11.613, 401.858) | `stay` | 581/0 | 0.609/-4.128 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 23610 | nonspell | (244.758, 432.000) | `stay` | 468/0 | -1.742/-1.742 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 27630 | nonspell | (192.000, 390.900) | `stay` | 174/0 | 2.542/2.542 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 28440 | nonspell | (361.377, 415.657) | `stay` | 187/0 | -1.467/-1.467 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 28789 | nonspell | (205.641, 432.000) | `up_fast` | 139/0 | -2.614/-2.614 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 29109 | nonspell | (144.232, 432.000) | `left_fast` | 138/0 | -2.880/-2.880 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 29478 | nonspell | (344.770, 416.442) | `stay` | 71/0 | 1.055/-2.623 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 30081 | nonspell | (68.740, 432.000) | `stay` | 144/0 | -1.564/-1.564 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 30793 | 65 神技「八方龍殺陣」 | (213.626, 412.526) | `stay` | 757/0 | -3.882/-3.882 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 31196 | 65 神技「八方龍殺陣」 | (132.308, 432.000) | `stay` | 1167/0 | 2.368/-0.372 | 0f/16f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 31499 | 65 神技「八方龍殺陣」 | (181.320, 423.031) | `stay` | 1139/0 | 2.892/-4.276 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 31879 | 65 神技「八方龍殺陣」 | (153.753, 424.959) | `stay` | 1182/0 | 1.623/-0.466 | 6f/6f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 32252 | 65 神技「八方龍殺陣」 | (172.747, 423.868) | `stay` | 1123/0 | -2.526/-2.526 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 32603 | 65 神技「八方龍殺陣」 | (139.298, 411.810) | `stay` | 1154/0 | -1.541/-1.541 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 32984 | 65 神技「八方龍殺陣」 | (185.441, 398.242) | `stay` | 1316/0 | 2.019/0.525 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35236 | nonspell | (192.000, 384.000) | `right_fast` | 125/0 | 0.604/-2.309 | 5f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 35577 | nonspell | (132.165, 362.905) | `stay` | 129/0 | 7.167/-0.556 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 35903 | nonspell | (193.846, 383.073) | `stay` | 118/0 | -1.834/-1.834 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 36404 | nonspell | (84.537, 423.314) | `stay` | 132/0 | 1.878/-8.355 | 0f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36708 | nonspell | (189.705, 419.516) | `stay` | 101/0 | -2.787/-2.787 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 37162 | nonspell | (24.000, 410.715) | `stay` | 173/0 | 0.688/0.688 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 37654 | nonspell | (246.070, 432.000) | `stay` | 171/0 | 5.959/-4.491 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 38000 | nonspell | (109.433, 429.172) | `stay` | 125/0 | 0.992/0.415 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 38755 | 69 回霊「夢想封印　侘」 | (376.000, 255.198) | `stay` | 403/0 | -8.395/-8.395 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 39249 | 69 回霊「夢想封印　侘」 | (8.000, 421.817) | `down_left` | 530/0 | -0.964/-0.964 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39566 | 69 回霊「夢想封印　侘」 | (233.819, 418.972) | `stay` | 339/0 | -1.983/-3.624 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 40259 | 69 回霊「夢想封印　侘」 | (333.444, 401.172) | `stay` | 606/0 | -3.126/-3.126 | 5f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 40592 | 69 回霊「夢想封印　侘」 | (269.951, 402.403) | `stay` | 434/0 | -6.198/-6.198 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 41085 | 69 回霊「夢想封印　侘」 | (112.295, 382.364) | `down_left_fast` | 652/0 | 1.626/1.626 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 43769 | 73 大結界「博麗弾幕結界」 | (217.013, 383.142) | `stay` | 1000/0 | -1.415/-1.415 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 44067 | 73 大結界「博麗弾幕結界」 | (142.800, 408.000) | `stay` | 756/0 | -1.605/-1.605 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 44467 | 73 大結界「博麗弾幕結界」 | (133.037, 394.089) | `stay` | 1187/0 | -1.314/-2.685 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44825 | 73 大結界「博麗弾幕結界」 | (259.449, 417.819) | `right_fast` | 1026/0 | -3.804/-3.804 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45136 | 73 大結界「博麗弾幕結界」 | (202.889, 432.000) | `up_fast` | 880/0 | 1.246/-2.036 | 6f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 45778 | 73 大結界「博麗弾幕結界」 | (302.360, 415.372) | `stay` | 1361/0 | -3.309/-3.309 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 46129 | 73 大結界「博麗弾幕結界」 | (170.575, 389.120) | `stay` | 1040/0 | -2.812/-2.812 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 32 | 4415 | 333 | 114 | 0 | 213 | 278 | 119.228 | 0.172 |
| 57 夢境「二重大結界」 | 6 | 754 | 54 | 8 | 0 | 43 | 24 | 227.284 | 0.426 |
| 61 散霊「夢想封印　寂」 | 6 | 702 | 37 | 20 | 0 | 17 | 47 | 103.126 | 0.182 |
| 65 神技「八方龍殺陣」 | 7 | 583 | 82 | 63 | 0 | 19 | 92 | 61.490 | 0.168 |
| 69 回霊「夢想封印　侘」 | 6 | 721 | 72 | 25 | 0 | 43 | 57 | 129.918 | 0.227 |
| 73 大結界「博麗弾幕結界」 | 7 | 750 | 113 | 67 | 0 | 46 | 61 | 141.056 | 0.065 |

## Interpretation

- Retained witnesses classify 19 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 30.254 ms median and 49.239 ms p95.
- The full enemy sensor produced 4237 snapshots; capture read time was `{'median': 33.585499972105026, 'p95': 57.36659996910021, 'max': 99.6453000116162}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 15.0}` frames, and 2 phase-counter discontinuities were excluded; 4765 decisions retained at least one robust-union body (maximum 53); 783 decisions contained latent contact-disabled geometry (maximum 53), and 935 contained bounded inactive-slot memory (maximum 39). 386 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.57904052734375, 'p95': 4.382804870605469, 'max': 14.813071250915527}` / `{'median': 2.701191544532776, 'p95': 3.9999210834503174, 'max': 91.48129272460938}` / `{'median': 1.1534175428096205e-05, 'p95': 2.6335325241088867, 'max': 91.48129272460938}`.
- The issue-time enemy guard retained 7925 observations, detected 4024 during-plan geometry changes, recertified 4024 decisions, and overrode 899 actions. Read/recertificate timing was `{'median': 2.57210002746433, 'p95': 5.4981999564915895, 'max': 26.3044000021182}` / `{'median': 6.540300004417077, 'p95': 14.707599999383092, 'max': 32.378099975176156}` ms; 1268 issue captures contained latent bodies (maximum 53), and 1402 contained dormant bodies (maximum 39).
- The synchronous spell-owner guard retained 6273 observations (6240 contact enabled, 33 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 6273}`.
- The terminal-threat heuristic covered 7925 decisions with horizon counts `{'0': 269, '10': 7616, '32': 40}`; it reported 3 collision and 9 sub-safety-clearance warnings, and relaxed 13 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 251, '3': 3814, '4': 1684, '5': 1489, '6': 687}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 263, '3': 4100, '4': 1754, '5': 1168, '6': 640}`.
- Adaptive delay supports were `{'2,3': 3036, '2,3,4': 74, '2,3,4,5': 11, '3,4': 1230, '3,4,5': 97, '3,4,5,6': 152, '4,5': 405, '4,5,6': 1664, '5,6': 940, '6': 316}`; 944 decisions changed their nominal first action, 29 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 4/4.
- Robust viability supplied 691 available policy queries (0 had new delay support outside the cached policy), constrained 381 decisions, and exposed 297 empty queried action sets. Recovery guidance was available/selected on 91/54 empty-kernel queries; distant-kernel guidance was available/selected on 148/139. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 5.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 25.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 81.58431221748455, 'p95': 298.9046670763105, 'max': 389.29680193908604}`, and `{'median': 0.0, 'p95': 15.135117530822754, 'max': 35.0599365234375}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 130, '1': 101, '2': 93, '3': 82, '4': 79, '5': 73, '6': 63, '7': 70}`.
- Global-horizon/local-prefix cross-tab covered 230 decisions: 0 had a winning global state but unsafe selected prefix, 84 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 2 selected actions were outside the reported winning set. 117 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 559 unique policies with solve-time statistics `{'median': 118.59470000490546, 'p95': 424.64809998637065, 'max': 680.4480000282638}` and first-observed ages `{'median': -4.0, 'p95': 8.0, 'max': 28.0}`. Policy status counts were `{'pending_future_epoch': 623, 'queryable': 829, 'expired': 1}`; 762 robust-mode decisions had no query.
- Of 3430 unambiguous output transitions, 2075 (0.605) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 18, 'late_collision_after_positive_causal_margin': 27, 'unresolved_planner_failure': 12, 'global_viability_kernel_exhausted_before_hit': 5, 'missing_pre_hit_alive_decision': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[4, 6, 0, 0, 0, 31, 6, 11, 16, 0, 5, 0, 0, 0, 4, 0, 0, 0, 4, 0, 0, 0, 9, 0, 0, 0, 5, 5, 0, 0, 0, 0, 4, 0, 0, 0, 0, 16, 0, 6, 0, 0, 0, 5, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 6, 0, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.324 during the 60 frames preceding a hit versus 0.153 outside those windows.
- Mean selected control-reserve deficit was 0.777 during the 60 frames preceding a hit versus 0.666 outside those windows.
- Soft recovery was selected on 0.013 of alive decisions in the 60-frame pre-hit windows versus 0.006 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
