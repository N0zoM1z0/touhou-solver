# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_004533

## Scope And Integrity

- Valid practice scope: `1..45842` (12489 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 22, at `[1837, 2606, 3092, 3549, 4050, 4508, 9866, 10947, 11723, 12336, 12905, 13445, 13924, 19979, 21891, 22584, 22965, 30843, 31782, 32771, 38475, 43950]`.
- Hard no-Bomb verification: **PASS** across 12489 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1837-T1`. It occurred during a nonspell phase at player (93.906, 398.005), with 391 bullets and 0 lasers. The projectile model reported pipeline clearance -1.407.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 9 |
| `observed_enemy_body_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 15
- `playfield_boundary`: 15
- `corridor_deadline_miss`: 6
- `pool_density_over_1000`: 5
- `action_lag_over_model`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1837 | nonspell | (93.906, 398.005) | `right` | 391/0 | -1.407/-1.407 | 6f/27f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 2606 | nonspell | (190.508, 432.000) | `left` | 93/0 | -0.878/-0.878 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 3092 | nonspell | (360.086, 412.076) | `stay` | 430/0 | -1.044/-1.044 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 3549 | nonspell | (287.401, 341.401) | `up_left` | 351/0 | 16.825/15.648 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 4050 | nonspell | (376.000, 355.349) | `up_right` | 978/0 | -2.673/-2.673 | 2f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 4508 | nonspell | (8.000, 409.210) | `up_fast` | 1308/0 | -2.056/-2.056 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 9866 | nonspell | (49.311, 432.000) | `left_fast` | 399/0 | -2.157/-2.157 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 10947 | nonspell | (8.000, 432.000) | `left_fast` | 201/0 | -19.235/-19.235 | 6f/14f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11723 | 57 夢境「二重大結界」 | (30.571, 432.000) | `up_right_fast` | 581/0 | -2.432/-2.432 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12336 | 57 夢境「二重大結界」 | (8.000, 424.000) | `up_fast` | 633/0 | -0.239/-1.525 | 3f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12905 | 57 夢境「二重大結界」 | (8.000, 424.000) | `up_fast` | 626/0 | 1.185/-2.212 | 2f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13445 | 57 夢境「二重大結界」 | (8.000, 428.000) | `up_right_fast` | 579/0 | -1.779/-1.779 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13924 | 57 夢境「二重大結界」 | (8.000, 428.000) | `up_fast` | 598/0 | -2.348/-2.348 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19979 | 61 散霊「夢想封印　寂」 | (178.319, 432.000) | `up_right_fast` | 363/0 | -17.491/-17.491 | 3f/10f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21891 | nonspell | (335.690, 316.747) | `up_fast` | 341/0 | -1.562/-1.562 | 11f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 22584 | nonspell | (28.264, 432.000) | `down` | 823/0 | -2.273/-2.273 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22965 | nonspell | (65.947, 355.788) | `up_right_fast` | 603/0 | -1.833/-1.833 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30843 | 65 神技「八方龍殺陣」 | (308.497, 429.172) | `up_left_fast` | 1099/0 | 0.864/0.090 | 0f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31782 | 65 神技「八方龍殺陣」 | (174.621, 432.000) | `up_left_fast` | 1120/0 | -1.863/-1.917 | 2f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32771 | 65 神技「八方龍殺陣」 | (153.596, 432.000) | `right_fast` | 1058/0 | 1.292/-1.462 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38475 | 69 回霊「夢想封印　侘」 | (76.757, 425.495) | `stay` | 471/0 | -1.186/-1.186 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43950 | 73 大結界「博麗弾幕結界」 | (93.335, 347.446) | `down_left_fast` | 1291/0 | -1.844/-1.844 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 11 | 7275 | 212 | 6 | 0 | 287 | 20 | 63.134 | 0.243 |
| 57 夢境「二重大結界」 | 5 | 1254 | 728 | 200 | 0 | 0 | 67 | 184.386 | 0.342 |
| 61 散霊「夢想封印　寂」 | 1 | 1030 | 1024 | 516 | 0 | 0 | 161 | 125.356 | 0.198 |
| 65 神技「八方龍殺陣」 | 3 | 960 | 502 | 412 | 0 | 0 | 39 | 66.105 | 0.431 |
| 69 回霊「夢想封印　侘」 | 1 | 1039 | 1034 | 698 | 0 | 0 | 172 | 94.289 | 0.133 |
| 73 大結界「博麗弾幕結界」 | 1 | 931 | 921 | 508 | 0 | 0 | 172 | 123.099 | 0.065 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.935 ms median and 31.603 ms p95.
- The full enemy sensor produced 6659 snapshots; capture read time was `{'median': 5.3078999917488545, 'p95': 17.729900006088428, 'max': 86.04290000221226}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 46.0}` frames, and 6 phase-counter discontinuities were excluded; 12170 decisions retained at least one robust-union body (maximum 58); 6722 decisions contained latent contact-disabled geometry (maximum 58), and 4995 contained bounded inactive-slot memory (maximum 37). 445 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.45477294921875, 'p95': 4.1666412353515625, 'max': 6.2645792961120605}` / `{'median': 2.44482159614563, 'p95': 3.899993896484375, 'max': 5.180156707763672}` / `{'median': 0.010867834091186523, 'p95': 1.7199821472167969, 'max': 9.500015258789062}`.
- The issue-time enemy guard retained 12489 observations, detected 5124 during-plan geometry changes, recertified 5124 decisions, and overrode 78 actions. Read/recertificate timing was `{'median': 1.5475000109290704, 'p95': 2.7780999953392893, 'max': 152.50909999303985}` / `{'median': 2.412950008874759, 'p95': 4.627500005881302, 'max': 123.84119999478571}` ms; 6708 issue captures contained latent bodies (maximum 58), and 4994 contained dormant bodies (maximum 37). Fresh/global transactions preserved 5046/5124 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9996 observations (9956 contact enabled, 40 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4332, '0x0059C9D0': 5664}`.
- The terminal-threat heuristic covered 12489 decisions with horizon counts `{'0': 60, '10': 12429}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 38, '3': 8583, '4': 3354, '5': 408, '6': 106}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1266, '3': 10053, '4': 1169, '5': 1}`.
- Adaptive delay supports were `{'1,2,3': 5, '1,2,3,4': 22, '2,3': 552, '2,3,4': 3692, '2,3,4,5': 4188, '2,3,4,5,6': 3154, '3,4': 33, '3,4,5': 359, '3,4,5,6': 469, '4,5,6': 14, '5,6': 1}`; 104 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 26/149.
- Robust viability supplied 4421 available policy queries (0 had new delay support outside the cached policy), constrained 287 decisions, and exposed 2340 empty queried action sets. Recovery guidance was available/selected on 730/0 empty-kernel queries; distant-kernel guidance was available/selected on 1325/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 685, '1': 614, '2': 525, '3': 460, '4': 539, '5': 554, '6': 512, '7': 532}`.
- Global-horizon/local-prefix cross-tab covered 2386 decisions: 5 had a winning global state but unsafe selected prefix, 1260 had a losing global state but safe short prefix, 3 selected globally certified actions contradicted the fresh local prefix checker, and 168 selected actions were outside the reported winning set. 986 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 631 unique policies with solve-time statistics `{'median': 116.4415000093868, 'p95': 387.93290000467096, 'max': 23460.345699990285}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1649.0}`. Policy status counts were `{'pending_future_epoch': 167, 'queryable': 4406, 'expired': 3998}`; 4150 robust-mode decisions had no query.
- Of 6945 unambiguous output transitions, 6609 (0.952) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 10, 'late_collision_after_positive_causal_margin': 2, 'unresolved_planner_failure': 1, 'global_viability_kernel_exhausted_before_hit': 9}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[27, 0, 0, 0, 15, 6, 5, 14, 4, 5, 4, 6, 6, 10, 11, 6, 4, 3, 5, 7, 10, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.552 during the 60 frames preceding a hit versus 0.218 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Exact Ordinary-Authority Audit

- **Observed:** 173/2,030 future-source projections completed. Across 7,275
  nonspell decisions, exact authority was applicable/effective on 287/287;
  56 sets were directional, 231 contained all 17 actions, and 12 exact
  predecessors were empty.
- **Observed:** a completed pending exact policy supplied 110 effective
  decisions. Before first hit 1837, 178/680 decisions were effective, of
  which 43 used the pending terminal. This physically validates the pending
  publication correction from CE-0244.
- **Observed:** authority was still effective on 0/287 decisions in the
  80-frame windows before the 11 nonspell hits. Their reasons were 280
  `future_policy_unavailable`, four exact-empty predecessors, and three
  player transitions. Therefore 22 hits versus the prior 24 and first hit
  1837 versus 1205 are different-RNG observations, not causal promotion.
- **Observed:** the serial solver completed 23 policies and its nonspell
  median fell from 908.551 ms to 63.134 ms, but dense complete sources missed
  their publication epochs. Representative exact solves were 6,939 ms
  (6,102.65 ms clearance, 809.52 ms viability), 19,783 ms (19,505.59 ms
  clearance, 236.52 ms viability), and 23,460 ms (23,199.30 ms clearance,
  226.88 ms viability). Complete sources contained up to 750 future
  annular-sector trajectories.
- **Inferred blocker:** exact future-hazard clearance construction, not the
  Boolean predecessor recurrence, dominates the remaining useful-authority
  deadline miss. Stage 5 is withheld until this path is accelerated and a
  fresh Stage-4A gate shows authority inside pressure windows.
