# TH08 Stage 2 No-Bomb Practice Review: lunatic_route2_stage2_unattended_20260724_042005

## Scope And Integrity

- Valid practice scope: `2..22886` (6087 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 8, at `[1582, 1977, 3039, 4117, 5040, 10529, 11770, 18035]`.
- Hard no-Bomb verification: **PASS** across 6087 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S1-F1582-T1`. It occurred during a nonspell phase at player (305.144, 87.946), with 74 bullets and 0 lasers. The projectile model reported pipeline clearance -4.780.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 4 |
| `observed_bullet_overlap` | 2 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `fast_mode`: 6
- `corridor_deadline_miss`: 5
- `playfield_boundary`: 2
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1582 | nonspell | (305.144, 87.946) | `down_fast` | 74/0 | -4.780/-4.980 | 4f/16f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 1977 | nonspell | (261.770, 78.817) | `down_left` | 65/0 | -2.432/-2.432 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 3039 | nonspell | (24.008, 24.005) | `right_fast` | 239/0 | -3.802/-3.802 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4117 | nonspell | (371.977, 414.064) | `up_fast` | 203/0 | -3.310/-3.510 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 5040 | nonspell | (37.908, 370.996) | `right_fast` | 262/0 | -10.644/-19.654 | 3f/3f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10529 | nonspell | (221.500, 387.804) | `right_fast` | 64/0 | 7.501/6.915 | 0f/0f | `observed_enemy_body_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 11770 | nonspell | (57.042, 432.000) | `stay` | 172/0 | -5.146/-5.146 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 18035 | nonspell | (369.495, 432.000) | `left_fast` | 689/0 | -5.018/-5.018 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 3383 | 3246 | 957 | 41 | 2248 | 214 | 274.781 | 0.100 |
| 16 | 0 | 589 | 576 | 267 | 11 | 309 | 36 | 184.010 | 0.165 |
| 20 | 0 | 699 | 676 | 403 | 0 | 273 | 46 | 149.492 | 0.324 |
| 24 | 0 | 750 | 728 | 320 | 9 | 408 | 45 | 179.014 | 0.207 |
| 28 | 0 | 666 | 648 | 487 | 0 | 161 | 46 | 170.553 | 0.332 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 21.483 ms median and 39.092 ms p95.
- The full enemy sensor produced 3678 snapshots; capture read time was `{'median': 23.959599988302216, 'p95': 46.19890000321902, 'max': 82.05729999463074}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 2 phase-counter discontinuities were excluded; 4668 decisions retained at least one contact-enabled body (maximum 18).
- Modeled action hold counts were `{'2': 53, '3': 500, '4': 5109, '5': 425}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 65, '3': 883, '4': 5139}`.
- Adaptive delay supports were `{'1,2,3': 6, '1,2,3,4': 1, '2,3': 65, '2,3,4': 74, '2,3,4,5': 875, '2,3,4,5,6': 1898, '3,4': 45, '3,4,5': 642, '3,4,5,6': 2481}`; 75 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 52/298.
- Robust viability supplied 5874 available policy queries (61 had new delay support outside the cached policy), constrained 3399 decisions, and exposed 2434 empty queried action sets. Recovery guidance was available/selected on 475/298 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 17.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 387 unique policies with solve-time statistics `{'median': 213.31569997710176, 'p95': 382.0906000037212, 'max': 450.2997000236064}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1765.0}`. Policy status counts were `{'pending_future_epoch': 114, 'queryable': 5876, 'expired': 23}`; 139 robust-mode decisions had no query.
- Of 3160 unambiguous output transitions, 2768 (0.876) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 3, 'global_viability_kernel_exhausted_before_hit': 4, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 7 hit windows with a positive warning lead; those leads were `[16, 6, 6, 5, 3, 0, 6, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.083 during the 60 frames preceding a hit versus 0.184 outside those windows.
- Soft recovery was selected on 0.077 of alive decisions in the 60-frame pre-hit windows versus 0.047 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 94.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Baseline Review

- This is the first accepted original-game Stage-2 baseline. All eight hits
  occurred in nonspell waves; spell IDs 16, 20, 24, and 28 completed without
  a hit.
- Canonical bullet slot 637 was absent from the active policy's snapshot at
  frame 1,498, appeared by frame 1,545, and hit at 1,582. The active policy
  targeted frame 1,546 and the next targeted 1,594, proving an asynchronous
  observation-to-policy blind interval.
- The rolling solver's p90 duration was about 25 game frames, yet policy lead
  remained clamped at 48. The next general correction is an adaptive lower
  lead bounded by solver timing and remaining horizon; ECL execution is still
  required for events created within the residual interval.
- Dialogue auto-confirm, post-stage no-save, exact-process termination, and
  hard no-Bomb all passed without manual intervention.
