# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_061949

## Scope And Integrity

- Valid practice scope: `2..44911` (11238 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 21, at `[1611, 1995, 3985, 4319, 7214, 7996, 13583, 13886, 14438, 23774, 24858, 30072, 31076, 31951, 32568, 33121, 38089, 39122, 39898, 41358, 43161]`.
- Hard no-Bomb verification: **PASS** across 11238 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1611-T1`. It occurred during a nonspell phase at player (52.072, 392.088), with 76 bullets and 0 lasers. The projectile model reported pipeline clearance 41.945.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 7 |
| `sensor_gap_or_unmodeled_hazard` | 5 |

Contributing factors:

- `fast_mode`: 12
- `playfield_boundary`: 11
- `action_lag_over_model`: 6
- `pool_density_over_1000`: 6
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1611 | nonspell | (52.072, 392.088) | `stay` | 76/0 | 41.945/38.355 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 1995 | nonspell | (344.887, 400.887) | `up_left_fast` | 412/0 | 22.039/22.039 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3985 | nonspell | (8.000, 432.000) | `right_fast` | 703/0 | -2.405/-2.405 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 4319 | nonspell | (192.000, 406.800) | `stay` | 424/0 | -6.730/-6.730 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 7214 | nonspell | (376.000, 424.000) | `up_fast` | 471/0 | -0.377/-2.641 | 2f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 7996 | nonspell | (41.162, 408.201) | `up_right_fast` | 772/0 | -2.211/-2.357 | 4f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13583 | nonspell | (260.503, 432.000) | `down_right_fast` | 359/0 | -3.659/-3.659 | 5f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13886 | nonspell | (376.000, 22.505) | `stay` | 428/0 | 6.861/-17.706 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 14438 | nonspell | (306.165, 426.710) | `stay` | 538/0 | 1.327/1.327 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 23774 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 1087/0 | 1.033/0.073 | 0f/4f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24858 | 103 幻波「赤眼催眠(マインドブローイング)」 | (157.860, 432.000) | `up_left` | 1025/0 | -2.771/-2.771 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30072 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (215.282, 432.000) | `down_right_fast` | 989/0 | -4.744/-8.723 | 9f/49f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31076 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (80.325, 432.000) | `up_right_fast` | 1014/0 | -7.774/-7.774 | 9f/135f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31951 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (243.555, 432.000) | `up_left_fast` | 1014/0 | -6.020/-7.188 | 34f/70f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32568 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (217.187, 424.821) | `left_fast` | 1007/0 | -5.672/-7.628 | 9f/137f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33121 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (230.130, 399.406) | `up_right_fast` | 984/0 | -9.640/-9.640 | 24f/167f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38089 | nonspell | (8.000, 432.000) | `stay` | 408/0 | -2.681/-2.681 | 0f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39122 | 111 懶惰「生神停止(マインドストッパー)」 | (189.900, 201.481) | `left_fast` | 245/0 | -1.263/-1.263 | 4f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39898 | 111 懶惰「生神停止(マインドストッパー)」 | (207.017, 193.878) | `up_left` | 344/0 | -1.591/-1.591 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41358 | 111 懶惰「生神停止(マインドストッパー)」 | (208.421, 197.706) | `up` | 354/0 | -1.833/-4.674 | 0f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43161 | 115 散符「真実の月(インビジブルフルムーン)」 | (34.023, 432.000) | `up_right` | 1210/0 | -1.508/-5.309 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 7198 | 30 | 25 | 0 | 4 | 11 | 1566.742 | 0.396 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 941 | 410 | 297 | 0 | 0 | 29 | 83.878 | 0.436 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 5 | 1057 | 1051 | 844 | 0 | 0 | 239 | 77.249 | 0.377 |
| 111 懶惰「生神停止(マインドストッパー)」 | 3 | 1056 | 1050 | 446 | 0 | 0 | 182 | 81.865 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 986 | 979 | 742 | 0 | 0 | 182 | 66.832 | 0.437 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.696 ms median and 32.078 ms p95.
- The full enemy sensor produced 6304 snapshots; capture read time was `{'median': 5.245699998340569, 'p95': 28.208700008690357, 'max': 850.5907999933697}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 108.0}` frames, and 9 phase-counter discontinuities were excluded; 10642 decisions retained at least one robust-union body (maximum 51); 8175 decisions contained latent contact-disabled geometry (maximum 51), and 3917 contained bounded inactive-slot memory (maximum 38). 552 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.863776683807373, 'p95': 4.277689615885417, 'max': 8.893898010253906}` / `{'median': 0.881311446428299, 'p95': 4.534307479858398, 'max': 4.707546710968018}` / `{'median': 0.0, 'p95': 3.5998241106669107, 'max': 7.966665983200073}`.
- The issue-time enemy guard retained 11238 observations, detected 3303 during-plan geometry changes, recertified 3303 decisions, and overrode 74 actions. Read/recertificate timing was `{'median': 1.5137000009417534, 'p95': 2.620499988552183, 'max': 152.99380000215024}` / `{'median': 3.2337000011466444, 'p95': 7.102100003976375, 'max': 300.79740000655875}` ms; 8150 issue captures contained latent bodies (maximum 51), and 3915 contained dormant bodies (maximum 38). Fresh/global transactions preserved 3229/3303 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8817 observations (8792 contact enabled, 25 anticipatory, 0 errors). 8817 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8817}`.
- The terminal-threat heuristic covered 11238 decisions with horizon counts `{'0': 496, '10': 10742}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 543, '3': 6678, '4': 2708, '5': 1002, '6': 307}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 266, '2': 955, '3': 7660, '4': 1656, '5': 683, '6': 18}`.
- Adaptive delay supports were `{'1': 17, '1,2': 60, '1,2,3': 204, '1,2,3,4': 189, '1,2,3,4,5': 12, '1,2,3,4,5,6': 74, '2,3': 609, '2,3,4': 2937, '2,3,4,5': 3167, '2,3,4,5,6': 2070, '3,4': 77, '3,4,5': 268, '3,4,5,6': 1221, '4,5,6': 321, '6': 12}`; 285 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 39/229.
- Robust viability supplied 3520 available policy queries (0 had new delay support outside the cached policy), constrained 4 decisions, and exposed 2354 empty queried action sets. Recovery guidance was available/selected on 168/0 empty-kernel queries; distant-kernel guidance was available/selected on 1225/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 559, '1': 505, '2': 415, '3': 333, '4': 407, '5': 459, '6': 403, '7': 439}`.
- Global-horizon/local-prefix cross-tab covered 1198 decisions: 1 had a winning global state but unsafe selected prefix, 568 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 24 selected actions were outside the reported winning set. 1354 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 643 unique policies with solve-time statistics `{'median': 74.25400000647642, 'p95': 185.27590000303462, 'max': 5566.654800000833}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 242.0}`. Policy status counts were `{'queryable': 3504, 'expired': 1108, 'pending_future_epoch': 84}`; 1176 robust-mode decisions had no query.
- Of 5800 unambiguous output transitions, 5452 (0.940) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 2, 'global_viability_kernel_exhausted_before_hit': 12, 'robust_action_set_exhausted_before_hit': 5, 'missing_pre_hit_alive_decision': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 16 hit windows with a positive warning lead; those leads were `[0, 0, 5, 0, 11, 4, 5, 0, 0, 4, 4, 49, 135, 70, 137, 167, 10, 18, 10, 14, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.484 during the 60 frames preceding a hit versus 0.366 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
