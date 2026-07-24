# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_183707

## Scope And Integrity

- Valid practice scope: `2..46061` (7720 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 34, at `[1050, 1748, 2230, 2643, 4118, 8911, 9506, 10516, 11592, 12087, 12565, 13011, 13951, 16500, 20774, 21947, 22386, 22834, 23395, 28769, 30958, 31361, 31822, 32224, 32606, 35822, 36313, 39434, 40015, 40670, 43798, 44435, 44930, 45918]`.
- Hard no-Bomb verification: **PASS** across 7720 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1050-T1`. It occurred during a nonspell phase at player (8.000, 432.000), with 232 bullets and 0 lasers. The projectile model reported pipeline clearance -4.119.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 18 |
| `observed_bullet_overlap` | 11 |
| `sensor_gap_or_unmodeled_hazard` | 4 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 25
- `playfield_boundary`: 21
- `pool_density_over_1000`: 10
- `corridor_deadline_miss`: 8
- `action_lag_over_model`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1050 | nonspell | (8.000, 432.000) | `left` | 232/0 | -4.119/-11.168 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1748 | nonspell | (8.000, 364.316) | `stay` | 546/0 | -0.483/-1.029 | 7f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2230 | nonspell | (346.636, 432.000) | `up_left_fast` | 319/0 | 2.002/-1.822 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2643 | nonspell | (8.000, 432.000) | `up_left` | 541/0 | -1.984/-1.984 | 13f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4118 | nonspell | (8.000, 430.374) | `down_right` | 1045/0 | -6.777/-6.777 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8911 | nonspell | (149.131, 417.858) | `up_left_fast` | 390/0 | -0.327/-2.703 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9506 | nonspell | (155.206, 432.000) | `left_fast` | 150/0 | -20.781/-29.905 | 25f/32f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10516 | nonspell | (339.260, 432.000) | `left_fast` | 120/0 | -1.633/-11.775 | 0f/6f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11592 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 534/0 | -1.402/-1.402 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12087 | 57 夢境「二重大結界」 | (374.672, 432.000) | `left_fast` | 605/0 | -3.448/-3.448 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12565 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 585/0 | -0.715/-1.199 | 4f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13011 | 57 夢境「二重大結界」 | (22.745, 432.000) | `up_left_fast` | 594/0 | -2.116/-2.116 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13951 | 57 夢境「二重大結界」 | (100.432, 270.875) | `left_fast` | 579/0 | -0.029/-2.860 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 16500 | nonspell | (114.736, 432.000) | `right_fast` | 485/0 | -2.003/-2.003 | 6f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20774 | 61 散霊「夢想封印　寂」 | (90.924, 432.000) | `right_fast` | 216/0 | -15.421/-15.421 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21947 | nonspell | (24.971, 361.088) | `up_right_fast` | 243/0 | 2.913/0.376 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22386 | nonspell | (40.263, 432.000) | `up_right_fast` | 585/0 | -1.383/-27.586 | 19f/25f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22834 | nonspell | (376.000, 429.172) | `up_fast` | 519/0 | -2.708/-2.708 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23395 | nonspell | (73.374, 432.000) | `up_right` | 712/0 | -2.034/-2.034 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28769 | nonspell | (21.800, 418.583) | `right_fast` | 140/0 | 0.624/0.624 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30958 | 65 神技「八方龍殺陣」 | (85.538, 432.000) | `left_fast` | 1112/0 | 0.079/-1.131 | 0f/18f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31361 | 65 神技「八方龍殺陣」 | (188.635, 420.500) | `stay` | 1070/0 | 0.116/-14.757 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31822 | 65 神技「八方龍殺陣」 | (223.040, 360.005) | `stay` | 1061/0 | -1.129/-11.915 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32224 | 65 神技「八方龍殺陣」 | (121.742, 360.201) | `down_right` | 1036/0 | -0.154/-31.646 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32606 | 65 神技「八方龍殺陣」 | (282.738, 393.958) | `down_left_fast` | 1089/0 | -0.366/-8.066 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35822 | nonspell | (40.971, 432.000) | `down_right_fast` | 107/0 | 2.070/-14.873 | 17f/22f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36313 | nonspell | (279.343, 432.000) | `right_fast` | 139/0 | 5.952/-6.244 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39434 | 69 回霊「夢想封印　侘」 | (8.071, 432.000) | `up_fast` | 557/0 | -0.576/-2.053 | 3f/20f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40015 | 69 回霊「夢想封印　侘」 | (353.090, 339.602) | `down_left_fast` | 722/0 | -6.068/-6.068 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40670 | 69 回霊「夢想封印　侘」 | (376.000, 376.887) | `up_right_fast` | 741/0 | 4.197/4.197 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43798 | 73 大結界「博麗弾幕結界」 | (345.603, 358.843) | `down_left_fast` | 1243/0 | -0.158/-0.158 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44435 | 73 大結界「博麗弾幕結界」 | (30.300, 357.272) | `down_fast` | 1289/0 | -2.269/-2.269 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44930 | 73 大結界「博麗弾幕結界」 | (198.136, 340.187) | `up_left` | 1342/0 | -1.820/-1.820 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45918 | 73 大結界「博麗弾幕結界」 | (103.154, 296.877) | `up_right_fast` | 1360/0 | -2.307/-2.307 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 16 | 4290 | 4194 | 1948 | 0 | 2200 | 953 | 166.100 | 0.197 |
| 57 夢境「二重大結界」 | 5 | 786 | 781 | 141 | 0 | 624 | 163 | 246.153 | 0.213 |
| 61 散霊「夢想封印　寂」 | 1 | 649 | 645 | 223 | 0 | 403 | 154 | 186.470 | 0.189 |
| 65 神技「八方龍殺陣」 | 5 | 605 | 597 | 489 | 0 | 107 | 156 | 66.565 | 0.356 |
| 69 回霊「夢想封印　侘」 | 3 | 699 | 694 | 344 | 0 | 345 | 168 | 140.308 | 0.111 |
| 73 大結界「博麗弾幕結界」 | 4 | 691 | 678 | 250 | 0 | 423 | 162 | 162.103 | 0.059 |

## Interpretation

- Retained witnesses classify 11 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 31.212 ms median and 56.315 ms p95.
- The full enemy sensor produced 6579 snapshots; capture read time was `{'median': 37.10999997565523, 'p95': 64.9730000004638, 'max': 99.11650000140071}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 16.0}` frames, and 5 phase-counter discontinuities were excluded; 7449 decisions retained at least one robust-union body (maximum 58); 1307 decisions contained latent contact-disabled geometry (maximum 58), and 3913 contained bounded inactive-slot memory (maximum 52). 592 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.4811782836914062, 'p95': 4.3669891357421875, 'max': 25.397542681012833}` / `{'median': 2.496213912963867, 'p95': 3.979027032852173, 'max': 120.18557739257812}` / `{'median': 0.014828711748123169, 'p95': 4.364686965942383, 'max': 120.18557739257812}`.
- The issue-time enemy guard retained 7720 observations, detected 3566 during-plan geometry changes, recertified 3566 decisions, and overrode 1826 actions. Read/recertificate timing was `{'median': 2.30534998991061, 'p95': 4.920700012007728, 'max': 25.547600002028048}` / `{'median': 12.144499996793456, 'p95': 21.507400000700727, 'max': 35.01870000036433}` ms; 1311 issue captures contained latent bodies (maximum 58), and 3931 contained dormant bodies (maximum 52).
- The synchronous spell-owner guard retained 3429 observations (3412 contact enabled, 17 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 1435, '0x00597600': 1994}`.
- The terminal-threat heuristic covered 7720 decisions with horizon counts `{'0': 43, '10': 6977, '32': 700}`; it reported 9 collision and 56 sub-safety-clearance warnings, and relaxed 92 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 42, '3': 81, '4': 584, '5': 2592, '6': 4421}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 48, '3': 157, '4': 449, '5': 4676, '6': 2390}`.
- Adaptive delay supports were `{'2,3': 46, '2,3,4,5': 120, '2,3,4,5,6': 179, '3,4,5': 80, '3,4,5,6': 5471, '4,5,6': 1824}`; 1974 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 106/206.
- Robust viability supplied 7589 available policy queries (0 had new delay support outside the cached policy), constrained 4102 decisions, and exposed 3395 empty queried action sets. Recovery guidance was available/selected on 919/598 empty-kernel queries; distant-kernel guidance was available/selected on 2070/1979. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 24.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 124.96399481450646, 'p95': 329.84845004941286, 'max': 505.9644256269407}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1153, '1': 1118, '2': 940, '3': 909, '4': 893, '5': 889, '6': 876, '7': 811}`.
- Global-horizon/local-prefix cross-tab covered 2691 decisions: 2 had a winning global state but unsafe selected prefix, 868 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 29 selected actions were outside the reported winning set. 2368 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1756 unique policies with solve-time statistics `{'median': 167.0088500250131, 'p95': 382.8221000148915, 'max': 522.2426000109408}` and first-observed ages `{'median': 5.0, 'p95': 10.0, 'max': 1802.0}`. Policy status counts were `{'pending_future_epoch': 35, 'queryable': 7592, 'expired': 17}`; 55 robust-mode decisions had no query.
- Of 4597 unambiguous output transitions, 3891 (0.846) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 34}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 23 hit windows with a positive warning lead; those leads were `[5, 7, 6, 18, 6, 6, 32, 6, 5, 4, 7, 5, 9, 11, 7, 0, 25, 5, 5, 0, 18, 5, 0, 0, 0, 22, 0, 20, 0, 0, 0, 6, 0, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.497 during the 60 frames preceding a hit versus 0.161 outside those windows.
- Mean selected control-reserve deficit was 6.323 during the 60 frames preceding a hit versus 1.144 outside those windows.
- Soft recovery was selected on 0.069 of alive decisions in the 60-frame pre-hit windows versus 0.082 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
