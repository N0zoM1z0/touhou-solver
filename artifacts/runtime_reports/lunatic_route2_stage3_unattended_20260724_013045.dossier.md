# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260724_013045

## Scope And Integrity

- Valid practice scope: `1..27610` (7887 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 11, at `[2729, 7937, 8731, 13852, 15227, 15561, 15869, 16437, 18936, 21594, 23891]`.
- Hard no-Bomb verification: **PASS** across 7887 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F2729-T1`. It occurred during a nonspell phase at player (14.900, 155.741), with 282 bullets and 0 lasers. The projectile model reported pipeline clearance 2.044.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 6 |
| `modeled_committed_prefix_collision` | 5 |

Contributing factors:

- `fast_mode`: 9
- `corridor_deadline_miss`: 4
- `playfield_boundary`: 2
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2729 | nonspell | (14.900, 155.741) | `up_fast` | 282/0 | 2.044/-1.906 | 4f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7937 | nonspell | (31.055, 181.548) | `up_fast` | 613/0 | -2.439/-2.639 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8731 | nonspell | (14.884, 423.426) | `up_fast` | 400/0 | -1.286/-1.286 | 3f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13852 | nonspell | (306.033, 400.870) | `up_fast` | 455/0 | 0.419/-3.046 | 3f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 15227 | 38 始符「エフェメラリティ137」 | (9.516, 421.590) | `up_fast` | 224/0 | -9.012/-9.012 | 3f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 15561 | 38 始符「エフェメラリティ137」 | (18.183, 308.636) | `down_fast` | 201/0 | -9.440/-9.440 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 15869 | 38 始符「エフェメラリティ137」 | (67.157, 249.592) | `left_fast` | 213/0 | -11.110/-11.110 | 6f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 16437 | 38 始符「エフェメラリティ137」 | (369.006, 422.789) | `left_fast` | 199/0 | -4.280/-4.280 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18936 | 42 野符「GHQクライシス」 | (347.313, 429.540) | `stay` | 457/0 | -3.516/-3.516 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21594 | nonspell | (163.192, 427.725) | `right` | 245/0 | -4.229/-4.229 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 23891 | 46 国体「三種の神器　郷」 | (363.610, 424.940) | `up_left_fast` | 363/0 | -1.417/-1.762 | 3f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 4183 | 4017 | 1612 | 170 | 2276 | 226 | 286.779 | 0.176 |
| 35 | 0 | 830 | 799 | 565 | 35 | 234 | 46 | 189.644 | 0.248 |
| 38 始符「エフェメラリティ137」 | 4 | 760 | 738 | 430 | 0 | 308 | 43 | 180.909 | 0.066 |
| 42 野符「GHQクライシス」 | 1 | 713 | 697 | 620 | 38 | 64 | 43 | 137.002 | 0.270 |
| 46 国体「三種の神器　郷」 | 1 | 866 | 839 | 653 | 51 | 185 | 49 | 194.546 | 0.270 |
| 50 | 0 | 535 | 518 | 424 | 10 | 84 | 39 | 225.091 | 0.358 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.697 ms median and 37.465 ms p95.
- Modeled action hold counts were `{'2': 60, '3': 3662, '4': 3790, '5': 375}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 11, '2': 125, '3': 5495, '4': 1970, '5': 286}`.
- Adaptive delay supports were `{'1,2': 11, '1,2,3': 89, '1,2,3,4': 30, '1,2,3,4,5,6': 30, '2,3': 195, '2,3,4': 1226, '2,3,4,5': 3063, '2,3,4,5,6': 2507, '3,4': 17, '3,4,5': 144, '3,4,5,6': 575}`; 93 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 53/459.
- Robust viability supplied 7608 available policy queries (304 had new delay support outside the cached policy), constrained 3151 decisions, and exposed 4304 empty queried action sets. Safe-action count and selected repair-volume statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 446 unique policies with solve-time statistics `{'median': 241.67045000649523, 'p95': 358.676599978935, 'max': 469.44580000126734}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 3574.0}`. Policy status counts were `{'pending_future_epoch': 151, 'queryable': 7608, 'expired': 35}`; 186 robust-mode decisions had no query.
- Of 4750 unambiguous output transitions, 4176 (0.879) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 7, 'robust_action_set_exhausted_before_hit': 4}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[15, 6, 10, 10, 10, 3, 6, 7, 0, 5, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.298 during the 60 frames preceding a hit versus 0.211 outside those windows.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 73.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
