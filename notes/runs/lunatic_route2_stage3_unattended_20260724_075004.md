# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260724_075004

## Scope And Integrity

- Valid practice scope: `2..27757` (6520 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 11, at `[1940, 2430, 8147, 15399, 15913, 16400, 22345, 23128, 26180, 26938, 27645]`.
- Hard no-Bomb verification: **PASS** across 6520 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F1940-T1`. It occurred during a nonspell phase at player (20.919, 100.247), with 413 bullets and 0 lasers. The projectile model reported pipeline clearance -0.343.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 4 |
| `active_laser_without_observed_overlap` | 2 |

Contributing factors:

- `fast_mode`: 5
- `corridor_deadline_miss`: 3
- `action_lag_over_model`: 2
- `playfield_boundary`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1940 | nonspell | (20.919, 100.247) | `up` | 413/0 | -0.343/-0.343 | 0f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2430 | nonspell | (374.033, 311.181) | `down_left_fast` | 372/0 | -2.390/-2.390 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8147 | nonspell | (199.104, 418.865) | `stay` | 546/0 | -3.592/-3.592 | 4f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 15399 | 38 始符「エフェメラリティ137」 | (69.627, 420.772) | `up_right_fast` | 237/0 | -2.341/-2.458 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 15913 | 38 始符「エフェメラリティ137」 | (370.068, 422.094) | `up_fast` | 198/0 | -6.152/-7.386 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 16400 | 38 始符「エフェメラリティ137」 | (14.812, 421.312) | `stay` | 206/0 | -2.439/-2.625 | 8f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22345 | nonspell | (8.545, 423.182) | `up_right` | 293/0 | -0.314/-1.922 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23128 | nonspell | (365.109, 420.253) | `up_fast` | 73/0 | -1.301/-1.388 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26180 | 50 虚史「幻想郷伝説」 | (82.824, 383.584) | `down_left_fast` | 258/190 | 5.375/0.683 | 0f/0f | `active_laser_without_observed_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26938 | 50 虚史「幻想郷伝説」 | (37.661, 419.863) | `up` | 333/192 | 3.664/3.664 | 0f/0f | `active_laser_without_observed_overlap` | `unresolved_planner_failure` |
| discovery | 27645 | 50 虚史「幻想郷伝説」 | (17.571, 424.914) | `stay` | 329/200 | -2.106/-2.147 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 3515 | 3422 | 1328 | 35 | 1814 | 445 | 235.808 | 0.155 |
| 35 | 0 | 717 | 699 | 448 | 5 | 204 | 90 | 175.662 | 0.170 |
| 38 始符「エフェメラリティ137」 | 3 | 668 | 656 | 255 | 0 | 389 | 84 | 185.825 | 0.052 |
| 42 | 0 | 590 | 580 | 476 | 0 | 90 | 80 | 173.205 | 0.268 |
| 46 | 0 | 667 | 661 | 544 | 0 | 87 | 94 | 193.474 | 0.248 |
| 50 虚史「幻想郷伝説」 | 3 | 363 | 356 | 195 | 0 | 132 | 80 | 272.929 | 0.312 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 22.901 ms median and 44.744 ms p95.
- The full enemy sensor produced 4283 snapshots; capture read time was `{'median': 29.497000010451302, 'p95': 60.01059999107383, 'max': 235.68559999694116}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 23.0}` frames, and 3 phase-counter discontinuities were excluded; 5166 decisions retained at least one contact-enabled body (maximum 8).
- The terminal-threat heuristic covered 6520 decisions with horizon counts `{'0': 54, '10': 6093, '32': 373}`; it reported 0 collision and 63 sub-safety-clearance warnings, and relaxed 373 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 47, '3': 295, '4': 4861, '5': 1053, '6': 264}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 61, '3': 556, '4': 5654, '5': 26, '6': 223}`.
- Adaptive delay supports were `{'1,2,3': 41, '1,2,3,4': 7, '1,2,3,4,5,6': 5, '2,3': 23, '2,3,4': 114, '2,3,4,5': 644, '2,3,4,5,6': 800, '3,4': 18, '3,4,5': 1095, '3,4,5,6': 3625, '4,5,6': 148}`; 94 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 142/415.
- Robust viability supplied 6374 available policy queries (40 had new delay support outside the cached policy), constrained 2716 decisions, and exposed 3246 empty queried action sets. Recovery guidance was available/selected on 1327/604 empty-kernel queries; distant-kernel guidance was available/selected on 1835/1817. Safe-action count, selected repair-volume, and selected recovery-distance statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}` `{'median': 3.0, 'p95': 153.0, 'max': 153.0}`, and `{'median': 81.58431221748455, 'p95': 229.08513701242165, 'max': 443.6935879635855}`.
- The rolling worker produced 873 unique policies with solve-time statistics `{'median': 217.70869998726994, 'p95': 343.1358999805525, 'max': 441.2175999896135}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 3598.0}`. Policy status counts were `{'pending_future_epoch': 40, 'queryable': 6374, 'expired': 12}`; 52 robust-mode decisions had no query.
- Of 3973 unambiguous output transitions, 3460 (0.871) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 8 hit windows with a positive warning lead; those leads were `[15, 13, 10, 6, 8, 15, 9, 6, 0, 0, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.276 during the 60 frames preceding a hit versus 0.176 outside those windows.
- Soft recovery was selected on 0.069 of alive decisions in the 60-frame pre-hit windows versus 0.097 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 58.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
