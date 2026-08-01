# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_130742

## Scope And Integrity

- Valid practice scope: `2..45285` (11324 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 21, at `[819, 1836, 2267, 3114, 3566, 4008, 10825, 11462, 12487, 12964, 13478, 18500, 20529, 22050, 22568, 23262, 30031, 30913, 39673, 42873, 43544]`.
- Hard no-Bomb verification: **PASS** across 11324 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F819-T1`. It occurred during a nonspell phase at player (8.000, 425.758), with 239 bullets and 0 lasers. The projectile model reported pipeline clearance 1.082.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 13 |
| `modeled_committed_prefix_collision` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 4 |

Contributing factors:

- `fast_mode`: 14
- `playfield_boundary`: 12
- `action_lag_over_model`: 8
- `corridor_deadline_miss`: 6
- `pool_density_over_1000`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 819 | nonspell | (8.000, 425.758) | `left` | 239/0 | 1.082/1.082 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 1836 | nonspell | (60.246, 432.000) | `up_right_fast` | 323/0 | -6.676/-10.991 | 27f/37f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 2267 | nonspell | (268.638, 350.476) | `up_right_fast` | 286/0 | -1.537/-1.537 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 3114 | nonspell | (352.082, 420.941) | `stay` | 417/0 | -1.454/-1.454 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3566 | nonspell | (344.499, 400.311) | `up_fast` | 473/0 | 25.076/15.933 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 4008 | nonspell | (269.825, 414.315) | `right` | 817/0 | 6.214/5.899 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 10825 | nonspell | (183.694, 432.000) | `left_fast` | 539/0 | -1.511/-1.511 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11462 | 57 夢境「二重大結界」 | (13.657, 422.343) | `up_right_fast` | 447/0 | 0.009/-2.287 | 2f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12487 | 57 夢境「二重大結界」 | (10.828, 429.172) | `up_right_fast` | 576/0 | 0.269/0.269 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12964 | 57 夢境「二重大結界」 | (8.000, 424.000) | `up_fast` | 609/0 | 0.504/-0.785 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13478 | 57 夢境「二重大結界」 | (12.879, 432.000) | `right_fast` | 625/0 | -1.843/-1.926 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18500 | nonspell | (189.419, 432.000) | `left_fast` | 420/0 | 1.123/-1.894 | 6f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 20529 | 61 散霊「夢想封印　寂」 | (371.121, 424.000) | `down_left` | 373/0 | -2.811/-6.254 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22050 | nonspell | (305.625, 432.000) | `left_fast` | 261/0 | 3.086/0.425 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22568 | nonspell | (376.000, 395.939) | `stay` | 848/0 | -3.095/-3.095 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 23262 | nonspell | (12.268, 432.000) | `down_right` | 718/0 | -4.418/-4.418 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30031 | nonspell | (367.515, 432.000) | `left_fast` | 157/0 | 4.721/-0.147 | 2f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 30913 | 65 神技「八方龍殺陣」 | (169.812, 429.172) | `up_left_fast` | 1166/0 | -0.972/-0.972 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39673 | 69 回霊「夢想封印　侘」 | (329.269, 425.495) | `right_fast` | 623/0 | -1.825/-2.049 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42873 | 73 大結界「博麗弾幕結界」 | (212.374, 376.900) | `left_fast` | 1000/0 | -2.278/-2.278 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43544 | 73 大結界「博麗弾幕結界」 | (142.018, 393.020) | `down_right` | 1296/0 | -3.216/-3.216 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 12 | 6376 | 378 | 104 | 0 | 401 | 28 | 724.008 | 0.246 |
| 57 夢境「二重大結界」 | 4 | 1203 | 811 | 227 | 0 | 0 | 95 | 185.578 | 0.351 |
| 61 散霊「夢想封印　寂」 | 1 | 1015 | 1009 | 460 | 0 | 0 | 167 | 127.237 | 0.238 |
| 65 神技「八方龍殺陣」 | 1 | 753 | 297 | 214 | 0 | 0 | 12 | 55.272 | 0.410 |
| 69 回霊「夢想封印　侘」 | 1 | 1045 | 919 | 617 | 0 | 0 | 159 | 95.931 | 0.156 |
| 73 大結界「博麗弾幕結界」 | 2 | 932 | 926 | 509 | 0 | 0 | 183 | 127.533 | 0.027 |

## Interpretation

- Retained witnesses classify 13 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.529 ms median and 32.909 ms p95.
- The full enemy sensor produced 6215 snapshots; capture read time was `{'median': 5.643599986797199, 'p95': 28.297599987126887, 'max': 556.1554000014439}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 98.0}` frames, and 12 phase-counter discontinuities were excluded; 11021 decisions retained at least one robust-union body (maximum 44); 5764 decisions contained latent contact-disabled geometry (maximum 44), and 4251 contained bounded inactive-slot memory (maximum 36). 350 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.502962112426758, 'p95': 4.330047607421875, 'max': 7.127970377604167}` / `{'median': 2.5952913761138916, 'p95': 3.9871714115142822, 'max': 9.567291259765625}` / `{'median': 0.49008221626281734, 'p95': 2.8259435381208147, 'max': 9.79998779296875}`.
- The issue-time enemy guard retained 11324 observations, detected 3957 during-plan geometry changes, recertified 3957 decisions, and overrode 58 actions. Read/recertificate timing was `{'median': 1.5635000017937273, 'p95': 2.7840000111609697, 'max': 93.28649999224581}` / `{'median': 2.4803999986033887, 'p95': 8.967700006905943, 'max': 432.24860000191256}` ms; 5756 issue captures contained latent bodies (maximum 45), and 4262 contained dormant bodies (maximum 36). Fresh/global transactions preserved 3931/3989 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9843 observations (9799 contact enabled, 44 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9843}`.
- The terminal-threat heuristic covered 11324 decisions with horizon counts `{'0': 31, '10': 11293}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 79, '3': 6949, '4': 2998, '5': 758, '6': 540}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1416, '3': 7938, '4': 1691, '5': 95, '6': 184}`.
- Adaptive delay supports were `{'1,2,3': 39, '1,2,3,4': 31, '2,3': 804, '2,3,4': 3468, '2,3,4,5': 3105, '2,3,4,5,6': 2517, '3,4': 82, '3,4,5': 365, '3,4,5,6': 701, '4,5': 18, '4,5,6': 148, '5,6': 24, '6': 22}`; 105 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 26/131.
- Robust viability supplied 4340 available policy queries (0 had new delay support outside the cached policy), constrained 401 decisions, and exposed 2131 empty queried action sets. Recovery guidance was available/selected on 696/0 empty-kernel queries; distant-kernel guidance was available/selected on 1242/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 664, '1': 566, '2': 507, '3': 438, '4': 563, '5': 523, '6': 518, '7': 561}`.
- Global-horizon/local-prefix cross-tab covered 2266 decisions: 0 had a winning global state but unsafe selected prefix, 1182 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 138 selected actions were outside the reported winning set. 911 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 644 unique policies with solve-time statistics `{'median': 124.92350001411978, 'p95': 224.64070000569336, 'max': 3322.8830999869388}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1697.0}`. Policy status counts were `{'pending_future_epoch': 320, 'queryable': 4322, 'expired': 2200}`; 2502 robust-mode decisions had no query.
- Of 6354 unambiguous output transitions, 6053 (0.953) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 3, 'robust_action_set_exhausted_before_hit': 6, 'late_collision_after_positive_causal_margin': 2, 'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 14 hit windows with a positive warning lead; those leads were `[0, 37, 0, 0, 0, 0, 5, 5, 6, 6, 8, 15, 9, 0, 0, 4, 5, 7, 9, 8, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.503 during the 60 frames preceding a hit versus 0.229 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
