# TH08 Stage 2 No-Bomb Practice Review: lunatic_route2_stage2_unattended_20260724_052616

## Scope And Integrity

- Valid practice scope: `3..23620` (6219 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 2, at `[8243, 22211]`.
- Hard no-Bomb verification: **PASS** across 6219 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S1-F8243-T1`. It occurred during spell 16 `声符「木菟咆哮」` at player (17.515, 414.667), with 815 bullets and 0 lasers. The projectile model reported pipeline clearance -0.934.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 1 |
| `observed_bullet_overlap` | 1 |

Contributing factors:

- `fast_mode`: 1
- `playfield_boundary`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 8243 | 16 声符「木菟咆哮」 | (17.515, 414.667) | `stay` | 815/0 | -0.934/-1.359 | 4f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 22211 | 28 夜盲「夜雀の歌」 | (37.184, 429.943) | `up_left_fast` | 595/0 | -2.045/-2.045 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 0 | 3537 | 3449 | 1360 | 69 | 1798 | 441 | 266.224 | 0.091 |
| 16 声符「木菟咆哮」 | 1 | 563 | 553 | 152 | 0 | 370 | 71 | 226.689 | 0.129 |
| 20 | 0 | 718 | 710 | 442 | 8 | 229 | 90 | 177.947 | 0.235 |
| 24 | 0 | 684 | 671 | 265 | 0 | 399 | 88 | 191.499 | 0.161 |
| 28 夜盲「夜雀の歌」 | 1 | 717 | 703 | 353 | 10 | 331 | 91 | 183.350 | 0.265 |

## Interpretation

- Retained witnesses classify 1 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 22.648 ms median and 41.096 ms p95.
- The full enemy sensor produced 3863 snapshots; capture read time was `{'median': 24.994300008984283, 'p95': 48.65790001349524, 'max': 94.96720001334324}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 3 phase-counter discontinuities were excluded; 4840 decisions retained at least one contact-enabled body (maximum 18).
- The terminal-threat heuristic covered 6219 decisions with horizon counts `{'0': 88, '10': 5813, '32': 318}`; it reported 3 collision and 44 sub-safety-clearance warnings, and relaxed 318 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 52, '3': 289, '4': 5176, '5': 702}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 66, '3': 1048, '4': 5105}`.
- Adaptive delay supports were `{'1,2,3': 35, '1,2,3,4': 7, '1,2,3,4,5,6': 6, '2,3': 34, '2,3,4': 294, '2,3,4,5': 651, '2,3,4,5,6': 1694, '3,4': 65, '3,4,5': 435, '3,4,5,6': 2998}`; 40 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 67/283.
- Robust viability supplied 6086 available policy queries (87 had new delay support outside the cached policy), constrained 3127 decisions, and exposed 2572 empty queried action sets. Recovery guidance was available/selected on 716/398 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 15.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 781 unique policies with solve-time statistics `{'median': 225.45230001560412, 'p95': 384.3879000050947, 'max': 465.94130000448786}` and first-observed ages `{'median': 3.0, 'p95': 10.0, 'max': 1799.0}`. Policy status counts were `{'pending_future_epoch': 40, 'queryable': 6087, 'expired': 10}`; 51 robust-mode decisions had no query.
- Of 3257 unambiguous output transitions, 2873 (0.882) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 1, 'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 2 hit windows with a positive warning lead; those leads were `[7, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.371 during the 60 frames preceding a hit versus 0.136 outside those windows.
- Soft recovery was selected on 0.029 of alive decisions in the 60-frame pre-hit windows versus 0.068 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 116.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Experiment Decision

This physically accepts CE-0070's clamped-alias certificate downgrade. Total
hits fell from five to two, nonspell from four to zero, and spell 20 from one
to zero. The controller preserved 3/4-frame cadence, 22.65/41.10-ms local
planning, hard no-Bomb behavior, automatic transitions, and exact process
termination.

It is not a clean Stage-2 result. The spell-16 frame-8,243 hit was an off-grid
singleton-mask failure retained as CE-0071. The spell-28 frame-22,211 hit
entered an empty global kernel and remains the next recovery-policy target.
