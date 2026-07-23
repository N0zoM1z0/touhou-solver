# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_025622

## Scope And Integrity

- Valid practice scope: `3..3303` (981 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 1, at `[2045]`.
- Hard no-Bomb verification: **PASS** across 981 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2045-T1`. It occurred during a nonspell phase at player (364.000, 428.565), with 717 bullets and 0 lasers. The projectile model reported pipeline clearance -0.311.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2045 | nonspell | (364.000, 428.565) | `left` | 717/0 | -0.311/-1.068 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 1 | 981 | 945 | 317 | 26 | 602 | 64 | 249.319 | 0.157 |

## Interpretation

- Retained witnesses classify 1 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 14.615 ms median and 31.667 ms p95.
- Modeled action hold counts were `{'2': 10, '3': 171, '4': 696, '5': 104}` overall.
- Modeled uncontrollable-prefix counts were `{'3': 349, '4': 632}`.
- Adaptive delay supports were `{'2,3': 1, '2,3,4': 18, '2,3,4,5': 18, '2,3,4,5,6': 143, '3,4': 10, '3,4,5': 251, '3,4,5,6': 540}`; 10 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 19/43.
- Robust viability supplied 945 available policy queries (26 had new delay support outside the cached policy), constrained 602 decisions, and exposed 317 empty queried action sets. Recovery guidance was available/selected on 64/34 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 10.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 44.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 64 unique policies with solve-time statistics `{'median': 249.31939999805763, 'p95': 359.0958999993745, 'max': 439.48210001690313}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 5.0}`. Policy status counts were `{'pending_future_epoch': 28, 'queryable': 944, 'expired': 1}`; 28 robust-mode decisions had no query.
- Of 505 unambiguous output transitions, 442 (0.875) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 1 hit windows with a positive warning lead; those leads were `[7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.059 during the 60 frames preceding a hit versus 0.159 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.041 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 128.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Discard Reason

This is a deliberately terminated latency experiment, not a completed Stage-5
trial. Continuous background full-pool reads still contended with the main
`ReadProcessMemory` stream: at frames 2,091..2,132 total read remained
18.51..32.31 ms while enemy snapshots were only 3..5 frames old. The process
was identity-targeted and killed at frame 3,303 after one hit. CE-0060 now
throttles background scans to one submission per 16 manager frames.
