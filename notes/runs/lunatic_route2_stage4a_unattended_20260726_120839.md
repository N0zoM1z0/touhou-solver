# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260726_120839

## Scope And Integrity

- Valid practice scope: `2..45275` (7349 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 26, at `[1051, 1888, 2414, 4184, 9023, 9331, 9900, 11398, 11778, 12174, 13405, 21340, 22021, 22646, 30912, 31887, 35523, 36131, 37740, 38178, 39041, 39866, 42777, 43118, 43672, 44123]`.
- Hard no-Bomb verification: **PASS** across 7349 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Input-Clock Shadow Finding

- The opt-in native FRScreen/MSG probe ran with
  `shadow_no_input_or_epoch_authority`; candidate verification and viability
  audit were disabled. It never changed the mask, epoch, delay/cadence
  evidence, estimator, policy, or worker.
- The trace retained 3,216 semantic observations:
  gate false/true/unknown `3134/81/1`. All logged observation reads were
  valid; one paired interval was unstable and therefore unknown. No signed
  MSG state `-2` was observed.
- There were five delayed same-frame auto-confirm pulse groups:
  `4963 x 4`, `6763 x 34`, `20998 x 6`, `29659 x 8`, and terminal
  `45275 x 20`. The v1 tracker incorrectly merged the first two while the MSG
  gate stayed active across a physical-frame change, so the compact trace has
  four episodes and `TP/FP/FN = 4/0/1` only relative to that delayed proxy.
  This is a retained telemetry segmentation defect, not a native-gate miss.
- At frame `20998`, desired/native input began at `0x85/0x84`; position moved
  `(75.6243, 413.5683) -> (358.5240, 413.5683)`, `282.8997 px` over
  `2.0464 s`, while FRScreen serial advanced 123. At `29659`,
  desired/native input began at `0x45/0x65`; position moved
  `(363.9006, 53.3685) -> (8.0000, 54.9949)`, `355.9044 px` over
  `2.6414 s`, with serial `+159`.
- Logged capture median/p95/max was `0.341/0.444/12.640 ms`.
  Hypothetical 50-ms cuts occurred on 2,744 gate-inactive repeats and five
  gate-active repeats, independently reproducing CE-0121's overlap.
- Raw JSONL SHA-256:
  `520d7e772464967a01d49b60a95f26b26f8a6c405e878c07d34a6ede3ceb903f`.
  Compact input-clock audit SHA-256:
  `76d052d36f9b5183fa01508f11504835400ad8fce39c92a42b28d69134b9f0cf`.
  The pulse proxy is not independent ground truth, total capture-call cost was
  not retained, synchronous issue-thread telemetry is physically
  perturbative, and no actuation consequence was tested.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1051-T1`. It occurred during a nonspell phase at player (8.000, 432.000), with 246 bullets and 0 lasers. The projectile model reported pipeline clearance -20.770.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 16 |
| `observed_bullet_overlap` | 9 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 21
- `fast_mode`: 20
- `corridor_deadline_miss`: 10
- `pool_density_over_1000`: 6
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1051 | nonspell | (8.000, 432.000) | `stay` | 246/0 | -20.770/-20.770 | 5f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1888 | nonspell | (76.132, 432.000) | `right_fast` | 290/0 | -2.758/-32.578 | 109f/139f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2414 | nonspell | (376.000, 402.136) | `down_left_fast` | 350/0 | -2.193/-2.193 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4184 | nonspell | (355.421, 418.200) | `down_fast` | 1103/0 | -0.017/-7.123 | 5f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9023 | nonspell | (48.000, 432.000) | `up_fast` | 136/0 | -6.522/-17.468 | 16f/27f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9331 | nonspell | (57.332, 388.851) | `right_fast` | 574/0 | 59.193/15.168 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 9900 | nonspell | (8.000, 408.000) | `up_fast` | 311/0 | -2.060/-25.030 | 12f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11398 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_left_fast` | 609/0 | -3.077/-3.077 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11778 | 57 夢境「二重大結界」 | (31.837, 340.640) | `down_right` | 596/0 | -2.839/-2.839 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 12174 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 607/0 | -0.886/-0.886 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13405 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 629/0 | -1.448/-1.448 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21340 | nonspell | (21.800, 432.000) | `up` | 291/0 | -1.794/-1.794 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22021 | nonspell | (84.607, 432.000) | `right_fast` | 804/0 | -1.837/-1.837 | 13f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22646 | nonspell | (313.336, 432.000) | `right_fast` | 633/0 | -1.911/-1.911 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30912 | 65 神技「八方龍殺陣」 | (224.880, 432.000) | `right_fast` | 1200/0 | -2.286/-2.286 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31887 | 65 神技「八方龍殺陣」 | (75.061, 432.000) | `down_left_fast` | 1079/0 | -4.065/-4.065 | 0f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35523 | nonspell | (8.000, 407.322) | `down_right_fast` | 85/0 | -1.912/-2.556 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36131 | nonspell | (376.000, 432.000) | `up` | 129/0 | -0.218/-0.704 | 0f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37740 | 69 回霊「夢想封印　侘」 | (376.000, 344.402) | `up_right_fast` | 492/0 | -6.651/-6.651 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38178 | 69 回霊「夢想封印　侘」 | (358.687, 339.998) | `stay` | 451/0 | -3.848/-3.848 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39041 | 69 回霊「夢想封印　侘」 | (376.000, 414.642) | `up_fast` | 644/0 | -6.321/-6.321 | 6f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39866 | 69 回霊「夢想封印　侘」 | (8.000, 317.634) | `up_fast` | 726/0 | -7.070/-7.070 | 5f/18f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42777 | 73 大結界「博麗弾幕結界」 | (218.608, 432.000) | `down_fast` | 1000/0 | -2.685/-2.685 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43118 | 73 大結界「博麗弾幕結界」 | (150.714, 391.633) | `down_left_fast` | 916/0 | -1.683/-1.683 | 0f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43672 | 73 大結界「博麗弾幕結界」 | (133.800, 432.000) | `stay` | 1290/0 | 1.613/-0.651 | 7f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 44123 | 73 大結界「博麗弾幕結界」 | (180.084, 432.000) | `down_fast` | 1317/0 | -0.127/-0.127 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 12 | 4046 | 3962 | 2087 | 0 | 1842 | 889 | 135.137 | 0.173 |
| 57 夢境「二重大結界」 | 4 | 732 | 722 | 108 | 0 | 600 | 155 | 218.724 | 0.238 |
| 61 | 0 | 660 | 655 | 191 | 0 | 443 | 147 | 153.572 | 0.096 |
| 65 神技「八方龍殺陣」 | 2 | 508 | 499 | 446 | 0 | 53 | 133 | 68.285 | 0.366 |
| 69 回霊「夢想封印　侘」 | 4 | 715 | 704 | 296 | 0 | 398 | 163 | 119.246 | 0.139 |
| 73 大結界「博麗弾幕結界」 | 4 | 688 | 674 | 272 | 0 | 380 | 158 | 132.127 | 0.035 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 30.924 ms median and 53.182 ms p95.
- The full enemy sensor produced 6625 snapshots; capture read time was `{'median': 28.330800007097423, 'p95': 55.137200048193336, 'max': 103.05550001794472}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 14.0}` frames, and 6 phase-counter discontinuities were excluded; 7088 decisions retained at least one robust-union body (maximum 58); 1274 decisions contained latent contact-disabled geometry (maximum 58), and 3524 contained bounded inactive-slot memory (maximum 52). 390 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.5343666076660156, 'p95': 4.181262969970703, 'max': 7.90423583984375}` / `{'median': 2.5952939987182617, 'p95': 3.9928762912750244, 'max': 86.88186645507812}` / `{'median': 0.00999993085861206, 'p95': 1.100006103515625, 'max': 86.88186645507812}`.
- The issue-time enemy guard retained 7349 observations, detected 2520 during-plan geometry changes, recertified 2520 decisions, and overrode 1343 actions. Read/recertificate timing was `{'median': 2.376299991738051, 'p95': 4.98259998857975, 'max': 27.404699998442084}` / `{'median': 13.347350031835958, 'p95': 21.300000022165477, 'max': 44.3307000095956}` ms; 1275 issue captures contained latent bodies (maximum 58), and 3523 contained dormant bodies (maximum 52).
- The synchronous spell-owner guard retained 5807 observations (5776 contact enabled, 31 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 5807}`.
- The terminal-threat heuristic covered 7349 decisions with horizon counts `{'0': 41, '10': 6628, '32': 680}`; it reported 9 collision and 75 sub-safety-clearance warnings, and relaxed 100 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 14, '3': 185, '4': 387, '5': 3551, '6': 3212}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 49, '3': 197, '4': 369, '5': 4927, '6': 1807}`.
- Adaptive delay supports were `{'2,3': 47, '2,3,4': 18, '2,3,4,5': 103, '2,3,4,5,6': 96, '3,4,5': 227, '3,4,5,6': 2997, '4,5': 48, '4,5,6': 3604, '5,6': 208, '6': 1}`; 1465 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 100/267.
- Robust viability supplied 7216 available policy queries (0 had new delay support outside the cached policy), constrained 3716 decisions, and exposed 3400 empty queried action sets. Recovery guidance was available/selected on 965/596 empty-kernel queries; distant-kernel guidance was available/selected on 2065/1982. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 15.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 121.85236969382254, 'p95': 310.6638054231616, 'max': 470.57411743528775}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1050, '1': 989, '2': 974, '3': 871, '4': 804, '5': 835, '6': 890, '7': 803}`.
- Global-horizon/local-prefix cross-tab covered 3423 decisions: 2 had a winning global state but unsafe selected prefix, 1344 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 45 selected actions were outside the reported winning set. 1816 newer issue-time hazard versions and 1 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1645 unique policies with solve-time statistics `{'median': 138.0366000230424, 'p95': 428.72510000597686, 'max': 648.9441000157967}` and first-observed ages `{'median': 5.0, 'p95': 11.0, 'max': 1778.0}`. Policy status counts were `{'pending_future_epoch': 31, 'queryable': 7217, 'expired': 13}`; 45 robust-mode decisions had no query.
- Of 4527 unambiguous output transitions, 3909 (0.863) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 22, 'missing_pre_hit_alive_decision': 1, 'late_collision_after_positive_causal_margin': 2, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[11, 139, 11, 11, 27, 0, 21, 9, 0, 4, 4, 5, 19, 5, 0, 19, 0, 17, 0, 0, 14, 18, 0, 17, 7, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.427 during the 60 frames preceding a hit versus 0.155 outside those windows.
- Mean selected control-reserve deficit was 12.951 during the 60 frames preceding a hit versus 6.875 outside those windows.
- Soft recovery was selected on 0.077 of alive decisions in the 60-frame pre-hit windows versus 0.079 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 10.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

The clock workload first requires corrected segmentation, then a no-write
movement-neutralization/pending-command/one-reset counterfactual and broader
negative workloads. The planner death ledger remains separate evidence; the
`26` hits are not a causal clock-sensor outcome.
