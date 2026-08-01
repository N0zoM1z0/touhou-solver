# TH08 Stage 4A / Reimu No-Bomb Practice Review: hard_route2_stage4a_unattended_20260801_184903

## Scope And Integrity

- Valid practice scope: `1..43553` (11571 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[1209, 11129, 11501, 12320, 12696, 13125, 20816, 21932, 34338, 37808, 41929, 43325]`.
- Hard no-Bomb verification: **PASS** across 11571 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S3-F1209-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 86 bullets and 0 lasers. The projectile model reported pipeline clearance -2.450.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 5 |
| `modeled_committed_prefix_collision` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 3 |

Contributing factors:

- `corridor_deadline_miss`: 7
- `fast_mode`: 7
- `playfield_boundary`: 5
- `action_lag_over_model`: 2
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1209 | nonspell | (376.000, 432.000) | `down` | 86/0 | -2.450/-2.450 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 11129 | 56 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 467/0 | -1.460/-1.460 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11501 | 56 夢境「二重大結界」 | (97.225, 252.574) | `left_fast` | 520/0 | 0.255/-2.454 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12320 | 56 夢境「二重大結界」 | (346.836, 341.733) | `up_fast` | 533/0 | -0.700/-1.564 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 12696 | 56 夢境「二重大結界」 | (350.083, 326.888) | `down_fast` | 534/0 | 12.681/2.094 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 13125 | 56 夢境「二重大結界」 | (28.469, 366.057) | `down` | 534/0 | -0.758/-0.758 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 20816 | nonspell | (25.890, 422.485) | `down_right` | 101/0 | 27.725/2.836 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 21932 | nonspell | (376.000, 432.000) | `stay` | 314/0 | 0.098/0.098 | 0f/8f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 34338 | nonspell | (127.279, 432.000) | `right_fast` | 107/0 | -3.306/-11.182 | 10f/17f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 37808 | 68 回霊「夢想封印　侘」 | (8.000, 432.000) | `stay` | 595/0 | -1.517/-1.517 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41929 | 72 大結界「博麗弾幕結界」 | (331.329, 424.962) | `left_fast` | 1020/0 | -2.352/-2.352 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 43325 | 72 大結界「博麗弾幕結界」 | (200.012, 397.308) | `left_fast` | 1048/0 | -2.866/-2.866 | 5f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 6886 | 723 | 69 | 0 | 921 | 35 | 204.404 | 0.212 |
| 56 夢境「二重大結界」 | 5 | 1156 | 1069 | 166 | 0 | 872 | 141 | 202.497 | 0.041 |
| 60 | 0 | 750 | 744 | 194 | 0 | 547 | 120 | 145.209 | 0.061 |
| 64 | 0 | 784 | 587 | 421 | 0 | 164 | 51 | 54.845 | 0.276 |
| 68 回霊「夢想封印　侘」 | 1 | 1047 | 1041 | 473 | 0 | 566 | 179 | 94.236 | 0.058 |
| 72 大結界「博麗弾幕結界」 | 2 | 948 | 940 | 400 | 0 | 529 | 176 | 130.830 | 0.016 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.149 ms median and 31.648 ms p95.
- The full enemy sensor produced 6203 snapshots; capture read time was `{'median': 5.855800001882017, 'p95': 22.270799992838874, 'max': 230.1834000099916}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 43.0}` frames, and 7 phase-counter discontinuities were excluded; 11235 decisions retained at least one robust-union body (maximum 51); 6261 decisions contained latent contact-disabled geometry (maximum 51), and 4482 contained bounded inactive-slot memory (maximum 37). 98 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.7165298461914062, 'p95': 4.0721282958984375, 'max': 6.0379638671875}` / `{'median': 2.7988736629486084, 'p95': 3.9928762912750244, 'max': 5.94915771484375}` / `{'median': 0.04776763916015625, 'p95': 1.293428897857666, 'max': 7.999925136566162}`.
- The issue-time enemy guard retained 11571 observations, detected 4563 during-plan geometry changes, recertified 4563 decisions, and overrode 269 actions. Read/recertificate timing was `{'median': 1.5393999929074198, 'p95': 2.8581999940797687, 'max': 98.25199999613687}` / `{'median': 2.4596000148449093, 'p95': 5.458700004965067, 'max': 69.85359999816865}` ms; 6269 issue captures contained latent bodies (maximum 51), and 4481 contained dormant bodies (maximum 37). Fresh/global transactions preserved 4309/4578 planned actions, relaxed 0 fresh/global empty intersections, inherited 5 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9140 observations (9100 contact enabled, 40 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3862, '0x00592230': 5278}`.
- The terminal-threat heuristic covered 11571 decisions with horizon counts `{'0': 21, '10': 11389, '32': 161}`; it reported 15 collision and 37 sub-safety-clearance warnings, and relaxed 57 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 26, '3': 7251, '4': 3641, '5': 357, '6': 296}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 26, '2': 1076, '3': 9195, '4': 1255, '5': 16, '6': 3}`.
- Adaptive delay supports were `{'1,2': 25, '1,2,3,4,5': 95, '1,2,3,4,5,6': 8, '2,3': 709, '2,3,4': 3497, '2,3,4,5': 3277, '2,3,4,5,6': 3313, '3,4': 59, '3,4,5': 97, '3,4,5,6': 479, '4,5': 2, '4,5,6': 5, '5,6': 3, '6': 2}`; 309 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 30/131.
- Robust viability supplied 5104 available policy queries (0 had new delay support outside the cached policy), constrained 3599 decisions, and exposed 1723 empty queried action sets. Recovery guidance was available/selected on 668/319 empty-kernel queries; distant-kernel guidance was available/selected on 855/809. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 9.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 58.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 67.88225099390856, 'p95': 240.0, 'max': 475.1757569573599}`, and `{'median': 0.0, 'p95': 17.378498077392578, 'max': 35.837764739990234}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 773, '1': 706, '2': 593, '3': 551, '4': 587, '5': 640, '6': 613, '7': 641}`.
- Global-horizon/local-prefix cross-tab covered 2828 decisions: 8 had a winning global state but unsafe selected prefix, 1050 had a losing global state but safe short prefix, 4 selected globally certified actions contradicted the fresh local prefix checker, and 20 selected actions were outside the reported winning set. 1247 newer issue-time hazard versions and 2 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 702 unique policies with solve-time statistics `{'median': 131.46259999484755, 'p95': 242.01489999541081, 'max': 2149.837800010573}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1732.0}`. Policy status counts were `{'pending_future_epoch': 131, 'queryable': 5081, 'expired': 2589}`; 2697 robust-mode decisions had no query.
- Of 6302 unambiguous output transitions, 6011 (0.954) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'late_collision_after_positive_causal_margin': 4, 'robust_action_set_exhausted_before_hit': 3, 'global_viability_kernel_exhausted_before_hit': 3, 'unresolved_planner_failure': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 6 hit windows with a positive warning lead; those leads were `[0, 3, 6, 0, 0, 0, 0, 8, 17, 8, 0, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.207 during the 60 frames preceding a hit versus 0.166 outside those windows.
- Mean selected control-reserve deficit was 1.931 during the 60 frames preceding a hit versus 0.376 outside those windows.
- Soft recovery was selected on 0.047 of alive decisions in the 60-frame pre-hit windows versus 0.024 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 5.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
