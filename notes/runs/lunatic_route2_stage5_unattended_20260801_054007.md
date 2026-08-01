# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_054007

## Scope And Integrity

- Valid practice scope: `1..44953` (11432 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 24, at `[1873, 2268, 2776, 3798, 4189, 11025, 11545, 12844, 13708, 14017, 14513, 23567, 24435, 28982, 30739, 31774, 32579, 33148, 35579, 36895, 39547, 41539, 42728, 44018]`.
- Hard no-Bomb verification: **PASS** across 11432 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1873-T1`. It occurred during a nonspell phase at player (189.162, 253.314), with 217 bullets and 0 lasers. The projectile model reported pipeline clearance -5.188.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 7 |
| `sensor_gap_or_unmodeled_hazard` | 6 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 16
- `playfield_boundary`: 15
- `action_lag_over_model`: 7
- `pool_density_over_1000`: 7

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1873 | nonspell | (189.162, 253.314) | `up_left` | 217/0 | -5.188/-5.188 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2268 | nonspell | (200.085, 409.170) | `right` | 274/0 | 18.975/1.000 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2776 | nonspell | (8.000, 327.348) | `left_fast` | 926/0 | 15.800/-1.199 | 55f/55f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 3798 | nonspell | (370.578, 432.000) | `down_right` | 856/0 | 7.096/3.681 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 4189 | nonspell | (124.000, 412.000) | `right_fast` | 257/0 | 9.060/9.060 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 11025 | nonspell | (37.072, 432.000) | `right_fast` | 884/0 | -3.022/-4.574 | 7f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11545 | nonspell | (376.000, 432.000) | `left_fast` | 884/0 | -13.503/-13.503 | 13f/24f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12844 | nonspell | (24.132, 432.000) | `right_fast` | 300/0 | 0.658/-2.580 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13708 | nonspell | (8.000, 423.090) | `up_right` | 398/0 | 9.132/1.361 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 14017 | nonspell | (198.505, 390.505) | `stay` | 574/0 | -6.431/-6.431 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 14513 | nonspell | (304.079, 426.911) | `stay` | 472/0 | 2.004/-29.268 | 16f/16f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 23567 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 1044/0 | -4.004/-4.004 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 24435 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `down_fast` | 975/0 | -3.091/-3.091 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 28982 | nonspell | (8.000, 432.000) | `up_fast` | 1105/0 | -1.547/-1.547 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30739 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (165.813, 432.000) | `left_fast` | 863/0 | -6.555/-6.555 | 8f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31774 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (182.308, 432.000) | `up_left_fast` | 1023/0 | -5.775/-8.760 | 34f/170f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32579 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (374.374, 430.374) | `up_left` | 1009/0 | -4.916/-7.348 | 15f/28f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33148 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (158.897, 395.810) | `left_fast` | 1014/0 | -4.992/-5.666 | 17f/75f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35579 | nonspell | (13.657, 394.605) | `right_fast` | 458/0 | -2.968/-6.113 | 2f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36895 | nonspell | (376.000, 421.741) | `left_fast` | 423/0 | -1.710/-1.710 | 0f/25f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39547 | 111 懶惰「生神停止(マインドストッパー)」 | (165.942, 183.738) | `up_fast` | 370/0 | -3.214/-3.214 | 0f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41539 | 111 懶惰「生神停止(マインドストッパー)」 | (183.272, 24.485) | `up_left_fast` | 501/0 | 0.810/-2.511 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42728 | 115 散符「真実の月(インビジブルフルムーン)」 | (232.573, 429.172) | `up_left_fast` | 1090/0 | 0.923/-4.770 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44018 | 115 散符「真実の月(インビジブルフルムーン)」 | (268.666, 430.374) | `up_right` | 1084/0 | -0.989/-0.989 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 14 | 7617 | 67 | 49 | 0 | 14 | 11 | 1128.368 | 0.394 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 888 | 367 | 289 | 0 | 0 | 15 | 59.928 | 0.402 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 4 | 861 | 856 | 660 | 0 | 0 | 192 | 77.638 | 0.313 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1044 | 1038 | 550 | 0 | 0 | 180 | 74.292 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1022 | 1015 | 689 | 0 | 0 | 183 | 67.935 | 0.445 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.614 ms median and 31.707 ms p95.
- The full enemy sensor produced 6279 snapshots; capture read time was `{'median': 5.291599984047934, 'p95': 25.654600001871586, 'max': 540.2782000019215}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 118.0}` frames, and 9 phase-counter discontinuities were excluded; 10823 decisions retained at least one robust-union body (maximum 51); 8281 decisions contained latent contact-disabled geometry (maximum 51), and 3935 contained bounded inactive-slot memory (maximum 38). 517 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.0785064697265625, 'max': 8.11578369140625}` / `{'median': 0.8517529368400574, 'p95': 4.534309387207031, 'max': 11.800013542175293}` / `{'median': 4.371138828673793e-08, 'p95': 4.419975280761719, 'max': 11.800013542175293}`.
- The issue-time enemy guard retained 11432 observations, detected 3104 during-plan geometry changes, recertified 3104 decisions, and overrode 37 actions. Read/recertificate timing was `{'median': 1.5235000028042123, 'p95': 2.64320001588203, 'max': 168.17069999524392}` / `{'median': 3.114449980785139, 'p95': 6.87169999582693, 'max': 307.3389000201132}` ms; 8256 issue captures contained latent bodies (maximum 51), and 3933 contained dormant bodies (maximum 38). Fresh/global transactions preserved 3067/3104 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9016 observations (8990 contact enabled, 26 anticipatory, 0 errors). 9016 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9016}`.
- The terminal-threat heuristic covered 11432 decisions with horizon counts `{'0': 497, '10': 10935}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 417, '3': 7265, '4': 2716, '5': 633, '6': 401}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 308, '2': 1048, '3': 7642, '4': 2032, '5': 400, '6': 2}`.
- Adaptive delay supports were `{'1': 48, '1,2': 142, '1,2,3': 63, '1,2,3,4': 166, '1,2,3,4,5': 56, '1,2,3,4,5,6': 19, '2,3': 714, '2,3,4': 2898, '2,3,4,5': 3440, '2,3,4,5,6': 2600, '3,4': 52, '3,4,5': 265, '3,4,5,6': 631, '4,5': 1, '4,5,6': 329, '5,6': 6, '6': 2}`; 184 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 42/237.
- Robust viability supplied 3343 available policy queries (0 had new delay support outside the cached policy), constrained 14 decisions, and exposed 2237 empty queried action sets. Recovery guidance was available/selected on 203/0 empty-kernel queries; distant-kernel guidance was available/selected on 1274/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 510, '1': 506, '2': 365, '3': 337, '4': 375, '5': 430, '6': 387, '7': 433}`.
- Global-horizon/local-prefix cross-tab covered 1191 decisions: 1 had a winning global state but unsafe selected prefix, 552 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 17 selected actions were outside the reported winning set. 1219 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 581 unique policies with solve-time statistics `{'median': 72.22130001173355, 'p95': 180.1215999876149, 'max': 3908.372200006852}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 125.0}`. Policy status counts were `{'queryable': 3328, 'expired': 922, 'pending_future_epoch': 97}`; 1004 robust-mode decisions had no query.
- Of 5835 unambiguous output transitions, 5497 (0.942) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 9, 'unresolved_planner_failure': 4, 'robust_action_set_exhausted_before_hit': 10, 'missing_pre_hit_alive_decision': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[0, 0, 55, 0, 0, 15, 24, 8, 0, 0, 16, 7, 7, 7, 21, 170, 28, 75, 10, 25, 18, 6, 11, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.489 during the 60 frames preceding a hit versus 0.351 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
