# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_112918

## Scope And Integrity

- Valid practice scope: `2..45235` (11105 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 22, at `[1947, 2598, 3797, 7284, 8280, 12532, 12979, 23407, 25485, 28506, 30565, 30978, 31588, 32239, 36151, 36998, 37411, 40869, 41790, 42832, 43299, 43873]`.
- Hard no-Bomb verification: **PASS** across 11105 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1947-T1`. It occurred during a nonspell phase at player (370.697, 281.467), with 421 bullets and 0 lasers. The projectile model reported pipeline clearance 7.902.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 8 |
| `sensor_gap_or_unmodeled_hazard` | 3 |

Contributing factors:

- `fast_mode`: 16
- `playfield_boundary`: 15
- `pool_density_over_1000`: 7
- `action_lag_over_model`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1947 | nonspell | (370.697, 281.467) | `down_right_fast` | 421/0 | 7.902/1.899 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2598 | nonspell | (160.385, 420.485) | `stay` | 343/0 | 27.386/12.000 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 3797 | nonspell | (376.000, 432.000) | `down_right_fast` | 474/0 | -4.106/-4.106 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 7284 | nonspell | (24.971, 374.514) | `up_fast` | 572/0 | 11.487/-2.708 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 8280 | nonspell | (308.569, 432.000) | `down_left` | 523/0 | -4.293/-4.293 | 0f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12532 | nonspell | (373.700, 430.458) | `left` | 270/0 | -3.273/-3.273 | 0f/24f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12979 | nonspell | (376.000, 432.000) | `up_left` | 280/0 | -3.301/-3.301 | 3f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 23407 | 103 幻波「赤眼催眠(マインドブローイング)」 | (190.039, 432.000) | `left_fast` | 1376/0 | -2.678/-2.678 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 25485 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right` | 1110/0 | -2.893/-2.893 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28506 | nonspell | (185.591, 432.000) | `down_right_fast` | 1081/0 | -2.077/-2.077 | 0f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 30565 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (178.974, 414.181) | `up_right_fast` | 984/0 | -4.885/-4.902 | 16f/46f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30978 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (175.410, 423.515) | `up_left_fast` | 994/0 | -5.294/-6.544 | 11f/61f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31588 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (142.707, 432.000) | `right_fast` | 1010/0 | -6.446/-6.446 | 9f/20f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32239 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (256.957, 432.000) | `up_right_fast` | 1008/0 | -6.918/-8.178 | 10f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36151 | nonspell | (8.000, 417.100) | `up_right_fast` | 448/0 | -2.387/-2.387 | 0f/14f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 36998 | nonspell | (24.762, 432.000) | `up` | 459/0 | -1.697/-1.697 | 0f/12f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 37411 | nonspell | (8.000, 432.000) | `up_fast` | 434/0 | -4.132/-4.132 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 40869 | 111 懶惰「生神停止(マインドストッパー)」 | (177.524, 191.280) | `up_left_fast` | 357/0 | -2.270/-2.466 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41790 | 111 懶惰「生神停止(マインドストッパー)」 | (190.768, 16.000) | `right_fast` | 502/0 | -3.022/-3.022 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42832 | 115 散符「真実の月(インビジブルフルムーン)」 | (261.376, 429.172) | `up_right_fast` | 1172/0 | -2.978/-2.978 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43299 | 115 散符「真実の月(インビジブルフルムーン)」 | (217.330, 429.172) | `up_left_fast` | 1058/0 | 0.032/0.032 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43873 | 115 散符「真実の月(インビジブルフルムーン)」 | (176.259, 428.000) | `up_fast` | 901/0 | -0.753/-0.879 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 11 | 7095 | 120 | 37 | 0 | 118 | 9 | 1130.484 | 0.435 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 893 | 520 | 427 | 0 | 0 | 71 | 102.781 | 0.458 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 4 | 983 | 977 | 775 | 0 | 0 | 226 | 77.689 | 0.304 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1049 | 1042 | 553 | 0 | 0 | 180 | 76.398 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 1085 | 1078 | 679 | 0 | 0 | 187 | 67.862 | 0.381 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.614 ms median and 32.429 ms p95.
- The full enemy sensor produced 6204 snapshots; capture read time was `{'median': 5.163649999303743, 'p95': 27.865200012456626, 'max': 777.4096000066493}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 112.0}` frames, and 18 phase-counter discontinuities were excluded; 10411 decisions retained at least one robust-union body (maximum 42); 7954 decisions contained latent contact-disabled geometry (maximum 41), and 3902 contained bounded inactive-slot memory (maximum 37). 420 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.799285888671875, 'p95': 3.231964111328125, 'max': 8.42852783203125}` / `{'median': 0.7992914021015167, 'p95': 3.0331568717956543, 'max': 4.70754861831665}` / `{'median': 0.0, 'p95': 1.0000114440917969, 'max': 6.682154417037964}`.
- The issue-time enemy guard retained 11105 observations, detected 3018 during-plan geometry changes, recertified 3018 decisions, and overrode 44 actions. Read/recertificate timing was `{'median': 0.9257000056095421, 'p95': 2.3440000077243894, 'max': 168.81020000437275}` / `{'median': 3.329749990371056, 'p95': 7.537500001490116, 'max': 254.7838999889791}` ms; 7937 issue captures contained latent bodies (maximum 41), and 3896 contained dormant bodies (maximum 37). Fresh/global transactions preserved 2980/3024 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8944 observations (8919 contact enabled, 25 anticipatory, 0 errors). 8944 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8944}`.
- The terminal-threat heuristic covered 11105 decisions with horizon counts `{'0': 569, '10': 10536}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 650, '3': 6913, '4': 2249, '5': 1011, '6': 282}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 466, '2': 1090, '3': 7212, '4': 1682, '5': 564, '6': 91}`.
- Adaptive delay supports were `{'1,2': 159, '1,2,3': 147, '1,2,3,4': 257, '1,2,3,4,5': 193, '1,2,3,4,5,6': 180, '2,3': 731, '2,3,4': 2779, '2,3,4,5': 2691, '2,3,4,5,6': 2720, '3,4': 42, '3,4,5': 2, '3,4,5,6': 670, '4,5': 3, '4,5,6': 494, '6': 37}`; 252 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 23/147.
- Robust viability supplied 3737 available policy queries (0 had new delay support outside the cached policy), constrained 118 decisions, and exposed 2471 empty queried action sets. Recovery guidance was available/selected on 185/0 empty-kernel queries; distant-kernel guidance was available/selected on 1542/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 590, '1': 556, '2': 430, '3': 410, '4': 384, '5': 457, '6': 477, '7': 433}`.
- Global-horizon/local-prefix cross-tab covered 1320 decisions: 2 had a winning global state but unsafe selected prefix, 644 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 25 selected actions were outside the reported winning set. 1418 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 673 unique policies with solve-time statistics `{'median': 77.12470000842586, 'p95': 181.78070001886226, 'max': 2172.3723000031896}` and first-observed ages `{'median': 3.0, 'p95': 7.0, 'max': 53.0}`. Policy status counts were `{'pending_future_epoch': 130, 'queryable': 3731, 'expired': 902}`; 1026 robust-mode decisions had no query.
- Of 5649 unambiguous output transitions, 5331 (0.944) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 2, 'missing_pre_hit_alive_decision': 1, 'late_collision_after_positive_causal_margin': 1, 'robust_action_set_exhausted_before_hit': 8, 'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[0, 0, 0, 0, 6, 24, 8, 7, 9, 6, 46, 61, 20, 19, 14, 12, 3, 10, 3, 6, 10, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.616 during the 60 frames preceding a hit versus 0.367 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 9.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
