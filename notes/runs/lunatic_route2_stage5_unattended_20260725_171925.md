# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260725_171925

## Scope And Integrity

- Valid practice scope: `2..45392` (6496 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 32, at `[1425, 2068, 2740, 3768, 4416, 8025, 10559, 11323, 12225, 12862, 13633, 14150, 22242, 23238, 24281, 24886, 25386, 28542, 30382, 30774, 31213, 31524, 31870, 32587, 33141, 37902, 38741, 39702, 40350, 41468, 42931, 43687]`.
- Hard no-Bomb verification: **PASS** across 6496 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1425-T1`. It occurred during a nonspell phase at player (376.000, 410.310), with 118 bullets and 0 lasers. The projectile model reported pipeline clearance -1.852.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 20 |
| `observed_bullet_overlap` | 12 |

Contributing factors:

- `playfield_boundary`: 18
- `fast_mode`: 17
- `pool_density_over_1000`: 10
- `action_lag_over_model`: 9
- `corridor_deadline_miss`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1425 | nonspell | (376.000, 410.310) | `left_fast` | 118/0 | -1.852/-1.852 | 9f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2068 | nonspell | (257.875, 432.000) | `down_right` | 431/0 | -0.483/-0.891 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2740 | nonspell | (28.467, 406.049) | `up_right` | 1103/0 | -2.479/-2.479 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3768 | nonspell | (370.414, 392.714) | `up_fast` | 523/0 | -3.546/-3.546 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4416 | nonspell | (160.490, 432.000) | `left_fast` | 507/0 | -3.162/-3.162 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8025 | nonspell | (8.000, 429.172) | `up_left_fast` | 681/0 | -1.856/-1.856 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10559 | nonspell | (182.578, 329.604) | `up_fast` | 756/0 | -23.411/-23.411 | 6f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11323 | nonspell | (49.500, 401.378) | `right` | 904/0 | -2.718/-2.718 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12225 | nonspell | (338.303, 287.882) | `down_left` | 314/0 | -3.706/-3.706 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12862 | nonspell | (376.000, 223.252) | `down` | 329/0 | -1.070/-1.070 | 5f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13633 | nonspell | (39.063, 432.000) | `down_right` | 399/0 | 0.314/-29.559 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14150 | nonspell | (8.000, 425.495) | `up_right_fast` | 523/0 | -5.288/-11.837 | 5f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22242 | nonspell | (43.972, 389.258) | `up_fast` | 474/0 | -3.515/-3.515 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23238 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `left_fast` | 1238/0 | -2.336/-2.336 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24281 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 416.000) | `right` | 1415/0 | -4.285/-4.285 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24886 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 858/0 | -3.599/-3.599 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25386 | 103 幻波「赤眼催眠(マインドブローイング)」 | (247.942, 392.642) | `down_fast` | 1040/0 | -3.785/-3.785 | 7f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28542 | nonspell | (268.658, 432.000) | `up` | 1107/0 | -3.277/-3.277 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30382 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (85.023, 423.868) | `down_right` | 944/0 | -8.832/-8.832 | 30f/81f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30774 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (182.756, 366.133) | `down_left` | 994/0 | -8.717/-9.606 | 82f/82f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31213 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (8.482, 355.980) | `down_right_fast` | 1002/0 | -2.043/-9.811 | 20f/20f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31524 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (265.381, 432.000) | `right_fast` | 994/0 | -8.983/-9.689 | 7f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31870 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (142.725, 390.242) | `right` | 1005/0 | -4.095/-8.435 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32587 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (218.946, 432.000) | `stay` | 1008/0 | -7.389/-9.275 | 65f/240f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33141 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (173.376, 414.584) | `up_fast` | 1011/0 | -1.230/-10.466 | 28f/28f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37902 | nonspell | (94.705, 432.000) | `left_fast` | 452/0 | 2.109/-1.579 | 6f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38741 | nonspell | (376.000, 432.000) | `left_fast` | 457/0 | -2.331/-2.331 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39702 | 111 懶惰「生神停止(マインドストッパー)」 | (376.000, 34.400) | `down` | 689/0 | -4.101/-4.327 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40350 | 111 懶惰「生神停止(マインドストッパー)」 | (166.421, 189.095) | `right` | 338/0 | -1.899/-10.076 | 0f/29f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41468 | 111 懶惰「生神停止(マインドストッパー)」 | (235.715, 206.202) | `down_fast` | 343/0 | -2.764/-3.629 | 6f/33f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42931 | 115 散符「真実の月(インビジブルフルムーン)」 | (36.000, 393.098) | `down_right_fast` | 970/0 | -6.600/-6.600 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43687 | 115 散符「真実の月(インビジブルフルムーン)」 | (281.005, 432.000) | `down_left` | 1143/0 | -2.131/-2.131 | 4f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 16 | 4082 | 3979 | 2476 | 0 | 1486 | 927 | 164.675 | 0.181 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 4 | 554 | 546 | 221 | 0 | 323 | 142 | 148.466 | 0.236 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 7 | 650 | 640 | 535 | 0 | 105 | 212 | 111.874 | 0.266 |
| 111 懶惰「生神停止(マインドストッパー)」 | 3 | 611 | 602 | 194 | 0 | 396 | 153 | 138.547 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 599 | 580 | 341 | 0 | 229 | 160 | 78.168 | 0.427 |

## Interpretation

- Retained witnesses classify 12 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 5.000 frames median and 8.000 frames p95. The local plan took 30.828 ms median and 62.506 ms p95.
- The full enemy sensor produced 5867 snapshots; capture read time was `{'median': 32.81020000576973, 'p95': 64.33540000580251, 'max': 145.57380002224818}`, snapshot age was `{'median': 7.0, 'p95': 11.0, 'max': 18.0}` frames, and 7 phase-counter discontinuities were excluded; 6007 decisions retained at least one robust-union body (maximum 50); 2479 decisions contained latent contact-disabled geometry (maximum 50), and 3273 contained bounded inactive-slot memory (maximum 47). 591 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.349189758300781, 'max': 10.175590515136719}` / `{'median': 0.0, 'p95': 4.410314559936523, 'max': 5.7767181396484375}` / `{'median': 0.0, 'p95': 4.310159683227539, 'max': 5.77659901936849}`.
- The issue-time enemy guard retained 6496 observations, detected 2161 during-plan geometry changes, recertified 2161 decisions, and overrode 722 actions. Read/recertificate timing was `{'median': 1.9802500028163195, 'p95': 4.378299985546619, 'max': 21.099900011904538}` / `{'median': 10.259300004690886, 'p95': 24.052599968854338, 'max': 60.01440004911274}` ms; 2443 issue captures contained latent bodies (maximum 50), and 3276 contained dormant bodies (maximum 47).
- The synchronous spell-owner guard retained 4775 observations (4761 contact enabled, 14 anticipatory, 0 errors). 4775 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 4775}`.
- The terminal-threat heuristic covered 6496 decisions with horizon counts `{'0': 46, '10': 6232, '32': 218}`; it reported 3 collision and 25 sub-safety-clearance warnings, and relaxed 41 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 46, '3': 115, '4': 125, '5': 357, '6': 5853}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 54, '3': 118, '4': 77, '5': 502, '6': 5745}`.
- Adaptive delay supports were `{'2,3': 49, '2,3,4,5,6': 212, '3,4,5': 23, '3,4,5,6': 2036, '4,5,6': 3431, '5,6': 478, '6': 267}`; 976 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 760/79.
- Robust viability supplied 6347 available policy queries (0 had new delay support outside the cached policy), constrained 2539 decisions, and exposed 3767 empty queried action sets. Recovery guidance was available/selected on 506/308 empty-kernel queries; distant-kernel guidance was available/selected on 2902/2632. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 136.7040599250805, 'p95': 360.9764535257113, 'max': 480.2665926337163}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 934, '1': 893, '2': 829, '3': 779, '4': 735, '5': 741, '6': 718, '7': 718}`.
- Global-horizon/local-prefix cross-tab covered 2903 decisions: 1 had a winning global state but unsafe selected prefix, 1688 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 11 selected actions were outside the reported winning set. 1312 newer issue-time hazard versions and 32 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1594 unique policies with solve-time statistics `{'median': 133.80879999022, 'p95': 435.8953000046313, 'max': 597.4431000067852}` and first-observed ages `{'median': 6.0, 'p95': 12.0, 'max': 1797.0}`. Policy status counts were `{'pending_future_epoch': 35, 'queryable': 6348, 'expired': 21}`; 57 robust-mode decisions had no query.
- Of 3827 unambiguous output transitions, 3686 (0.963) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 32}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 22 hit windows with a positive warning lead; those leads were `[16, 0, 0, 0, 5, 6, 6, 0, 0, 5, 6, 10, 0, 0, 7, 5, 7, 0, 81, 82, 20, 7, 6, 240, 28, 12, 5, 0, 29, 33, 0, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.316 during the 60 frames preceding a hit versus 0.193 outside those windows.
- Mean selected control-reserve deficit was 7.840 during the 60 frames preceding a hit versus 5.852 outside those windows.
- Soft recovery was selected on 0.031 of alive decisions in the 60-frame pre-hit windows versus 0.050 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
