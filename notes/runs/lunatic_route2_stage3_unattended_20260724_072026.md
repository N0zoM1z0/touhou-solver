# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260724_072026

## Scope And Integrity

- Valid practice scope: `2..27924` (6437 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 10, at `[744, 2114, 8118, 8627, 9216, 19050, 23788, 26261, 26816, 27133]`.
- Hard no-Bomb verification: **PASS** across 6437 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F744-T1`. It occurred during a nonspell phase at player (372.147, 417.114), with 184 bullets and 0 lasers. The projectile model reported pipeline clearance -2.056.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 5 |
| `modeled_committed_prefix_collision` | 4 |
| `observed_laser_overlap` | 1 |

Contributing factors:

- `fast_mode`: 7
- `corridor_deadline_miss`: 3
- `playfield_boundary`: 3
- `action_lag_over_model`: 2
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 744 | nonspell | (372.147, 417.114) | `left_fast` | 184/0 | -2.056/-2.154 | 2f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2114 | nonspell | (13.495, 414.685) | `right_fast` | 1055/0 | -2.617/-2.617 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8118 | nonspell | (30.753, 425.649) | `right` | 445/0 | -1.715/-1.715 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8627 | nonspell | (370.900, 134.144) | `up_left_fast` | 256/0 | -2.086/-2.086 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9216 | nonspell | (351.039, 18.165) | `left_fast` | 403/0 | -2.768/-2.768 | 9f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19050 | 42 野符「GHQクライシス」 | (26.001, 387.946) | `up_fast` | 487/0 | 1.906/-1.463 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23788 | 46 国体「三種の神器　郷」 | (27.487, 426.685) | `up_right_fast` | 441/0 | 1.272/-3.399 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26261 | 50 虚史「幻想郷伝説」 | (94.445, 424.531) | `stay` | 251/170 | -4.183/-4.183 | 0f/0f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26816 | 50 虚史「幻想郷伝説」 | (240.294, 432.000) | `stay` | 245/190 | 1.993/-0.955 | 7f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27133 | 50 虚史「幻想郷伝説」 | (247.739, 432.000) | `left_fast` | 240/200 | 1.664/1.664 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 3574 | 3480 | 1328 | 63 | 1843 | 452 | 230.201 | 0.161 |
| 35 | 0 | 665 | 648 | 462 | 9 | 165 | 89 | 176.613 | 0.177 |
| 38 | 0 | 600 | 589 | 285 | 0 | 275 | 80 | 188.599 | 0.108 |
| 42 野符「GHQクライシス」 | 1 | 588 | 583 | 406 | 0 | 165 | 82 | 166.537 | 0.247 |
| 46 国体「三種の神器　郷」 | 1 | 703 | 695 | 491 | 0 | 171 | 96 | 200.849 | 0.315 |
| 50 虚史「幻想郷伝説」 | 3 | 307 | 301 | 180 | 8 | 99 | 78 | 262.623 | 0.272 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 1 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 23.923 ms median and 46.089 ms p95.
- The full enemy sensor produced 4257 snapshots; capture read time was `{'median': 29.884899995522574, 'p95': 59.823299990966916, 'max': 267.57460000226274}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 22.0}` frames, and 3 phase-counter discontinuities were excluded; 5147 decisions retained at least one contact-enabled body (maximum 7).
- The terminal-threat heuristic covered 6437 decisions with horizon counts `{'0': 55, '10': 6007, '32': 375}`; it reported 2 collision and 63 sub-safety-clearance warnings, and relaxed 375 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 51, '3': 228, '4': 4975, '5': 950, '6': 233}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 60, '3': 280, '4': 5881, '5': 17, '6': 199}`.
- Adaptive delay supports were `{'1,2,3': 35, '1,2,3,4': 66, '1,2,3,4,5': 28, '1,2,3,4,5,6': 6, '2,3': 13, '2,3,4': 30, '2,3,4,5': 637, '2,3,4,5,6': 611, '3,4': 196, '3,4,5': 692, '3,4,5,6': 4008, '4,5,6': 48, '5,6': 67}`; 72 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 162/392.
- Robust viability supplied 6296 available policy queries (80 had new delay support outside the cached policy), constrained 2718 decisions, and exposed 3152 empty queried action sets. Recovery guidance was available/selected on 1228/612 empty-kernel queries; distant-kernel guidance was available/selected on 1861/1830. Safe-action count, selected repair-volume, and selected recovery-distance statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}` `{'median': 3.0, 'p95': 153.0, 'max': 153.0}`, and `{'median': 81.58431221748455, 'p95': 258.48791074245617, 'max': 401.2779585275025}`.
- The rolling worker produced 877 unique policies with solve-time statistics `{'median': 213.944499992067, 'p95': 323.01100000040606, 'max': 446.5830000117421}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1801.0}`. Policy status counts were `{'pending_future_epoch': 39, 'queryable': 6298, 'expired': 14}`; 55 robust-mode decisions had no query.
- Of 3925 unambiguous output transitions, 3416 (0.870) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 8 hit windows with a positive warning lead; those leads were `[6, 8, 4, 6, 12, 7, 7, 0, 7, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.369 during the 60 frames preceding a hit versus 0.181 outside those windows.
- Soft recovery was selected on 0.050 of alive decisions in the 60-frame pre-hit windows versus 0.097 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 72.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
