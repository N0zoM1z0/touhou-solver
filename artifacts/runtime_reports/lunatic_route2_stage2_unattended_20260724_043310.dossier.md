# TH08 Stage 2 No-Bomb Practice Review: lunatic_route2_stage2_unattended_20260724_043310

## Scope And Integrity

- Valid practice scope: `2..23279` (6110 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 5, at `[3548, 5243, 13517, 16736, 17664]`.
- Hard no-Bomb verification: **PASS** across 6110 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S1-F3548-T1`. It occurred during a nonspell phase at player (369.774, 27.384), with 214 bullets and 0 lasers. The projectile model reported pipeline clearance -3.705.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 4 |
| `modeled_committed_prefix_collision` | 1 |

Contributing factors:

- `fast_mode`: 3
- `corridor_deadline_miss`: 2
- `playfield_boundary`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3548 | nonspell | (369.774, 27.384) | `down_fast` | 214/0 | -3.705/-3.705 | 4f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 5243 | nonspell | (200.646, 418.374) | `up_fast` | 194/0 | 3.490/-2.315 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13517 | 20 猛毒「毒蛾の暗闇演舞」 | (304.104, 429.644) | `stay` | 523/0 | -3.503/-3.503 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 16736 | nonspell | (369.960, 423.280) | `stay` | 788/0 | -2.400/-2.600 | 2f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 17664 | nonspell | (358.704, 424.655) | `left_fast` | 132/0 | -4.726/-4.726 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 3563 | 3489 | 1197 | 17 | 2275 | 442 | 276.136 | 0.105 |
| 16 | 0 | 543 | 535 | 128 | 0 | 407 | 71 | 222.197 | 0.192 |
| 20 猛毒「毒蛾の暗闇演舞」 | 1 | 623 | 614 | 250 | 7 | 361 | 76 | 182.252 | 0.277 |
| 24 | 0 | 709 | 694 | 233 | 12 | 454 | 87 | 194.614 | 0.211 |
| 28 | 0 | 672 | 665 | 419 | 8 | 246 | 90 | 181.060 | 0.339 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 22.516 ms median and 41.569 ms p95.
- The full enemy sensor produced 3837 snapshots; capture read time was `{'median': 25.962499988963827, 'p95': 51.134599983925, 'max': 85.54890000959858}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 11.0}` frames, and 3 phase-counter discontinuities were excluded; 4651 decisions retained at least one contact-enabled body (maximum 17).
- Modeled action hold counts were `{'2': 53, '3': 461, '4': 4925, '5': 671}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 50, '3': 644, '4': 5416}`.
- Adaptive delay supports were `{'1,2,3': 10, '1,2,3,4': 17, '2,3': 160, '2,3,4': 19, '2,3,4,5': 262, '2,3,4,5,6': 1796, '3,4': 90, '3,4,5': 376, '3,4,5,6': 3380}`; 25 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 64/333.
- Robust viability supplied 5997 available policy queries (44 had new delay support outside the cached policy), constrained 3743 decisions, and exposed 2227 empty queried action sets. Recovery guidance was available/selected on 519/298 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 7.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 35.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 766 unique policies with solve-time statistics `{'median': 224.86435000610072, 'p95': 386.28659999812953, 'max': 449.7261999931652}` and first-observed ages `{'median': 3.0, 'p95': 10.0, 'max': 1794.0}`. Policy status counts were `{'pending_future_epoch': 40, 'queryable': 5996, 'expired': 11}`; 50 robust-mode decisions had no query.
- Of 3092 unambiguous output transitions, 2658 (0.860) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 3, 'robust_action_set_exhausted_before_hit': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 5 hit windows with a positive warning lead; those leads were `[6, 6, 8, 7, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.270 during the 60 frames preceding a hit versus 0.170 outside those windows.
- Soft recovery was selected on 0.070 of alive decisions in the 60-frame pre-hit windows versus 0.047 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 85.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
