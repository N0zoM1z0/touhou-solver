# TH08 Stage 4A / Reimu No-Bomb Practice Review: hard_route2_stage4a_unattended_20260801_191508

## Scope And Integrity

- Valid practice scope: `2..44730` (12268 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[1975, 2830, 4443, 8994, 10007, 10625, 10941, 11344, 11822, 12965, 16878, 20962, 22073, 35209, 38602, 39151, 43598, 44374]`.
- Hard no-Bomb verification: **PASS** across 12268 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S3-F1975-T1`. It occurred during a nonspell phase at player (33.526, 432.000), with 54 bullets and 0 lasers. The projectile model reported pipeline clearance 0.510.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 8 |
| `modeled_committed_prefix_collision` | 5 |
| `sensor_gap_or_unmodeled_hazard` | 3 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 12
- `fast_mode`: 11
- `corridor_deadline_miss`: 4
- `action_lag_over_model`: 2
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1975 | nonspell | (33.526, 432.000) | `left_fast` | 54/0 | 0.510/-21.155 | 17f/23f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 2830 | nonspell | (363.223, 321.114) | `stay` | 419/0 | 0.406/0.406 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 4443 | nonspell | (123.372, 412.201) | `stay` | 390/0 | 0.189/-2.217 | 3f/5f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 8994 | nonspell | (198.785, 432.000) | `right` | 123/0 | -13.159/-13.159 | 5f/11f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 10007 | nonspell | (241.840, 416.000) | `up_fast` | 89/0 | -1.542/-8.513 | 7f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 10625 | 56 夢境「二重大結界」 | (31.321, 312.983) | `left_fast` | 482/0 | -0.324/-0.324 | 0f/2f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 10941 | 56 夢境「二重大結界」 | (359.737, 295.213) | `up_left_fast` | 518/0 | 1.657/1.657 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 11344 | 56 夢境「二重大結界」 | (368.293, 432.000) | `up_fast` | 531/0 | -0.086/-2.300 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11822 | 56 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 536/0 | -1.799/-1.799 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12965 | 56 夢境「二重大結界」 | (8.000, 428.000) | `up_right_fast` | 526/0 | -3.464/-3.464 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 16878 | nonspell | (374.374, 423.452) | `up_left` | 230/0 | -2.396/-2.715 | 3f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 20962 | nonspell | (214.835, 432.000) | `down_left` | 90/0 | 5.232/2.463 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22073 | nonspell | (8.000, 406.601) | `up_right_fast` | 293/0 | -3.048/-3.048 | 3f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 35209 | nonspell | (8.000, 432.000) | `up_left` | 125/0 | -16.126/-16.126 | 5f/10f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 38602 | 68 回霊「夢想封印　侘」 | (25.431, 429.172) | `up_left_fast` | 664/0 | -2.549/-2.549 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39151 | 68 回霊「夢想封印　侘」 | (376.000, 432.000) | `up_left` | 703/0 | -1.285/-1.285 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43598 | 72 大結界「博麗弾幕結界」 | (336.952, 372.971) | `right_fast` | 1057/0 | -0.678/-1.980 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44374 | 72 大結界「博麗弾幕結界」 | (62.186, 428.130) | `right_fast` | 1050/0 | 1.468/-2.903 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 6925 | 695 | 26 | 0 | 822 | 35 | 704.595 | 0.212 |
| 56 夢境「二重大結界」 | 5 | 1210 | 1078 | 387 | 0 | 691 | 128 | 141.978 | 0.109 |
| 60 | 0 | 1081 | 1074 | 652 | 0 | 422 | 166 | 64.288 | 0.058 |
| 64 | 0 | 897 | 787 | 635 | 0 | 152 | 84 | 50.559 | 0.263 |
| 68 回霊「夢想封印　侘」 | 2 | 1115 | 1108 | 674 | 0 | 434 | 181 | 60.726 | 0.037 |
| 72 大結界「博麗弾幕結界」 | 2 | 1040 | 1033 | 553 | 0 | 480 | 184 | 86.456 | 0.001 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 17.536 ms median and 31.842 ms p95.
- The full enemy sensor produced 6489 snapshots; capture read time was `{'median': 5.607099999906495, 'p95': 19.93809998384677, 'max': 261.15889998618513}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 31.0}` frames, and 6 phase-counter discontinuities were excluded; 11946 decisions retained at least one robust-union body (maximum 51); 6682 decisions contained latent contact-disabled geometry (maximum 51), and 4975 contained bounded inactive-slot memory (maximum 26). 209 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.976104736328125, 'p95': 4.072113037109375, 'max': 28.309065461158752}` / `{'median': 3.0086331367492676, 'p95': 3.8987674713134766, 'max': 11.600001335144043}` / `{'median': 0.006022214889526367, 'p95': 1.7803605886606069, 'max': 39.909066796302795}`.
- The issue-time enemy guard retained 12268 observations, detected 4505 during-plan geometry changes, recertified 4505 decisions, and overrode 242 actions. Read/recertificate timing was `{'median': 1.5487000055145472, 'p95': 2.930200018454343, 'max': 135.98890000139363}` / `{'median': 2.4034999951254576, 'p95': 5.934099986916408, 'max': 247.69330001436174}` ms; 6686 issue captures contained latent bodies (maximum 51), and 4981 contained dormant bodies (maximum 26). Fresh/global transactions preserved 4263/4505 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9811 observations (9769 contact enabled, 42 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9811}`.
- The terminal-threat heuristic covered 12268 decisions with horizon counts `{'0': 27, '10': 12241}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 26, '3': 8552, '4': 3198, '5': 380, '6': 112}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 991, '3': 9978, '4': 1271, '5': 27, '6': 1}`.
- Adaptive delay supports were `{'1,2,3': 39, '1,2,3,4': 32, '2,3': 350, '2,3,4': 3943, '2,3,4,5': 3886, '2,3,4,5,6': 3400, '3,4': 19, '3,4,5': 284, '3,4,5,6': 306, '4,5,6': 4, '5,6': 4, '6': 1}`; 264 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 27/123.
- Robust viability supplied 5775 available policy queries (0 had new delay support outside the cached policy), constrained 3001 decisions, and exposed 2927 empty queried action sets. Recovery guidance was available/selected on 584/359 empty-kernel queries; distant-kernel guidance was available/selected on 1732/1673. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 7.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 81.58431221748455, 'p95': 326.3372488699382, 'max': 486.6210024238576}`, and `{'median': 0.0, 'p95': 13.738067626953125, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 878, '1': 807, '2': 622, '3': 651, '4': 675, '5': 713, '6': 732, '7': 697}`.
- Global-horizon/local-prefix cross-tab covered 3084 decisions: 7 had a winning global state but unsafe selected prefix, 1703 had a losing global state but safe short prefix, 7 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 1435 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 778 unique policies with solve-time statistics `{'median': 78.6991500062868, 'p95': 198.19950000965036, 'max': 3073.0024999938905}` and first-observed ages `{'median': 3.0, 'p95': 4.0, 'max': 1760.0}`. Policy status counts were `{'pending_future_epoch': 121, 'queryable': 5750, 'expired': 2486}`; 2582 robust-mode decisions had no query.
- Of 6423 unambiguous output transitions, 6111 (0.951) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 8, 'late_collision_after_positive_causal_margin': 1, 'unresolved_planner_failure': 1, 'global_viability_kernel_exhausted_before_hit': 8}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 15 hit windows with a positive warning lead; those leads were `[23, 0, 5, 11, 9, 2, 0, 7, 3, 4, 5, 0, 5, 10, 7, 10, 8, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.391 during the 60 frames preceding a hit versus 0.154 outside those windows.
- Mean selected control-reserve deficit was 3.806 during the 60 frames preceding a hit versus 0.224 outside those windows.
- Soft recovery was selected on 0.041 of alive decisions in the 60-frame pre-hit windows versus 0.023 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
