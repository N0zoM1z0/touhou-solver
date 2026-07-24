# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_152719

## Scope And Integrity

- Valid practice scope: `1..43928` (7571 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 21, at `[12492, 13096, 23152, 23816, 27040, 28041, 28402, 29104, 29948, 30292, 30748, 31215, 31643, 32077, 36304, 38427, 38860, 39633, 40117, 40706, 41768]`.
- Hard no-Bomb verification: **PASS** across 7571 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F12492-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 276 bullets and 0 lasers. The projectile model reported pipeline clearance -3.435.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 17 |
| `observed_bullet_overlap` | 4 |

Contributing factors:

- `playfield_boundary`: 13
- `fast_mode`: 12
- `pool_density_over_1000`: 7
- `action_lag_over_model`: 5
- `corridor_deadline_miss`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 12492 | nonspell | (376.000, 432.000) | `up_fast` | 276/0 | -3.435/-3.435 | 0f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13096 | nonspell | (376.000, 347.863) | `down_fast` | 189/0 | -1.964/-1.964 | 7f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23152 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up` | 880/0 | -1.915/-1.915 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23816 | 103 幻波「赤眼催眠(マインドブローイング)」 | (156.516, 422.242) | `right_fast` | 835/0 | -3.055/-3.881 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27040 | nonspell | (181.530, 432.000) | `up_fast` | 1047/0 | -1.338/-1.338 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28041 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (64.134, 432.000) | `up_left` | 833/0 | -7.682/-8.581 | 47f/53f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28402 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (203.142, 361.289) | `up_left_fast` | 990/0 | -8.072/-10.476 | 41f/41f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29104 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (42.681, 432.000) | `stay` | 1009/0 | -11.187/-11.187 | 9f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29948 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (376.000, 432.000) | `left_fast` | 1014/0 | -6.187/-8.170 | 33f/63f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30292 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (203.601, 415.900) | `down_right_fast` | 998/0 | -6.144/-10.311 | 40f/40f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30748 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (142.393, 377.344) | `stay` | 1022/0 | -7.928/-9.658 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31215 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (139.466, 432.000) | `right_fast` | 1019/0 | -5.986/-10.573 | 13f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31643 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (178.248, 399.358) | `down_right` | 1027/0 | -10.139/-10.139 | 33f/41f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32077 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (376.000, 432.000) | `left_fast` | 990/0 | -8.145/-8.416 | 14f/26f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36304 | nonspell | (8.000, 432.000) | `stay` | 424/0 | -2.187/-2.187 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38427 | 111 懶惰「生神停止(マインドストッパー)」 | (173.480, 432.000) | `stay` | 412/0 | -1.750/-1.750 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38860 | 111 懶惰「生神停止(マインドストッパー)」 | (161.210, 187.558) | `stay` | 338/0 | -2.239/-2.996 | 9f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39633 | 111 懶惰「生神停止(マインドストッパー)」 | (161.940, 196.660) | `up_fast` | 331/0 | -2.801/-2.801 | 6f/39f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40117 | 111 懶惰「生神停止(マインドストッパー)」 | (8.000, 432.000) | `up_fast` | 425/0 | -3.093/-3.093 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40706 | 111 懶惰「生神停止(マインドストッパー)」 | (155.005, 230.495) | `down_left` | 352/0 | -2.937/-2.937 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41768 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 432.000) | `up_fast` | 1145/0 | -2.442/-2.442 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 4913 | 4802 | 2880 | 0 | 1901 | 771 | 342.276 | 0.151 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 399 | 388 | 106 | 0 | 282 | 77 | 263.974 | 0.170 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 9 | 799 | 786 | 656 | 0 | 122 | 252 | 135.710 | 0.262 |
| 111 懶惰「生神停止(マインドストッパー)」 | 5 | 760 | 754 | 182 | 0 | 566 | 155 | 234.990 | 0.162 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 700 | 684 | 440 | 0 | 231 | 143 | 305.960 | 0.419 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 27.847 ms median and 47.502 ms p95.
- The full enemy sensor produced 6135 snapshots; capture read time was `{'median': 31.224199978169054, 'p95': 57.71870000171475, 'max': 93.81219997885637}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 17.0}` frames, and 6 phase-counter discontinuities were excluded; 2807 decisions retained at least one contact-enabled body (maximum 36).
- The synchronous spell-owner guard retained 2658 observations (2640 contact enabled, 18 anticipatory, 0 errors). 2658 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 2658}`.
- The terminal-threat heuristic covered 7571 decisions with horizon counts `{'0': 64, '10': 7317, '32': 190}`; it reported 2 collision and 60 sub-safety-clearance warnings, and relaxed 48 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 47, '3': 184, '4': 912, '5': 4584, '6': 1844}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 54, '3': 100, '4': 2489, '5': 3673, '6': 1255}`.
- Adaptive delay supports were `{'2,3': 51, '2,3,4': 24, '2,3,4,5': 94, '2,3,4,5,6': 473, '3,4,5': 250, '3,4,5,6': 5317, '4,5': 3, '4,5,6': 869, '5,6': 490}`; 288 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 270/220.
- Robust viability supplied 7414 available policy queries (0 had new delay support outside the cached policy), constrained 3102 decisions, and exposed 4264 empty queried action sets. Recovery guidance was available/selected on 763/472 empty-kernel queries; distant-kernel guidance was available/selected on 3312/3155. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 112.0, 'p95': 294.15642097360376, 'max': 477.32588448564155}`, and `{'median': 0.0, 'p95': 25.372583389282227, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1014, '1': 948, '2': 940, '3': 982, '4': 909, '5': 889, '6': 867, '7': 865}`.
- The rolling worker produced 1398 unique policies with solve-time statistics `{'median': 285.00865001115017, 'p95': 474.1574999934528, 'max': 546.5874999936204}` and first-observed ages `{'median': 7.0, 'p95': 13.0, 'max': 1802.0}`. Policy status counts were `{'pending_future_epoch': 31, 'queryable': 7414, 'expired': 22}`; 53 robust-mode decisions had no query.
- Of 4041 unambiguous output transitions, 3471 (0.859) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 21}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[21, 15, 8, 5, 5, 53, 41, 24, 63, 40, 0, 18, 41, 26, 10, 5, 15, 39, 10, 0, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.439 during the 60 frames preceding a hit versus 0.175 outside those windows.
- Mean selected control-reserve deficit was 10.327 during the 60 frames preceding a hit versus 2.634 outside those windows.
- Soft recovery was selected on 0.057 of alive decisions in the 60-frame pre-hit windows versus 0.068 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
