# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_105457

## Scope And Integrity

- Valid practice scope: `3..41483` (7397 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 14, at `[2218, 8006, 11255, 12717, 23567, 29773, 34494, 36204, 36505, 36974, 37709, 38046, 39298, 40530]`.
- Hard no-Bomb verification: **PASS** across 7397 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2218-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 543 bullets and 0 lasers. The projectile model reported pipeline clearance -1.206.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 7 |
| `modeled_committed_prefix_collision` | 5 |
| `sensor_gap_or_unmodeled_hazard` | 2 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 8
- `corridor_deadline_miss`: 3
- `pool_density_over_1000`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2218 | nonspell | (376.000, 432.000) | `up_fast` | 543/0 | -1.206/-1.206 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8006 | nonspell | (18.285, 432.000) | `left_fast` | 738/0 | -0.583/-0.583 | 0f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11255 | nonspell | (351.300, 395.979) | `up_left_fast` | 890/0 | 1.618/-4.893 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12717 | nonspell | (20.788, 432.000) | `up_left_fast` | 223/0 | -1.978/-1.978 | 4f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23567 | 103 幻波「赤眼催眠(マインドブローイング)」 | (14.505, 428.000) | `up_fast` | 1050/0 | 1.201/-0.653 | 5f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29773 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (223.724, 432.000) | `right` | 1001/0 | -6.107/-6.107 | 0f/236f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34494 | nonspell | (370.401, 432.000) | `up_fast` | 467/0 | -3.852/-3.852 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36204 | 111 懶惰「生神停止(マインドストッパー)」 | (183.300, 220.211) | `down_left` | 353/0 | -0.338/-0.338 | 0f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36505 | 111 懶惰「生神停止(マインドストッパー)」 | (191.572, 90.628) | `up` | 96/0 | 75.980/20.663 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 36974 | 111 懶惰「生神停止(マインドストッパー)」 | (176.440, 228.125) | `stay` | 337/0 | -1.362/-1.362 | 0f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37709 | 111 懶惰「生神停止(マインドストッパー)」 | (192.661, 211.699) | `up_left_fast` | 342/0 | -2.237/-2.237 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38046 | 111 懶惰「生神停止(マインドストッパー)」 | (194.045, 83.999) | `down_left` | 96/0 | 66.251/26.598 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 39298 | 115 散符「真実の月(インビジブルフルムーン)」 | (373.172, 429.172) | `up_left_fast` | 1281/0 | 1.364/-0.137 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40530 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 432.000) | `down_left_fast` | 958/0 | -4.254/-4.254 | 0f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 4596 | 4474 | 2444 | 0 | 1993 | 739 | 325.596 | 0.166 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 679 | 667 | 354 | 0 | 310 | 114 | 388.870 | 0.319 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 529 | 512 | 402 | 0 | 110 | 109 | 290.435 | 0.282 |
| 111 懶惰「生神停止(マインドストッパー)」 | 5 | 857 | 848 | 162 | 0 | 686 | 134 | 312.090 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 736 | 719 | 343 | 0 | 371 | 144 | 287.926 | 0.375 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 22.631 ms median and 37.733 ms p95.
- The full enemy sensor produced 5717 snapshots; capture read time was `{'median': 32.79399999883026, 'p95': 53.245099988998845, 'max': 87.70999999251217}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 220 decisions retained at least one contact-enabled body (maximum 37).
- The terminal-threat heuristic covered 7397 decisions with horizon counts `{'0': 88, '10': 6933, '32': 376}`; it reported 1 collision and 72 sub-safety-clearance warnings, and relaxed 45 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 44, '3': 178, '4': 1385, '5': 3851, '6': 1939}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 52, '3': 95, '4': 3208, '5': 2529, '6': 1513}`.
- Adaptive delay supports were `{'1,2,3': 16, '1,2,3,4,5': 22, '1,2,3,4,5,6': 7, '2,3': 29, '2,3,4,5': 63, '2,3,4,5,6': 1421, '3,4,5': 234, '3,4,5,6': 4883, '4,5': 1, '4,5,6': 593, '5,6': 128}`; 379 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 127/183.
- Robust viability supplied 7220 available policy queries (0 had new delay support outside the cached policy), constrained 3470 decisions, and exposed 3705 empty queried action sets. Recovery guidance was available/selected on 772/459 empty-kernel queries; distant-kernel guidance was available/selected on 2605/2519. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 8.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 102.44998779892558, 'p95': 291.97260145431454, 'max': 417.22895393296955}`, and `{'median': 0.0, 'p95': 25.372583389282227, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 923, '1': 953, '2': 945, '3': 860, '4': 909, '5': 887, '6': 855, '7': 888}`.
- The rolling worker produced 1240 unique policies with solve-time statistics `{'median': 317.89045000914484, 'p95': 466.9941999891307, 'max': 539.0158999944106}` and first-observed ages `{'median': 7.0, 'p95': 14.0, 'max': 1812.0}`. Policy status counts were `{'pending_future_epoch': 30, 'queryable': 7219, 'expired': 42}`; 71 robust-mode decisions had no query.
- Of 4147 unambiguous output transitions, 3889 (0.938) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 12, 'missing_pre_hit_alive_decision': 1, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[4, 12, 9, 23, 10, 236, 8, 24, 0, 15, 7, 0, 10, 11]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.371 during the 60 frames preceding a hit versus 0.191 outside those windows.
- Mean selected control-reserve deficit was 8.874 during the 60 frames preceding a hit versus 2.333 outside those windows.
- Soft recovery was selected on 0.023 of alive decisions in the 60-frame pre-hit windows versus 0.065 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 42.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Spell-111 Full-Pool Diagnostic

- This run enabled the opt-in full-pool transform trace. The compact
  source-hashed report covers all active spell-111 bullets at every retained
  decision: 189,877 samples and 100 percent pool coverage.
- **Observed:** active transform flags were always zero, original/tag flags
  were always `0x00100202`, queue cursor was always zero, and no queued
  0x40/0x80/0x100 stop lifecycle appeared.
- **Observed:** same-slot groups still changed from normal velocity to zero at
  frames 35,689 and 36,047, then resumed at 35,788 and 36,148.
- **Conclusion:** the earlier queued-transform hypothesis is rejected for
  spell 111. The later static/native investigation identified ECL callback 12
  as the mechanism. This run validates causal diagnosis, not survival.
