# TH08 Stage 1 No-Bomb Practice Review: lunatic_route2_stage1_unattended_20260724_070946

## Scope And Integrity

- Valid practice scope: `2..20786` (4754 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 4, at `[1444, 5430, 5863, 6938]`.
- Hard no-Bomb verification: **PASS** across 4754 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S0-F1444-T1`. It occurred during a nonspell phase at player (346.143, 421.859), with 78 bullets and 0 lasers. The projectile model reported pipeline clearance -1.390.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 4 |

Contributing factors:

- `corridor_deadline_miss`: 2
- `fast_mode`: 2
- `playfield_boundary`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1444 | nonspell | (346.143, 421.859) | `left_fast` | 78/0 | -1.390/-1.390 | 4f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 5430 | 1 蛍符「地上の彗星」 | (192.217, 431.407) | `stay` | 382/0 | -10.605/-10.605 | 4f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 5863 | 1 蛍符「地上の彗星」 | (129.501, 420.727) | `down` | 350/0 | -6.745/-6.745 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 6938 | nonspell | (15.842, 190.395) | `down_right_fast` | 173/0 | -0.970/-0.970 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 2 | 2824 | 2734 | 465 | 60 | 1988 | 350 | 226.551 | 0.073 |
| 1 蛍符「地上の彗星」 | 2 | 668 | 650 | 288 | 15 | 326 | 85 | 140.863 | 0.242 |
| 5 | 0 | 575 | 558 | 201 | 6 | 297 | 75 | 201.277 | 0.113 |
| 9 | 0 | 687 | 680 | 188 | 0 | 408 | 90 | 246.198 | 0.129 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 22.350 ms median and 40.822 ms p95.
- The full enemy sensor produced 3004 snapshots; capture read time was `{'median': 27.693750016624108, 'p95': 50.117399980081245, 'max': 79.5681000163313}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 3 phase-counter discontinuities were excluded; 4513 decisions retained at least one contact-enabled body (maximum 17).
- The terminal-threat heuristic covered 4754 decisions with horizon counts `{'0': 69, '10': 4299, '32': 386}`; it reported 0 collision and 34 sub-safety-clearance warnings, and relaxed 386 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 53, '3': 542, '4': 3500, '5': 659}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 65, '3': 588, '4': 4101}`.
- Adaptive delay supports were `{'1,2,3': 32, '1,2,3,4': 12, '2,3': 37, '2,3,4': 123, '2,3,4,5': 685, '2,3,4,5,6': 877, '3,4': 23, '3,4,5': 524, '3,4,5,6': 2441}`; 25 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 51/226.
- Robust viability supplied 4622 available policy queries (81 had new delay support outside the cached policy), constrained 3019 decisions, and exposed 1142 empty queried action sets. Recovery guidance was available/selected on 561/319 empty-kernel queries; distant-kernel guidance was available/selected on 482/476. Safe-action count, selected repair-volume, and selected recovery-distance statistics were `{'median': 9.0, 'p95': 17.0, 'max': 17.0}` `{'median': 51.0, 'p95': 153.0, 'max': 153.0}`, and `{'median': 65.96969000988257, 'p95': 252.98221281347034, 'max': 416.0}`.
- The rolling worker produced 600 unique policies with solve-time statistics `{'median': 216.93394999601878, 'p95': 354.57349999342114, 'max': 439.20529997558333}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1792.0}`. Policy status counts were `{'pending_future_epoch': 40, 'queryable': 4621, 'expired': 12}`; 51 robust-mode decisions had no query.
- Of 2529 unambiguous output transitions, 2221 (0.878) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 3, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 3 hit windows with a positive warning lead; those leads were `[12, 4, 0, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.284 during the 60 frames preceding a hit versus 0.103 outside those windows.
- Soft recovery was selected on 0.054 of alive decisions in the 60-frame pre-hit windows versus 0.072 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 9.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
