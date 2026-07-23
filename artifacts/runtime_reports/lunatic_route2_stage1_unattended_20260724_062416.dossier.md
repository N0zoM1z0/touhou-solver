# TH08 Stage 1 No-Bomb Practice Review: lunatic_route2_stage1_unattended_20260724_062416

## Scope And Integrity

- Valid practice scope: `2..20939` (4719 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 4, at `[1137, 2596, 13710, 14195]`.
- Hard no-Bomb verification: **PASS** across 4719 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S0-F1137-T1`. It occurred during a nonspell phase at player (10.908, 425.358), with 219 bullets and 0 lasers. The projectile model reported pipeline clearance -3.216.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 2 |
| `observed_bullet_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 4
- `playfield_boundary`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1137 | nonspell | (10.908, 425.358) | `right_fast` | 219/0 | -3.216/-3.216 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2596 | nonspell | (16.048, 22.850) | `up_right_fast` | 106/0 | 1.944/-12.858 | 3f/5f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13710 | 5 灯符「ファイヤフライフェノメノン」 | (371.010, 429.657) | `up_fast` | 379/0 | -1.332/-1.332 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14195 | 5 灯符「ファイヤフライフェノメノン」 | (364.132, 423.711) | `left_fast` | 430/0 | -0.187/-0.660 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 2 | 2853 | 2781 | 737 | 50 | 1777 | 360 | 225.665 | 0.088 |
| 1 | 0 | 597 | 590 | 325 | 0 | 233 | 80 | 133.278 | 0.221 |
| 5 灯符「ファイヤフライフェノメノン」 | 2 | 600 | 594 | 229 | 0 | 343 | 78 | 205.481 | 0.181 |
| 9 | 0 | 669 | 654 | 144 | 0 | 428 | 89 | 250.380 | 0.119 |

## Interpretation

- Retained witnesses classify 1 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 23.534 ms median and 42.208 ms p95.
- The full enemy sensor produced 3061 snapshots; capture read time was `{'median': 27.83620002446696, 'p95': 50.668399984715506, 'max': 76.56169999972917}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 3 phase-counter discontinuities were excluded; 4483 decisions retained at least one contact-enabled body (maximum 34).
- The terminal-threat heuristic covered 4719 decisions with horizon counts `{'0': 72, '10': 4287, '32': 360}`; it reported 0 collision and 36 sub-safety-clearance warnings, and relaxed 360 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 51, '3': 424, '4': 3219, '5': 1025}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 69, '3': 373, '4': 4277}`.
- Adaptive delay supports were `{'1,2,3': 8, '1,2,3,4': 8, '2,3': 72, '2,3,4': 163, '2,3,4,5': 618, '2,3,4,5,6': 807, '3,4': 24, '3,4,5': 447, '3,4,5,6': 2572}`; 55 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 49/246.
- Robust viability supplied 4619 available policy queries (50 had new delay support outside the cached policy), constrained 2781 decisions, and exposed 1435 empty queried action sets. Recovery guidance was available/selected on 481/293 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 8.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 42.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 607 unique policies with solve-time statistics `{'median': 214.6461999800522, 'p95': 344.25480000209063, 'max': 447.44179997360334}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1801.0}`. Policy status counts were `{'pending_future_epoch': 40, 'queryable': 4619, 'expired': 15}`; 55 robust-mode decisions had no query.
- Of 2696 unambiguous output transitions, 2378 (0.882) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 4}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 4 hit windows with a positive warning lead; those leads were `[4, 5, 7, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.416 during the 60 frames preceding a hit versus 0.115 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.067 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 10.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
