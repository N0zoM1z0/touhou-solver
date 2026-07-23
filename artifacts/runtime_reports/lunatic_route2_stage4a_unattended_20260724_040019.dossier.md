# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_040019

## Scope And Integrity

- Valid practice scope: `2..45775` (10525 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 27, at `[958, 1554, 1893, 2551, 3962, 4516, 8806, 9505, 10483, 10794, 11496, 11951, 12334, 12724, 13359, 13911, 20864, 22620, 23251, 27755, 28825, 31588, 32416, 35223, 36483, 39495, 43395]`.
- Hard no-Bomb verification: **PASS** across 10525 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F958-T1`. It occurred during a nonspell phase at player (33.607, 421.701), with 346 bullets and 0 lasers. The projectile model reported pipeline clearance -1.853.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 12 |
| `modeled_committed_prefix_collision` | 11 |
| `observed_enemy_body_overlap` | 4 |

Contributing factors:

- `fast_mode`: 19
- `corridor_deadline_miss`: 12
- `playfield_boundary`: 10
- `pool_density_over_1000`: 4
- `enemy_body_absent_from_action_snapshot`: 3
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 958 | nonspell | (33.607, 421.701) | `left_fast` | 346/0 | -1.853/-1.853 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 1554 | nonspell | (23.718, 305.162) | `down_fast` | 339/0 | -2.198/-2.198 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1893 | nonspell | (10.031, 423.331) | `up_fast` | 322/0 | -1.966/-2.374 | 3f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 2551 | nonspell | (356.906, 424.793) | `up_fast` | 596/0 | -0.504/-3.006 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3962 | nonspell | (18.499, 325.513) | `down_right` | 843/0 | -0.775/-2.548 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4516 | nonspell | (376.000, 415.249) | `down_left` | 1235/0 | -4.028/-4.028 | 0f/35f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8806 | nonspell | (206.236, 412.000) | `up_fast` | 778/0 | 17.189/15.859 | 0f/0f | `observed_enemy_body_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 9505 | nonspell | (44.049, 428.256) | `right_fast` | 149/0 | -4.970/-7.469 | 11f/17f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10483 | nonspell | (150.593, 408.010) | `up_right_fast` | 141/0 | 4.987/-4.170 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10794 | nonspell | (244.394, 415.169) | `stay` | 578/0 | 53.724/-2.909 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11496 | 57 夢境「二重大結界」 | (10.952, 411.578) | `up_right_fast` | 501/0 | -0.131/-3.043 | 3f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11951 | 57 夢境「二重大結界」 | (65.907, 427.483) | `right_fast` | 598/0 | 0.380/-2.361 | 3f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12334 | 57 夢境「二重大結界」 | (10.559, 415.240) | `up_fast` | 596/0 | -3.365/-3.565 | 3f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12724 | 57 夢境「二重大結界」 | (58.828, 425.665) | `right_fast` | 609/0 | -2.340/-2.340 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13359 | 57 夢境「二重大結界」 | (375.255, 416.221) | `up_fast` | 607/0 | 0.277/-1.445 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13911 | 57 夢境「二重大結界」 | (361.571, 428.823) | `up_left` | 619/0 | -1.430/-1.430 | 3f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 20864 | 61 散霊「夢想封印　寂」 | (367.097, 402.845) | `stay` | 384/0 | -3.182/-3.182 | 3f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 22620 | nonspell | (371.985, 416.781) | `down_left_fast` | 807/0 | -3.969/-3.969 | 4f/18f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23251 | nonspell | (25.937, 420.765) | `left_fast` | 710/0 | -3.850/-3.850 | 4f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27755 | nonspell | (8.000, 430.427) | `up` | 129/0 | -6.051/-6.051 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 28825 | nonspell | (375.679, 101.770) | `left` | 172/0 | -1.700/-1.700 | 0f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 31588 | 65 神技「八方龍殺陣」 | (221.548, 416.563) | `up_fast` | 1169/0 | -2.269/-10.161 | 0f/12f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 32416 | 65 神技「八方龍殺陣」 | (354.996, 401.702) | `up_right_fast` | 1209/0 | -17.353/-20.663 | 4f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35223 | nonspell | (312.823, 427.906) | `up_fast` | 72/0 | -3.341/-12.264 | 5f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36483 | nonspell | (356.709, 419.981) | `up_fast` | 102/0 | -1.626/-1.626 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39495 | 69 回霊「夢想封印　侘」 | (10.213, 312.505) | `up_fast` | 704/0 | -0.425/-0.425 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43395 | 73 大結界「博麗弾幕結界」 | (218.601, 389.249) | `stay` | 1000/0 | -1.305/-1.305 | 6f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 16 | 6063 | 5885 | 1938 | 91 | 3856 | 370 | 252.473 | 0.198 |
| 57 夢境「二重大結界」 | 6 | 991 | 979 | 79 | 12 | 890 | 64 | 284.506 | 0.277 |
| 61 散霊「夢想封印　寂」 | 1 | 880 | 856 | 160 | 15 | 692 | 57 | 260.188 | 0.164 |
| 65 神技「八方龍殺陣」 | 2 | 782 | 757 | 450 | 0 | 307 | 55 | 341.786 | 0.191 |
| 69 回霊「夢想封印　侘」 | 1 | 925 | 905 | 579 | 12 | 326 | 61 | 213.201 | 0.251 |
| 73 大結界「博麗弾幕結界」 | 1 | 884 | 867 | 430 | 0 | 437 | 62 | 382.774 | 0.080 |

## Interpretation

- Retained witnesses classify 12 bullet overlaps, 0 laser overlaps, and 4 exact same-epoch enemy-body overlaps; 3 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 21.364 ms median and 38.782 ms p95.
- The full enemy sensor produced 6448 snapshots; capture read time was `{'median': 25.240250004571863, 'p95': 45.963300013681874, 'max': 110.63850001664832}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 8257 decisions retained at least one contact-enabled body (maximum 36).
- Modeled action hold counts were `{'2': 51, '3': 1522, '4': 7800, '5': 1152}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 64, '3': 2458, '4': 7817, '5': 186}`.
- Adaptive delay supports were `{'2,3': 97, '2,3,4': 600, '2,3,4,5': 2059, '2,3,4,5,6': 3639, '3,4': 15, '3,4,5': 559, '3,4,5,6': 3556}`; 143 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 108/574.
- Robust viability supplied 10249 available policy queries (130 had new delay support outside the cached policy), constrained 6508 decisions, and exposed 3636 empty queried action sets. Recovery guidance was available/selected on 1412/873 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 5.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 28.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 669 unique policies with solve-time statistics `{'median': 266.71510000596754, 'p95': 408.3247999951709, 'max': 473.1752000225242}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1782.0}`. Policy status counts were `{'pending_future_epoch': 134, 'queryable': 10248, 'expired': 53}`; 186 robust-mode decisions had no query.
- Of 5915 unambiguous output transitions, 5139 (0.869) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 12, 'global_viability_kernel_exhausted_before_hit': 14, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 24 hit windows with a positive warning lead; those leads were `[6, 5, 9, 7, 6, 35, 0, 17, 0, 0, 5, 9, 6, 6, 8, 7, 9, 18, 10, 5, 6, 12, 4, 15, 6, 6, 11]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.375 during the 60 frames preceding a hit versus 0.180 outside those windows.
- Soft recovery was selected on 0.040 of alive decisions in the 60-frame pre-hit windows versus 0.085 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 6.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
