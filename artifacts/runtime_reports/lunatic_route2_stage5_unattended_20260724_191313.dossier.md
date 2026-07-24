# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_191313

## Scope And Integrity

- Valid practice scope: `2..45204` (7223 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 28, at `[1934, 4448, 8254, 10690, 11061, 12485, 14270, 22809, 23413, 24500, 25238, 29403, 29714, 30053, 30369, 30707, 31143, 31439, 31801, 32121, 32543, 32884, 33410, 39856, 41629, 42782, 43465, 44729]`.
- Hard no-Bomb verification: **PASS** across 7223 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1934-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 735 bullets and 0 lasers. The projectile model reported pipeline clearance -2.900.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 16 |
| `observed_bullet_overlap` | 11 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 19
- `pool_density_over_1000`: 16
- `playfield_boundary`: 15
- `action_lag_over_model`: 14
- `corridor_deadline_miss`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1934 | nonspell | (376.000, 432.000) | `up_fast` | 735/0 | -2.900/-2.900 | 0f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4448 | nonspell | (199.454, 430.694) | `up_right_fast` | 321/0 | -1.700/-1.700 | 0f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8254 | nonspell | (8.000, 417.921) | `right_fast` | 552/0 | -2.871/-2.871 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10690 | nonspell | (259.886, 348.984) | `up_fast` | 906/0 | 2.014/2.014 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11061 | nonspell | (94.627, 369.373) | `up_right_fast` | 809/0 | -3.898/-9.762 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12485 | nonspell | (8.000, 432.000) | `up_left_fast` | 260/0 | -2.123/-2.123 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14270 | nonspell | (8.000, 432.000) | `up_fast` | 541/0 | -1.439/-4.756 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22809 | 103 幻波「赤眼催眠(マインドブローイング)」 | (172.955, 418.989) | `up_left` | 1080/0 | -3.697/-3.697 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23413 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 847/0 | -0.119/-2.467 | 5f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24500 | 103 幻波「赤眼催眠(マインドブローイング)」 | (48.659, 366.859) | `down_right` | 1010/0 | -4.407/-4.407 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25238 | 103 幻波「赤眼催眠(マインドブローイング)」 | (10.683, 432.000) | `left_fast` | 1217/0 | -4.302/-4.302 | 0f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29403 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (81.379, 432.000) | `down_left` | 922/0 | -9.676/-9.676 | 5f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29714 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (27.315, 332.900) | `up` | 1030/0 | -10.365/-11.215 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 30053 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (8.000, 362.375) | `stay` | 1002/0 | -5.486/-10.508 | 39f/39f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30369 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (176.261, 432.000) | `left_fast` | 1014/0 | -6.485/-8.711 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30707 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (186.593, 329.008) | `left_fast` | 1014/0 | -8.351/-10.996 | 24f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31143 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (132.126, 372.000) | `down_right_fast` | 1006/0 | -3.759/-9.221 | 6f/21f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31439 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (265.571, 386.040) | `down_left` | 1005/0 | -10.250/-11.187 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 31801 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (194.198, 361.442) | `up_left` | 1010/0 | -5.640/-8.492 | 14f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32121 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (208.444, 432.000) | `left` | 1012/0 | -8.673/-9.065 | 15f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32543 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (72.383, 109.113) | `up` | 1026/0 | -10.352/-18.873 | 6f/45f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32884 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (150.813, 330.986) | `up_right_fast` | 996/0 | -10.409/-18.306 | 32f/32f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33410 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (195.892, 432.000) | `right_fast` | 995/0 | -8.148/-10.611 | 31f/50f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39856 | 111 懶惰「生神停止(マインドストッパー)」 | (33.456, 195.045) | `down_right_fast` | 1048/0 | -2.938/-2.938 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41629 | 111 懶惰「生神停止(マインドストッパー)」 | (254.828, 218.198) | `up_right_fast` | 332/0 | -2.309/-2.309 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42782 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.959, 432.000) | `up_right_fast` | 1300/0 | -2.570/-2.570 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43465 | 115 散符「真実の月(インビジブルフルムーン)」 | (259.811, 432.000) | `right_fast` | 1173/0 | -1.929/-9.343 | 4f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44729 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 432.000) | `up_fast` | 1290/0 | -2.111/-2.111 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 4530 | 4397 | 3065 | 0 | 1325 | 940 | 183.462 | 0.206 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 4 | 588 | 575 | 198 | 0 | 377 | 153 | 181.217 | 0.307 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 12 | 777 | 769 | 635 | 0 | 126 | 261 | 117.369 | 0.327 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 650 | 645 | 302 | 0 | 338 | 167 | 131.383 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 678 | 668 | 314 | 0 | 342 | 171 | 73.163 | 0.330 |

## Interpretation

- Retained witnesses classify 11 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 7.000 frames p95. The local plan took 28.531 ms median and 57.242 ms p95.
- The full enemy sensor produced 6164 snapshots; capture read time was `{'median': 32.17269999731798, 'p95': 60.36170001607388, 'max': 102.31519999797456}`, snapshot age was `{'median': 6.0, 'p95': 11.0, 'max': 19.0}` frames, and 7 phase-counter discontinuities were excluded; 5032 decisions retained at least one robust-union body (maximum 46); 2672 decisions contained latent contact-disabled geometry (maximum 43), and 3403 contained bounded inactive-slot memory (maximum 43). 524 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 2.4314727783203125, 'max': 4.668904622395833}` / `{'median': 0.0, 'p95': 2.595299243927002, 'max': 4.697320938110352}` / `{'median': 0.0, 'p95': 1.0, 'max': 4.784840459408967}`.
- The issue-time enemy guard retained 7223 observations, detected 2307 during-plan geometry changes, recertified 2307 decisions, and overrode 870 actions. Read/recertificate timing was `{'median': 2.2382999886758626, 'p95': 4.721600009361282, 'max': 21.791000006487593}` / `{'median': 12.24260000162758, 'p95': 22.15150001575239, 'max': 34.34480002033524}` ms; 2669 issue captures contained latent bodies (maximum 43), and 3405 contained dormant bodies (maximum 43).
- The synchronous spell-owner guard retained 2692 observations (2673 contact enabled, 19 anticipatory, 0 errors). 2692 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 2692}`.
- The terminal-threat heuristic covered 7223 decisions with horizon counts `{'0': 127, '10': 6868, '32': 228}`; it reported 1 collision and 22 sub-safety-clearance warnings, and relaxed 32 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 58, '3': 145, '4': 670, '5': 2728, '6': 3622}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 72, '3': 186, '4': 950, '5': 3710, '6': 2305}`.
- Adaptive delay supports were `{'2,3': 62, '2,3,4': 66, '2,3,4,5': 95, '2,3,4,5,6': 573, '3,4': 18, '3,4,5': 11, '3,4,5,6': 4326, '4,5,6': 1593, '5,6': 444, '6': 35}`; 1123 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 236/184.
- Robust viability supplied 7054 available policy queries (0 had new delay support outside the cached policy), constrained 2508 decisions, and exposed 4514 empty queried action sets. Recovery guidance was available/selected on 538/287 empty-kernel queries; distant-kernel guidance was available/selected on 3549/3247. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 116.48175822848829, 'p95': 320.0, 'max': 509.24257481086556}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1053, '1': 970, '2': 969, '3': 867, '4': 792, '5': 817, '6': 842, '7': 744}`.
- Global-horizon/local-prefix cross-tab covered 3753 decisions: 0 had a winning global state but unsafe selected prefix, 2502 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 5 selected actions were outside the reported winning set. 1474 newer issue-time hazard versions and 3 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1692 unique policies with solve-time statistics `{'median': 151.7811000085203, 'p95': 365.36330002127215, 'max': 484.63449999690056}` and first-observed ages `{'median': 6.0, 'p95': 11.0, 'max': 1808.0}`. Policy status counts were `{'pending_future_epoch': 27, 'queryable': 7054, 'expired': 38}`; 65 robust-mode decisions had no query.
- Of 4085 unambiguous output transitions, 3433 (0.840) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 26, 'missing_pre_hit_alive_decision': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 20 hit windows with a positive warning lead; those leads were `[15, 16, 0, 0, 0, 8, 5, 0, 12, 0, 24, 5, 0, 39, 6, 24, 21, 0, 14, 15, 45, 32, 50, 0, 6, 13, 10, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.506 during the 60 frames preceding a hit versus 0.196 outside those windows.
- Mean selected control-reserve deficit was 6.272 during the 60 frames preceding a hit versus 2.091 outside those windows.
- Soft recovery was selected on 0.021 of alive decisions in the 60-frame pre-hit windows versus 0.050 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
