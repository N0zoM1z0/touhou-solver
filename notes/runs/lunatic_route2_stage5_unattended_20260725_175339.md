# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260725_175339

## Scope And Integrity

- Valid practice scope: `2..46335` (7216 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 27, at `[2162, 4287, 8042, 10694, 11183, 12311, 12743, 14117, 14453, 23025, 23683, 24942, 28462, 31422, 32303, 32721, 33173, 33812, 34232, 38627, 40523, 41228, 42665, 43875, 44538, 45427, 46095]`.
- Hard no-Bomb verification: **PASS** across 7216 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2162-T1`. It occurred during a nonspell phase at player (316.399, 415.029), with 606 bullets and 0 lasers. The projectile model reported pipeline clearance -2.913.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 17 |
| `observed_bullet_overlap` | 10 |

Contributing factors:

- `fast_mode`: 17
- `playfield_boundary`: 17
- `pool_density_over_1000`: 12
- `action_lag_over_model`: 5
- `corridor_deadline_miss`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2162 | nonspell | (316.399, 415.029) | `up_right_fast` | 606/0 | -2.913/-6.494 | 4f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4287 | nonspell | (368.546, 432.000) | `up_left_fast` | 367/0 | -3.825/-3.825 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8042 | nonspell | (376.000, 425.495) | `left_fast` | 678/0 | -2.260/-2.260 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10694 | nonspell | (351.477, 408.029) | `right_fast` | 894/0 | -0.025/-0.025 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11183 | nonspell | (376.000, 432.000) | `stay` | 899/0 | -1.896/-6.115 | 0f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12311 | nonspell | (376.000, 18.300) | `down_right` | 294/0 | -2.485/-4.646 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12743 | nonspell | (75.721, 432.000) | `up_left` | 133/0 | -2.593/-15.606 | 14f/30f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14117 | nonspell | (193.439, 432.000) | `right_fast` | 491/0 | -3.583/-3.583 | 4f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14453 | nonspell | (278.048, 432.000) | `up_left_fast` | 491/0 | -1.955/-1.955 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23025 | 103 幻波「赤眼催眠(マインドブローイング)」 | (258.714, 418.989) | `up_right` | 1093/0 | -4.890/-4.890 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23683 | 103 幻波「赤眼催眠(マインドブローイング)」 | (341.557, 432.000) | `up_right_fast` | 1225/0 | -2.249/-4.222 | 19f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24942 | 103 幻波「赤眼催眠(マインドブローイング)」 | (355.300, 415.939) | `left` | 1442/0 | -3.940/-3.940 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28462 | nonspell | (70.425, 391.029) | `down_left_fast` | 1030/0 | 0.527/0.527 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31422 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (126.654, 378.189) | `up_left_fast` | 990/0 | -9.019/-9.780 | 69f/91f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32303 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (220.024, 432.000) | `right_fast` | 1019/0 | -7.805/-9.809 | 55f/236f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32721 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (156.904, 418.989) | `up_right` | 1001/0 | -6.877/-6.877 | 13f/113f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33173 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (121.781, 432.000) | `left_fast` | 983/0 | -6.439/-7.060 | 10f/30f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33812 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (152.282, 429.172) | `up_left_fast` | 1019/0 | -9.324/-9.324 | 18f/176f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34232 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (147.635, 432.000) | `down_right_fast` | 1016/0 | -8.997/-8.997 | 12f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38627 | nonspell | (8.000, 361.526) | `up_right` | 380/0 | -2.582/-2.582 | 4f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40523 | 111 懶惰「生神停止(マインドストッパー)」 | (63.864, 94.868) | `down_left` | 233/0 | -3.106/-6.728 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41228 | 111 懶惰「生神停止(マインドストッパー)」 | (215.394, 199.742) | `up_left_fast` | 340/0 | -2.719/-2.719 | 0f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42665 | 111 懶惰「生神停止(マインドストッパー)」 | (188.536, 174.351) | `up` | 388/0 | -3.233/-3.233 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43875 | 115 散符「真実の月(インビジブルフルムーン)」 | (372.969, 432.000) | `right_fast` | 1177/0 | -1.993/-8.033 | 5f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44538 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 432.000) | `up_right_fast` | 1165/0 | -1.374/-1.374 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45427 | 115 散符「真実の月(インビジブルフルムーン)」 | (213.021, 432.000) | `up_fast` | 1194/0 | -3.116/-3.116 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 46095 | 115 散符「真実の月(インビジブルフルムーン)」 | (116.142, 432.000) | `up_left` | 1163/0 | -1.139/-1.139 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 11 | 4705 | 4603 | 3305 | 0 | 1281 | 1007 | 164.689 | 0.224 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 3 | 536 | 519 | 244 | 0 | 275 | 148 | 138.937 | 0.310 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 6 | 698 | 691 | 590 | 0 | 99 | 221 | 109.498 | 0.350 |
| 111 懶惰「生神停止(マインドストッパー)」 | 3 | 631 | 618 | 226 | 0 | 389 | 156 | 136.105 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 4 | 646 | 636 | 308 | 0 | 323 | 165 | 86.317 | 0.400 |

## Interpretation

- Retained witnesses classify 10 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 5.000 frames median and 7.000 frames p95. The local plan took 29.216 ms median and 58.284 ms p95.
- The full enemy sensor produced 6430 snapshots; capture read time was `{'median': 31.940800021402538, 'p95': 62.47289996827021, 'max': 154.07219994813204}`, snapshot age was `{'median': 6.0, 'p95': 10.0, 'max': 16.0}` frames, and 6 phase-counter discontinuities were excluded; 6839 decisions retained at least one robust-union body (maximum 42); 2644 decisions contained latent contact-disabled geometry (maximum 41), and 3438 contained bounded inactive-slot memory (maximum 41). 471 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.093038082122803, 'max': 5.124987284342448}` / `{'median': 0.7710329294204712, 'p95': 4.110498428344727, 'max': 4.710229396820068}` / `{'median': 0.0, 'p95': 1.0, 'max': 6.387526988983154}`.
- The issue-time enemy guard retained 7216 observations, detected 2206 during-plan geometry changes, recertified 2206 decisions, and overrode 835 actions. Read/recertificate timing was `{'median': 1.9514999876264483, 'p95': 4.354499978944659, 'max': 24.68199998838827}` / `{'median': 10.679850005544722, 'p95': 24.669200007338077, 'max': 48.15530002815649}` ms; 2631 issue captures contained latent bodies (maximum 41), and 3437 contained dormant bodies (maximum 41).
- The synchronous spell-owner guard retained 5404 observations (5388 contact enabled, 16 anticipatory, 0 errors). 5404 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 5404}`.
- The terminal-threat heuristic covered 7216 decisions with horizon counts `{'0': 50, '10': 6964, '32': 202}`; it reported 1 collision and 29 sub-safety-clearance warnings, and relaxed 27 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 52, '3': 129, '4': 188, '5': 2082, '6': 4765}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 63, '3': 150, '4': 417, '5': 4303, '6': 2283}`.
- Adaptive delay supports were `{'1,2,3': 8, '1,2,3,4': 6, '2,3': 76, '2,3,4': 29, '2,3,4,5': 29, '2,3,4,5,6': 354, '3,4': 55, '3,4,5': 44, '3,4,5,6': 3313, '4,5,6': 2727, '5,6': 575}`; 1133 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 306/122.
- Robust viability supplied 7067 available policy queries (0 had new delay support outside the cached policy), constrained 2367 decisions, and exposed 4673 empty queried action sets. Recovery guidance was available/selected on 579/323 empty-kernel queries; distant-kernel guidance was available/selected on 3700/3420. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 144.88616221019868, 'p95': 351.2719744016024, 'max': 520.430590953299}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1077, '1': 980, '2': 960, '3': 837, '4': 801, '5': 774, '6': 813, '7': 825}`.
- Global-horizon/local-prefix cross-tab covered 3802 decisions: 2 had a winning global state but unsafe selected prefix, 2525 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 5 selected actions were outside the reported winning set. 1446 newer issue-time hazard versions and 5 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1697 unique policies with solve-time statistics `{'median': 135.04989998182282, 'p95': 423.95560001023114, 'max': 596.9418000313453}` and first-observed ages `{'median': 5.0, 'p95': 11.0, 'max': 1796.0}`. Policy status counts were `{'pending_future_epoch': 46, 'queryable': 7071, 'expired': 14}`; 64 robust-mode decisions had no query.
- Of 4388 unambiguous output transitions, 4057 (0.925) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 27}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 22 hit windows with a positive warning lead; those leads were `[23, 13, 4, 0, 17, 9, 30, 17, 4, 0, 19, 0, 4, 91, 236, 113, 30, 176, 18, 10, 0, 22, 0, 9, 5, 6, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.427 during the 60 frames preceding a hit versus 0.223 outside those windows.
- Mean selected control-reserve deficit was 8.888 during the 60 frames preceding a hit versus 5.174 outside those windows.
- Soft recovery was selected on 0.006 of alive decisions in the 60-frame pre-hit windows versus 0.052 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
