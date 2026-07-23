# TH08 Stage 1 No-Bomb Practice Review: lunatic_route2_stage1_unattended_20260724_050922

## Scope And Integrity

- Valid practice scope: `2..20786` (4850 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 4, at `[4814, 5332, 14604, 19823]`.
- Hard no-Bomb verification: **PASS** across 4850 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S0-F4814-T1`. It occurred during spell 1 `蛍符「地上の彗星」` at player (283.462, 411.957), with 393 bullets and 0 lasers. The projectile model reported pipeline clearance 0.359.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 2 |
| `observed_bullet_overlap` | 2 |

Contributing factors:

- `fast_mode`: 2
- `playfield_boundary`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4814 | 1 蛍符「地上の彗星」 | (283.462, 411.957) | `down_fast` | 393/0 | 0.359/-1.367 | 2f/2f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 5332 | 1 蛍符「地上の彗星」 | (9.852, 426.653) | `up_fast` | 402/0 | -3.332/-3.332 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14604 | 5 灯符「ファイヤフライフェノメノン」 | (13.274, 417.544) | `up_right` | 379/0 | -0.537/-0.537 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19823 | 9 蠢符「ナイトバグトルネード」 | (366.322, 424.728) | `stay` | 181/0 | -1.647/-1.793 | 5f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 0 | 2929 | 2859 | 575 | 61 | 2238 | 357 | 234.610 | 0.116 |
| 1 蛍符「地上の彗星」 | 2 | 623 | 603 | 301 | 0 | 302 | 76 | 139.235 | 0.273 |
| 5 灯符「ファイヤフライフェノメノン」 | 1 | 590 | 579 | 188 | 8 | 386 | 77 | 205.192 | 0.122 |
| 9 蠢符「ナイトバグトルネード」 | 1 | 708 | 702 | 100 | 0 | 602 | 91 | 249.973 | 0.167 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 22.035 ms median and 40.612 ms p95.
- The full enemy sensor produced 2963 snapshots; capture read time was `{'median': 27.547800011234358, 'p95': 50.815299997339025, 'max': 107.77549998601899}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 11.0}` frames, and 3 phase-counter discontinuities were excluded; 4614 decisions retained at least one contact-enabled body (maximum 17).
- The terminal-threat heuristic covered 4850 decisions with horizon counts `{'0': 49, '10': 4704, '32': 97}`; it reported 3 collision and 17 sub-safety-clearance warnings.
- Modeled action hold counts were `{'2': 59, '3': 453, '4': 3980, '5': 358}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 66, '3': 1103, '4': 3681}`.
- Adaptive delay supports were `{'1,2,3': 42, '1,2,3,4': 8, '2,3': 108, '2,3,4': 206, '2,3,4,5': 1037, '2,3,4,5,6': 1101, '3,4': 37, '3,4,5': 583, '3,4,5,6': 1728}`; 17 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 36/220.
- Robust viability supplied 4743 available policy queries (69 had new delay support outside the cached policy), constrained 3528 decisions, and exposed 1164 empty queried action sets. Recovery guidance was available/selected on 355/193 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 9.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 42.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 601 unique policies with solve-time statistics `{'median': 223.82980000111274, 'p95': 344.90850000292994, 'max': 439.05309998081066}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1806.0}`. Policy status counts were `{'pending_future_epoch': 38, 'queryable': 4743, 'expired': 11}`; 49 robust-mode decisions had no query.
- Of 2461 unambiguous output transitions, 2170 (0.882) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 3, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 4 hit windows with a positive warning lead; those leads were `[2, 9, 7, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.316 during the 60 frames preceding a hit versus 0.136 outside those windows.
- Soft recovery was selected on 0.013 of alive decisions in the 60-frame pre-hit windows versus 0.041 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 8.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Experiment Decision

This was the random physical acceptance gate for CE-0069's
boundary-conditional terminal warning. It activated on 97/4,850 decisions
while retaining 3/4-frame median/p95 cadence and 22.04/40.61-ms planning.
Unlike the rejected always-on Stage-4A trial, it did not impose a measurable
control-cadence regression.

The aggregate result is neutral: four hits versus four in the prior Stage-1
baseline. Nonspell improved from two hits to zero, spell 1 regressed from zero
to two, and spells 5 and 9 remained at one each. Accept the conditional
runtime gate, but do not claim a survival improvement. The retained failure
mechanism is global viability-kernel exhaustion before three hits and local
robust-action exhaustion before one.
