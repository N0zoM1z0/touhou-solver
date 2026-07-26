# TH08 Stage 4A / Reimu No-Bomb Practice Review: hard_route2_stage4a_unattended_20260726_202439

## Scope And Integrity

- Valid practice scope: `2..44606` (13535 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 15, at `[3419, 4404, 8983, 10727, 11625, 12184, 12723, 13107, 17618, 19976, 21797, 28431, 30660, 31701, 38863]`.
- Hard no-Bomb verification: **PASS** across 13535 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S3-F3419-T1`. It occurred during a nonspell phase at player (18.991, 417.009), with 148 bullets and 0 lasers. The projectile model reported pipeline clearance 1.075.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 7 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 11
- `playfield_boundary`: 10
- `corridor_deadline_miss`: 7

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3419 | nonspell | (18.991, 417.009) | `up_right_fast` | 148/0 | 1.075/0.746 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4404 | nonspell | (103.446, 421.659) | `up` | 540/0 | -2.409/-2.409 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8983 | nonspell | (27.851, 432.000) | `up_right` | 138/0 | -20.117/-21.254 | 9f/14f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10727 | 56 夢境「二重大結界」 | (8.000, 428.000) | `up_right_fast` | 452/0 | -2.089/-2.089 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11625 | 56 夢境「二重大結界」 | (22.287, 235.508) | `up_fast` | 539/0 | 1.530/-1.867 | 2f/2f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12184 | 56 夢境「二重大結界」 | (372.747, 432.000) | `up_fast` | 529/0 | -1.824/-1.824 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12723 | 56 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 540/0 | -1.802/-1.802 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13107 | 56 夢境「二重大結界」 | (374.171, 420.000) | `up_fast` | 552/0 | 2.310/-1.889 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 17618 | nonspell | (8.000, 424.000) | `up_right_fast` | 370/0 | 0.231/-1.438 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19976 | 60 散霊「夢想封印　寂」 | (315.601, 432.000) | `up_right_fast` | 181/0 | -2.724/-12.187 | 10f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21797 | nonspell | (359.090, 430.447) | `left` | 425/0 | -3.146/-3.146 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28431 | nonspell | (376.000, 16.000) | `down` | 152/0 | -3.320/-3.320 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30660 | 64 神技「八方鬼縛陣」 | (372.747, 432.000) | `up_fast` | 839/0 | -1.531/-6.961 | 3f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31701 | 64 神技「八方鬼縛陣」 | (316.918, 408.000) | `down_left_fast` | 790/0 | -2.608/-2.608 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38863 | 68 回霊「夢想封印　侘」 | (12.879, 338.011) | `down_left_fast` | 675/0 | -3.361/-3.361 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 7840 | 7687 | 3188 | 0 | 4457 | 941 | 159.108 | 0.150 |
| 56 夢境「二重大結界」 | 5 | 1223 | 1212 | 227 | 0 | 957 | 162 | 246.708 | 0.164 |
| 60 散霊「夢想封印　寂」 | 1 | 1273 | 1265 | 315 | 0 | 921 | 156 | 169.693 | 0.166 |
| 64 神技「八方鬼縛陣」 | 2 | 1145 | 1129 | 938 | 0 | 191 | 157 | 60.065 | 0.294 |
| 68 回霊「夢想封印　侘」 | 1 | 1173 | 1164 | 449 | 0 | 715 | 171 | 111.780 | 0.083 |
| 72 | 0 | 881 | 857 | 376 | 0 | 458 | 142 | 142.285 | 0.034 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 12.903 ms median and 22.274 ms p95.
- The full enemy sensor produced 6882 snapshots; capture read time was `{'median': 10.026400035712868, 'p95': 26.404400006867945, 'max': 51.366400031838566}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 10.0}` frames, and 6 phase-counter discontinuities were excluded; 13142 decisions retained at least one robust-union body (maximum 52); 2643 decisions contained latent contact-disabled geometry (maximum 51), and 7006 contained bounded inactive-slot memory (maximum 44). 215 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.46343994140625, 'p95': 4.425323486328125, 'max': 17.883291880289715}` / `{'median': 2.463444232940674, 'p95': 3.922954559326172, 'max': 5.5}` / `{'median': 0.006425917148590088, 'p95': 3.2599925994873047, 'max': 12.383291880289715}`.
- The issue-time enemy guard retained 13535 observations, detected 2672 during-plan geometry changes, recertified 2672 decisions, and overrode 1435 actions. Read/recertificate timing was `{'median': 1.8836999661289155, 'p95': 3.7047999794594944, 'max': 21.263800037559122}` / `{'median': 2.315650024684146, 'p95': 4.842100024688989, 'max': 12.732700037304312}` ms; 2643 issue captures contained latent bodies (maximum 51), and 6978 contained dormant bodies (maximum 44).
- The synchronous spell-owner guard retained 10412 observations (10375 contact enabled, 37 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4461, '0x00587A90': 5951}`.
- The terminal-threat heuristic covered 13535 decisions with horizon counts `{'0': 73, '10': 12670, '32': 792}`; it reported 10 collision and 100 sub-safety-clearance warnings, and relaxed 122 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 373, '3': 11878, '4': 1284}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 91, '2': 2504, '3': 10540, '4': 400}`.
- Adaptive delay supports were `{'1,2': 74, '1,2,3': 64, '1,2,3,4': 271, '1,2,3,4,5': 9, '2,3': 1045, '2,3,4': 6112, '2,3,4,5': 3866, '2,3,4,5,6': 1729, '3,4': 57, '3,4,5': 71, '3,4,5,6': 237}`; 1462 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 45/262.
- Robust viability supplied 13314 available policy queries (0 had new delay support outside the cached policy), constrained 7699 decisions, and exposed 5493 empty queried action sets. Recovery guidance was available/selected on 1395/655 empty-kernel queries; distant-kernel guidance was available/selected on 3476/3351. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 5.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 23.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 113.13708498984761, 'p95': 309.01132665324747, 'max': 480.0}`, and `{'median': 0.0, 'p95': 16.0, 'max': 44.8758819103241}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1936, '1': 1806, '2': 1527, '3': 1622, '4': 1554, '5': 1655, '6': 1548, '7': 1666}`.
- Global-horizon/local-prefix cross-tab covered 8836 decisions: 6 had a winning global state but unsafe selected prefix, 3423 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 68 selected actions were outside the reported winning set. 2330 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1729 unique policies with solve-time statistics `{'median': 151.3771999743767, 'p95': 429.975499981083, 'max': 574.3907000287436}` and first-observed ages `{'median': 2.0, 'p95': 8.0, 'max': 1776.0}`. Policy status counts were `{'pending_future_epoch': 60, 'queryable': 13315, 'expired': 17}`; 78 robust-mode decisions had no query.
- Of 7091 unambiguous output transitions, 6483 (0.914) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 14, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[0, 3, 14, 4, 2, 5, 6, 5, 5, 14, 7, 3, 5, 0, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.449 during the 60 frames preceding a hit versus 0.139 outside those windows.
- Mean selected control-reserve deficit was 10.843 during the 60 frames preceding a hit versus 3.667 outside those windows.
- Soft recovery was selected on 0.072 of alive decisions in the 60-frame pre-hit windows versus 0.051 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 20.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Viability Differential

This run was intentionally captured with `--viability-audit`; its hit count is
not a controller A/B. All 1,741 capsules are readable, all 1,729 trace
references resolve, and the bundle SHA-256 is
`89b1bd71e299a429091092a59da0cfc628a259fdf181a68c546bccb5d78592e6`.

Of 120 stratified same-root pre-hit queries, 61 were empty. Six became viable
at 8/4 pixels, eight were primary finite-horizon collapses, and 47 remained
losing/unresolved. Fresh 16-pixel recomputation rescued zero. Uniform
fine-grid induction is therefore not the main correction.

CE-0127 is the immediate correctness gate. On 168 globally winning decisions,
the issue-time enemy recertifier changed an in-mask planned action to an
out-of-mask action while telemetry still reported an unrelaxed global
constraint. The canonical frame-3353 override changed `up_fast` to
`down_fast`; the next query was empty and the first hit followed at 3419.
This is not a prevented-hit claim because the exact fresh intersection was
not serialized.

See `notes/HARD_STAGE4A_VIABILITY_DIFFERENTIAL_20260726.md` and
`artifacts/viability_audit/hard_stage4a_20260726_202439_root_cause.json`.
