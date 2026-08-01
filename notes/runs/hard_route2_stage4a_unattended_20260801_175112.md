# TH08 Stage 4A / Reimu No-Bomb Practice Review: hard_route2_stage4a_unattended_20260801_175112

## Scope And Integrity

- Valid practice scope: `1..42957` (11396 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 11, at `[11440, 12023, 12508, 12987, 13730, 21471, 21816, 34478, 35529, 36038, 37142]`.
- Hard no-Bomb verification: **PASS** across 11396 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S3-F11440-T1`. It occurred during spell 56 `夢境「二重大結界」` at player (11.253, 432.000), with 547 bullets and 0 lasers. The projectile model reported pipeline clearance -1.433.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 6 |
| `observed_bullet_overlap` | 5 |

Contributing factors:

- `playfield_boundary`: 10
- `fast_mode`: 9
- `corridor_deadline_miss`: 4
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 11440 | 56 夢境「二重大結界」 | (11.253, 432.000) | `up_right` | 547/0 | -1.433/-1.433 | 2f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12023 | 56 夢境「二重大結界」 | (8.000, 423.090) | `right_fast` | 532/0 | -1.413/-1.413 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12508 | 56 夢境「二重大結界」 | (8.000, 428.000) | `up_right_fast` | 541/0 | -3.048/-3.048 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12987 | 56 夢境「二重大結界」 | (10.828, 425.172) | `up_right_fast` | 544/0 | -1.685/-1.685 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13730 | 56 夢境「二重大結界」 | (10.828, 423.515) | `down_right_fast` | 546/0 | -2.789/-2.789 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21471 | nonspell | (19.606, 432.000) | `right_fast` | 298/0 | -1.483/-1.630 | 3f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 21816 | nonspell | (17.137, 385.479) | `stay` | 347/0 | -4.232/-4.232 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 34478 | nonspell | (371.121, 432.000) | `up_fast` | 126/0 | -2.535/-2.535 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 35529 | 68 回霊「夢想封印　侘」 | (32.485, 432.000) | `up_right_fast` | 421/0 | -0.377/-3.600 | 6f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36038 | 68 回霊「夢想封印　侘」 | (376.000, 422.402) | `down_left_fast` | 527/0 | -3.055/-3.055 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37142 | 68 回霊「夢想封印　侘」 | (367.515, 432.000) | `left_fast` | 678/0 | -2.346/-2.346 | 3f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 6766 | 587 | 35 | 0 | 847 | 29 | 324.184 | 0.196 |
| 56 夢境「二重大結界」 | 5 | 1153 | 1087 | 234 | 0 | 0 | 145 | 204.634 | 0.282 |
| 60 | 0 | 827 | 821 | 240 | 0 | 0 | 136 | 149.967 | 0.146 |
| 64 | 0 | 594 | 304 | 164 | 0 | 0 | 11 | 63.012 | 0.362 |
| 68 回霊「夢想封印　侘」 | 3 | 1119 | 1008 | 421 | 0 | 0 | 160 | 102.260 | 0.194 |
| 72 | 0 | 937 | 930 | 484 | 0 | 0 | 178 | 124.356 | 0.005 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.953 ms median and 32.725 ms p95.
- The full enemy sensor produced 6115 snapshots; capture read time was `{'median': 5.773699987912551, 'p95': 25.707900000270456, 'max': 295.5147000029683}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 42.0}` frames, and 5 phase-counter discontinuities were excluded; 11052 decisions retained at least one robust-union body (maximum 42); 6127 decisions contained latent contact-disabled geometry (maximum 42), and 4361 contained bounded inactive-slot memory (maximum 25). 90 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 3.041656494140625, 'p95': 4.268669128417969, 'max': 10.118621826171875}` / `{'median': 3.0331625938415527, 'p95': 3.850555419921875, 'max': 9.942626953125}` / `{'median': 0.4116325378417969, 'p95': 0.7037213643391929, 'max': 1.3220787048339844}`.
- The issue-time enemy guard retained 11396 observations, detected 3895 during-plan geometry changes, recertified 3895 decisions, and overrode 105 actions. Read/recertificate timing was `{'median': 1.5510999946855009, 'p95': 2.931800001533702, 'max': 140.0314999918919}` / `{'median': 2.451399981509894, 'p95': 6.214699998963624, 'max': 50.94389998703264}` ms; 6120 issue captures contained latent bodies (maximum 42), and 4359 contained dormant bodies (maximum 25). Fresh/global transactions preserved 3801/3906 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8920 observations (8879 contact enabled, 41 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3693, '0x00597600': 5227}`.
- The terminal-threat heuristic covered 11396 decisions with horizon counts `{'0': 23, '10': 11373}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 28, '3': 7369, '4': 3460, '5': 416, '6': 123}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 25, '2': 1181, '3': 8952, '4': 1214, '5': 1, '6': 23}`.
- Adaptive delay supports were `{'1,2': 24, '1,2,3': 88, '1,2,3,4': 23, '2,3': 589, '2,3,4': 3283, '2,3,4,5': 4076, '2,3,4,5,6': 2662, '3,4': 21, '3,4,5': 210, '3,4,5,6': 404, '4,5': 9, '4,5,6': 1, '5,6': 1, '6': 5}`; 122 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 36/204.
- Robust viability supplied 4737 available policy queries (0 had new delay support outside the cached policy), constrained 847 decisions, and exposed 1578 empty queried action sets. Recovery guidance was available/selected on 609/0 empty-kernel queries; distant-kernel guidance was available/selected on 930/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 10.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 749, '1': 646, '2': 541, '3': 543, '4': 538, '5': 611, '6': 559, '7': 550}`.
- Global-horizon/local-prefix cross-tab covered 2738 decisions: 6 had a winning global state but unsafe selected prefix, 948 had a losing global state but safe short prefix, 6 selected globally certified actions contradicted the fresh local prefix checker, and 211 selected actions were outside the reported winning set. 1058 newer issue-time hazard versions and 3 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 659 unique policies with solve-time statistics `{'median': 134.53410001238808, 'p95': 246.55189999612048, 'max': 2429.786399996374}` and first-observed ages `{'median': 3.0, 'p95': 4.0, 'max': 1668.0}`. Policy status counts were `{'pending_future_epoch': 210, 'queryable': 4717, 'expired': 2896}`; 3086 robust-mode decisions had no query.
- Of 5971 unambiguous output transitions, 5695 (0.954) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 8, 'robust_action_set_exhausted_before_hit': 2, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[5, 8, 6, 4, 5, 5, 0, 5, 13, 9, 12]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.447 during the 60 frames preceding a hit versus 0.184 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 23.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
