# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_124930

## Scope And Integrity

- Valid practice scope: `1..44593` (13326 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 15, at `[2167, 3987, 10983, 14043, 24013, 24931, 29133, 31196, 31745, 32263, 32806, 33121, 39543, 40693, 43846]`.
- Hard no-Bomb verification: **PASS** across 13326 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2167-T1`. It occurred during a nonspell phase at player (8.000, 424.000), with 657 bullets and 0 lasers. The projectile model reported pipeline clearance 0.587.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 4 |

Contributing factors:

- `fast_mode`: 12
- `playfield_boundary`: 9
- `pool_density_over_1000`: 6
- `corridor_deadline_miss`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2167 | nonspell | (8.000, 424.000) | `up_right_fast` | 657/0 | 0.587/-2.485 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3987 | nonspell | (12.600, 432.000) | `right` | 709/0 | -0.760/-1.808 | 1f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10983 | nonspell | (93.465, 403.515) | `up_fast` | 886/0 | -17.015/-17.015 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14043 | nonspell | (74.325, 410.306) | `left_fast` | 405/0 | -0.137/-1.753 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24013 | 103 幻波「赤眼催眠(マインドブローイング)」 | (375.818, 432.000) | `up_left_fast` | 1102/0 | -1.266/-1.266 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24931 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 376.565) | `up_fast` | 1359/0 | -1.780/-1.780 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29133 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (78.021, 432.000) | `up_fast` | 799/0 | -2.500/-2.500 | 7f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31196 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (355.743, 432.000) | `right_fast` | 1018/0 | -3.456/-3.907 | 30f/120f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31745 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (268.645, 364.463) | `up_right` | 1018/0 | -7.075/-7.075 | 20f/81f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32263 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (170.511, 432.000) | `left_fast` | 1009/0 | -5.179/-5.179 | 4f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32806 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (212.999, 385.631) | `left_fast` | 977/0 | -6.408/-8.877 | 11f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33121 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (217.899, 432.000) | `right_fast` | 1001/0 | -6.885/-6.885 | 4f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39543 | 111 懶惰「生神停止(マインドストッパー)」 | (192.863, 166.837) | `right_fast` | 385/0 | -3.035/-3.035 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40693 | 111 懶惰「生神停止(マインドストッパー)」 | (231.720, 218.457) | `down_right` | 341/0 | -1.312/-3.518 | 3f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43846 | 115 散符「真実の月(インビジブルフルムーン)」 | (27.283, 432.000) | `down_left_fast` | 960/0 | -3.891/-3.891 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 8455 | 8321 | 5583 | 0 | 2717 | 1055 | 122.045 | 0.158 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 985 | 971 | 492 | 0 | 479 | 169 | 103.915 | 0.315 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 6 | 1405 | 1397 | 1132 | 0 | 249 | 275 | 79.797 | 0.300 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1249 | 1242 | 531 | 0 | 698 | 180 | 86.127 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1232 | 1215 | 756 | 0 | 450 | 182 | 56.953 | 0.430 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 10.699 ms median and 22.656 ms p95.
- The full enemy sensor produced 6899 snapshots; capture read time was `{'median': 5.511900002602488, 'p95': 24.582199985161424, 'max': 51.27789999824017}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 12521 decisions retained at least one robust-union body (maximum 41); 5074 decisions contained latent contact-disabled geometry (maximum 29), and 6439 contained bounded inactive-slot memory (maximum 37). 252 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 2.93157958984375, 'max': 5.2785186767578125}` / `{'median': 0.0, 'p95': 2.931584358215332, 'max': 4.678522109985352}` / `{'median': 0.0, 'p95': 0.9892818927764893, 'max': 6.458237171173096}`.
- The issue-time enemy guard retained 13326 observations, detected 2674 during-plan geometry changes, recertified 2674 decisions, and overrode 54 actions. Read/recertificate timing was `{'median': 1.7092999769374728, 'p95': 3.34840000141412, 'max': 13.62189999781549}` / `{'median': 3.3556500275153667, 'p95': 6.040700012817979, 'max': 16.024700016714633}` ms; 5043 issue captures contained latent bodies (maximum 29), and 6460 contained dormant bodies (maximum 37). Fresh/global transactions preserved 2620/2674 planned actions, relaxed 5 fresh/global empty intersections, inherited 15 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9652 observations (9622 contact enabled, 30 anticipatory, 0 errors). 9652 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9652}`.
- The terminal-threat heuristic covered 13326 decisions with horizon counts `{'0': 76, '10': 13015, '32': 235}`; it reported 3 collision and 57 sub-safety-clearance warnings, and relaxed 59 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2111, '3': 9258, '4': 1785, '5': 172}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 62, '2': 5471, '3': 5876, '4': 1917}`.
- Adaptive delay supports were `{'1,2': 159, '1,2,3': 69, '1,2,3,4': 126, '1,2,3,4,5': 7, '2,3': 1182, '2,3,4': 6673, '2,3,4,5': 2064, '2,3,4,5,6': 1633, '3,4': 24, '3,4,5': 288, '3,4,5,6': 1101}`; 119 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 31/221.
- Robust viability supplied 13146 available policy queries (0 had new delay support outside the cached policy), constrained 4593 decisions, and exposed 8494 empty queried action sets. Recovery guidance was available/selected on 1136/476 empty-kernel queries; distant-kernel guidance was available/selected on 6780/6428. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 128.0, 'p95': 332.938432746957, 'max': 497.80317395532944}`, and `{'median': 0.0, 'p95': 21.373247861862183, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2085, '1': 1646, '2': 1458, '3': 1558, '4': 1551, '5': 1584, '6': 1703, '7': 1561}`.
- Global-horizon/local-prefix cross-tab covered 8902 decisions: 4 had a winning global state but unsafe selected prefix, 5730 had a losing global state but safe short prefix, 3 selected globally certified actions contradicted the fresh local prefix checker, and 21 selected actions were outside the reported winning set. 2201 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1861 unique policies with solve-time statistics `{'median': 94.04200001154095, 'p95': 301.68110004160553, 'max': 403.7884999997914}` and first-observed ages `{'median': 2.0, 'p95': 6.0, 'max': 1797.0}`. Policy status counts were `{'pending_future_epoch': 78, 'queryable': 13148, 'expired': 24}`; 104 robust-mode decisions had no query.
- Of 6650 unambiguous output transitions, 6042 (0.909) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 15}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[4, 7, 0, 8, 7, 4, 15, 120, 81, 15, 23, 12, 5, 11, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.405 during the 60 frames preceding a hit versus 0.186 outside those windows.
- Mean selected control-reserve deficit was 8.037 during the 60 frames preceding a hit versus 3.958 outside those windows.
- Soft recovery was selected on 0.023 of alive decisions in the 60-frame pre-hit windows versus 0.040 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
