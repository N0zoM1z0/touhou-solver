# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_120128

## Scope And Integrity

- Valid practice scope: `2..46022` (7430 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 31, at `[2146, 4018, 11656, 12351, 12848, 14059, 21734, 22955, 23515, 23861, 24386, 25005, 27955, 28760, 30069, 30453, 30748, 31121, 31558, 31975, 32294, 32697, 33376, 33912, 34213, 38903, 40203, 40719, 41118, 41759, 42493]`.
- Hard no-Bomb verification: **PASS** across 7430 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2146-T1`. It occurred during a nonspell phase at player (367.515, 419.515), with 563 bullets and 0 lasers. The projectile model reported pipeline clearance 1.584.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 15 |
| `sensor_gap_or_unmodeled_hazard` | 9 |
| `observed_bullet_overlap` | 7 |

Contributing factors:

- `action_lag_over_model`: 20
- `fast_mode`: 17
- `playfield_boundary`: 16
- `pool_density_over_1000`: 12
- `corridor_deadline_miss`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2146 | nonspell | (367.515, 419.515) | `up_left_fast` | 563/0 | 1.584/-0.730 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4018 | nonspell | (8.000, 430.455) | `right` | 727/0 | -1.696/-1.696 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11656 | nonspell | (361.858, 364.957) | `up_left_fast` | 898/0 | -15.107/-15.107 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12351 | nonspell | (376.000, 283.231) | `down_right_fast` | 293/0 | -2.314/-2.314 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12848 | nonspell | (374.532, 432.000) | `up_left_fast` | 255/0 | -1.389/-1.389 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14059 | nonspell | (16.132, 432.000) | `left_fast` | 424/0 | -0.092/-2.654 | 6f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21734 | nonspell | (344.792, 420.500) | `down_left` | 484/0 | -0.823/-0.823 | 0f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22955 | 103 幻波「赤眼催眠(マインドブローイング)」 | (374.869, 326.989) | `up_fast` | 644/0 | -3.185/-3.185 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23515 | 103 幻波「赤眼催眠(マインドブローイング)」 | (166.763, 432.000) | `up` | 1015/0 | 7.215/-1.469 | 34f/34f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23861 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.978, 163.552) | `down_left` | 978/0 | 0.299/-5.072 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 24386 | 103 幻波「赤眼催眠(マインドブローイング)」 | (363.696, 27.384) | `up_left_fast` | 1090/0 | 7.298/-2.400 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25005 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 331.817) | `down_right_fast` | 1027/0 | -0.608/-1.860 | 31f/31f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27955 | nonspell | (158.995, 432.000) | `right_fast` | 1017/0 | 0.236/0.236 | 0f/5f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28760 | nonspell | (140.963, 432.000) | `up` | 1055/0 | -1.049/-1.049 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30069 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (8.000, 432.000) | `up_fast` | 778/0 | -5.092/-9.073 | 21f/28f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30453 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (8.000, 162.326) | `down` | 987/0 | -4.867/-9.605 | 35f/77f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30748 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (376.000, 339.501) | `stay` | 1014/0 | -3.607/-7.689 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 31121 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (164.033, 420.616) | `stay` | 1001/0 | -1.964/-7.606 | 42f/42f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31558 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (143.770, 236.241) | `up` | 997/0 | -1.294/-9.837 | 31f/31f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31975 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (119.582, 369.935) | `up` | 988/0 | 3.825/-9.415 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32294 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (298.890, 281.958) | `up_fast` | 999/0 | -8.745/-8.985 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 32697 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (152.226, 428.000) | `up_right_fast` | 1013/0 | -6.084/-9.628 | 30f/107f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33376 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (376.000, 182.134) | `down_left_fast` | 1001/0 | -9.008/-9.825 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 33912 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (68.848, 30.616) | `down` | 1014/0 | -2.046/-7.351 | 217f/217f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34213 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (112.875, 39.818) | `down_fast` | 1008/0 | -3.311/-8.796 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 38903 | nonspell | (376.000, 432.000) | `left_fast` | 473/0 | -1.915/-1.915 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40203 | 111 懶惰「生神停止(マインドストッパー)」 | (217.043, 237.029) | `left_fast` | 246/0 | -4.085/-4.085 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40719 | 111 懶惰「生神停止(マインドストッパー)」 | (361.858, 93.640) | `up_left` | 1021/0 | 10.225/-1.973 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41118 | 111 懶惰「生神停止(マインドストッパー)」 | (305.065, 396.420) | `up_right_fast` | 804/0 | 13.810/6.011 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 41759 | 111 懶惰「生神停止(マインドストッパー)」 | (139.547, 293.978) | `down` | 339/0 | 1.244/1.163 | 0f/18f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42493 | 111 懶惰「生神停止(マインドストッパー)」 | (203.030, 226.747) | `left` | 345/0 | 14.392/7.414 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 5175 | 5048 | 2717 | 0 | 2275 | 805 | 332.492 | 0.173 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 5 | 488 | 472 | 106 | 0 | 366 | 81 | 467.030 | 0.096 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 11 | 346 | 335 | 207 | 0 | 122 | 129 | 590.880 | 0.102 |
| 111 懶惰「生神停止(マインドストッパー)」 | 5 | 721 | 714 | 106 | 0 | 608 | 118 | 366.564 | 0.000 |
| 115 | 0 | 700 | 677 | 431 | 0 | 241 | 137 | 300.601 | 0.450 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 23.595 ms median and 45.858 ms p95.
- The full enemy sensor produced 5688 snapshots; capture read time was `{'median': 35.70110001601279, 'p95': 66.93529998301528, 'max': 613.0368000012822}`, snapshot age was `{'median': 5.0, 'p95': 10.0, 'max': 57.0}` frames, and 8 phase-counter discontinuities were excluded; 145 decisions retained at least one contact-enabled body (maximum 37).
- The terminal-threat heuristic covered 7430 decisions with horizon counts `{'0': 91, '10': 6946, '32': 393}`; it reported 4 collision and 80 sub-safety-clearance warnings, and relaxed 67 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 51, '3': 170, '4': 1398, '5': 3819, '6': 1992}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 28, '3': 165, '4': 3206, '5': 3266, '6': 765}`.
- Adaptive delay supports were `{'1,2,3': 50, '1,2,3,4': 23, '2,3': 14, '2,3,4': 21, '2,3,4,5': 44, '2,3,4,5,6': 1808, '3,4': 12, '3,4,5': 471, '3,4,5,6': 4040, '4,5': 17, '4,5,6': 797, '5,6': 10, '6': 123}`; 332 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 343/489.
- Robust viability supplied 7246 available policy queries (0 had new delay support outside the cached policy), constrained 3612 decisions, and exposed 3567 empty queried action sets. Recovery guidance was available/selected on 917/545 empty-kernel queries; distant-kernel guidance was available/selected on 2464/2391. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 15.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 101.19288512538814, 'p95': 315.56932677305633, 'max': 422.4121210382107}`, and `{'median': 0.0, 'p95': 28.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 914, '1': 962, '2': 954, '3': 862, '4': 935, '5': 836, '6': 893, '7': 890}`.
- The rolling worker produced 1270 unique policies with solve-time statistics `{'median': 355.14805000275373, 'p95': 623.4982000023592, 'max': 766.1491000035312}` and first-observed ages `{'median': 8.0, 'p95': 42.0, 'max': 1809.0}`. Policy status counts were `{'pending_future_epoch': 41, 'queryable': 7244, 'expired': 43}`; 82 robust-mode decisions had no query.
- Of 4474 unambiguous output transitions, 3867 (0.864) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 25, 'missing_pre_hit_alive_decision': 5, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[0, 8, 0, 13, 3, 15, 15, 0, 34, 0, 0, 31, 5, 5, 28, 77, 0, 42, 31, 0, 0, 107, 0, 217, 0, 5, 5, 0, 0, 18, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.320 during the 60 frames preceding a hit versus 0.188 outside those windows.
- Mean selected control-reserve deficit was 9.515 during the 60 frames preceding a hit versus 2.139 outside those windows.
- Soft recovery was selected on 0.036 of alive decisions in the 60-frame pre-hit windows versus 0.074 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 27.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Callback And Performance Audit

This run did pass the callback-activation gate that the aggregate dossier
cannot express. Spell 111 covered ECL timer values 1 through 709 and eight
loop resets; 672 of 721 lookahead rows contained a future callback, and 544
attached at least one native bullet. Moving and stopped tagged bullets both
received future trajectories. The model was therefore connected to both local
and global planning, unlike run `20260724_113250`.

That activation exposed an implementation bottleneck rather than accepting
the model. Spell 107 attached trajectories on 315 of 346 decisions, with
median 988 and maximum 1,022 bullets. Its local planner took
`40.20/463.87 ms` median/p95 and decision cadence fell to `7/37` frames.
Spell 103 emitted four or six callback events on every decision and reached
`333.19 ms` local p95. By contrast spell 115 emitted no events and retained
`26.33/39.90 ms` local planning with `4/6`-frame cadence.

Two decisions were also cross-epoch joins. Frame 27,169 combined a spell-103
source at 25,364 with a bullet capture ending at 27,165 (span 1,801); frame
36,140 combined spell 107 across a 1,800-frame jump. These match the native
spell-start counter adjustment and are not 30-second physical reads. Their
plans and uncertainty envelopes are invalid.

The 31-hit result is therefore retained as a regression and causal
counterexample, not evidence that exact callback motion is harmful. CE-0086
tracks sparse native projection and explicit sensor-epoch rejection before
the required cross-stage physical trial.
