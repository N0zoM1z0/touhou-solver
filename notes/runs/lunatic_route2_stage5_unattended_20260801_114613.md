# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_114613

## Scope And Integrity

- Valid practice scope: `1..44428` (10815 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[558, 2192, 2600, 3270, 4043, 7069, 12353, 12866, 13733, 14470, 29067, 32336, 35535, 37046, 39185, 40821, 42053, 43678]`.
- Hard no-Bomb verification: **PASS** across 10815 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F558-T1`. It occurred during a nonspell phase at player (49.236, 412.555), with 630 bullets and 0 lasers. The projectile model reported pipeline clearance -2.563.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `sensor_gap_or_unmodeled_hazard` | 6 |
| `observed_bullet_overlap` | 4 |

Contributing factors:

- `fast_mode`: 15
- `playfield_boundary`: 12
- `action_lag_over_model`: 6
- `pool_density_over_1000`: 3
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 558 | nonspell | (49.236, 412.555) | `up_right_fast` | 630/0 | -2.563/-2.710 | 3f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 2192 | nonspell | (186.191, 432.000) | `down_right_fast` | 516/0 | 10.019/-2.793 | 59f/59f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 2600 | nonspell | (8.000, 416.810) | `stay` | 434/0 | 15.284/15.284 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3270 | nonspell | (8.000, 16.000) | `down_left_fast` | 626/0 | -1.367/-1.367 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 4043 | nonspell | (350.914, 432.000) | `up` | 753/0 | 9.114/0.840 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 7069 | nonspell | (376.000, 322.036) | `up_fast` | 698/0 | 17.533/-0.950 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 12353 | nonspell | (376.000, 308.594) | `left_fast` | 354/0 | -2.505/-2.505 | 0f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12866 | nonspell | (8.000, 431.664) | `up_fast` | 257/0 | -2.344/-20.325 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13733 | nonspell | (376.000, 368.200) | `stay` | 377/0 | 9.799/0.510 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 14470 | nonspell | (271.560, 421.855) | `right_fast` | 519/0 | 7.215/-1.341 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 29067 | nonspell | (8.000, 428.747) | `right_fast` | 1060/0 | -1.959/-1.959 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 32336 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (203.953, 401.379) | `down_fast` | 1015/0 | -8.401/-8.748 | 18f/66f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35535 | nonspell | (376.000, 432.000) | `up_fast` | 545/0 | -3.027/-3.027 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 37046 | nonspell | (8.000, 425.495) | `right_fast` | 414/0 | -2.677/-2.677 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39185 | 111 懶惰「生神停止(マインドストッパー)」 | (196.903, 20.686) | `up_right_fast` | 496/0 | -2.870/-2.870 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40821 | 111 懶惰「生神停止(マインドストッパー)」 | (175.998, 153.885) | `up_fast` | 376/0 | -2.210/-2.926 | 6f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42053 | 115 散符「真実の月(インビジブルフルムーン)」 | (238.326, 432.000) | `up_fast` | 1181/0 | -2.885/-2.885 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43678 | 115 散符「真実の月(インビジブルフルムーン)」 | (367.870, 422.272) | `up_right_fast` | 968/0 | -0.669/-12.802 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 13 | 7184 | 21 | 2 | 0 | 24 | 3 | 1610.906 | 0.475 |
| 103 | 0 | 828 | 495 | 428 | 0 | 0 | 62 | 101.885 | 0.362 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 701 | 695 | 497 | 0 | 0 | 156 | 79.643 | 0.338 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1040 | 1034 | 548 | 0 | 0 | 180 | 70.386 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1062 | 1054 | 688 | 0 | 0 | 185 | 65.382 | 0.464 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.574 ms median and 32.313 ms p95.
- The full enemy sensor produced 5963 snapshots; capture read time was `{'median': 5.171099997824058, 'p95': 27.074400015408173, 'max': 554.3236999947112}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 101.0}` frames, and 14 phase-counter discontinuities were excluded; 10111 decisions retained at least one robust-union body (maximum 51); 7872 decisions contained latent contact-disabled geometry (maximum 51), and 3452 contained bounded inactive-slot memory (maximum 38). 351 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.85699462890625, 'p95': 4.5816650390625, 'max': 6.707550048828125}` / `{'median': 1.0, 'p95': 4.632940292358398, 'max': 4.70754861831665}` / `{'median': 1.3113021850585938e-06, 'p95': 2.1423301696777344, 'max': 4.678517818450928}`.
- The issue-time enemy guard retained 10815 observations, detected 2906 during-plan geometry changes, recertified 2906 decisions, and overrode 46 actions. Read/recertificate timing was `{'median': 0.964400009252131, 'p95': 2.3858000058680773, 'max': 270.5233999877237}` / `{'median': 3.107949989498593, 'p95': 6.946100009372458, 'max': 263.93600000301376}` ms; 7843 issue captures contained latent bodies (maximum 51), and 3451 contained dormant bodies (maximum 38). Fresh/global transactions preserved 2862/2908 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8527 observations (8501 contact enabled, 26 anticipatory, 0 errors). 8527 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8527}`.
- The terminal-threat heuristic covered 10815 decisions with horizon counts `{'0': 704, '10': 10111}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 662, '3': 6477, '4': 2465, '5': 1036, '6': 175}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 289, '2': 710, '3': 7265, '4': 1879, '5': 653, '6': 19}`.
- Adaptive delay supports were `{'1': 91, '1,2': 83, '1,2,3': 186, '1,2,3,4': 478, '1,2,3,4,5': 117, '1,2,3,4,5,6': 201, '2,3': 307, '2,3,4': 1986, '2,3,4,5': 3918, '2,3,4,5,6': 1997, '3,4': 7, '3,4,5': 251, '3,4,5,6': 900, '4,5': 10, '4,5,6': 275, '5,6': 1, '6': 7}`; 201 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 58/385.
- Robust viability supplied 3299 available policy queries (0 had new delay support outside the cached policy), constrained 24 decisions, and exposed 2163 empty queried action sets. Recovery guidance was available/selected on 224/0 empty-kernel queries; distant-kernel guidance was available/selected on 1267/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 534, '1': 451, '2': 407, '3': 329, '4': 372, '5': 383, '6': 428, '7': 395}`.
- Global-horizon/local-prefix cross-tab covered 1288 decisions: 0 had a winning global state but unsafe selected prefix, 646 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 12 selected actions were outside the reported winning set. 1396 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 586 unique policies with solve-time statistics `{'median': 73.54269998904783, 'p95': 179.17649997980334, 'max': 2230.485200008843}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 106.0}`. Policy status counts were `{'queryable': 3290, 'expired': 336, 'pending_future_epoch': 92}`; 419 robust-mode decisions had no query.
- Of 5590 unambiguous output transitions, 5257 (0.940) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 8, 'unresolved_planner_failure': 5, 'global_viability_kernel_exhausted_before_hit': 5}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[5, 59, 0, 8, 0, 0, 10, 5, 0, 0, 5, 66, 5, 5, 11, 9, 8, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.352 during the 60 frames preceding a hit versus 0.412 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
