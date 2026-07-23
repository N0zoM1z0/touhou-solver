# TH08 Stage 1 No-Bomb Practice Review: lunatic_route2_stage1_unattended_20260724_063701

## Scope And Integrity

- Valid practice scope: `2..21037` (4771 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 4, at `[2571, 13676, 14278, 14695]`.
- Hard no-Bomb verification: **PASS** across 4771 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S0-F2571-T1`. It occurred during a nonspell phase at player (12.978, 33.703), with 75 bullets and 0 lasers. The projectile model reported pipeline clearance -1.911.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 3 |
| `modeled_committed_prefix_collision` | 1 |

Contributing factors:

- `fast_mode`: 3
- `corridor_deadline_miss`: 1
- `playfield_boundary`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2571 | nonspell | (12.978, 33.703) | `up` | 75/0 | -1.911/-20.014 | 8f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13676 | 5 灯符「ファイヤフライフェノメノン」 | (369.727, 403.772) | `up_fast` | 472/0 | -0.055/-4.604 | 4f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14278 | 5 灯符「ファイヤフライフェノメノン」 | (372.049, 426.883) | `left_fast` | 382/0 | -3.944/-3.944 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14695 | 5 灯符「ファイヤフライフェノメノン」 | (24.534, 427.941) | `right_fast` | 652/0 | 4.352/-0.355 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 1 | 2894 | 2811 | 573 | 31 | 2006 | 359 | 225.933 | 0.071 |
| 1 | 0 | 609 | 590 | 358 | 0 | 196 | 82 | 128.791 | 0.229 |
| 5 灯符「ファイヤフライフェノメノン」 | 3 | 615 | 606 | 171 | 0 | 423 | 80 | 213.727 | 0.064 |
| 9 | 0 | 653 | 646 | 81 | 0 | 479 | 89 | 249.667 | 0.161 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 23.447 ms median and 41.205 ms p95.
- The full enemy sensor produced 3091 snapshots; capture read time was `{'median': 27.544099983060732, 'p95': 50.07529997965321, 'max': 79.09650000510737}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 3 phase-counter discontinuities were excluded; 4539 decisions retained at least one contact-enabled body (maximum 20).
- The terminal-threat heuristic covered 4771 decisions with horizon counts `{'0': 52, '10': 4381, '32': 338}`; it reported 0 collision and 29 sub-safety-clearance warnings, and relaxed 338 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 47, '3': 430, '4': 3631, '5': 663}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 88, '3': 354, '4': 4329}`.
- Adaptive delay supports were `{'1,2,3': 25, '1,2,3,4': 1, '2,3': 98, '2,3,4': 45, '2,3,4,5': 573, '2,3,4,5,6': 1245, '3,4': 21, '3,4,5': 399, '3,4,5,6': 2364}`; 35 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 50/242.
- Robust viability supplied 4653 available policy queries (31 had new delay support outside the cached policy), constrained 3104 decisions, and exposed 1183 empty queried action sets. Recovery guidance was available/selected on 408/284 empty-kernel queries; distant-kernel guidance was available/selected on 738/725. Safe-action count, selected repair-volume, and selected recovery-distance statistics were `{'median': 9.0, 'p95': 17.0, 'max': 17.0}` `{'median': 53.0, 'p95': 153.0, 'max': 153.0}`, and `{'median': 115.37764081484765, 'p95': 298.9046670763105, 'max': 351.2719744016024}`.
- The rolling worker produced 610 unique policies with solve-time statistics `{'median': 218.7549000082072, 'p95': 347.95570001006126, 'max': 432.0791999925859}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1786.0}`. Policy status counts were `{'pending_future_epoch': 37, 'queryable': 4651, 'expired': 14}`; 49 robust-mode decisions had no query.
- Of 2639 unambiguous output transitions, 2322 (0.880) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 4}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 4 hit windows with a positive warning lead; those leads were `[8, 10, 3, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.173 during the 60 frames preceding a hit versus 0.104 outside those windows.
- Soft recovery was selected on 0.027 of alive decisions in the 60-frame pre-hit windows versus 0.065 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Experiment Decision

This complete run is **rejected as an algorithm acceptance variant**. Distant
recovery was available on 738 queries and total hits remained four, but the
new priority existed only in final selection. At frame 2,512 the policy
reported `down_left_fast=32` pixels as the best recovery distance while the
beam issued `up=81.58`; intermediate pruning had already removed the better
first action. CE-0075 retains this failure and its minimized regression.

The physical run remains valid discovery evidence. Its 3/4-frame cadence
shows the query cost was serviceable, and its changed trajectory supplied the
pruning counterexample.
