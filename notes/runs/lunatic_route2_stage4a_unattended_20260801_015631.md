# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_015631

## Scope And Integrity

- Valid practice scope: `2..45499` (12077 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 20, at `[2009, 3165, 4237, 9297, 11548, 12039, 12575, 13234, 21538, 22416, 23073, 27965, 30568, 32057, 36657, 40160, 43026, 43337, 44351, 45226]`.
- Hard no-Bomb verification: **PASS** across 12077 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2009-T1`. It occurred during a nonspell phase at player (8.000, 415.613), with 196 bullets and 0 lasers. The projectile model reported pipeline clearance -2.440.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 8 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 17
- `playfield_boundary`: 10
- `corridor_deadline_miss`: 8
- `pool_density_over_1000`: 4
- `action_lag_over_model`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2009 | nonspell | (8.000, 415.613) | `left` | 196/0 | -2.440/-2.440 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 3165 | nonspell | (96.000, 420.572) | `right_fast` | 211/0 | -0.525/-0.693 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 4237 | nonspell | (22.142, 411.022) | `down_right_fast` | 984/0 | -2.018/-2.018 | 0f/11f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 9297 | nonspell | (346.027, 432.000) | `right_fast` | 777/0 | -9.532/-13.035 | 6f/14f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11548 | 57 夢境「二重大結界」 | (107.800, 261.745) | `left_fast` | 590/0 | -2.047/-2.047 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12039 | 57 夢境「二重大結界」 | (10.828, 429.172) | `up_right_fast` | 629/0 | 2.106/1.227 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12575 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 582/0 | -1.784/-1.784 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13234 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 607/0 | -1.780/-1.780 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21538 | nonspell | (150.639, 426.339) | `stay` | 266/0 | -1.512/-1.512 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22416 | nonspell | (21.332, 432.000) | `down_right_fast` | 946/0 | -1.741/-2.977 | 3f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 23073 | nonspell | (11.700, 432.000) | `up_fast` | 562/0 | -3.144/-3.144 | 6f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 27965 | nonspell | (376.000, 432.000) | `up_fast` | 81/0 | -3.468/-3.468 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30568 | 65 神技「八方龍殺陣」 | (199.706, 424.293) | `up_left_fast` | 1210/0 | -2.488/-2.488 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32057 | 65 神技「八方龍殺陣」 | (246.755, 409.049) | `up_left_fast` | 1170/0 | -1.481/-1.481 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36657 | nonspell | (369.495, 432.000) | `up_left` | 62/0 | -1.615/-1.615 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 40160 | 69 回霊「夢想封印　侘」 | (12.000, 432.000) | `right_fast` | 702/0 | -3.374/-3.374 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43026 | 73 大結界「博麗弾幕結界」 | (219.552, 401.000) | `down_left_fast` | 980/0 | -1.188/-1.188 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43337 | 73 大結界「博麗弾幕結界」 | (146.484, 385.068) | `left_fast` | 816/0 | -2.377/-2.377 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44351 | 73 大結界「博麗弾幕結界」 | (175.435, 369.123) | `down_left_fast` | 1354/0 | -0.484/-0.484 | 0f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45226 | 73 大結界「博麗弾幕結界」 | (55.422, 329.895) | `left_fast` | 1343/0 | -3.251/-3.978 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 6941 | 591 | 78 | 0 | 494 | 43 | 555.111 | 0.258 |
| 57 夢境「二重大結界」 | 4 | 1135 | 1116 | 226 | 0 | 0 | 174 | 184.490 | 0.271 |
| 61 | 0 | 1022 | 1015 | 395 | 0 | 0 | 165 | 122.867 | 0.217 |
| 65 神技「八方龍殺陣」 | 2 | 856 | 830 | 616 | 0 | 0 | 124 | 67.868 | 0.418 |
| 69 回霊「夢想封印　侘」 | 1 | 1080 | 1073 | 719 | 0 | 0 | 180 | 88.583 | 0.148 |
| 73 大結界「博麗弾幕結界」 | 4 | 1043 | 1036 | 484 | 0 | 0 | 187 | 126.046 | 0.035 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.980 ms median and 30.876 ms p95.
- The full enemy sensor produced 6477 snapshots; capture read time was `{'median': 5.344099990907125, 'p95': 21.07070000784006, 'max': 158.66729999834206}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 112.0}` frames, and 6 phase-counter discontinuities were excluded; 11786 decisions retained at least one robust-union body (maximum 51); 6480 decisions contained latent contact-disabled geometry (maximum 51), and 4832 contained bounded inactive-slot memory (maximum 29). 291 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.276885986328125, 'p95': 4.0464630126953125, 'max': 4.8097076416015625}` / `{'median': 2.429863214492798, 'p95': 3.9676663875579834, 'max': 14.499862670898438}` / `{'median': 0.015598634878794315, 'p95': 1.2934308052062988, 'max': 14.499862670898438}`.
- The issue-time enemy guard retained 12077 observations, detected 4902 during-plan geometry changes, recertified 4902 decisions, and overrode 111 actions. Read/recertificate timing was `{'median': 1.5477999986615032, 'p95': 2.879100007703528, 'max': 92.47190000314731}` / `{'median': 2.4534499971196055, 'p95': 4.835100000491366, 'max': 19.143600002280436}` ms; 6483 issue captures contained latent bodies (maximum 51), and 4848 contained dormant bodies (maximum 29). Fresh/global transactions preserved 4791/4902 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9850 observations (9807 contact enabled, 43 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4164, '0x0059C9D0': 5686}`.
- The terminal-threat heuristic covered 12077 decisions with horizon counts `{'0': 22, '10': 12055}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 110, '3': 7930, '4': 3325, '5': 422, '6': 290}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1605, '3': 8955, '4': 1517}`.
- Adaptive delay supports were `{'1,2,3': 1, '1,2,3,4,5,6': 26, '2,3': 818, '2,3,4': 3109, '2,3,4,5': 4379, '2,3,4,5,6': 3001, '3,4': 2, '3,4,5': 221, '3,4,5,6': 514, '4,5,6': 6}`; 141 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 29/159.
- Robust viability supplied 5661 available policy queries (0 had new delay support outside the cached policy), constrained 494 decisions, and exposed 2518 empty queried action sets. Recovery guidance was available/selected on 790/0 empty-kernel queries; distant-kernel guidance was available/selected on 1277/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 882, '1': 787, '2': 614, '3': 613, '4': 673, '5': 705, '6': 659, '7': 728}`.
- Global-horizon/local-prefix cross-tab covered 2941 decisions: 0 had a winning global state but unsafe selected prefix, 1294 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 209 selected actions were outside the reported winning set. 1221 newer issue-time hazard versions and 2 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 873 unique policies with solve-time statistics `{'median': 122.66119998821523, 'p95': 228.28180000942666, 'max': 1337.9710000008345}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1795.0}`. Policy status counts were `{'pending_future_epoch': 68, 'queryable': 5652, 'expired': 2438}`; 2497 robust-mode decisions had no query.
- Of 6658 unambiguous output transitions, 6324 (0.950) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 7, 'late_collision_after_positive_causal_margin': 1, 'global_viability_kernel_exhausted_before_hit': 12}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 17 hit windows with a positive warning lead; those leads were `[8, 0, 11, 14, 3, 8, 6, 6, 0, 5, 10, 5, 9, 0, 5, 5, 7, 3, 9, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.447 during the 60 frames preceding a hit versus 0.232 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Exact Ordinary Authority Audit

- **Observed:** 124/1,933 future-source projections completed. Exact authority
  was eligible/applicable/effective on 527/494/479 of 6,941 nonspell
  decisions. Before first hit 2009 it was applicable on 278 decisions; 102
  had fewer than 17 allowed actions.
- **Observed:** the 43 unique complete nonspell policies had solve-time
  median/p95/max 555/1,119/1,338 ms. Clearance was 18/560/766 ms and Boolean
  viability was 355/926/1,038 ms. Relative to `011902`, this physically
  validates the exact interior recurrence acceleration.
- **Observed:** the nine nonspell 80-frame hit windows contained 238 decisions
  and zero applicable/effective authority. The canonical 33-decision window
  was entirely `future_policy_unavailable`; captured source roots 1915..2007
  chiefly failed on nonzero transform programs, with opcode-`0x19` mixed in.
- **Observed aggregate:** armed phase transitions failed 903 projections,
  installed callbacks 304, and transforms 175. Phase coverage remains a later
  broad blocker, but the canonical first-hit correction is transform/opcode
  closure.
- **Inference:** total hits 26→20 and first hit 796→2009 are encouraging but
  different-RNG observations. Promotion requires a fresh run with nonzero
  exact authority in nonspell pressure windows.
