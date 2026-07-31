# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260731_220830

## Scope And Integrity

- Valid practice scope: `2..45081` (10016 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 23, at `[939, 1964, 2325, 4166, 9023, 9540, 11048, 11528, 12187, 16468, 17305, 20359, 21793, 22301, 28161, 28645, 30653, 31458, 34787, 36392, 42635, 43313, 44168]`.
- Hard no-Bomb verification: **PASS** across 10016 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F939-T1`. It occurred during a nonspell phase at player (109.387, 330.242), with 154 bullets and 0 lasers. The projectile model reported pipeline clearance -3.781.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 17 |
| `observed_bullet_overlap` | 5 |
| `observed_multiple_hazard_overlap` | 1 |

Contributing factors:

- `fast_mode`: 17
- `playfield_boundary`: 17
- `corridor_deadline_miss`: 10
- `action_lag_over_model`: 6
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 939 | nonspell | (109.387, 330.242) | `up_right_fast` | 154/0 | -3.781/-3.781 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1964 | nonspell | (8.000, 426.628) | `down_left_fast` | 150/0 | -5.887/-14.476 | 12f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2325 | nonspell | (259.084, 432.000) | `down_fast` | 6/0 | -1.328/-1.328 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4166 | nonspell | (347.669, 432.000) | `left` | 1023/0 | -3.338/-3.338 | 5f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9023 | nonspell | (221.436, 432.000) | `right_fast` | 130/0 | -0.198/-2.398 | 3f/5f | `observed_multiple_hazard_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 9540 | nonspell | (376.000, 423.090) | `down_left_fast` | 93/0 | -2.317/-20.457 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11048 | 57 夢境「二重大結界」 | (8.000, 424.000) | `up_fast` | 623/0 | 0.472/-1.527 | 3f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11528 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 606/0 | -0.643/-0.643 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12187 | 57 夢境「二重大結界」 | (8.000, 432.000) | `right_fast` | 631/0 | -2.761/-2.761 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 16468 | nonspell | (308.118, 432.000) | `down_left_fast` | 450/0 | -2.835/-2.835 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 17305 | nonspell | (331.990, 383.666) | `up` | 299/0 | -5.273/-5.273 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20359 | 61 散霊「夢想封印　寂」 | (376.000, 425.495) | `up_fast` | 230/0 | -6.938/-6.938 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21793 | nonspell | (8.000, 428.747) | `up_left` | 811/0 | -2.791/-3.197 | 5f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22301 | nonspell | (8.000, 420.952) | `up` | 584/0 | -4.109/-4.109 | 5f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28161 | nonspell | (376.000, 432.000) | `down_right` | 119/0 | -1.729/-1.729 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28645 | nonspell | (8.000, 432.000) | `down` | 129/0 | -2.032/-2.032 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30653 | 65 神技「八方龍殺陣」 | (134.091, 383.230) | `up_right_fast` | 1050/0 | -1.464/-1.464 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31458 | 65 神技「八方龍殺陣」 | (197.227, 432.000) | `right_fast` | 1210/0 | -1.474/-1.474 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 34787 | nonspell | (317.243, 432.000) | `left_fast` | 129/0 | -1.310/-4.394 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 36392 | nonspell | (287.425, 429.172) | `up_left_fast` | 144/0 | -2.365/-2.365 | 0f/12f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 42635 | 73 大結界「博麗弾幕結界」 | (212.356, 376.900) | `left_fast` | 990/0 | -1.570/-1.570 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43313 | 73 大結界「博麗弾幕結界」 | (149.660, 387.880) | `right_fast` | 1295/0 | -1.536/-1.536 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44168 | 73 大結界「博麗弾幕結界」 | (195.208, 371.324) | `down_right_fast` | 1345/0 | -0.618/-0.618 | 0f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 14 | 4705 | 2180 | 1140 | 0 | 0 | 138 | 1087.175 | 0.182 |
| 57 夢境「二重大結界」 | 3 | 1207 | 821 | 289 | 0 | 0 | 81 | 179.788 | 0.303 |
| 61 散霊「夢想封印　寂」 | 1 | 1047 | 1005 | 370 | 0 | 0 | 117 | 145.536 | 0.187 |
| 65 神技「八方龍殺陣」 | 2 | 956 | 421 | 339 | 0 | 0 | 25 | 59.909 | 0.458 |
| 69 | 0 | 1101 | 556 | 314 | 0 | 0 | 41 | 90.042 | 0.161 |
| 73 大結界「博麗弾幕結界」 | 3 | 1000 | 945 | 500 | 0 | 0 | 146 | 129.828 | 0.074 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 6.000 frames p95. The local plan took 17.215 ms median and 58.683 ms p95.
- The full enemy sensor produced 6266 snapshots; capture read time was `{'median': 6.793799992010463, 'p95': 73.40239999757614, 'max': 132.40030000451952}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 19.0}` frames, and 5 phase-counter discontinuities were excluded; 9709 decisions retained at least one robust-union body (maximum 59); 5627 decisions contained latent contact-disabled geometry (maximum 59), and 3804 contained bounded inactive-slot memory (maximum 22). 405 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.759998321533203, 'p95': 4.5696563720703125, 'max': 10.549886067708334}` / `{'median': 2.8323280811309814, 'p95': 3.9946272373199463, 'max': 90.8092041015625}` / `{'median': 0.006794194380442264, 'p95': 3.333333969116211, 'max': 90.8092041015625}`.
- The issue-time enemy guard retained 10016 observations, detected 4160 during-plan geometry changes, recertified 4160 decisions, and overrode 52 actions. Read/recertificate timing was `{'median': 1.6038000030675903, 'p95': 3.5208999906899408, 'max': 31.322799986810423}` / `{'median': 3.4385500039206818, 'p95': 16.340000001946464, 'max': 50.786399995558895}` ms; 5622 issue captures contained latent bodies (maximum 59), and 3800 contained dormant bodies (maximum 22). Fresh/global transactions preserved 4108/4160 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 7794 observations (7761 contact enabled, 33 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3306, '0x00597600': 4488}`.
- The terminal-threat heuristic covered 10016 decisions with horizon counts `{'0': 293, '10': 9723}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 15, '3': 2690, '4': 2550, '5': 1674, '6': 3087}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 15, '3': 3960, '4': 3310, '5': 1233, '6': 1498}`.
- Adaptive delay supports were `{'2,3': 184, '2,3,4': 587, '2,3,4,5': 2448, '2,3,4,5,6': 5529, '3,4': 79, '3,4,5': 284, '3,4,5,6': 749, '4,5': 6, '4,5,6': 145, '5,6': 1, '6': 4}`; 132 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 104/83.
- Robust viability supplied 5928 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 2952 empty queried action sets. Recovery guidance was available/selected on 857/0 empty-kernel queries; distant-kernel guidance was available/selected on 1514/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 826, '1': 763, '2': 721, '3': 682, '4': 756, '5': 694, '6': 739, '7': 747}`.
- Global-horizon/local-prefix cross-tab covered 2619 decisions: 3 had a winning global state but unsafe selected prefix, 1173 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 198 selected actions were outside the reported winning set. 1897 newer issue-time hazard versions and 10 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 548 unique policies with solve-time statistics `{'median': 156.77660000801552, 'p95': 2370.573799998965, 'max': 3305.138800002169}` and first-observed ages `{'median': 3.0, 'p95': 16.0, 'max': 1949.0}`. Policy status counts were `{'expired': 3610, 'queryable': 5848, 'pending_future_epoch': 262}`; 3792 robust-mode decisions had no query.
- Of 5814 unambiguous output transitions, 5688 (0.978) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 17, 'robust_action_set_exhausted_before_hit': 5, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 16 hit windows with a positive warning lead; those leads were `[0, 19, 0, 13, 5, 4, 5, 3, 3, 0, 0, 4, 12, 7, 0, 0, 3, 0, 5, 12, 3, 4, 11]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.432 during the 60 frames preceding a hit versus 0.198 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Causal Diagnosis

This run does not falsify the retained directional predecessor or the earlier
observed-body early-kill gains. Its exact ordinary hard lane never activated:
all 10,016 prepublication records had `coverage_complete=false`,
`authority_eligible=false`, and no allowed actions.

Of 1,754 future-source attempts, zero completed. The failure distribution was:

- 1,726 manager-frame crossings during the former sparse manager/pool scan;
- 16 impossible auxiliary call depths, consistent with a torn live root;
- four non-null indexed enemies without the then-missing timeline-visible
  field;
- three dynamic direct-fire counts;
- three reached auxiliary `0x1A` instructions;
- two FRScreen transition/message-clock boundaries.

The ordinary rolling worker compounded that source starvation with 3,610
expired policies and 3,792 no-query decisions. Its no-hazard bootstrap
viability pass took 2,995.6 ms. Thus the 23 hits are fallback-path evidence,
not a physical test of exact ordinary authority.

The subsequent correction captures manager plus all 480 ordinary slots in
one contiguous read, lowers the reached residual semantics under source v3,
uses terminal-first exact rejection, adds a proved all-clear kernel path, and
separates hard membership from soft recovery scans. A new physical gate must
measure complete-projection and authority-effective counts before comparing
hits.
