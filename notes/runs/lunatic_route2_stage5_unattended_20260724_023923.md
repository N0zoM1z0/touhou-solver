# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_023923

## Scope And Integrity

- Valid practice scope: `3..41615` (8160 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 18, at `[820, 1435, 2520, 3985, 11674, 30014, 30755, 31215, 33683, 34315, 35727, 36126, 36874, 37625, 38031, 38377, 39392, 41309]`.
- Hard no-Bomb verification: **PASS** across 8160 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F820-T1`. It occurred during a nonspell phase at player (19.312, 389.159), with 182 bullets and 0 lasers. The projectile model reported pipeline clearance -2.620.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 5 |
| `sensor_gap_or_unmodeled_hazard` | 2 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 11
- `corridor_deadline_miss`: 4
- `playfield_boundary`: 3
- `pool_density_over_1000`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 820 | nonspell | (19.312, 389.159) | `up_fast` | 182/0 | -2.620/-2.620 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1435 | nonspell | (110.895, 217.567) | `up_left_fast` | 111/0 | -0.700/-0.700 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 2520 | nonspell | (374.765, 422.655) | `up_left_fast` | 331/0 | -1.054/-1.054 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3985 | nonspell | (20.226, 418.392) | `down_right_fast` | 714/0 | -4.521/-4.521 | 3f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11674 | nonspell | (15.106, 394.919) | `up_right_fast` | 880/0 | 9.024/3.460 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30014 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (168.920, 428.432) | `up_right_fast` | 882/0 | -4.413/-4.413 | 0f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30755 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (152.735, 394.470) | `right_fast` | 1011/0 | -7.493/-7.493 | 5f/42f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31215 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (149.371, 424.185) | `up_fast` | 997/0 | -3.562/-4.295 | 0f/80f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33683 | nonspell | (48.370, 408.708) | `up_fast` | 464/0 | -1.158/-2.817 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 34315 | nonspell | (20.524, 368.930) | `up` | 437/0 | -2.071/-2.071 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 35727 | 111 懶惰「生神停止(マインドストッパー)」 | (193.071, 222.759) | `stay` | 241/0 | -2.436/-2.436 | 3f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36126 | 111 懶惰「生神停止(マインドストッパー)」 | (196.159, 117.316) | `up_fast` | 96/0 | 32.034/28.678 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 36874 | 111 懶惰「生神停止(マインドストッパー)」 | (189.930, 225.723) | `down` | 338/0 | -2.851/-2.851 | 3f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 37625 | 111 懶惰「生神停止(マインドストッパー)」 | (193.576, 215.494) | `down_right` | 336/0 | -0.676/-1.015 | 7f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 38031 | 111 懶惰「生神停止(マインドストッパー)」 | (184.460, 430.428) | `stay` | 96/0 | -4.060/-4.060 | 10f/20f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 38377 | 111 懶惰「生神停止(マインドストッパー)」 | (271.583, 343.437) | `stay` | 96/0 | -1.593/-1.593 | 0f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 39392 | 115 散符「真実の月(インビジブルフルムーン)」 | (98.798, 427.159) | `up_fast` | 1088/0 | -1.302/-1.302 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41309 | 115 散符「真実の月(インビジブルフルムーン)」 | (12.160, 381.281) | `stay` | 1103/0 | 0.391/-0.315 | 0f/8f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 4989 | 4823 | 2833 | 62 | 1954 | 353 | 276.785 | 0.257 |
| 103 | 0 | 808 | 791 | 456 | 0 | 335 | 61 | 339.502 | 0.392 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 3 | 586 | 570 | 478 | 0 | 92 | 45 | 264.512 | 0.162 |
| 111 懶惰「生神停止(マインドストッパー)」 | 6 | 918 | 898 | 198 | 0 | 700 | 64 | 233.431 | 0.079 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 859 | 838 | 504 | 0 | 334 | 62 | 244.670 | 0.385 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 13.720 ms median and 27.212 ms p95.
- Modeled action hold counts were `{'2': 1, '3': 62, '4': 5330, '5': 2767}` overall.
- Modeled uncontrollable-prefix counts were `{'3': 88, '4': 7967, '5': 105}`.
- Adaptive delay supports were `{'2,3': 1, '2,3,4': 46, '2,3,4,5': 55, '2,3,4,5,6': 74, '3,4': 72, '3,4,5': 1054, '3,4,5,6': 6858}`; 385 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 111/476.
- Robust viability supplied 7920 available policy queries (62 had new delay support outside the cached policy), constrained 3415 decisions, and exposed 4469 empty queried action sets. Recovery guidance was available/selected on 685/383 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 585 unique policies with solve-time statistics `{'median': 268.4882000030484, 'p95': 400.306499999715, 'max': 447.59270001668483}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1795.0}`. Policy status counts were `{'pending_future_epoch': 95, 'queryable': 7920, 'expired': 60}`; 155 robust-mode decisions had no query.
- Of 4602 unambiguous output transitions, 4007 (0.871) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 8, 'robust_action_set_exhausted_before_hit': 9, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 16 hit windows with a positive warning lead; those leads were `[6, 3, 3, 12, 0, 19, 42, 80, 4, 4, 10, 0, 9, 11, 20, 10, 8, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.193 during the 60 frames preceding a hit versus 0.272 outside those windows.
- Soft recovery was selected on 0.043 of alive decisions in the 60-frame pre-hit windows versus 0.050 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 13.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Causal Review

- Relative to `20260724_022420`, total hits fell 20 to 18 and nonspell hits
  fell 12 to 7. This is an improvement witness, not a deterministic clear-rate
  estimate.
- Frame 11,674 is an exact enemy-body overlap. Stable next-frame telemetry
  contains 23 enabled bodies; the immediately preceding action snapshot
  contains none. The remaining prevention gap is future ECL contact
  activation, not failure to enumerate the current pool.
- Synchronous full-pool sensing cost 13.97 ms mean. Read median rose 11.10 to
  24.91 ms, cadence p95 rose four to five frames, and available policy queries
  fell 20 percent.
- CE-0060 moves the same full sensor to an asynchronous snapshot pipeline with
  age projection and bounded uncertainty. A third physical run is required to
  accept latency restoration.
