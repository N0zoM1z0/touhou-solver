# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_104835

## Scope And Integrity

- Valid practice scope: `1..44812` (11067 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 16, at `[1867, 3844, 4177, 8014, 13117, 14412, 23774, 25064, 32999, 35415, 38434, 39902, 41554, 42407, 43070, 43539]`.
- Hard no-Bomb verification: **PASS** across 11067 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1867-T1`. It occurred during a nonspell phase at player (376.000, 406.973), with 291 bullets and 0 lasers. The projectile model reported pipeline clearance 52.646.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 5 |
| `sensor_gap_or_unmodeled_hazard` | 4 |

Contributing factors:

- `fast_mode`: 11
- `playfield_boundary`: 10
- `pool_density_over_1000`: 6
- `action_lag_over_model`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1867 | nonspell | (376.000, 406.973) | `right_fast` | 291/0 | 52.646/25.163 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3844 | nonspell | (371.532, 299.191) | `up` | 385/0 | -2.899/-27.659 | 42f/42f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 4177 | nonspell | (340.000, 432.000) | `left_fast` | 256/0 | -5.873/-5.873 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 8014 | nonspell | (273.739, 415.868) | `up_fast` | 794/0 | 8.108/7.299 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 13117 | nonspell | (322.430, 427.400) | `up_left` | 162/0 | 6.046/-0.144 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 14412 | nonspell | (136.558, 425.505) | `left` | 514/0 | 12.180/12.180 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 23774 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left` | 1089/0 | -1.381/-1.381 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 25064 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 1077/0 | -2.113/-2.113 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32999 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (194.950, 428.000) | `up_left_fast` | 1010/0 | -7.909/-7.909 | 5f/145f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35415 | nonspell | (8.000, 420.000) | `right_fast` | 444/0 | -3.459/-3.459 | 2f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 38434 | nonspell | (8.000, 428.747) | `right_fast` | 382/0 | -3.982/-3.982 | 0f/13f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39902 | 111 懶惰「生神停止(マインドストッパー)」 | (190.315, 39.000) | `left_fast` | 489/0 | -2.018/-2.018 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41554 | 111 懶惰「生神停止(マインドストッパー)」 | (188.868, 200.786) | `up_left_fast` | 359/0 | -1.862/-3.044 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42407 | 115 散符「真実の月(インビジブルフルムーン)」 | (243.449, 428.000) | `up_fast` | 1184/0 | 0.580/-1.629 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43070 | 115 散符「真実の月(インビジブルフルムーン)」 | (257.112, 432.000) | `up_left_fast` | 1173/0 | -3.431/-3.490 | 4f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43539 | 115 散符「真実の月(インビジブルフルムーン)」 | (134.002, 432.000) | `up_right` | 1055/0 | -2.092/-2.092 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 7175 | 46 | 21 | 0 | 36 | 6 | 1133.340 | 0.401 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 964 | 551 | 325 | 0 | 0 | 54 | 122.387 | 0.371 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 840 | 833 | 635 | 0 | 0 | 185 | 76.882 | 0.380 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1037 | 1030 | 568 | 0 | 0 | 180 | 70.615 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 1051 | 1043 | 691 | 0 | 0 | 186 | 68.856 | 0.506 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.520 ms median and 32.224 ms p95.
- The full enemy sensor produced 6088 snapshots; capture read time was `{'median': 5.245750013273209, 'p95': 26.416300010168925, 'max': 364.4346999935806}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 115.0}` frames, and 13 phase-counter discontinuities were excluded; 10466 decisions retained at least one robust-union body (maximum 49); 7992 decisions contained latent contact-disabled geometry (maximum 49), and 3796 contained bounded inactive-slot memory (maximum 38). 326 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.8017668724060059, 'p95': 4.4199676513671875, 'max': 5.297332763671875}` / `{'median': 0.9416463077068329, 'p95': 4.581676483154297, 'max': 5.926130294799805}` / `{'median': 8.742277657347586e-08, 'p95': 2.0000038146972656, 'max': 7.0239222049713135}`.
- The issue-time enemy guard retained 11067 observations, detected 3020 during-plan geometry changes, recertified 3020 decisions, and overrode 36 actions. Read/recertificate timing was `{'median': 1.4842000091448426, 'p95': 2.5391000090166926, 'max': 179.08299999544397}` / `{'median': 3.1788499909453094, 'p95': 7.024699996691197, 'max': 244.84070000471547}` ms; 7966 issue captures contained latent bodies (maximum 49), and 3800 contained dormant bodies (maximum 38). Fresh/global transactions preserved 2984/3020 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8832 observations (8807 contact enabled, 25 anticipatory, 0 errors). 8832 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8832}`.
- The terminal-threat heuristic covered 11067 decisions with horizon counts `{'0': 497, '10': 10570}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 576, '3': 6811, '4': 2695, '5': 800, '6': 185}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 387, '2': 714, '3': 7875, '4': 1749, '5': 293, '6': 49}`.
- Adaptive delay supports were `{'1': 16, '1,2': 170, '1,2,3': 213, '1,2,3,4': 180, '1,2,3,4,5': 180, '1,2,3,4,5,6': 46, '2,3': 751, '2,3,4': 2308, '2,3,4,5': 3117, '2,3,4,5,6': 2545, '3,4': 48, '3,4,5': 175, '3,4,5,6': 1147, '4,5': 1, '4,5,6': 156, '5,6': 7, '6': 7}`; 229 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 22/135.
- Robust viability supplied 3503 available policy queries (0 had new delay support outside the cached policy), constrained 36 decisions, and exposed 2240 empty queried action sets. Recovery guidance was available/selected on 221/0 empty-kernel queries; distant-kernel guidance was available/selected on 1273/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 582, '1': 496, '2': 373, '3': 371, '4': 409, '5': 408, '6': 454, '7': 410}`.
- Global-horizon/local-prefix cross-tab covered 1196 decisions: 1 had a winning global state but unsafe selected prefix, 565 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 28 selected actions were outside the reported winning set. 1416 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 611 unique policies with solve-time statistics `{'median': 74.00910000433214, 'p95': 183.292799978517, 'max': 1514.7571999987122}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 66.0}`. Policy status counts were `{'queryable': 3493, 'expired': 362, 'pending_future_epoch': 94}`; 446 robust-mode decisions had no query.
- Of 5654 unambiguous output transitions, 5324 (0.942) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 8, 'robust_action_set_exhausted_before_hit': 4, 'late_collision_after_positive_causal_margin': 1, 'unresolved_planner_failure': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 11 hit windows with a positive warning lead; those leads were `[0, 42, 0, 0, 0, 0, 3, 7, 145, 9, 13, 6, 8, 6, 10, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.579 during the 60 frames preceding a hit versus 0.362 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
