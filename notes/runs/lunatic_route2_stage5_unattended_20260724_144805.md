# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_144805

## Scope And Integrity

- Valid practice scope: `2..39650` (6901 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 16, at `[2160, 11238, 12249, 22592, 23206, 23715, 28265, 28594, 29108, 33956, 34740, 35444, 36493, 37222, 38244, 38925]`.
- Hard no-Bomb verification: **PASS** across 6901 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2160-T1`. It occurred during a nonspell phase at player (376.000, 427.058), with 624 bullets and 0 lasers. The projectile model reported pipeline clearance -1.500.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 4 |
| `enemy_body_contact_candidate` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 10
- `playfield_boundary`: 7
- `pool_density_over_1000`: 7
- `action_lag_over_model`: 5
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2160 | nonspell | (376.000, 427.058) | `up_left_fast` | 624/0 | -1.500/-1.500 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11238 | nonspell | (328.897, 375.314) | `up_fast` | 905/0 | 4.371/0.362 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12249 | nonspell | (16.132, 275.714) | `left_fast` | 220/0 | -0.885/-2.780 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22592 | 103 幻波「赤眼催眠(マインドブローイング)」 | (179.438, 406.142) | `down_fast` | 1158/0 | 0.239/0.239 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23206 | 103 幻波「赤眼催眠(マインドブローイング)」 | (244.437, 432.000) | `right` | 832/0 | -3.009/-3.009 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23715 | 103 幻波「赤眼催眠(マインドブローイング)」 | (179.412, 431.763) | `down_right` | 1084/0 | -3.373/-3.373 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28265 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (161.496, 432.000) | `right` | 1028/0 | -8.397/-8.397 | 64f/71f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28594 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (161.242, 386.242) | `up_fast` | 1010/0 | -6.356/-8.524 | 23f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29108 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (164.612, 382.770) | `down_left` | 1022/0 | -5.850/-7.511 | 30f/30f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33956 | 111 懶惰「生神停止(マインドストッパー)」 | (204.048, 416.000) | `up_fast` | 507/0 | -3.004/-3.004 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34740 | 111 懶惰「生神停止(マインドストッパー)」 | (161.621, 16.000) | `right_fast` | 439/0 | -2.873/-2.873 | 5f/22f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35444 | 111 懶惰「生神停止(マインドストッパー)」 | (189.247, 34.400) | `down` | 594/0 | -3.495/-3.495 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36493 | 115 散符「真実の月(インビジブルフルムーン)」 | (184.492, 120.686) | `up_fast` | 0/0 | 9999.000/0.737 | 0f/0f | `enemy_body_contact_candidate` | `unresolved_planner_failure` |
| discovery | 37222 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 432.000) | `up_fast` | 1151/0 | -1.474/-1.474 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38244 | 115 散符「真実の月(インビジブルフルムーン)」 | (9.626, 425.495) | `stay` | 975/0 | -3.482/-3.482 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38925 | 115 散符「真実の月(インビジブルフルムーン)」 | (260.414, 432.000) | `up_right_fast` | 1083/0 | -1.003/-1.003 | 4f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 4355 | 4250 | 2239 | 0 | 1981 | 677 | 342.355 | 0.137 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 3 | 497 | 483 | 109 | 0 | 374 | 82 | 291.099 | 0.131 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 3 | 413 | 399 | 257 | 0 | 137 | 107 | 138.111 | 0.337 |
| 111 懶惰「生神停止(マインドストッパー)」 | 3 | 797 | 785 | 229 | 0 | 556 | 138 | 185.866 | 0.012 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 4 | 839 | 821 | 305 | 0 | 506 | 142 | 293.327 | 0.297 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 24.950 ms median and 43.180 ms p95.
- The full enemy sensor produced 5360 snapshots; capture read time was `{'median': 32.59280000929721, 'p95': 56.873699999414384, 'max': 89.68629999435507}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 16.0}` frames, and 7 phase-counter discontinuities were excluded; 157 decisions retained at least one contact-enabled body (maximum 36).
- The terminal-threat heuristic covered 6901 decisions with horizon counts `{'0': 75, '10': 6546, '32': 280}`; it reported 2 collision and 44 sub-safety-clearance warnings, and relaxed 45 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 47, '3': 90, '4': 1143, '5': 4740, '6': 881}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 54, '3': 110, '4': 3046, '5': 3085, '6': 606}`.
- Adaptive delay supports were `{'2,3': 51, '2,3,4': 43, '2,3,4,5': 139, '2,3,4,5,6': 487, '3,4,5': 223, '3,4,5,6': 5083, '4,5': 18, '4,5,6': 752, '5,6': 95, '6': 10}`; 158 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 89/266.
- Robust viability supplied 6738 available policy queries (0 had new delay support outside the cached policy), constrained 3554 decisions, and exposed 3139 empty queried action sets. Recovery guidance was available/selected on 728/399 empty-kernel queries; distant-kernel guidance was available/selected on 2271/2201. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 19.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 107.33126291998991, 'p95': 279.42798714516766, 'max': 415.0758966743311}`, and `{'median': 0.0, 'p95': 23.76815390586853, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 921, '1': 849, '2': 907, '3': 824, '4': 818, '5': 853, '6': 789, '7': 777}`.
- The rolling worker produced 1146 unique policies with solve-time statistics `{'median': 304.06970001058653, 'p95': 485.8115999959409, 'max': 578.4226999967359}` and first-observed ages `{'median': 6.0, 'p95': 14.0, 'max': 1812.0}`. Policy status counts were `{'pending_future_epoch': 29, 'queryable': 6739, 'expired': 44}`; 74 robust-mode decisions had no query.
- Of 3847 unambiguous output transitions, 3274 (0.851) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 15, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 11 hit windows with a positive warning lead; those leads were `[5, 0, 4, 6, 13, 8, 71, 23, 30, 0, 22, 0, 0, 4, 0, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.400 during the 60 frames preceding a hit versus 0.140 outside those windows.
- Mean selected control-reserve deficit was 6.903 during the 60 frames preceding a hit versus 1.248 outside those windows.
- Soft recovery was selected on 0.054 of alive decisions in the 60-frame pre-hit windows versus 0.071 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 9.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Investigation

The 16-versus-31 hit delta is not a causal improvement claim. Native RNG,
respawn position, Power, and phase length differ. This run is useful because
it provides independent performance and counterexample evidence.

The sparse C++ piecewise projector passed the physical performance gate:

| Phase | Local p95 before/after ms | Cadence p95 before/after |
| --- | ---: | ---: |
| spell 103 | 326.38 / 43.19 | 25 / 7 |
| spell 107 | 463.61 / 50.44 | 37 / 8 |
| spell 111 | 142.72 / 40.95 | 13 / 6 |

Spell 107 retained 385 event rows and 382 attached rows, plus 186,521
lightweight planning projections; 99,176 carried projected velocity events.
Spell 111 retained 756/524 event/attached rows, 104,595 planning projections,
and 102,870 projected-event samples. Its callback population includes 28,761
stopped and 75,834 moving samples. Diagnostic transform objects were not
enabled. The analyzer was corrected to understand this default field instead
of falsely reporting zero coverage.

The corrected Stage-5 reserve replay reconstructs retained stop/resume events.
Disabled/enabled reserve variants preserve hard counts at 28 robust collisions
and 45 negative certificates over 300 rows, and 18/24 over 60 pre-hit rows.
Zero-deficit selections improve `87 -> 206` and `8 -> 27`. This supports
CE-0089's ordering correction across another stage, but 15/16 physical hits
still followed viability-kernel exhaustion.

### Frame 36,493

This hit is part of a five-run spell-115 cluster at upper-center coordinates
with zero bullets and lasers. In this trace:

- frame 36,472 issued `up_fast` toward a retained corridor target at
  `(184,16)` after spell 111 ended;
- spell 115 activated at frame 36,475 with player `y=192.69`, no projectile
  hazard, and a live owner pointer;
- the old direction continued through frame 36,490; 14 residual items
  contributed approach potential, and item 1891 became a predicted collection;
- the hit began at frame 36,493 at `(184.49,120.69)`;
- the hit-edge contact read spanned frames 36,496..36,497, so its empty body
  set is not a stable proof against contact.

CE-0090 therefore treats body contact as a strong hypothesis, not an observed
native overlap. The correction synchronously reads the active spell owner's
small geometry window and plans against both latent contact modes. It also
drops previous-context direction inertia at a spell boundary and sharply
reduces/bounds item approach shaping. The exact first boundary state replays
from `up_fast` to `down`; physical acceptance requires a fresh Stage-5 run.
