# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_103320

## Scope And Integrity

- Valid practice scope: `2..43185` (10844 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 16, at `[1941, 2269, 2581, 3721, 4477, 11372, 12591, 13209, 13553, 13881, 14469, 30439, 34979, 36545, 38585, 42074]`.
- Hard no-Bomb verification: **PASS** across 10844 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1941-T1`. It occurred during a nonspell phase at player (376.000, 422.551), with 734 bullets and 0 lasers. The projectile model reported pipeline clearance 5.002.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 3 |

Contributing factors:

- `fast_mode`: 10
- `playfield_boundary`: 8
- `action_lag_over_model`: 7
- `pool_density_over_1000`: 2
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1941 | nonspell | (376.000, 422.551) | `stay` | 734/0 | 5.002/-0.257 | 0f/39f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 2269 | nonspell | (375.047, 146.619) | `down` | 405/0 | -0.248/-0.750 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 2581 | nonspell | (160.887, 291.213) | `up_fast` | 238/0 | -2.721/-12.643 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 3721 | nonspell | (175.887, 432.000) | `left_fast` | 797/0 | -0.127/-2.055 | 3f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 4477 | nonspell | (247.109, 402.726) | `up_left` | 293/0 | -0.850/-0.850 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 11372 | nonspell | (352.524, 423.515) | `up_fast` | 910/0 | -2.448/-2.448 | 4f/14f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12591 | nonspell | (8.000, 135.342) | `right_fast` | 296/0 | -3.638/-3.638 | 2f/30f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13209 | nonspell | (8.000, 359.272) | `down_right_fast` | 97/0 | -2.593/-2.593 | 0f/12f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13553 | nonspell | (160.887, 323.348) | `up_left_fast` | 372/0 | -11.484/-28.689 | 12f/12f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13881 | nonspell | (295.975, 417.504) | `up_right_fast` | 239/0 | 12.874/12.874 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 14469 | nonspell | (62.373, 412.159) | `stay` | 519/0 | 6.268/3.081 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 30439 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (235.684, 397.842) | `right` | 1019/0 | -3.318/-9.283 | 9f/22f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34979 | nonspell | (44.027, 432.000) | `up_right_fast` | 388/0 | -3.144/-3.144 | 2f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36545 | nonspell | (8.000, 425.100) | `up_right_fast` | 475/0 | -2.850/-2.850 | 2f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 38585 | 111 懶惰「生神停止(マインドストッパー)」 | (221.254, 194.531) | `right` | 333/0 | -2.003/-3.281 | 4f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42074 | 115 散符「真実の月(インビジブルフルムーン)」 | (373.172, 429.172) | `up_left_fast` | 1156/0 | -1.438/-1.438 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 13 | 7277 | 61 | 12 | 0 | 48 | 6 | 1916.411 | 0.374 |
| 103 | 0 | 825 | 392 | 328 | 0 | 0 | 37 | 99.274 | 0.414 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 736 | 730 | 529 | 0 | 0 | 162 | 76.846 | 0.300 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1011 | 1005 | 574 | 0 | 0 | 178 | 71.797 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 995 | 988 | 747 | 0 | 0 | 184 | 65.710 | 0.457 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.380 ms median and 32.596 ms p95.
- The full enemy sensor produced 6001 snapshots; capture read time was `{'median': 5.374100001063198, 'p95': 27.87340001668781, 'max': 472.40589998546056}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 69.0}` frames, and 7 phase-counter discontinuities were excluded; 10164 decisions retained at least one robust-union body (maximum 49); 7679 decisions contained latent contact-disabled geometry (maximum 49), and 3876 contained bounded inactive-slot memory (maximum 37). 298 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.22967529296875, 'p95': 4.707550048828125, 'max': 7.457542419433594}` / `{'median': 1.1451144814491272, 'p95': 4.632939338684082, 'max': 4.710234642028809}` / `{'median': 6.139278411865234e-06, 'p95': 2.286265317131491, 'max': 3.047259611241958}`.
- The issue-time enemy guard retained 10844 observations, detected 3148 during-plan geometry changes, recertified 3148 decisions, and overrode 55 actions. Read/recertificate timing was `{'median': 1.4822999946773052, 'p95': 2.851199998985976, 'max': 210.45600000070408}` / `{'median': 3.1722999992780387, 'p95': 7.492000004276633, 'max': 259.29670000914484}` ms; 7651 issue captures contained latent bodies (maximum 49), and 3865 contained dormant bodies (maximum 37). Fresh/global transactions preserved 3093/3148 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8196 observations (8170 contact enabled, 26 anticipatory, 0 errors). 8196 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8196}`.
- The terminal-threat heuristic covered 10844 decisions with horizon counts `{'0': 564, '10': 10280}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 656, '3': 6438, '4': 2371, '5': 986, '6': 393}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 262, '2': 2217, '3': 5690, '4': 2222, '5': 438, '6': 15}`.
- Adaptive delay supports were `{'1,2': 152, '1,2,3': 397, '1,2,3,4': 250, '1,2,3,4,5': 72, '1,2,3,4,5,6': 23, '2,3': 659, '2,3,4': 2836, '2,3,4,5': 2779, '2,3,4,5,6': 1936, '3,4': 87, '3,4,5': 341, '3,4,5,6': 1277, '4,5': 10, '4,5,6': 14, '5,6': 2, '6': 9}`; 205 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 34/174.
- Robust viability supplied 3176 available policy queries (0 had new delay support outside the cached policy), constrained 48 decisions, and exposed 2190 empty queried action sets. Recovery guidance was available/selected on 176/0 empty-kernel queries; distant-kernel guidance was available/selected on 1310/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 524, '1': 431, '2': 356, '3': 317, '4': 367, '5': 405, '6': 391, '7': 385}`.
- Global-horizon/local-prefix cross-tab covered 1342 decisions: 0 had a winning global state but unsafe selected prefix, 694 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 19 selected actions were outside the reported winning set. 1456 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 567 unique policies with solve-time statistics `{'median': 70.4729999997653, 'p95': 176.99810001067817, 'max': 2983.5369999927934}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 117.0}`. Policy status counts were `{'queryable': 3164, 'expired': 494, 'pending_future_epoch': 82}`; 564 robust-mode decisions had no query.
- Of 5467 unambiguous output transitions, 5150 (0.942) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 8, 'late_collision_after_positive_causal_margin': 2, 'missing_pre_hit_alive_decision': 1, 'unresolved_planner_failure': 2, 'global_viability_kernel_exhausted_before_hit': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 11 hit windows with a positive warning lead; those leads were `[39, 0, 0, 9, 0, 14, 30, 12, 12, 0, 0, 22, 7, 8, 17, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.422 during the 60 frames preceding a hit versus 0.341 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
