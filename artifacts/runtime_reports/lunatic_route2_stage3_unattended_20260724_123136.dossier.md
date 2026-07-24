# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260724_123136

## Scope And Integrity

- Valid practice scope: `2..27805` (5577 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 8, at `[2655, 3500, 8004, 14756, 26246, 26759, 27421, 27757]`.
- Hard no-Bomb verification: **PASS** across 5577 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F2655-T1`. It occurred during a nonspell phase at player (8.000, 236.140), with 344 bullets and 0 lasers. The projectile model reported pipeline clearance -1.339.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 3 |

Contributing factors:

- `fast_mode`: 5
- `playfield_boundary`: 4
- `action_lag_over_model`: 3
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2655 | nonspell | (8.000, 236.140) | `up_left_fast` | 344/0 | -1.339/-2.018 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3500 | nonspell | (102.609, 16.000) | `up_left_fast` | 519/0 | -2.878/-2.878 | 0f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8004 | nonspell | (8.000, 432.000) | `right_fast` | 637/0 | -1.422/-1.422 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14756 | nonspell | (243.381, 425.495) | `up_right` | 447/0 | -1.435/-1.435 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26246 | 50 虚史「幻想郷伝説」 | (232.846, 432.000) | `down_right` | 264/200 | -2.216/-2.216 | 0f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26759 | 50 虚史「幻想郷伝説」 | (373.715, 426.462) | `up_fast` | 237/190 | -2.571/-2.571 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27421 | 50 虚史「幻想郷伝説」 | (223.682, 415.845) | `down_right` | 253/200 | -2.092/-2.092 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27757 | 50 虚史「幻想郷伝説」 | (206.879, 420.616) | `left_fast` | 51/170 | -0.156/-0.179 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 3083 | 2988 | 1263 | 0 | 1658 | 566 | 270.748 | 0.124 |
| 35 | 0 | 551 | 540 | 435 | 0 | 99 | 125 | 213.176 | 0.000 |
| 38 | 0 | 565 | 554 | 271 | 0 | 282 | 109 | 220.703 | 0.083 |
| 42 | 0 | 484 | 469 | 394 | 0 | 73 | 112 | 173.360 | 0.124 |
| 46 | 0 | 586 | 578 | 437 | 0 | 127 | 134 | 225.765 | 0.159 |
| 50 虚史「幻想郷伝説」 | 4 | 308 | 292 | 159 | 0 | 127 | 92 | 292.093 | 0.129 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 28.058 ms median and 47.205 ms p95.
- The full enemy sensor produced 4486 snapshots; capture read time was `{'median': 38.64725001039915, 'p95': 67.25170000572689, 'max': 221.1922999995295}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 19.0}` frames, and 3 phase-counter discontinuities were excluded; 4379 decisions retained at least one contact-enabled body (maximum 8).
- The terminal-threat heuristic covered 5577 decisions with horizon counts `{'0': 50, '10': 5021, '32': 506}`; it reported 0 collision and 67 sub-safety-clearance warnings, and relaxed 96 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 50, '3': 171, '4': 877, '5': 4271, '6': 208}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 27, '3': 211, '4': 1560, '5': 3601, '6': 178}`.
- Adaptive delay supports were `{'1,2,3': 27, '1,2,3,4': 25, '2,3': 30, '2,3,4': 80, '2,3,4,5': 40, '2,3,4,5,6': 130, '3,4': 12, '3,4,5': 239, '3,4,5,6': 4156, '4,5': 28, '4,5,6': 754, '5,6': 56}`; 130 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 198/441.
- Robust viability supplied 5421 available policy queries (0 had new delay support outside the cached policy), constrained 2366 decisions, and exposed 2959 empty queried action sets. Recovery guidance was available/selected on 989/445 empty-kernel queries; distant-kernel guidance was available/selected on 1900/1823. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 2.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 112.0, 'p95': 288.44410203711914, 'max': 435.2470562795342}`, and `{'median': 0.0, 'p95': 16.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 757, '1': 753, '2': 723, '3': 667, '4': 616, '5': 643, '6': 610, '7': 652}`.
- The rolling worker produced 1138 unique policies with solve-time statistics `{'median': 245.10844999167603, 'p95': 398.4403999929782, 'max': 478.3097000035923}` and first-observed ages `{'median': 5.0, 'p95': 13.0, 'max': 3592.0}`. Policy status counts were `{'pending_future_epoch': 32, 'queryable': 5422, 'expired': 15}`; 48 robust-mode decisions had no query.
- Of 3634 unambiguous output transitions, 3080 (0.848) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 8}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 6 hit windows with a positive warning lead; those leads were `[5, 21, 10, 9, 14, 0, 0, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.272 during the 60 frames preceding a hit versus 0.107 outside those windows.
- Mean selected control-reserve deficit was 7.876 during the 60 frames preceding a hit versus 0.801 outside those windows.
- Soft recovery was selected on 0.012 of alive decisions in the 60-frame pre-hit windows versus 0.088 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 77.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
