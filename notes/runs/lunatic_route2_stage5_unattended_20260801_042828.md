# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_042828

## Scope And Integrity

- Valid practice scope: `2..44279` (11454 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[2617, 3492, 4380, 12885, 13749, 14058, 23986, 25357, 28148, 28640, 30581, 36581, 37233, 37670, 39426, 40712, 43347, 43842]`.
- Hard no-Bomb verification: **PASS** across 11454 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2617-T1`. It occurred during a nonspell phase at player (8.000, 268.057), with 556 bullets and 0 lasers. The projectile model reported pipeline clearance -3.468.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 14
- `playfield_boundary`: 13
- `pool_density_over_1000`: 7
- `action_lag_over_model`: 3
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2617 | nonspell | (8.000, 268.057) | `up_left_fast` | 556/0 | -3.468/-3.468 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 3492 | nonspell | (8.000, 432.000) | `up_fast` | 993/0 | -1.988/-1.988 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 4380 | nonspell | (8.000, 407.599) | `down_left_fast` | 501/0 | -0.259/-0.259 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12885 | nonspell | (12.600, 432.000) | `up_left` | 263/0 | -2.283/-2.283 | 2f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13749 | nonspell | (215.693, 375.737) | `up_fast` | 399/0 | -2.251/-2.251 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 14058 | nonspell | (376.000, 432.000) | `down_right` | 524/0 | 3.642/3.642 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 23986 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 1110/0 | -2.171/-2.171 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25357 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `right_fast` | 1417/0 | -2.308/-2.308 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28148 | nonspell | (200.741, 432.000) | `right_fast` | 1020/0 | -1.351/-1.963 | 9f/12f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 28640 | nonspell | (13.657, 426.343) | `up_left_fast` | 1068/0 | -1.902/-2.232 | 2f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 30581 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (101.930, 432.000) | `down_left_fast` | 1001/0 | -6.489/-6.619 | 6f/49f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36581 | nonspell | (8.000, 404.278) | `down_right_fast` | 438/0 | -1.633/-1.633 | 6f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 37233 | nonspell | (8.000, 426.447) | `right_fast` | 472/0 | -3.140/-3.140 | 3f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 37670 | nonspell | (370.343, 416.860) | `right` | 403/0 | -1.769/-1.769 | 3f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 39426 | 111 懶惰「生神停止(マインドストッパー)」 | (221.854, 68.964) | `down_right_fast` | 436/0 | -1.505/-1.505 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40712 | 111 懶惰「生神停止(マインドストッパー)」 | (148.085, 213.930) | `up_left` | 342/0 | -2.281/-2.281 | 0f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43347 | 115 散符「真実の月(インビジブルフルムーン)」 | (15.428, 429.172) | `up_right_fast` | 1152/0 | -1.493/-1.493 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43842 | 115 散符「真実の月(インビジブルフルムーン)」 | (172.147, 429.172) | `up_right_fast` | 1070/0 | -1.366/-1.366 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 11 | 7717 | 0 | 0 | 0 | 0 | 0 | - | 0.360 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 866 | 830 | 496 | 0 | 0 | 163 | 106.335 | 0.409 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 820 | 814 | 613 | 0 | 0 | 182 | 76.490 | 0.356 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1031 | 1025 | 502 | 0 | 0 | 180 | 74.162 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1020 | 1014 | 688 | 0 | 0 | 184 | 67.792 | 0.500 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.621 ms median and 34.033 ms p95.
- The full enemy sensor produced 6322 snapshots; capture read time was `{'median': 5.449149997730274, 'p95': 26.883400001679547, 'max': 76.58330000413116}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 22.0}` frames, and 7 phase-counter discontinuities were excluded; 10810 decisions retained at least one robust-union body (maximum 49); 8432 decisions contained latent contact-disabled geometry (maximum 49), and 3941 contained bounded inactive-slot memory (maximum 36). 331 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.0, 'p95': 4.684429168701172, 'max': 8.3221435546875}` / `{'median': 1.0, 'p95': 4.5343122482299805, 'max': 4.9499969482421875}` / `{'median': 8.742277657347586e-08, 'p95': 1.0684280395507812, 'max': 5.251709938049316}`.
- The issue-time enemy guard retained 11454 observations, detected 3538 during-plan geometry changes, recertified 3538 decisions, and overrode 49 actions. Read/recertificate timing was `{'median': 1.6423500055680051, 'p95': 3.3152999967569485, 'max': 64.64840000262484}` / `{'median': 3.146850001940038, 'p95': 6.655599994701333, 'max': 121.28619999566581}` ms; 8405 issue captures contained latent bodies (maximum 49), and 3928 contained dormant bodies (maximum 37). Fresh/global transactions preserved 3489/3538 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8433 observations (8406 contact enabled, 27 anticipatory, 0 errors). 8433 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8433}`.
- The terminal-threat heuristic covered 11454 decisions with horizon counts `{'0': 546, '10': 10908}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 504, '3': 6057, '4': 2933, '5': 1294, '6': 666}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 284, '2': 332, '3': 8415, '4': 1705, '5': 718}`.
- Adaptive delay supports were `{'1,2': 157, '1,2,3': 79, '1,2,3,4': 109, '1,2,3,4,5': 154, '1,2,3,4,5,6': 327, '2,3': 513, '2,3,4': 1608, '2,3,4,5': 3119, '2,3,4,5,6': 3680, '3,4': 68, '3,4,5': 196, '3,4,5,6': 1439, '4,5,6': 5}`; 238 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 69/321.
- Robust viability supplied 3683 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 2299 empty queried action sets. Recovery guidance was available/selected on 261/0 empty-kernel queries; distant-kernel guidance was available/selected on 1417/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 606, '1': 507, '2': 439, '3': 358, '4': 395, '5': 469, '6': 440, '7': 469}`.
- Global-horizon/local-prefix cross-tab covered 1342 decisions: 1 had a winning global state but unsafe selected prefix, 656 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 24 selected actions were outside the reported winning set. 1561 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 709 unique policies with solve-time statistics `{'median': 79.87420000426937, 'p95': 178.76170000818092, 'max': 214.87110000452958}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 10.0}`. Policy status counts were `{'pending_future_epoch': 39, 'queryable': 3682, 'expired': 4}`; 42 robust-mode decisions had no query.
- Of 5839 unambiguous output transitions, 5477 (0.938) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'late_collision_after_positive_causal_margin': 2, 'robust_action_set_exhausted_before_hit': 8, 'missing_pre_hit_alive_decision': 1, 'global_viability_kernel_exhausted_before_hit': 7}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 15 hit windows with a positive warning lead; those leads were `[0, 6, 8, 8, 0, 0, 8, 4, 12, 10, 49, 8, 10, 10, 6, 21, 6, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.394 during the 60 frames preceding a hit versus 0.342 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
