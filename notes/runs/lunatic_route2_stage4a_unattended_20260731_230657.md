# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260731_230657

## Scope And Integrity

- Valid practice scope: `2..45036` (11481 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[499, 1259, 3900, 4201, 8818, 9852, 11464, 11951, 12581, 13090, 21835, 22626, 30926, 37553, 38192, 39868, 42622, 44501]`.
- Hard no-Bomb verification: **PASS** across 11481 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F499-T1`. It occurred during a nonspell phase at player (192.000, 384.000), with 112 bullets and 0 lasers. The projectile model reported pipeline clearance 0.390.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 9 |
| `modeled_committed_prefix_collision` | 8 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 15
- `playfield_boundary`: 14
- `corridor_deadline_miss`: 10
- `pool_density_over_1000`: 2
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 499 | nonspell | (192.000, 384.000) | `stay` | 112/0 | 0.390/0.390 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 1259 | nonspell | (8.000, 420.686) | `up_fast` | 317/0 | -2.575/-2.575 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3900 | nonspell | (363.443, 432.000) | `left` | 681/0 | -1.722/-1.868 | 3f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4201 | nonspell | (266.713, 432.000) | `right_fast` | 856/0 | 0.406/-12.797 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 8818 | nonspell | (368.895, 432.000) | `right_fast` | 766/0 | -18.502/-18.502 | 5f/14f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 9852 | nonspell | (203.868, 432.000) | `right_fast` | 528/0 | 0.773/-3.389 | 4f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11464 | 57 夢境「二重大結界」 | (376.000, 428.000) | `up_fast` | 572/0 | -1.769/-1.769 | 0f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11951 | 57 夢境「二重大結界」 | (8.000, 424.000) | `up_fast` | 617/0 | 0.500/-1.552 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12581 | 57 夢境「二重大結界」 | (8.000, 413.797) | `up_right_fast` | 608/0 | -2.260/-2.260 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13090 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 607/0 | -3.837/-3.837 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21835 | nonspell | (21.085, 432.000) | `up_right_fast` | 764/0 | -0.710/-2.073 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22626 | nonspell | (8.000, 408.163) | `up` | 839/0 | -1.009/-3.071 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30926 | 65 神技「八方龍殺陣」 | (170.879, 410.595) | `down_left_fast` | 1099/0 | -2.297/-2.355 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37553 | 69 回霊「夢想封印　侘」 | (66.687, 432.000) | `up_right_fast` | 405/0 | -4.058/-4.058 | 4f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 38192 | 69 回霊「夢想封印　侘」 | (376.000, 401.505) | `up_right_fast` | 503/0 | -4.378/-4.524 | 7f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39868 | 69 回霊「夢想封印　侘」 | (376.000, 432.000) | `up_fast` | 727/0 | -3.138/-3.138 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42622 | 73 大結界「博麗弾幕結界」 | (211.516, 371.695) | `down_left_fast` | 980/0 | -2.518/-2.518 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44501 | 73 大結界「博麗弾幕結界」 | (35.661, 375.168) | `up_right_fast` | 1323/0 | 2.769/-0.294 | 5f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 6274 | 4127 | 1721 | 0 | 0 | 212 | 529.610 | 0.199 |
| 57 夢境「二重大結界」 | 4 | 1178 | 1059 | 273 | 0 | 0 | 121 | 178.760 | 0.348 |
| 61 | 0 | 1021 | 1001 | 459 | 0 | 0 | 150 | 111.187 | 0.239 |
| 65 神技「八方龍殺陣」 | 1 | 866 | 436 | 349 | 0 | 0 | 30 | 64.413 | 0.413 |
| 69 回霊「夢想封印　侘」 | 3 | 1173 | 788 | 473 | 0 | 0 | 77 | 88.932 | 0.164 |
| 73 大結界「博麗弾幕結界」 | 2 | 969 | 947 | 499 | 0 | 0 | 172 | 116.914 | 0.032 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 17.114 ms median and 41.273 ms p95.
- The full enemy sensor produced 6623 snapshots; capture read time was `{'median': 6.767700004274957, 'p95': 50.12020000140183, 'max': 74.66899999417365}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 13.0}` frames, and 7 phase-counter discontinuities were excluded; 10795 decisions retained at least one robust-union body (maximum 58); 6190 decisions contained latent contact-disabled geometry (maximum 58), and 4331 contained bounded inactive-slot memory (maximum 26). 329 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.7477264404296875, 'p95': 4.3300323486328125, 'max': 7.810871124267578}` / `{'median': 2.9147636890411377, 'p95': 3.9229559898376465, 'max': 4.0799970626831055}` / `{'median': 0.5367660522460938, 'p95': 3.7757701873779297, 'max': 7.937309145927429}`.
- The issue-time enemy guard retained 11481 observations, detected 4504 during-plan geometry changes, recertified 4504 decisions, and overrode 57 actions. Read/recertificate timing was `{'median': 1.4969000039855018, 'p95': 3.0203000060282648, 'max': 14.491300011286512}` / `{'median': 3.0306499975267798, 'p95': 9.411099992576055, 'max': 34.237599989864975}` ms; 6200 issue captures contained latent bodies (maximum 58), and 4335 contained dormant bodies (maximum 26). Fresh/global transactions preserved 4447/4504 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8532 observations (8498 contact enabled, 34 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 8532}`.
- The terminal-threat heuristic covered 11481 decisions with horizon counts `{'0': 682, '10': 10799}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 605, '3': 3396, '4': 4094, '5': 3383, '6': 3}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 452, '2': 218, '3': 6058, '4': 4334, '5': 419}`.
- Adaptive delay supports were `{'1': 251, '1,2': 64, '1,2,3': 78, '1,2,3,4': 2, '1,2,3,4,5': 410, '1,2,3,4,5,6': 209, '2,3': 22, '2,3,4': 644, '2,3,4,5': 4056, '2,3,4,5,6': 4333, '3,4': 192, '3,4,5': 418, '3,4,5,6': 801, '4,5,6': 1}`; 114 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 23/215.
- Robust viability supplied 8358 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 3774 empty queried action sets. Recovery guidance was available/selected on 962/0 empty-kernel queries; distant-kernel guidance was available/selected on 2358/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 4.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1192, '1': 1111, '2': 1011, '3': 945, '4': 1045, '5': 1035, '6': 985, '7': 1034}`.
- Global-horizon/local-prefix cross-tab covered 4110 decisions: 13 had a winning global state but unsafe selected prefix, 1610 had a losing global state but safe short prefix, 11 selected globally certified actions contradicted the fresh local prefix checker, and 312 selected actions were outside the reported winning set. 2606 newer issue-time hazard versions and 3 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 762 unique policies with solve-time statistics `{'median': 139.86455000122078, 'p95': 1773.8269999972545, 'max': 3138.7504000012996}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1927.0}`. Policy status counts were `{'pending_future_epoch': 243, 'queryable': 8295, 'expired': 2758}`; 2938 robust-mode decisions had no query.
- Of 6506 unambiguous output transitions, 6362 (0.978) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'late_collision_after_positive_causal_margin': 1, 'global_viability_kernel_exhausted_before_hit': 12, 'missing_pre_hit_alive_decision': 1, 'robust_action_set_exhausted_before_hit': 4}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 16 hit windows with a positive warning lead; those leads were `[0, 5, 8, 0, 14, 8, 5, 6, 6, 5, 5, 11, 3, 7, 14, 3, 10, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.482 during the 60 frames preceding a hit versus 0.206 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Experiment Validity Correction

This accepted no-Bomb replay is **not** a valid future-source/ordinary-authority
gate. The launch omitted `--runtime-ecl-static-image` and its immutable hash,
so `ordinary_future_ecl` was never constructed. The trace contains zero
`ordinary_future_source_projection` records; all 6,127 state-eligible
nonspell decisions report `future_policy_unavailable`, zero complete coverage,
and zero authority. Its 18 hits and first hit 499 describe the fallback path
only and must not be compared as an authority result.
