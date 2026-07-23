# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_022420

## Scope And Integrity

- Valid practice scope: `2..41917` (10157 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 20, at `[4348, 6810, 10993, 11719, 12863, 14154, 14497, 21524, 22360, 23851, 34295, 34715, 35314, 36055, 36816, 37588, 38322, 39485, 40142, 41403]`.
- Hard no-Bomb verification: **PASS** across 10157 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F4348-T1`. It occurred during a nonspell phase at player (155.400, 426.343), with 448 bullets and 0 lasers. The projectile model reported pipeline clearance -0.667.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 8 |
| `sensor_gap_or_unmodeled_hazard` | 2 |

Contributing factors:

- `fast_mode`: 9
- `corridor_deadline_miss`: 8
- `playfield_boundary`: 4
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4348 | nonspell | (155.400, 426.343) | `left` | 448/0 | -0.667/-3.535 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 6810 | nonspell | (181.139, 317.654) | `up_fast` | 448/0 | 29.048/-1.299 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10993 | nonspell | (364.360, 397.226) | `up_left_fast` | 875/0 | 8.506/2.243 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11719 | nonspell | (322.352, 359.046) | `up_left_fast` | 889/0 | -1.506/-1.506 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12863 | nonspell | (14.840, 429.252) | `up_right` | 267/0 | -2.429/-2.429 | 0f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14154 | nonspell | (27.125, 428.255) | `right_fast` | 523/0 | -4.717/-4.717 | 3f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14497 | nonspell | (293.538, 401.210) | `stay` | 461/0 | -3.614/-3.614 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 21524 | nonspell | (278.297, 366.850) | `up_left_fast` | 446/0 | -2.957/-2.957 | 0f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22360 | nonspell | (230.644, 374.234) | `up_fast` | 413/0 | 1.037/-3.313 | 2f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 23851 | 103 幻波「赤眼催眠(マインドブローイング)」 | (20.271, 410.466) | `up` | 1463/0 | -1.676/-1.676 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34295 | nonspell | (221.594, 370.076) | `down` | 472/0 | -2.590/-3.948 | 4f/23f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 34715 | nonspell | (115.238, 366.216) | `down_right_fast` | 425/0 | -2.125/-2.432 | 2f/14f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 35314 | nonspell | (12.342, 426.456) | `up_fast` | 460/0 | -2.219/-2.219 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36055 | 111 懶惰「生神停止(マインドストッパー)」 | (190.716, 224.623) | `stay` | 243/0 | -2.403/-2.467 | 5f/12f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36816 | 111 懶惰「生神停止(マインドストッパー)」 | (191.396, 210.243) | `stay` | 337/0 | -1.356/-1.356 | 3f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 37588 | 111 懶惰「生神停止(マインドストッパー)」 | (190.855, 222.014) | `up` | 333/0 | -1.776/-1.776 | 3f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38322 | 111 懶惰「生神停止(マインドストッパー)」 | (195.517, 215.862) | `down` | 334/0 | -2.769/-3.274 | 8f/17f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 39485 | 115 散符「真実の月(インビジブルフルムーン)」 | (31.252, 430.123) | `up_left_fast` | 1170/0 | 0.871/-1.136 | 4f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40142 | 115 散符「真実の月(インビジブルフルムーン)」 | (22.470, 429.073) | `up` | 1185/0 | -2.421/-2.421 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41403 | 115 散符「真実の月(インビジブルフルムーン)」 | (371.214, 384.658) | `stay` | 1081/0 | -1.305/-1.305 | 0f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 12 | 6370 | 6187 | 3379 | 228 | 2679 | 365 | 304.084 | 0.224 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 1011 | 989 | 516 | 0 | 473 | 61 | 298.095 | 0.370 |
| 107 | 0 | 639 | 627 | 497 | 0 | 130 | 41 | 256.795 | 0.258 |
| 111 懶惰「生神停止(マインドストッパー)」 | 4 | 1054 | 1039 | 232 | 3 | 804 | 63 | 234.403 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 1083 | 1062 | 580 | 14 | 482 | 64 | 217.680 | 0.261 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 16.862 ms median and 34.361 ms p95.
- Modeled action hold counts were `{'2': 50, '3': 3101, '4': 6906, '5': 100}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 76, '3': 6717, '4': 3364}`.
- Adaptive delay supports were `{'1,2,3': 16, '1,2,3,4': 1, '2,3': 225, '2,3,4': 1232, '2,3,4,5': 3796, '2,3,4,5,6': 3760, '3,4': 5, '3,4,5': 431, '3,4,5,6': 691}`; 343 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 75/605.
- Robust viability supplied 9904 available policy queries (245 had new delay support outside the cached policy), constrained 4568 decisions, and exposed 5204 empty queried action sets. Recovery guidance was available/selected on 775/416 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 1.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 594 unique policies with solve-time statistics `{'median': 276.1211000033654, 'p95': 421.2699000199791, 'max': 485.62680001487024}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1792.0}`. Policy status counts were `{'pending_future_epoch': 108, 'queryable': 9902, 'expired': 87}`; 193 robust-mode decisions had no query.
- Of 5329 unambiguous output transitions, 4600 (0.863) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 11, 'robust_action_set_exhausted_before_hit': 9}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[9, 0, 0, 10, 17, 11, 6, 9, 10, 9, 23, 14, 9, 12, 6, 15, 17, 14, 8, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.178 during the 60 frames preceding a hit versus 0.230 outside those windows.
- Soft recovery was selected on 0.083 of alive decisions in the 60-frame pre-hit windows versus 0.039 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
