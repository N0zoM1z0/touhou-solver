# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_193820

## Scope And Integrity

- Valid practice scope: `2..45403` (13586 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 20, at `[1489, 2482, 3544, 3869, 4408, 6958, 11344, 11668, 12321, 13041, 14090, 23701, 24360, 25438, 30612, 31847, 33466, 42019, 42969, 43690]`.
- Hard no-Bomb verification: **PASS** across 13586 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1489-T1`. It occurred during a nonspell phase at player (364.247, 432.000), with 86 bullets and 0 lasers. The projectile model reported pipeline clearance -0.189.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 9 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `fast_mode`: 18
- `playfield_boundary`: 15
- `pool_density_over_1000`: 6
- `enemy_body_absent_from_action_snapshot`: 2
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1489 | nonspell | (364.247, 432.000) | `down_left_fast` | 86/0 | -0.189/-3.304 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2482 | nonspell | (376.000, 432.000) | `up_left_fast` | 484/0 | -1.914/-1.914 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3544 | nonspell | (10.300, 432.000) | `up_right` | 368/0 | 0.025/-8.573 | 9f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3869 | nonspell | (9.626, 394.998) | `down_right_fast` | 661/0 | 1.473/-5.022 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4408 | nonspell | (10.828, 414.458) | `down_fast` | 518/0 | -0.517/-23.013 | 14f/20f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 6958 | nonspell | (345.449, 420.000) | `up_fast` | 504/0 | 56.866/-17.033 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11344 | nonspell | (119.288, 396.147) | `up_fast` | 928/0 | -1.500/-21.684 | 26f/32f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11668 | nonspell | (331.462, 393.782) | `up_fast` | 726/0 | -13.230/-19.582 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12321 | nonspell | (370.343, 405.094) | `left_fast` | 309/0 | 3.179/0.050 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13041 | nonspell | (41.877, 432.000) | `right_fast` | 298/0 | -1.788/-1.788 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14090 | nonspell | (12.000, 432.000) | `right_fast` | 566/0 | -4.015/-5.578 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23701 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 1087/0 | -3.172/-3.172 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24360 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 859/0 | -2.641/-2.641 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25438 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 1037/0 | -2.296/-2.296 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30612 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (75.731, 432.000) | `up_right_fast` | 983/0 | -5.336/-7.820 | 3f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31847 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (14.505, 432.000) | `up_right_fast` | 1007/0 | -5.810/-7.297 | 27f/61f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33466 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (208.742, 432.000) | `left_fast` | 1015/0 | -6.015/-6.853 | 10f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42019 | 111 懶惰「生神停止(マインドストッパー)」 | (154.324, 16.000) | `right_fast` | 434/0 | -1.957/-1.957 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42969 | 115 散符「真実の月(インビジブルフルムーン)」 | (268.444, 432.000) | `up_left_fast` | 1083/0 | -2.571/-3.484 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43690 | 115 散符「真実の月(インビジブルフルムーン)」 | (254.298, 429.700) | `up` | 1163/0 | -1.739/-2.189 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 11 | 8942 | 8799 | 6424 | 0 | 2353 | 1139 | 112.574 | 0.247 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 3 | 1026 | 1012 | 519 | 0 | 487 | 176 | 107.823 | 0.268 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 3 | 1188 | 1178 | 943 | 0 | 234 | 234 | 77.980 | 0.362 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1185 | 1177 | 703 | 0 | 467 | 178 | 79.470 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1245 | 1229 | 649 | 0 | 571 | 184 | 57.192 | 0.349 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 2 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 10.663 ms median and 21.985 ms p95.
- The full enemy sensor produced 7064 snapshots; capture read time was `{'median': 5.613299959804863, 'p95': 23.86420010589063, 'max': 49.91100006736815}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 11.0}` frames, and 6 phase-counter discontinuities were excluded; 12881 decisions retained at least one robust-union body (maximum 48); 5105 decisions contained latent contact-disabled geometry (maximum 48), and 6864 contained bounded inactive-slot memory (maximum 45). 340 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.534290313720703, 'max': 6.7604827880859375}` / `{'median': 0.7816059291362762, 'p95': 4.5342912673950195, 'max': 6.06666374206543}` / `{'median': 4.371138828673793e-08, 'p95': 2.6499977111816406, 'max': 12.13332748413086}`.
- The issue-time enemy guard retained 13586 observations, detected 2652 during-plan geometry changes, recertified 2652 decisions, and overrode 63 actions. Read/recertificate timing was `{'median': 1.7383999656885862, 'p95': 3.3780999947339296, 'max': 12.835799949243665}` / `{'median': 3.125699993688613, 'p95': 5.95889997202903, 'max': 12.995800003409386}` ms; 5075 issue captures contained latent bodies (maximum 48), and 6872 contained dormant bodies (maximum 45). Fresh/global transactions preserved 2589/2652 planned actions, relaxed 6 fresh/global empty intersections, inherited 11 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9964 observations (9936 contact enabled, 28 anticipatory, 0 errors). 9964 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9964}`.
- The terminal-threat heuristic covered 13586 decisions with horizon counts `{'0': 74, '10': 13356, '32': 156}`; it reported 1 collision and 50 sub-safety-clearance warnings, and relaxed 45 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1520, '3': 10440, '4': 1612, '5': 14}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 11, '2': 4640, '3': 7314, '4': 1621}`.
- Adaptive delay supports were `{'1,2,3': 252, '1,2,3,4': 93, '2,3': 1029, '2,3,4': 6484, '2,3,4,5': 3456, '2,3,4,5,6': 1229, '3,4': 1, '3,4,5': 183, '3,4,5,6': 849, '4,5,6': 10}`; 135 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 16/168.
- Robust viability supplied 13395 available policy queries (0 had new delay support outside the cached policy), constrained 4112 decisions, and exposed 9238 empty queried action sets. Recovery guidance was available/selected on 954/367 empty-kernel queries; distant-kernel guidance was available/selected on 7655/7342. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 143.10835055998655, 'p95': 342.4149529445231, 'max': 532.8264257710948}`, and `{'median': 0.0, 'p95': 20.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2100, '1': 1753, '2': 1425, '3': 1608, '4': 1562, '5': 1631, '6': 1677, '7': 1639}`.
- Global-horizon/local-prefix cross-tab covered 8498 decisions: 1 had a winning global state but unsafe selected prefix, 6112 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 19 selected actions were outside the reported winning set. 2114 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1911 unique policies with solve-time statistics `{'median': 94.45189998950809, 'p95': 295.7417999859899, 'max': 427.2423000074923}` and first-observed ages `{'median': 2.0, 'p95': 6.0, 'max': 1798.0}`. Policy status counts were `{'pending_future_epoch': 70, 'queryable': 13396, 'expired': 13}`; 84 robust-mode decisions had no query.
- Of 7102 unambiguous output transitions, 6530 (0.919) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 20}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 17 hit windows with a positive warning lead; those leads were `[5, 4, 14, 7, 20, 0, 32, 0, 0, 7, 6, 8, 7, 7, 13, 61, 23, 3, 6, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.583 during the 60 frames preceding a hit versus 0.228 outside those windows.
- Mean selected control-reserve deficit was 11.884 during the 60 frames preceding a hit versus 3.944 outside those windows.
- Soft recovery was selected on 0.011 of alive decisions in the 60-frame pre-hit windows versus 0.030 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
