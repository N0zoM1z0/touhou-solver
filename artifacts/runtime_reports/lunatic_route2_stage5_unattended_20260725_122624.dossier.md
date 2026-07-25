# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260725_122624

## Scope And Integrity

- Valid practice scope: `2..44065` (8233 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 20, at `[1838, 7733, 12361, 12702, 14390, 23149, 23886, 24513, 28773, 29121, 29426, 30258, 30862, 31306, 32074, 37555, 38354, 39058, 39779, 43800]`.
- Hard no-Bomb verification: **PASS** across 8233 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1838-T1`. It occurred during a nonspell phase at player (376.000, 423.868), with 760 bullets and 0 lasers. The projectile model reported pipeline clearance -1.368.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 12 |
| `observed_bullet_overlap` | 7 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 15
- `fast_mode`: 14
- `pool_density_over_1000`: 8
- `action_lag_over_model`: 3
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1838 | nonspell | (376.000, 423.868) | `up_fast` | 760/0 | -1.368/-1.368 | 0f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7733 | nonspell | (342.636, 432.000) | `right_fast` | 643/0 | -1.191/-7.551 | 14f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12361 | nonspell | (376.000, 295.769) | `up_left_fast` | 338/0 | -2.600/-2.600 | 0f/17f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12702 | nonspell | (8.000, 407.083) | `left_fast` | 253/0 | 0.395/-22.023 | 0f/6f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14390 | nonspell | (323.927, 432.000) | `right_fast` | 208/0 | -1.619/-14.793 | 8f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23149 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `stay` | 891/0 | -2.379/-2.379 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23886 | 103 幻波「赤眼催眠(マインドブローイング)」 | (89.161, 432.000) | `left_fast` | 1258/0 | -5.611/-5.611 | 7f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24513 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 385.442) | `stay` | 1254/0 | -2.955/-3.455 | 8f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28773 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (158.702, 432.000) | `left_fast` | 990/0 | -8.425/-8.425 | 17f/31f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29121 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (166.601, 373.931) | `down_left` | 1006/0 | -6.218/-8.301 | 48f/48f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29426 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (204.586, 408.000) | `stay` | 1013/0 | -8.059/-8.778 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 30258 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (124.970, 432.000) | `down_fast` | 991/0 | -7.177/-8.607 | 5f/41f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30862 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (376.000, 432.000) | `left_fast` | 1010/0 | -8.144/-8.322 | 74f/79f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31306 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (205.376, 432.000) | `down_right` | 1007/0 | -2.830/-9.160 | 130f/136f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32074 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (155.293, 390.600) | `down_fast` | 1014/0 | -4.611/-8.523 | 57f/85f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37555 | nonspell | (376.000, 416.282) | `up_fast` | 427/0 | -0.252/-0.252 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38354 | 111 懶惰「生神停止(マインドストッパー)」 | (8.000, 50.798) | `right_fast` | 232/0 | -4.048/-4.048 | 3f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39058 | 111 懶惰「生神停止(マインドストッパー)」 | (228.885, 210.676) | `down` | 337/0 | -4.047/-4.047 | 4f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39779 | 111 懶惰「生神停止(マインドストッパー)」 | (200.859, 197.801) | `right_fast` | 345/0 | -3.878/-3.878 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43800 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 432.000) | `up_fast` | 1274/0 | -1.129/-1.129 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 5287 | 5181 | 3469 | 0 | 1676 | 963 | 147.006 | 0.177 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 3 | 509 | 502 | 185 | 0 | 317 | 106 | 143.539 | 0.300 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 7 | 878 | 869 | 714 | 0 | 153 | 250 | 97.992 | 0.335 |
| 111 懶惰「生神停止(マインドストッパー)」 | 3 | 785 | 771 | 300 | 0 | 462 | 165 | 121.791 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 774 | 754 | 579 | 0 | 170 | 166 | 61.416 | 0.431 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 22.432 ms median and 42.514 ms p95.
- The full enemy sensor produced 6243 snapshots; capture read time was `{'median': 21.691599977202713, 'p95': 42.77570001431741, 'max': 75.43009999790229}`, snapshot age was `{'median': 6.0, 'p95': 10.0, 'max': 15.0}` frames, and 6 phase-counter discontinuities were excluded; 7744 decisions retained at least one robust-union body (maximum 42); 3097 decisions contained latent contact-disabled geometry (maximum 41), and 4046 contained bounded inactive-slot memory (maximum 41). 426 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 3.5004043579101562, 'max': 6.202446356052306}` / `{'median': 0.0, 'p95': 2.969846725463867, 'max': 4.707546710968018}` / `{'median': 0.0, 'p95': 1.0, 'max': 6.246059666955617}`.
- The issue-time enemy guard retained 8233 observations, detected 2269 during-plan geometry changes, recertified 2269 decisions, and overrode 787 actions. Read/recertificate timing was `{'median': 1.8338999943807721, 'p95': 3.9130000513978302, 'max': 19.18510001269169}` / `{'median': 9.285999985877424, 'p95': 18.235999974422157, 'max': 27.75649999966845}` ms; 3092 issue captures contained latent bodies (maximum 41), and 4043 contained dormant bodies (maximum 41).
- The synchronous spell-owner guard retained 5972 observations (5953 contact enabled, 19 anticipatory, 0 errors). 5972 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 5972}`.
- The terminal-threat heuristic covered 8233 decisions with horizon counts `{'0': 45, '10': 8012, '32': 176}`; it reported 0 collision and 40 sub-safety-clearance warnings, and relaxed 52 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 51, '3': 340, '4': 3146, '5': 3630, '6': 1066}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 56, '3': 440, '4': 5177, '5': 1794, '6': 766}`.
- Adaptive delay supports were `{'2,3': 154, '2,3,4': 27, '2,3,4,5': 199, '2,3,4,5,6': 746, '3,4': 92, '3,4,5': 239, '3,4,5,6': 6072, '4,5,6': 266, '5,6': 438}`; 1091 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 75/332.
- Robust viability supplied 8077 available policy queries (0 had new delay support outside the cached policy), constrained 2778 decisions, and exposed 5247 empty queried action sets. Recovery guidance was available/selected on 700/396 empty-kernel queries; distant-kernel guidance was available/selected on 3966/3748. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 128.9961239727768, 'p95': 357.77087639996637, 'max': 480.2665926337163}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1223, '1': 1105, '2': 1039, '3': 995, '4': 910, '5': 927, '6': 921, '7': 957}`.
- Global-horizon/local-prefix cross-tab covered 4803 decisions: 1 had a winning global state but unsafe selected prefix, 3124 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 19 selected actions were outside the reported winning set. 1630 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1650 unique policies with solve-time statistics `{'median': 115.86064999573864, 'p95': 408.58349998597987, 'max': 529.7883999883197}` and first-observed ages `{'median': 4.0, 'p95': 10.0, 'max': 1809.0}`. Policy status counts were `{'pending_future_epoch': 36, 'queryable': 8075, 'expired': 34}`; 68 robust-mode decisions had no query.
- Of 4652 unambiguous output transitions, 3868 (0.831) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 19, 'missing_pre_hit_alive_decision': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[9, 24, 17, 6, 18, 7, 15, 8, 31, 48, 0, 41, 79, 136, 85, 4, 7, 13, 9, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.329 during the 60 frames preceding a hit versus 0.202 outside those windows.
- Mean selected control-reserve deficit was 9.771 during the 60 frames preceding a hit versus 4.739 outside those windows.
- Soft recovery was selected on 0.062 of alive decisions in the 60-frame pre-hit windows versus 0.048 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
