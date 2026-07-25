# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260725_103655

## Scope And Integrity

- Valid practice scope: `2..45466` (6884 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 34, at `[1804, 4209, 7242, 8023, 11002, 12716, 13652, 14181, 22990, 23474, 23889, 24371, 24816, 25269, 28462, 29436, 29742, 30100, 30526, 30836, 31176, 31487, 32067, 32508, 32922, 33317, 33637, 36096, 39768, 40357, 42848, 43489, 44297, 44989]`.
- Hard no-Bomb verification: **PASS** across 6884 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1804-T1`. It occurred during a nonspell phase at player (345.594, 109.912), with 635 bullets and 0 lasers. The projectile model reported pipeline clearance -1.104.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 23 |
| `observed_bullet_overlap` | 9 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 22
- `fast_mode`: 20
- `pool_density_over_1000`: 20
- `action_lag_over_model`: 18
- `corridor_deadline_miss`: 6
- `enemy_body_absent_from_action_snapshot`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1804 | nonspell | (345.594, 109.912) | `up_right_fast` | 635/0 | -1.104/-1.104 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4209 | nonspell | (376.000, 431.755) | `up_right_fast` | 529/0 | -1.748/-1.748 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7242 | nonspell | (353.495, 414.110) | `left_fast` | 598/0 | 3.652/-0.425 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8023 | nonspell | (8.000, 432.000) | `left` | 686/0 | -2.774/-2.774 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11002 | nonspell | (337.995, 432.000) | `up_left_fast` | 869/0 | 9.593/1.381 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12716 | nonspell | (8.000, 432.000) | `stay` | 255/0 | -1.653/-1.653 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13652 | nonspell | (25.004, 432.000) | `up_left_fast` | 367/0 | -2.054/-15.222 | 15f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14181 | nonspell | (14.505, 432.000) | `right_fast` | 516/0 | -5.609/-5.609 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22990 | 103 幻波「赤眼催眠(マインドブローイング)」 | (189.279, 432.000) | `down_fast` | 1087/0 | -2.905/-2.905 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23474 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 422.542) | `left` | 1053/0 | -3.477/-3.477 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23889 | 103 幻波「赤眼催眠(マインドブローイング)」 | (248.132, 378.332) | `up` | 1042/0 | -3.045/-3.045 | 9f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24371 | 103 幻波「赤眼催眠(マインドブローイング)」 | (329.185, 330.494) | `up_right` | 1061/0 | -3.847/-3.847 | 25f/25f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24816 | 103 幻波「赤眼催眠(マインドブローイング)」 | (208.263, 432.000) | `down_fast` | 1073/0 | -1.638/-1.638 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25269 | 103 幻波「赤眼催眠(マインドブローイング)」 | (192.000, 432.000) | `down_fast` | 1066/0 | -4.758/-4.758 | 0f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28462 | nonspell | (136.419, 432.000) | `up_fast` | 1042/0 | -2.242/-2.242 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29436 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (58.769, 432.000) | `down_fast` | 702/0 | -10.189/-10.189 | 52f/52f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29742 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (270.679, 432.000) | `down` | 989/0 | -8.267/-10.753 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 30100 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (167.052, 268.280) | `down_left_fast` | 1005/0 | -8.723/-34.179 | 48f/48f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30526 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (131.602, 241.101) | `up` | 1015/0 | -8.897/-10.244 | 124f/124f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30836 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (186.191, 194.191) | `down_right_fast` | 1000/0 | -13.389/-13.389 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 31176 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (192.000, 432.000) | `down_fast` | 991/0 | -8.614/-11.089 | 37f/37f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31487 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (240.435, 358.815) | `up_left` | 1029/0 | -9.831/-10.140 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 32067 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (30.769, 176.470) | `up` | 1023/0 | -5.548/-11.188 | 240f/240f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32508 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (278.565, 409.373) | `up_right_fast` | 1005/0 | -9.400/-10.788 | 134f/134f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32922 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (350.119, 282.093) | `stay` | 1005/0 | -9.165/-11.380 | 108f/108f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33317 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (8.000, 317.804) | `up_left` | 1005/0 | -10.216/-10.216 | 44f/84f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33637 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (265.409, 432.000) | `down_left` | 1017/0 | -8.863/-11.239 | 8f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36096 | nonspell | (364.500, 432.000) | `left_fast` | 396/0 | -1.632/-1.632 | 4f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39768 | 111 懶惰「生神停止(マインドストッパー)」 | (8.000, 16.000) | `down_fast` | 600/0 | -13.000/-30.500 | 75f/80f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40357 | 111 懶惰「生神停止(マインドストッパー)」 | (192.267, 161.942) | `stay` | 351/0 | -3.358/-7.700 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42848 | 115 散符「真実の月(インビジブルフルムーン)」 | (141.299, 432.000) | `down_left_fast` | 1076/0 | -2.188/-2.309 | 0f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43489 | 115 散符「真実の月(インビジブルフルムーン)」 | (123.409, 432.000) | `up_fast` | 1165/0 | -2.634/-6.532 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44297 | 115 散符「真実の月(インビジブルフルムーン)」 | (114.262, 432.000) | `up_right_fast` | 1077/0 | -1.972/-6.863 | 5f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44989 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 432.000) | `down_right` | 1153/0 | -0.432/-0.432 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 4433 | 4339 | 2866 | 0 | 1452 | 939 | 161.691 | 0.164 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 6 | 556 | 544 | 112 | 0 | 432 | 128 | 255.119 | 0.067 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 12 | 643 | 634 | 515 | 0 | 110 | 267 | 102.019 | 0.223 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 614 | 609 | 277 | 0 | 324 | 157 | 111.072 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 4 | 638 | 620 | 277 | 0 | 333 | 165 | 76.137 | 0.281 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 2 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 8.000 frames p95. The local plan took 31.061 ms median and 71.462 ms p95.
- The full enemy sensor produced 6186 snapshots; capture read time was `{'median': 21.67139999801293, 'p95': 48.11780000454746, 'max': 91.07419999781996}`, snapshot age was `{'median': 7.0, 'p95': 14.0, 'max': 19.0}` frames, and 5 phase-counter discontinuities were excluded; 6439 decisions retained at least one robust-union body (maximum 42); 2671 decisions contained latent contact-disabled geometry (maximum 41), and 3339 contained bounded inactive-slot memory (maximum 41). 589 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 1.9796498616536458, 'max': 5.293037414550781}` / `{'median': 0.0, 'p95': 2.12131929397583, 'max': 4.678518295288086}` / `{'median': 0.0, 'p95': 1.0, 'max': 5.0895399305555555}`.
- The issue-time enemy guard retained 6884 observations, detected 2171 during-plan geometry changes, recertified 2171 decisions, and overrode 803 actions. Read/recertificate timing was `{'median': 2.1832000056747347, 'p95': 4.530999984126538, 'max': 23.919900006148964}` / `{'median': 16.254199988907203, 'p95': 27.850699989357963, 'max': 42.912500008242205}` ms; 2668 issue captures contained latent bodies (maximum 41), and 3337 contained dormant bodies (maximum 41).
- The synchronous spell-owner guard retained 5054 observations (5036 contact enabled, 18 anticipatory, 0 errors). 5054 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 5054}`.
- The terminal-threat heuristic covered 6884 decisions with horizon counts `{'0': 40, '10': 6617, '32': 227}`; it reported 5 collision and 26 sub-safety-clearance warnings, and relaxed 48 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 42, '3': 110, '4': 351, '5': 2623, '6': 3758}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 50, '3': 197, '4': 645, '5': 3179, '6': 2813}`.
- Adaptive delay supports were `{'2,3': 105, '2,3,4': 13, '2,3,4,5': 51, '2,3,4,5,6': 266, '3,4': 89, '3,4,5': 30, '3,4,5,6': 3734, '4,5': 29, '4,5,6': 2451, '5,6': 116}`; 1074 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 181/215.
- Robust viability supplied 6746 available policy queries (0 had new delay support outside the cached policy), constrained 2651 decisions, and exposed 4047 empty queried action sets. Recovery guidance was available/selected on 582/335 empty-kernel queries; distant-kernel guidance was available/selected on 3189/2903. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 124.96399481450646, 'p95': 342.4149529445231, 'max': 497.80317395532944}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 936, '1': 978, '2': 946, '3': 816, '4': 768, '5': 792, '6': 768, '7': 742}`.
- Global-horizon/local-prefix cross-tab covered 3408 decisions: 0 had a winning global state but unsafe selected prefix, 2137 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 10 selected actions were outside the reported winning set. 1196 newer issue-time hazard versions and 6 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1656 unique policies with solve-time statistics `{'median': 126.43275001028087, 'p95': 414.0775999985635, 'max': 574.338100006571}` and first-observed ages `{'median': 6.0, 'p95': 12.0, 'max': 1787.0}`. Policy status counts were `{'pending_future_epoch': 32, 'queryable': 6744, 'expired': 14}`; 44 robust-mode decisions had no query.
- Of 3689 unambiguous output transitions, 3110 (0.843) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 31, 'missing_pre_hit_alive_decision': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 25 hit windows with a positive warning lead; those leads were `[6, 8, 0, 5, 0, 11, 21, 8, 0, 0, 9, 25, 9, 9, 0, 52, 0, 48, 124, 0, 37, 0, 240, 134, 108, 84, 8, 10, 80, 0, 23, 6, 11, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.391 during the 60 frames preceding a hit versus 0.140 outside those windows.
- Mean selected control-reserve deficit was 9.913 during the 60 frames preceding a hit versus 1.492 outside those windows.
- Soft recovery was selected on 0.033 of alive decisions in the 60-frame pre-hit windows versus 0.055 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
