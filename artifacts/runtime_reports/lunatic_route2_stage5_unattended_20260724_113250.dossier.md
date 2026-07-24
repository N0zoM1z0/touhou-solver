# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_113250

## Scope And Integrity

- Valid practice scope: `2..45097` (8279 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 21, at `[1889, 7465, 10798, 12069, 12700, 22805, 23236, 23819, 24473, 28379, 31039, 31672, 32497, 33325, 36997, 37492, 39706, 41151, 41978, 43542, 44353]`.
- Hard no-Bomb verification: **PASS** across 8279 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1889-T1`. It occurred during a nonspell phase at player (376.000, 44.721), with 603 bullets and 0 lasers. The projectile model reported pipeline clearance -1.943.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 3 |
| `enemy_body_contact_candidate` | 1 |

Contributing factors:

- `fast_mode`: 12
- `playfield_boundary`: 12
- `pool_density_over_1000`: 8
- `corridor_deadline_miss`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1889 | nonspell | (376.000, 44.721) | `down_right` | 603/0 | -1.943/-1.943 | 0f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7465 | nonspell | (195.078, 432.000) | `up_right_fast` | 622/0 | 11.350/1.790 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10798 | nonspell | (26.624, 397.029) | `down_fast` | 870/0 | 13.212/3.730 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 12069 | nonspell | (376.000, 148.737) | `down_left_fast` | 316/0 | -3.927/-3.927 | 5f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12700 | nonspell | (362.200, 238.231) | `left_fast` | 245/0 | -2.149/-2.149 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22805 | 103 幻波「赤眼催眠(マインドブローイング)」 | (151.522, 432.000) | `left` | 1073/0 | -1.749/-1.749 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23236 | 103 幻波「赤眼催眠(マインドブローイング)」 | (211.070, 432.000) | `up_fast` | 1067/0 | -3.047/-3.047 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23819 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 428.847) | `right` | 847/0 | -1.367/-1.367 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24473 | 103 幻波「赤眼催眠(マインドブローイング)」 | (320.800, 431.029) | `left` | 862/0 | -3.064/-3.064 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28379 | nonspell | (8.000, 432.000) | `down_right_fast` | 1088/0 | -1.984/-1.984 | 4f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31039 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (243.287, 378.921) | `stay` | 1027/0 | -6.969/-7.039 | 0f/138f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31672 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (69.796, 361.884) | `down` | 1002/0 | -2.300/-4.665 | 45f/72f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32497 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (157.152, 363.652) | `stay` | 1004/0 | -6.912/-6.912 | 14f/39f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33325 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (142.935, 343.518) | `stay` | 1019/0 | -7.324/-7.324 | 0f/231f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36997 | nonspell | (8.000, 278.450) | `up_fast` | 506/0 | -1.980/-1.980 | 8f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37492 | nonspell | (376.000, 406.941) | `down_right_fast` | 459/0 | -1.750/-1.750 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39706 | 111 懶惰「生神停止(マインドストッパー)」 | (185.953, 77.259) | `up_fast` | 332/0 | 49.423/-1.118 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 41151 | 111 懶惰「生神停止(マインドストッパー)」 | (165.284, 223.870) | `down_right` | 337/0 | -1.536/-1.840 | 0f/27f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41978 | 115 散符「真実の月(インビジブルフルムーン)」 | (208.831, 118.306) | `up_fast` | 0/0 | 9999.000/6.325 | 0f/0f | `enemy_body_contact_candidate` | `unresolved_planner_failure` |
| discovery | 43542 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 432.000) | `up_right_fast` | 1293/0 | -1.704/-1.713 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44353 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 427.646) | `right_fast` | 957/0 | -0.345/-1.785 | 4f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 5099 | 4989 | 2927 | 0 | 2026 | 812 | 323.455 | 0.179 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 4 | 546 | 534 | 120 | 0 | 413 | 79 | 437.575 | 0.171 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 4 | 1021 | 1004 | 885 | 0 | 119 | 203 | 326.719 | 0.265 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 844 | 830 | 260 | 0 | 570 | 148 | 259.962 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 769 | 761 | 359 | 0 | 380 | 140 | 305.362 | 0.414 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 5.000 frames p95. The local plan took 23.482 ms median and 38.408 ms p95.
- The full enemy sensor produced 6487 snapshots; capture read time was `{'median': 34.65169999981299, 'p95': 54.267199971945956, 'max': 501.65150000248104}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 36.0}` frames, and 11 phase-counter discontinuities were excluded; 195 decisions retained at least one contact-enabled body (maximum 37).
- The terminal-threat heuristic covered 8279 decisions with horizon counts `{'0': 75, '10': 7893, '32': 311}`; it reported 2 collision and 43 sub-safety-clearance warnings, and relaxed 59 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 48, '3': 122, '4': 2014, '5': 4645, '6': 1450}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 49, '3': 120, '4': 3785, '5': 3975, '6': 350}`.
- Adaptive delay supports were `{'1,2,3,4': 19, '2,3': 30, '2,3,4': 33, '2,3,4,5': 256, '2,3,4,5,6': 1149, '3,4,5': 108, '3,4,5,6': 5150, '4,5,6': 1534}`; 556 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 161/496.
- Robust viability supplied 8118 available policy queries (0 had new delay support outside the cached policy), constrained 3508 decisions, and exposed 4551 empty queried action sets. Recovery guidance was available/selected on 877/529 empty-kernel queries; distant-kernel guidance was available/selected on 3133/3006. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 1.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 116.48175822848829, 'p95': 279.8856909525744, 'max': 483.7189266505912}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1126, '1': 1033, '2': 1039, '3': 1005, '4': 970, '5': 1021, '6': 970, '7': 954}`.
- The rolling worker produced 1382 unique policies with solve-time statistics `{'median': 321.2539500091225, 'p95': 476.66729998309165, 'max': 659.7363000037149}` and first-observed ages `{'median': 7.0, 'p95': 15.0, 'max': 1816.0}`. Policy status counts were `{'pending_future_epoch': 32, 'queryable': 8114, 'expired': 41}`; 69 robust-mode decisions had no query.
- Of 4728 unambiguous output transitions, 4084 (0.864) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 18, 'unresolved_planner_failure': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 14 hit windows with a positive warning lead; those leads were `[15, 0, 0, 16, 7, 0, 12, 0, 0, 9, 138, 72, 39, 231, 15, 7, 0, 27, 0, 6, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.119 during the 60 frames preceding a hit versus 0.192 outside those windows.
- Mean selected control-reserve deficit was 6.562 during the 60 frames preceding a hit versus 2.420 outside those windows.
- Soft recovery was selected on 0.096 of alive decisions in the 60-frame pre-hit windows versus 0.064 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
