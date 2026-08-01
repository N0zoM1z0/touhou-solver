# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_174525

## Scope And Integrity

- Valid practice scope: `2..12810` (3015 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `runtime_error`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **NO**.
- Native hit edges: 10, at `[1210, 1636, 2490, 3562, 3929, 4243, 8871, 10508, 11827, 12698]`.
- Hard no-Bomb verification: **PASS** across 3015 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1210-T1`. It occurred during a nonspell phase at player (373.172, 413.858), with 270 bullets and 0 lasers. The projectile model reported pipeline clearance -1.078.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 6 |
| `observed_bullet_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 2 |

Contributing factors:

- `playfield_boundary`: 9
- `fast_mode`: 7
- `action_lag_over_model`: 4
- `corridor_deadline_miss`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1210 | nonspell | (373.172, 413.858) | `up_left_fast` | 270/0 | -1.078/-1.078 | 0f/13f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 1636 | nonspell | (333.874, 432.000) | `up_left_fast` | 190/0 | 15.123/-1.445 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2490 | nonspell | (207.272, 428.174) | `down` | 378/0 | 40.621/24.425 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3562 | nonspell | (167.342, 415.191) | `left` | 311/0 | -5.536/-5.536 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 3929 | nonspell | (175.801, 432.000) | `right_fast` | 306/0 | 0.088/-1.694 | 3f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 4243 | nonspell | (208.705, 432.000) | `stay` | 850/0 | -3.405/-3.405 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 8871 | nonspell | (344.000, 432.000) | `left_fast` | 558/0 | -1.446/-15.374 | 8f/19f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 10508 | nonspell | (8.000, 432.000) | `up_fast` | 123/0 | -2.254/-10.975 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11827 | 57 夢境「二重大結界」 | (16.000, 432.000) | `up_right_fast` | 611/0 | 0.423/-3.229 | 2f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12698 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 630/0 | -1.451/-1.451 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 2293 | 359 | 43 | 0 | 583 | 22 | 164.921 | 0.281 |
| 57 夢境「二重大結界」 | 2 | 722 | 430 | 189 | 0 | 0 | 46 | 180.981 | 0.328 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 18.031 ms median and 38.355 ms p95.
- The full enemy sensor produced 1670 snapshots; capture read time was `{'median': 6.682200008071959, 'p95': 39.350500010186806, 'max': 411.7078999988735}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 91.0}` frames, and 3 phase-counter discontinuities were excluded; 2728 decisions retained at least one robust-union body (maximum 40); 1541 decisions contained latent contact-disabled geometry (maximum 40), and 1269 contained bounded inactive-slot memory (maximum 24). 191 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.7787017822265625, 'p95': 4.011386871337891, 'max': 6.311902046203613}` / `{'median': 2.931608200073242, 'p95': 3.8987720012664795, 'max': 4.0799970626831055}` / `{'median': 0.6226189136505127, 'p95': 3.8505382537841797, 'max': 6.20001220703125}`.
- The issue-time enemy guard retained 3015 observations, detected 1337 during-plan geometry changes, recertified 1337 decisions, and overrode 24 actions. Read/recertificate timing was `{'median': 1.3691999774891883, 'p95': 2.54690001020208, 'max': 136.7303000006359}` / `{'median': 2.7277999906800687, 'p95': 9.360600000945851, 'max': 532.951300003333}` ms; 1539 issue captures contained latent bodies (maximum 40), and 1279 contained dormant bodies (maximum 29). Fresh/global transactions preserved 1344/1369 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 1694 observations (1694 contact enabled, 0 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 1694}`.
- The terminal-threat heuristic covered 3015 decisions with horizon counts `{'0': 21, '10': 2994}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 23, '3': 1831, '4': 600, '5': 322, '6': 239}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 30, '3': 2383, '4': 600, '6': 2}`.
- Adaptive delay supports were `{'1,2,3': 6, '1,2,3,4': 24, '2,3': 277, '2,3,4': 652, '2,3,4,5': 825, '2,3,4,5,6': 1199, '3,4': 21, '3,4,5': 3, '4,5,6': 6, '6': 2}`; 35 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 10/73.
- Robust viability supplied 789 available policy queries (0 had new delay support outside the cached policy), constrained 583 decisions, and exposed 232 empty queried action sets. Recovery guidance was available/selected on 152/0 empty-kernel queries; distant-kernel guidance was available/selected on 60/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 13.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 105, '1': 113, '2': 90, '3': 92, '4': 94, '5': 96, '6': 86, '7': 113}`.
- Global-horizon/local-prefix cross-tab covered 463 decisions: 0 had a winning global state but unsafe selected prefix, 161 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 24 selected actions were outside the reported winning set. 90 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 68 unique policies with solve-time statistics `{'median': 180.98079999617767, 'p95': 941.8162000074517, 'max': 3864.931699994486}` and first-observed ages `{'median': 2.0, 'p95': 26.0, 'max': 1665.0}`. Policy status counts were `{'pending_future_epoch': 166, 'queryable': 778, 'expired': 1684}`; 1839 robust-mode decisions had no query.
- Of 1395 unambiguous output transitions, 1331 (0.954) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 5, 'unresolved_planner_failure': 2, 'late_collision_after_positive_causal_margin': 1, 'missing_pre_hit_alive_decision': 1, 'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 6 hit windows with a positive warning lead; those leads were `[13, 0, 0, 0, 9, 0, 19, 8, 4, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.603 during the 60 frames preceding a hit versus 0.268 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
