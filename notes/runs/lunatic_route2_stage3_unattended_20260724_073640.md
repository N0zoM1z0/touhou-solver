# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260724_073640

## Scope And Integrity

- Valid practice scope: `2..27924` (6398 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[3088, 4217, 6856, 8156, 8625, 8957, 14044, 18989, 23043, 26306, 26900, 27225]`.
- Hard no-Bomb verification: **PASS** across 6398 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F3088-T1`. It occurred during a nonspell phase at player (8.850, 245.048), with 201 bullets and 0 lasers. The projectile model reported pipeline clearance -23.133.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 3 |
| `observed_laser_overlap` | 1 |

Contributing factors:

- `fast_mode`: 8
- `action_lag_over_model`: 3
- `playfield_boundary`: 3
- `corridor_deadline_miss`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3088 | nonspell | (8.850, 245.048) | `up_fast` | 201/0 | -23.133/-23.133 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 4217 | nonspell | (371.400, 426.145) | `up_fast` | 270/0 | -1.896/-1.896 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 6856 | 35 産霊「ファーストピラミッド」 | (370.527, 426.727) | `right_fast` | 414/0 | -3.714/-3.714 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8156 | nonspell | (374.071, 334.236) | `stay` | 921/0 | -2.018/-2.018 | 0f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8625 | nonspell | (367.515, 29.841) | `down_left_fast` | 232/0 | -3.593/-3.723 | 4f/21f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8957 | nonspell | (367.290, 409.126) | `down_left` | 361/0 | -1.666/-1.666 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14044 | nonspell | (364.512, 419.193) | `down_left_fast` | 431/0 | 0.200/-0.533 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18989 | 42 野符「GHQクライシス」 | (18.256, 426.015) | `right_fast` | 483/0 | -1.321/-1.321 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23043 | nonspell | (363.162, 420.336) | `up_fast` | 407/0 | -3.977/-3.977 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26306 | 50 虚史「幻想郷伝説」 | (44.242, 419.250) | `left` | 247/190 | -1.537/-1.537 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26900 | 50 虚史「幻想郷伝説」 | (17.758, 422.242) | `right` | 231/190 | -4.301/-4.301 | 0f/0f | `observed_laser_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 27225 | 50 虚史「幻想郷伝説」 | (258.272, 428.000) | `up_right_fast` | 299/200 | -3.699/-3.937 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 3523 | 3421 | 1293 | 47 | 1761 | 451 | 233.916 | 0.123 |
| 35 産霊「ファーストピラミッド」 | 1 | 678 | 665 | 408 | 11 | 207 | 90 | 182.087 | 0.124 |
| 38 | 0 | 605 | 594 | 267 | 0 | 266 | 80 | 180.852 | 0.091 |
| 42 野符「GHQクライシス」 | 1 | 575 | 567 | 389 | 0 | 168 | 81 | 161.580 | 0.178 |
| 46 | 0 | 707 | 698 | 561 | 8 | 106 | 95 | 191.500 | 0.239 |
| 50 虚史「幻想郷伝説」 | 3 | 310 | 304 | 121 | 6 | 142 | 78 | 260.604 | 0.200 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 1 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 24.087 ms median and 47.197 ms p95.
- The full enemy sensor produced 4246 snapshots; capture read time was `{'median': 30.43929999694228, 'p95': 62.21580001874827, 'max': 273.9226999983657}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 20.0}` frames, and 3 phase-counter discontinuities were excluded; 5157 decisions retained at least one contact-enabled body (maximum 8).
- The terminal-threat heuristic covered 6398 decisions with horizon counts `{'0': 60, '10': 5838, '32': 500}`; it reported 3 collision and 77 sub-safety-clearance warnings, and relaxed 500 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 51, '3': 283, '4': 4462, '5': 1369, '6': 233}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 42, '3': 629, '4': 5476, '5': 49, '6': 202}`.
- Adaptive delay supports were `{'1,2,3,4,5': 16, '1,2,3,4,5,6': 48, '2,3': 2, '2,3,4': 168, '2,3,4,5': 587, '2,3,4,5,6': 327, '3,4': 8, '3,4,5': 439, '3,4,5,6': 4666, '4,5,6': 45, '5,6': 92}`; 84 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 172/368.
- Robust viability supplied 6249 available policy queries (72 had new delay support outside the cached policy), constrained 2650 decisions, and exposed 3039 empty queried action sets. Recovery guidance was available/selected on 1182/607 empty-kernel queries; distant-kernel guidance was available/selected on 1771/1750. Safe-action count, selected repair-volume, and selected recovery-distance statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}` `{'median': 5.0, 'p95': 153.0, 'max': 153.0}`, and `{'median': 80.0, 'p95': 240.0, 'max': 381.65953414005}`.
- The rolling worker produced 875 unique policies with solve-time statistics `{'median': 214.37719999812543, 'p95': 329.6859999827575, 'max': 446.4768999896478}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1796.0}`. Policy status counts were `{'pending_future_epoch': 42, 'queryable': 6251, 'expired': 14}`; 58 robust-mode decisions had no query.
- Of 3801 unambiguous output transitions, 3298 (0.868) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'late_collision_after_positive_causal_margin': 3, 'global_viability_kernel_exhausted_before_hit': 9}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 7 hit windows with a positive warning lead; those leads were `[0, 6, 7, 22, 21, 0, 11, 5, 6, 0, 0, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.222 during the 60 frames preceding a hit versus 0.140 outside those windows.
- Soft recovery was selected on 0.123 of alive decisions in the 60-frame pre-hit windows versus 0.098 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
