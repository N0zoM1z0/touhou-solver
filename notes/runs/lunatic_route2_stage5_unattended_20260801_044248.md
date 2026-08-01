# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_044248

## Scope And Integrity

- Valid practice scope: `1..41757` (10653 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 13, at `[1863, 2427, 2757, 4200, 13607, 14407, 23775, 24853, 29213, 35366, 36567, 37653, 41277]`.
- Hard no-Bomb verification: **PASS** across 10653 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1863-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 735 bullets and 0 lasers. The projectile model reported pipeline clearance 1.557.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 3 |
| `sensor_gap_or_unmodeled_hazard` | 2 |

Contributing factors:

- `playfield_boundary`: 10
- `fast_mode`: 8
- `action_lag_over_model`: 5
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1863 | nonspell | (376.000, 432.000) | `down_right_fast` | 735/0 | 1.557/1.557 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2427 | nonspell | (8.000, 432.000) | `down_left` | 364/0 | -0.034/-0.034 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 2757 | nonspell | (263.030, 432.000) | `down_left` | 904/0 | 11.731/3.853 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 4200 | nonspell | (42.524, 368.000) | `up_fast` | 579/0 | -3.896/-3.896 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 13607 | nonspell | (368.000, 428.747) | `down_left_fast` | 31/0 | -1.092/-1.384 | 2f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 14407 | nonspell | (102.240, 428.747) | `right` | 466/0 | -4.466/-4.466 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 23775 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `stay` | 1089/0 | -2.020/-2.020 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24853 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 1037/0 | -2.390/-2.390 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29213 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (192.831, 432.000) | `right_fast` | 1000/0 | -5.154/-5.154 | 13f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35366 | nonspell | (368.000, 432.000) | `up_fast` | 469/0 | -2.188/-2.188 | 3f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36567 | 111 懶惰「生神停止(マインドストッパー)」 | (160.156, 23.779) | `up_right_fast` | 434/0 | -3.965/-3.965 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37653 | 111 懶惰「生神停止(マインドストッパー)」 | (192.864, 28.000) | `stay` | 499/0 | -1.732/-1.732 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41277 | 115 散符「真実の月(インビジブルフルムーン)」 | (13.052, 432.000) | `right_fast` | 1309/0 | -2.814/-2.861 | 3f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 7155 | 0 | 0 | 0 | 0 | 0 | - | 0.365 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 822 | 787 | 405 | 0 | 0 | 144 | 112.628 | 0.372 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 652 | 646 | 448 | 0 | 0 | 141 | 78.031 | 0.268 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1037 | 1030 | 531 | 0 | 0 | 180 | 71.741 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 987 | 980 | 748 | 0 | 0 | 182 | 67.166 | 0.461 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.387 ms median and 33.690 ms p95.
- The full enemy sensor produced 5781 snapshots; capture read time was `{'median': 5.4106000025058165, 'p95': 25.34699998795986, 'max': 118.6262999981409}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 22.0}` frames, and 7 phase-counter discontinuities were excluded; 9944 decisions retained at least one robust-union body (maximum 42); 7516 decisions contained latent contact-disabled geometry (maximum 42), and 3933 contained bounded inactive-slot memory (maximum 36). 243 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.0, 'p95': 4.5816650390625, 'max': 7.56719970703125}` / `{'median': 1.0, 'p95': 4.581647872924805, 'max': 4.707547664642334}` / `{'median': 8.742277657347586e-08, 'p95': 1.28546142578125, 'max': 3.6499996185302734}`.
- The issue-time enemy guard retained 10653 observations, detected 3280 during-plan geometry changes, recertified 3280 decisions, and overrode 44 actions. Read/recertificate timing was `{'median': 1.6465000080643222, 'p95': 3.2918999932007864, 'max': 67.2913000016706}` / `{'median': 3.049449995160103, 'p95': 6.454599992139265, 'max': 97.32679999433458}` ms; 7495 issue captures contained latent bodies (maximum 42), and 3932 contained dormant bodies (maximum 36). Fresh/global transactions preserved 3236/3280 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 7619 observations (7594 contact enabled, 25 anticipatory, 0 errors). 7619 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 7619}`.
- The terminal-threat heuristic covered 10653 decisions with horizon counts `{'0': 605, '10': 10048}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 439, '3': 5820, '4': 2814, '5': 800, '6': 780}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 314, '2': 187, '3': 7613, '4': 2329, '5': 210}`.
- Adaptive delay supports were `{'1': 123, '1,2': 95, '1,2,3': 31, '1,2,3,4': 80, '1,2,3,4,5': 168, '1,2,3,4,5,6': 262, '2,3': 404, '2,3,4': 1859, '2,3,4,5': 2581, '2,3,4,5,6': 3525, '3,4': 11, '3,4,5': 480, '3,4,5,6': 1021, '4,5,6': 13}`; 176 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 39/192.
- Robust viability supplied 3443 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 2132 empty queried action sets. Recovery guidance was available/selected on 183/0 empty-kernel queries; distant-kernel guidance was available/selected on 1250/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 568, '1': 515, '2': 379, '3': 325, '4': 393, '5': 443, '6': 425, '7': 395}`.
- Global-horizon/local-prefix cross-tab covered 1295 decisions: 2 had a winning global state but unsafe selected prefix, 664 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 14 selected actions were outside the reported winning set. 1412 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 647 unique policies with solve-time statistics `{'median': 76.84930000687018, 'p95': 179.84959999739658, 'max': 223.7539000052493}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 8.0}`. Policy status counts were `{'pending_future_epoch': 42, 'queryable': 3443, 'expired': 1}`; 43 robust-mode decisions had no query.
- Of 5343 unambiguous output transitions, 5022 (0.940) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 2, 'robust_action_set_exhausted_before_hit': 3, 'late_collision_after_positive_causal_margin': 2, 'global_viability_kernel_exhausted_before_hit': 6}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[0, 7, 0, 0, 6, 0, 5, 4, 21, 6, 4, 6, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.568 during the 60 frames preceding a hit versus 0.331 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
