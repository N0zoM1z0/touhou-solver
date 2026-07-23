# TH08 Stage 1 No-Bomb Practice Review: lunatic_route2_stage1_unattended_20260724_064421

## Scope And Integrity

- Valid practice scope: `3..21008` (4712 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 4, at `[1072, 5859, 6269, 7019]`.
- Hard no-Bomb verification: **PASS** across 4712 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S0-F1072-T1`. It occurred during a nonspell phase at player (28.879, 29.267), with 172 bullets and 0 lasers. The projectile model reported pipeline clearance 0.597.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 2 |
| `modeled_committed_prefix_collision` | 1 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 3
- `corridor_deadline_miss`: 2
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1072 | nonspell | (28.879, 29.267) | `up` | 172/0 | 0.597/-0.197 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 5859 | 1 蛍符「地上の彗星」 | (361.157, 422.444) | `up_fast` | 287/0 | -2.400/-2.400 | 4f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 6269 | 1 蛍符「地上の彗星」 | (130.288, 420.689) | `left_fast` | 335/0 | 7.629/0.289 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7019 | nonspell | (361.280, 23.017) | `left_fast` | 218/0 | -2.919/-2.919 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 2 | 2872 | 2796 | 477 | 86 | 1954 | 358 | 233.965 | 0.084 |
| 1 蛍符「地上の彗星」 | 2 | 621 | 605 | 332 | 0 | 232 | 84 | 137.327 | 0.178 |
| 5 | 0 | 566 | 549 | 223 | 12 | 253 | 75 | 201.834 | 0.071 |
| 9 | 0 | 653 | 647 | 85 | 0 | 467 | 90 | 250.661 | 0.110 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 23.696 ms median and 42.574 ms p95.
- The full enemy sensor produced 3084 snapshots; capture read time was `{'median': 28.773950019967742, 'p95': 51.2985999812372, 'max': 78.1522000033874}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 4 phase-counter discontinuities were excluded; 4460 decisions retained at least one contact-enabled body (maximum 22).
- The terminal-threat heuristic covered 4712 decisions with horizon counts `{'0': 52, '10': 4184, '32': 476}`; it reported 1 collision and 39 sub-safety-clearance warnings, and relaxed 476 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 52, '3': 469, '4': 3144, '5': 1047}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 73, '3': 316, '4': 4323}`.
- Adaptive delay supports were `{'1,2,3': 39, '1,2,3,4,5,6': 1, '2,3': 13, '2,3,4': 35, '2,3,4,5': 675, '2,3,4,5,6': 1203, '3,4': 16, '3,4,5': 291, '3,4,5,6': 2439}`; 24 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 61/212.
- Robust viability supplied 4597 available policy queries (98 had new delay support outside the cached policy), constrained 2906 decisions, and exposed 1117 empty queried action sets. Recovery guidance was available/selected on 536/330 empty-kernel queries; distant-kernel guidance was available/selected on 560/555. Safe-action count, selected repair-volume, and selected recovery-distance statistics were `{'median': 9.0, 'p95': 17.0, 'max': 17.0}` `{'median': 46.0, 'p95': 153.0, 'max': 153.0}`, and `{'median': 80.0, 'p95': 224.57070156189118, 'max': 373.52376095772007}`.
- The rolling worker produced 607 unique policies with solve-time statistics `{'median': 220.53250001044944, 'p95': 351.4007999910973, 'max': 438.12169999000616}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1786.0}`. Policy status counts were `{'pending_future_epoch': 42, 'queryable': 4597, 'expired': 9}`; 51 robust-mode decisions had no query.
- Of 2498 unambiguous output transitions, 2195 (0.879) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 4}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 3 hit windows with a positive warning lead; those leads were `[7, 7, 0, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.014 during the 60 frames preceding a hit versus 0.098 outside those windows.
- Soft recovery was selected on 0.042 of alive decisions in the 60-frame pre-hit windows versus 0.075 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 3.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
