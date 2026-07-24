# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260724_132007

## Scope And Integrity

- Valid practice scope: `2..28026` (5561 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 15, at `[745, 2320, 2631, 5923, 8067, 9135, 13794, 15526, 15945, 17140, 26315, 26710, 27028, 27348, 27696]`.
- Hard no-Bomb verification: **PASS** across 5561 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F745-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 184 bullets and 0 lasers. The projectile model reported pipeline clearance -1.521.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 5 |
| `active_laser_without_observed_overlap` | 3 |

Contributing factors:

- `playfield_boundary`: 12
- `fast_mode`: 8
- `corridor_deadline_miss`: 7
- `action_lag_over_model`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 745 | nonspell | (376.000, 432.000) | `up_left_fast` | 184/0 | -1.521/-1.521 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2320 | nonspell | (376.000, 432.000) | `left` | 347/0 | -3.070/-3.070 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2631 | nonspell | (8.000, 136.919) | `up_right_fast` | 162/0 | 0.605/-0.396 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 5923 | 35 産霊「ファーストピラミッド」 | (366.485, 24.485) | `left_fast` | 305/0 | -1.508/-1.654 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8067 | nonspell | (376.000, 342.518) | `up_fast` | 695/0 | -2.792/-2.792 | 6f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9135 | nonspell | (8.000, 420.000) | `up_fast` | 493/0 | -0.425/-3.625 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13794 | nonspell | (238.124, 421.888) | `right` | 429/0 | -4.951/-4.951 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 15526 | 38 始符「エフェメラリティ137」 | (8.000, 299.744) | `stay` | 289/0 | -8.119/-8.119 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 15945 | 38 始符「エフェメラリティ137」 | (15.373, 432.000) | `right_fast` | 195/0 | -9.949/-9.949 | 5f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 17140 | 38 始符「エフェメラリティ137」 | (9.359, 323.217) | `up_fast` | 426/0 | -1.689/-1.689 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26315 | 50 虚史「幻想郷伝説」 | (261.322, 432.000) | `right` | 240/180 | 9.104/7.062 | 0f/0f | `active_laser_without_observed_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26710 | 50 虚史「幻想郷伝説」 | (376.000, 432.000) | `down_right_fast` | 319/200 | -3.243/-3.534 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27028 | 50 虚史「幻想郷伝説」 | (82.399, 388.300) | `up` | 303/200 | -5.023/-5.023 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27348 | 50 虚史「幻想郷伝説」 | (217.007, 429.700) | `up` | 288/200 | 8.089/-5.148 | 0f/0f | `active_laser_without_observed_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27696 | 50 虚史「幻想郷伝説」 | (136.704, 432.000) | `down_left` | 302/196 | 7.732/-4.089 | 0f/0f | `active_laser_without_observed_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 3052 | 2960 | 1330 | 0 | 1592 | 497 | 325.184 | 0.323 |
| 35 産霊「ファーストピラミッド」 | 1 | 584 | 573 | 389 | 0 | 181 | 117 | 253.899 | 0.243 |
| 38 始符「エフェメラリティ137」 | 3 | 589 | 578 | 217 | 0 | 353 | 103 | 271.455 | 0.167 |
| 42 | 0 | 492 | 478 | 387 | 0 | 87 | 108 | 229.371 | 0.395 |
| 46 | 0 | 547 | 536 | 390 | 0 | 130 | 119 | 277.538 | 0.375 |
| 50 虚史「幻想郷伝説」 | 5 | 297 | 288 | 153 | 0 | 129 | 73 | 413.871 | 0.137 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 27.704 ms median and 47.955 ms p95.
- The full enemy sensor produced 4488 snapshots; capture read time was `{'median': 41.10104999563191, 'p95': 69.76029998622835, 'max': 327.045400015777}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 28.0}` frames, and 2 phase-counter discontinuities were excluded; 4402 decisions retained at least one contact-enabled body (maximum 12).
- The terminal-threat heuristic covered 5561 decisions with horizon counts `{'0': 48, '10': 4995, '32': 518}`; it reported 2 collision and 67 sub-safety-clearance warnings, and relaxed 75 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 49, '3': 167, '4': 668, '5': 4319, '6': 358}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 61, '3': 173, '4': 2479, '5': 2657, '6': 191}`.
- Adaptive delay supports were `{'1,2,3': 36, '1,2,3,4': 27, '2,3': 13, '2,3,4': 21, '2,3,4,5': 84, '2,3,4,5,6': 219, '3,4,5': 132, '3,4,5,6': 4445, '4,5,6': 582, '5,6': 2}`; 144 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 88/202.
- Robust viability supplied 5413 available policy queries (0 had new delay support outside the cached policy), constrained 2472 decisions, and exposed 2866 empty queried action sets. Recovery guidance was available/selected on 937/520 empty-kernel queries; distant-kernel guidance was available/selected on 1833/1762. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 4.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 101.19288512538814, 'p95': 289.77232442039735, 'max': 437.0080090799252}`, and `{'median': 4.0, 'p95': 27.059947967529297, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 674, '1': 732, '2': 717, '3': 683, '4': 628, '5': 683, '6': 669, '7': 627}`.
- The rolling worker produced 1017 unique policies with solve-time statistics `{'median': 300.8634000143502, 'p95': 461.0570000077132, 'max': 604.5472999976482}` and first-observed ages `{'median': 6.0, 'p95': 15.0, 'max': 3595.0}`. Policy status counts were `{'pending_future_epoch': 30, 'queryable': 5411, 'expired': 19}`; 47 robust-mode decisions had no query.
- Of 2972 unambiguous output transitions, 2559 (0.861) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 14, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[8, 4, 5, 7, 10, 11, 7, 4, 14, 0, 0, 6, 0, 0, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.422 during the 60 frames preceding a hit versus 0.304 outside those windows.
- Mean selected control-reserve deficit was 7.391 during the 60 frames preceding a hit versus 2.788 outside those windows.
- Soft recovery was selected on 0.054 of alive decisions in the 60-frame pre-hit windows versus 0.098 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 14.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
