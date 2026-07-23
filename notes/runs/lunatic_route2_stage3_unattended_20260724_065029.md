# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260724_065029

## Scope And Integrity

- Valid practice scope: `2..26892` (6108 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 7, at `[743, 1695, 14038, 21057, 25561, 25971, 26295]`.
- Hard no-Bomb verification: **PASS** across 6108 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F743-T1`. It occurred during a nonspell phase at player (362.925, 426.520), with 184 bullets and 0 lasers. The projectile model reported pipeline clearance -2.007.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 2 |
| `observed_bullet_overlap` | 2 |
| `observed_laser_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 3
- `action_lag_over_model`: 2
- `corridor_deadline_miss`: 2
- `playfield_boundary`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 743 | nonspell | (362.925, 426.520) | `stay` | 184/0 | -2.007/-2.007 | 0f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1695 | nonspell | (357.536, 424.995) | `up_left` | 181/0 | -2.466/-2.466 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14038 | nonspell | (177.240, 427.818) | `right_fast` | 415/0 | 0.489/0.489 | 0f/4f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21057 | nonspell | (10.823, 430.583) | `right_fast` | 76/0 | -5.052/-5.052 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25561 | 50 虚史「幻想郷伝説」 | (286.917, 422.242) | `right` | 271/200 | -4.682/-4.682 | 0f/7f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25971 | 50 虚史「幻想郷伝説」 | (93.234, 431.628) | `up_right` | 339/200 | -2.970/-2.970 | 0f/12f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 26295 | 50 虚史「幻想郷伝説」 | (201.894, 427.556) | `right_fast` | 285/200 | -2.234/-2.234 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 3223 | 3132 | 1070 | 33 | 1789 | 418 | 244.511 | 0.143 |
| 35 | 0 | 688 | 679 | 534 | 0 | 117 | 91 | 179.979 | 0.051 |
| 38 | 0 | 645 | 640 | 273 | 5 | 312 | 81 | 190.163 | 0.109 |
| 42 | 0 | 566 | 561 | 441 | 0 | 114 | 80 | 165.418 | 0.254 |
| 46 | 0 | 682 | 677 | 520 | 0 | 111 | 95 | 193.765 | 0.260 |
| 50 虚史「幻想郷伝説」 | 3 | 304 | 243 | 82 | 0 | 130 | 27 | 1255.298 | 0.216 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 2 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 24.317 ms median and 48.185 ms p95.
- The full enemy sensor produced 4102 snapshots; capture read time was `{'median': 29.9438500078395, 'p95': 61.6664000262972, 'max': 231.28060001181439}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 15.0}` frames, and 3 phase-counter discontinuities were excluded; 4891 decisions retained at least one contact-enabled body (maximum 9).
- The terminal-threat heuristic covered 6108 decisions with horizon counts `{'0': 52, '10': 5655, '32': 401}`; it reported 1 collision and 75 sub-safety-clearance warnings, and relaxed 401 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 52, '3': 307, '4': 4077, '5': 1452, '6': 220}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 67, '3': 485, '4': 5322, '5': 38, '6': 196}`.
- Adaptive delay supports were `{'1,2,3': 86, '1,2,3,4': 7, '1,2,3,4,5,6': 13, '2,3': 14, '2,3,4': 91, '2,3,4,5': 352, '2,3,4,5,6': 821, '3,4': 90, '3,4,5': 484, '3,4,5,6': 4010, '4,5,6': 47, '5,6': 93}`; 104 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 170/346.
- Robust viability supplied 5932 available policy queries (38 had new delay support outside the cached policy), constrained 2573 decisions, and exposed 2920 empty queried action sets. Recovery guidance was available/selected on 1038/517 empty-kernel queries; distant-kernel guidance was available/selected on 1772/1761. Safe-action count, selected repair-volume, and selected recovery-distance statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}` `{'median': 5.0, 'p95': 153.0, 'max': 153.0}`, and `{'median': 86.16263691415206, 'p95': 236.2371689637344, 'max': 387.31898998112655}`.
- The rolling worker produced 792 unique policies with solve-time statistics `{'median': 216.5518499969039, 'p95': 340.2481999946758, 'max': 1660.3445000073407}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 3591.0}`. Policy status counts were `{'pending_future_epoch': 39, 'queryable': 5921, 'expired': 75}`; 103 robust-mode decisions had no query.
- Of 3741 unambiguous output transitions, 3276 (0.876) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 7}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 6 hit windows with a positive warning lead; those leads were `[9, 6, 4, 7, 7, 12, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.419 during the 60 frames preceding a hit versus 0.151 outside those windows.
- Soft recovery was selected on 0.054 of alive decisions in the 60-frame pre-hit windows versus 0.087 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 89.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Experiment Decision

This is an **accepted cross-stage distant-recovery checkpoint** and a rejected
dense-laser result. The run reached `route_complete`, used no Bomb input, and
auto-confirm emitted a native wall pulse at frame 4,700 without manual input.

Against complete Stage-3 baseline `20260724_013045`, total hits fell from 11
to seven. Before spell 50, phase counts changed from
nonspell/38/42/46 `5/4/1/1` to `4/0/0/0`; distant recovery was selected on
1,761 queries while cadence remained 3/5 frames. The runs are not a controlled
RNG ablation, so this accepts a cross-stage checkpoint rather than assigning a
precise causal reduction.

Spell 50 is separately rejected. Its 200 lasers drove corridor solve
median/p95 to 1255/1565 ms and produced three hits, including two exact laser
overlaps. CE-0076 treats global segment-trajectory clearance throughput as the
next correction boundary.
