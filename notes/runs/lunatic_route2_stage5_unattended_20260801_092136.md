# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_092136

## Scope And Integrity

- Valid practice scope: `1..44200` (11120 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 15, at `[1863, 2171, 2742, 3796, 4243, 7498, 10859, 12466, 13574, 13875, 14407, 35002, 36418, 37900, 39097]`.
- Hard no-Bomb verification: **PASS** across 11120 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1863-T1`. It occurred during a nonspell phase at player (376.000, 420.686), with 538 bullets and 0 lasers. The projectile model reported pipeline clearance 1.920.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `sensor_gap_or_unmodeled_hazard` | 6 |
| `observed_bullet_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 11
- `action_lag_over_model`: 8
- `fast_mode`: 8
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1863 | nonspell | (376.000, 420.686) | `right_fast` | 538/0 | 1.920/1.920 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2171 | nonspell | (192.000, 384.000) | `stay` | 366/0 | 1.233/1.233 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 2742 | nonspell | (103.121, 422.800) | `stay` | 755/0 | 0.567/0.567 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3796 | nonspell | (363.826, 432.000) | `down_fast` | 468/0 | -4.008/-4.008 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 4243 | nonspell | (100.000, 16.000) | `up_fast` | 346/0 | -21.934/-21.934 | 27f/62f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 7498 | nonspell | (18.153, 432.000) | `left` | 782/0 | -3.700/-12.633 | 0f/15f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 10859 | nonspell | (376.000, 432.000) | `up_right` | 872/0 | -2.131/-2.131 | 3f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12466 | nonspell | (376.000, 432.000) | `down_left` | 252/0 | -1.705/-1.705 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13574 | nonspell | (376.000, 139.794) | `up_right_fast` | 368/0 | 5.893/0.949 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 13875 | nonspell | (376.000, 21.657) | `down_right` | 455/0 | 3.480/-7.269 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 14407 | nonspell | (34.049, 430.095) | `stay` | 529/0 | 11.851/6.016 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 35002 | nonspell | (8.000, 419.082) | `down_right_fast` | 478/0 | -1.975/-1.975 | 3f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 36418 | nonspell | (8.000, 417.233) | `down_right_fast` | 392/0 | -2.290/-4.235 | 15f/32f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 37900 | nonspell | (376.000, 432.000) | `left_fast` | 447/0 | -3.174/-3.174 | 3f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39097 | 111 懶惰「生神停止(マインドストッパー)」 | (202.530, 27.878) | `left_fast` | 403/0 | -2.236/-2.236 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 14 | 7658 | 57 | 17 | 0 | 45 | 8 | 1383.888 | 0.405 |
| 103 | 0 | 827 | 471 | 407 | 0 | 0 | 56 | 99.778 | 0.421 |
| 107 | 0 | 664 | 657 | 445 | 0 | 0 | 143 | 76.884 | 0.363 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1016 | 1009 | 709 | 0 | 0 | 177 | 64.404 | 0.002 |
| 115 | 0 | 955 | 947 | 769 | 0 | 0 | 182 | 67.034 | 0.553 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.218 ms median and 31.860 ms p95.
- The full enemy sensor produced 6127 snapshots; capture read time was `{'median': 5.123000009916723, 'p95': 25.96820000326261, 'max': 428.10569997527637}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 95.0}` frames, and 7 phase-counter discontinuities were excluded; 10462 decisions retained at least one robust-union body (maximum 51); 7999 decisions contained latent contact-disabled geometry (maximum 51), and 3784 contained bounded inactive-slot memory (maximum 38). 269 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.684572007921007, 'p95': 4.707550048828125, 'max': 9.541539001464844}` / `{'median': 2.220447540283203, 'p95': 4.6715240478515625, 'max': 5.061916351318359}` / `{'median': 0.049999237060546875, 'p95': 4.254464149475098, 'max': 9.41103286743164}`.
- The issue-time enemy guard retained 11120 observations, detected 2921 during-plan geometry changes, recertified 2921 decisions, and overrode 56 actions. Read/recertificate timing was `{'median': 1.4919999812263995, 'p95': 2.9399000050034374, 'max': 182.0812000078149}` / `{'median': 3.206800000043586, 'p95': 6.8543000088538975, 'max': 346.475600003032}` ms; 7967 issue captures contained latent bodies (maximum 51), and 3779 contained dormant bodies (maximum 38). Fresh/global transactions preserved 2865/2921 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8663 observations (8638 contact enabled, 25 anticipatory, 0 errors). 8663 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8663}`.
- The terminal-threat heuristic covered 11120 decisions with horizon counts `{'0': 537, '10': 10583}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 515, '3': 7148, '4': 2434, '5': 681, '6': 342}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 168, '2': 1827, '3': 7257, '4': 1817, '5': 43, '6': 8}`.
- Adaptive delay supports were `{'1,2': 156, '1,2,3': 214, '1,2,3,4': 490, '1,2,3,4,5': 31, '1,2,3,4,5,6': 55, '2,3': 522, '2,3,4': 3197, '2,3,4,5': 2675, '2,3,4,5,6': 1938, '3,4': 24, '3,4,5': 573, '3,4,5,6': 1224, '4,5': 12, '4,5,6': 1, '6': 8}`; 180 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 26/127.
- Robust viability supplied 3141 available policy queries (0 had new delay support outside the cached policy), constrained 45 decisions, and exposed 2347 empty queried action sets. Recovery guidance was available/selected on 245/0 empty-kernel queries; distant-kernel guidance was available/selected on 1324/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 511, '1': 421, '2': 383, '3': 283, '4': 373, '5': 416, '6': 363, '7': 391}`.
- Global-horizon/local-prefix cross-tab covered 1395 decisions: 5 had a winning global state but unsafe selected prefix, 819 had a losing global state but safe short prefix, 4 selected globally certified actions contradicted the fresh local prefix checker, and 17 selected actions were outside the reported winning set. 1532 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 566 unique policies with solve-time statistics `{'median': 70.24889999593142, 'p95': 160.47790000448003, 'max': 2834.357700019609}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 128.0}`. Policy status counts were `{'queryable': 3127, 'expired': 385, 'pending_future_epoch': 88}`; 459 robust-mode decisions had no query.
- Of 6059 unambiguous output transitions, 5729 (0.946) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 2, 'missing_pre_hit_alive_decision': 2, 'unresolved_planner_failure': 3, 'late_collision_after_positive_causal_margin': 1, 'robust_action_set_exhausted_before_hit': 7}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 8 hit windows with a positive warning lead; those leads were `[0, 0, 0, 0, 62, 15, 8, 8, 0, 0, 0, 8, 32, 5, 12]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.546 during the 60 frames preceding a hit versus 0.378 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 18.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Retained Provenance

- Source worktree based on `b47a495`; candidate used source semantics v11,
  future projection v4, exact ordinary prepublication authority, and the
  observed-body early-kill objective.
- Raw trace SHA-256:
  `88c3a874934e7ff5b3f3f53b47da20cbf9b1d29cc125c4d4ced6c4d80ee75f6d`.
- Verified replay slot 14 SHA-256:
  `60cc4485bc86d56d3c07727aee42e298e4d483659d88608552d5216823072de5`;
  Route 2, Lunatic, Stage 5, empty Bomb list.
- Supervisor exited normally; game, controller, replay helper, and injected
  keys were fully cleaned up.
