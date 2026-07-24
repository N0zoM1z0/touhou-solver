# TH08 Stage 2 No-Bomb Practice Review: lunatic_route2_stage2_unattended_20260724_091120

## Scope And Integrity

- Valid practice scope: `1..23129` (5723 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 3, at `[4284, 5040, 17491]`.
- Hard no-Bomb verification: **PASS** across 5723 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S1-F4284-T1`. It occurred during a nonspell phase at player (376.000, 379.861), with 77 bullets and 0 lasers. The projectile model reported pipeline clearance -3.061.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 2
- `playfield_boundary`: 2
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4284 | nonspell | (376.000, 379.861) | `stay` | 77/0 | -3.061/-3.061 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 5040 | nonspell | (36.999, 361.277) | `up_fast` | 259/0 | 13.956/9.378 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 17491 | nonspell | (117.596, 428.540) | `left_fast` | 231/0 | -0.862/-0.862 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 3234 | 3161 | 1090 | 30 | 2024 | 420 | 260.138 | 0.053 |
| 16 | 0 | 541 | 530 | 141 | 0 | 362 | 71 | 215.481 | 0.111 |
| 20 | 0 | 641 | 628 | 348 | 0 | 262 | 89 | 178.740 | 0.211 |
| 24 | 0 | 670 | 656 | 219 | 0 | 425 | 86 | 203.446 | 0.146 |
| 28 | 0 | 637 | 630 | 416 | 0 | 202 | 90 | 182.166 | 0.185 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 24.424 ms median and 42.302 ms p95.
- The full enemy sensor produced 3860 snapshots; capture read time was `{'median': 26.47449998767115, 'p95': 50.76460001873784, 'max': 79.39890000852756}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 11.0}` frames, and 2 phase-counter discontinuities were excluded; 4433 decisions retained at least one contact-enabled body (maximum 18).
- The terminal-threat heuristic covered 5723 decisions with horizon counts `{'0': 51, '10': 5183, '32': 489}`; it reported 4 collision and 50 sub-safety-clearance warnings, and relaxed 96 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 50, '3': 242, '4': 3881, '5': 1550}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 61, '3': 241, '4': 5414, '5': 7}`.
- Adaptive delay supports were `{'1,2,3': 25, '1,2,3,4': 1, '2,3': 113, '2,3,4': 79, '2,3,4,5': 58, '2,3,4,5,6': 444, '3,4': 40, '3,4,5': 460, '3,4,5,6': 4503}`; 74 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 79/347.
- Robust viability supplied 5605 available policy queries (30 had new delay support outside the cached policy), constrained 3275 decisions, and exposed 2214 empty queried action sets. Recovery guidance was available/selected on 802/422 empty-kernel queries; distant-kernel guidance was available/selected on 1179/1141. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 6.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 31.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 101.19288512538814, 'p95': 336.0, 'max': 499.85597925802585}`, and `{'median': 0.0, 'p95': 14.241926193237305, 'max': 42.34314584732056}`.
- The rolling worker produced 756 unique policies with solve-time statistics `{'median': 217.988599993987, 'p95': 356.15779997897334, 'max': 477.80160000547767}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1794.0}`. Policy status counts were `{'pending_future_epoch': 35, 'queryable': 5604, 'expired': 11}`; 45 robust-mode decisions had no query.
- Of 3205 unambiguous output transitions, 2735 (0.853) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 1, 'global_viability_kernel_exhausted_before_hit': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 2 hit windows with a positive warning lead; those leads were `[4, 0, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.054 during the 60 frames preceding a hit versus 0.105 outside those windows.
- Mean selected control-reserve deficit was 0.991 during the 60 frames preceding a hit versus 0.485 outside those windows.
- Soft recovery was selected on 0.071 of alive decisions in the 60-frame pre-hit windows versus 0.078 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 117.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
