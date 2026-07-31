# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_002006

## Scope And Integrity

- Valid practice scope: `1..45460` (11242 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 24, at `[1205, 1994, 2790, 3111, 3893, 4199, 8809, 9488, 10048, 11768, 12757, 13267, 13797, 20123, 21852, 22542, 23047, 28726, 31230, 35339, 39173, 39866, 43042, 43360]`.
- Hard no-Bomb verification: **PASS** across 11242 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1205-T1`. It occurred during a nonspell phase at player (342.534, 411.300), with 232 bullets and 0 lasers. The projectile model reported pipeline clearance -1.936.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 12 |
| `modeled_committed_prefix_collision` | 8 |
| `observed_enemy_body_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 2 |

Contributing factors:

- `fast_mode`: 17
- `playfield_boundary`: 14
- `corridor_deadline_miss`: 12
- `action_lag_over_model`: 3
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1205 | nonspell | (342.534, 411.300) | `up` | 232/0 | -1.936/-1.936 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1994 | nonspell | (8.000, 397.410) | `down_fast` | 203/0 | -2.755/-2.755 | 2f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2790 | nonspell | (369.495, 384.448) | `up_fast` | 650/0 | -1.480/-6.214 | 7f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3111 | nonspell | (192.000, 384.000) | `stay` | 341/0 | 9.807/9.807 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3893 | nonspell | (362.636, 423.515) | `up_left_fast` | 642/0 | 2.577/-1.484 | 3f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 4199 | nonspell | (339.322, 432.000) | `left_fast` | 955/0 | 1.242/-0.737 | 4f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 8809 | nonspell | (376.000, 424.000) | `up_fast` | 770/0 | -17.011/-17.961 | 2f/10f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 9488 | nonspell | (171.395, 432.000) | `left_fast` | 172/0 | -0.186/-5.516 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10048 | nonspell | (376.000, 432.000) | `left_fast` | 100/0 | -2.352/-3.783 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11768 | 57 夢境「二重大結界」 | (14.900, 432.000) | `up_right_fast` | 623/0 | -0.680/-2.796 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12757 | 57 夢境「二重大結界」 | (8.000, 424.000) | `up_fast` | 607/0 | 1.302/-2.425 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13267 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 630/0 | -1.451/-1.451 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13797 | 57 夢境「二重大結界」 | (9.626, 421.970) | `up_right` | 575/0 | -2.663/-2.663 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20123 | 61 散霊「夢想封印　寂」 | (174.919, 424.000) | `up_fast` | 586/0 | -20.386/-20.386 | 3f/13f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21852 | nonspell | (20.133, 410.101) | `up_right_fast` | 325/0 | 17.502/9.488 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22542 | nonspell | (18.112, 423.896) | `up` | 797/0 | -3.076/-3.076 | 3f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 23047 | nonspell | (22.543, 432.000) | `up_left_fast` | 587/0 | -3.508/-4.210 | 2f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 28726 | nonspell | (22.142, 432.000) | `down_right_fast` | 155/0 | -2.905/-2.905 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 31230 | 65 神技「八方龍殺陣」 | (201.152, 425.100) | `down` | 1272/0 | -1.376/-6.869 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35339 | nonspell | (352.000, 432.000) | `left_fast` | 97/0 | -6.505/-10.357 | 10f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39173 | 69 回霊「夢想封印　侘」 | (376.000, 363.912) | `up_right` | 760/0 | -2.274/-2.274 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39866 | 69 回霊「夢想封印　侘」 | (57.558, 432.000) | `left` | 676/0 | -2.250/-2.250 | 3f/3f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 43042 | 73 大結界「博麗弾幕結界」 | (225.134, 402.100) | `right_fast` | 1000/0 | -2.415/-2.415 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43360 | 73 大結界「博麗弾幕結界」 | (159.097, 374.774) | `up_right_fast` | 856/0 | 0.453/-0.464 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 14 | 6146 | 2575 | 1023 | 0 | 136 | 133 | 908.551 | 0.189 |
| 57 夢境「二重大結界」 | 4 | 1164 | 975 | 233 | 0 | 0 | 108 | 195.250 | 0.341 |
| 61 散霊「夢想封印　寂」 | 1 | 1033 | 1008 | 446 | 0 | 0 | 146 | 133.374 | 0.198 |
| 65 神技「八方龍殺陣」 | 1 | 791 | 384 | 296 | 0 | 0 | 19 | 66.938 | 0.474 |
| 69 回霊「夢想封印　侘」 | 2 | 1136 | 600 | 322 | 0 | 0 | 48 | 107.697 | 0.227 |
| 73 大結界「博麗弾幕結界」 | 2 | 972 | 916 | 560 | 0 | 0 | 142 | 119.203 | 0.040 |

## Interpretation

- Retained witnesses classify 12 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 18.275 ms median and 45.658 ms p95.
- The full enemy sensor produced 6538 snapshots; capture read time was `{'median': 6.788400001823902, 'p95': 54.78039999434259, 'max': 253.15319999936037}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 41.0}` frames, and 7 phase-counter discontinuities were excluded; 10760 decisions retained at least one robust-union body (maximum 50); 6118 decisions contained latent contact-disabled geometry (maximum 50), and 4298 contained bounded inactive-slot memory (maximum 30). 418 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.969991683959961, 'p95': 4.3787384033203125, 'max': 11.568092346191406}` / `{'median': 2.995175361633301, 'p95': 3.9985740184783936, 'max': 82.06683349609375}` / `{'median': 0.5000035762786865, 'p95': 1.837036371231079, 'max': 82.06683349609375}`.
- The issue-time enemy guard retained 11242 observations, detected 4585 during-plan geometry changes, recertified 4585 decisions, and overrode 98 actions. Read/recertificate timing was `{'median': 1.5185500014922582, 'p95': 3.1580000068061054, 'max': 48.92499999550637}` / `{'median': 2.9707999929087237, 'p95': 11.513400007970631, 'max': 175.11450000165496}` ms; 6119 issue captures contained latent bodies (maximum 50), and 4300 contained dormant bodies (maximum 30). Fresh/global transactions preserved 4487/4585 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8659 observations (8624 contact enabled, 35 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3840, '0x00597600': 4819}`.
- The terminal-threat heuristic covered 11242 decisions with horizon counts `{'0': 374, '10': 10868}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 244, '3': 3488, '4': 3594, '5': 3239, '6': 677}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 239, '3': 5702, '4': 4271, '5': 1029, '6': 1}`.
- Adaptive delay supports were `{'1,2': 51, '1,2,3': 68, '1,2,3,4': 216, '1,2,3,4,5': 50, '1,2,3,4,5,6': 255, '2,3': 25, '2,3,4': 470, '2,3,4,5': 3305, '2,3,4,5,6': 5671, '3,4': 43, '3,4,5': 515, '3,4,5,6': 567, '4,5': 2, '4,5,6': 3, '6': 1}`; 155 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 36/177.
- Robust viability supplied 6458 available policy queries (0 had new delay support outside the cached policy), constrained 136 decisions, and exposed 2880 empty queried action sets. Recovery guidance was available/selected on 939/0 empty-kernel queries; distant-kernel guidance was available/selected on 1723/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 893, '1': 894, '2': 747, '3': 760, '4': 819, '5': 766, '6': 788, '7': 791}`.
- Global-horizon/local-prefix cross-tab covered 3176 decisions: 5 had a winning global state but unsafe selected prefix, 1457 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 246 selected actions were outside the reported winning set. 1799 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 596 unique policies with solve-time statistics `{'median': 158.8935500039952, 'p95': 1803.852700002608, 'max': 2921.2869000039063}` and first-observed ages `{'median': 3.0, 'p95': 10.0, 'max': 1790.0}`. Policy status counts were `{'pending_future_epoch': 379, 'queryable': 6383, 'expired': 3812}`; 4116 robust-mode decisions had no query.
- Of 6269 unambiguous output transitions, 6121 (0.976) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 14, 'unresolved_planner_failure': 1, 'robust_action_set_exhausted_before_hit': 9}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 21 hit windows with a positive warning lead; those leads were `[0, 11, 13, 0, 6, 4, 10, 6, 7, 8, 8, 6, 5, 13, 0, 6, 8, 7, 7, 16, 8, 3, 8, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.434 during the 60 frames preceding a hit versus 0.205 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

The v4 source audit retained 1,942 projections: 159 complete and 1,783
fail-closed. The former `10069` and legal auxiliary-delay-root failures are
absent. Remaining failures classify as 628 armed phase successors, 571
manager-frame crossings, 180 unsupported ECL opcodes, 172 transform programs,
137 installed callbacks, 56 unsupported movement roots, 33 timer/PC drifts,
four call-depth roots, and two unlowered velocities.

Across 6,146 nonspell decisions, exact authority was applicable 136 times and
effective at issue 135 times. Of those sets, 120 admitted all 17 actions and
only 16 were nontrivial. Before the canonical hit, 95/472 decisions were
applicable but all 95 admitted every action. Across the 80-frame windows
before all 14 nonspell hits, authority was applicable/effective on **0/383**
decisions.

The first-hit window exposes a causal delivery fault in addition to source
coverage. Source roots 1137 through 1200 were complete, but the rolling worker
was blocked by a completed non-authoritative future policy staged for frame
1186. The controller spent 1,403/737 ms on UNKNOWN-source kernels, withheld
the pending kernel from the pre-publication predecessor, and submitted the next
solve only at frame 1190. Future runs must not consume a worker slot for an
incomplete source and must use a completed exact pending kernel as the
pre-publication terminal set. Stage 5 remains gated because this run did not
materially improve Stage 4A.
