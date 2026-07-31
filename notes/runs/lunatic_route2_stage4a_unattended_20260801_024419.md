# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_024419

## Scope And Integrity

- Valid practice scope: `2..45788` (11790 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 22, at `[1291, 1636, 2030, 2497, 2905, 3816, 4212, 8810, 9319, 11585, 12286, 12875, 13355, 13744, 21839, 22379, 22768, 32743, 37296, 43349, 43836, 45053]`.
- Hard no-Bomb verification: **PASS** across 11790 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1291-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 165 bullets and 0 lasers. The projectile model reported pipeline clearance 11.422.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 8 |
| `sensor_gap_or_unmodeled_hazard` | 7 |
| `modeled_committed_prefix_collision` | 6 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 16
- `playfield_boundary`: 10
- `corridor_deadline_miss`: 9
- `action_lag_over_model`: 8
- `pool_density_over_1000`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1291 | nonspell | (376.000, 432.000) | `down_right` | 165/0 | 11.422/0.709 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1636 | nonspell | (23.210, 291.885) | `up` | 377/0 | 3.947/-1.635 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2030 | nonspell | (370.622, 425.495) | `up_left_fast` | 350/0 | 7.914/0.569 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 2497 | nonspell | (185.436, 401.305) | `stay` | 316/0 | -4.300/-4.300 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 2905 | nonspell | (172.840, 371.961) | `stay` | 375/0 | 26.180/26.180 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3816 | nonspell | (373.054, 428.161) | `left_fast` | 498/0 | 3.612/-1.830 | 2f/2f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 4212 | nonspell | (213.693, 431.533) | `down_right` | 785/0 | 11.929/-4.331 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 8810 | nonspell | (373.653, 432.000) | `up_fast` | 769/0 | -15.477/-15.477 | 5f/11f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 9319 | nonspell | (353.367, 424.000) | `up_fast` | 706/0 | -2.743/-11.834 | 11f/16f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11585 | 57 夢境「二重大結界」 | (9.347, 428.000) | `up_right_fast` | 527/0 | -2.780/-2.780 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12286 | 57 夢境「二重大結界」 | (8.000, 426.564) | `up_right_fast` | 593/0 | -1.918/-1.918 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12875 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 581/0 | -1.784/-1.784 | 0f/2f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13355 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 596/0 | -2.974/-2.974 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13744 | 57 夢境「二重大結界」 | (10.828, 429.172) | `up_right_fast` | 591/0 | 1.048/1.048 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21839 | nonspell | (310.702, 421.343) | `down_right_fast` | 351/0 | 15.439/5.203 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 22379 | nonspell | (8.000, 432.000) | `down_fast` | 450/0 | -16.973/-16.973 | 0f/11f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22768 | nonspell | (278.134, 418.915) | `stay` | 968/0 | 6.826/1.588 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 32743 | 65 神技「八方龍殺陣」 | (209.211, 427.121) | `down_right_fast` | 1256/0 | -2.586/-2.586 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37296 | nonspell | (13.657, 406.343) | `up_right_fast` | 93/0 | 2.861/-11.608 | 13f/18f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 43349 | 73 大結界「博麗弾幕結界」 | (208.779, 376.621) | `left_fast` | 980/0 | 1.250/-1.917 | 5f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43836 | 73 大結界「博麗弾幕結界」 | (156.503, 390.454) | `down_right_fast` | 1293/0 | -2.989/-3.520 | 4f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45053 | 73 大結界「博麗弾幕結界」 | (177.930, 369.253) | `down_left_fast` | 1320/0 | 0.081/0.081 | 0f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 13 | 6611 | 342 | 53 | 0 | 380 | 26 | 909.436 | 0.212 |
| 57 夢境「二重大結界」 | 5 | 1243 | 735 | 167 | 0 | 0 | 75 | 185.861 | 0.301 |
| 61 | 0 | 1012 | 1006 | 451 | 0 | 0 | 166 | 125.992 | 0.183 |
| 65 神技「八方龍殺陣」 | 1 | 900 | 348 | 264 | 0 | 0 | 14 | 57.300 | 0.403 |
| 69 | 0 | 1035 | 1028 | 718 | 0 | 0 | 177 | 93.760 | 0.236 |
| 73 大結界「博麗弾幕結界」 | 3 | 989 | 982 | 495 | 0 | 0 | 185 | 130.201 | 0.064 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.639 ms median and 33.151 ms p95.
- The full enemy sensor produced 6417 snapshots; capture read time was `{'median': 5.502300002262928, 'p95': 26.61459999217186, 'max': 710.6637000106275}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 82.0}` frames, and 7 phase-counter discontinuities were excluded; 11569 decisions retained at least one robust-union body (maximum 59); 6029 decisions contained latent contact-disabled geometry (maximum 59), and 4602 contained bounded inactive-slot memory (maximum 20). 395 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.74505615234375, 'p95': 4.330047607421875, 'max': 8.88718032836914}` / `{'median': 2.7978897094726562, 'p95': 3.8987653255462646, 'max': 6.533321380615234}` / `{'median': 0.4904308319091797, 'p95': 3.3999977111816406, 'max': 6.533323764801025}`.
- The issue-time enemy guard retained 11790 observations, detected 4266 during-plan geometry changes, recertified 4266 decisions, and overrode 70 actions. Read/recertificate timing was `{'median': 1.597449998371303, 'p95': 2.9322000045794994, 'max': 319.21370000054594}` / `{'median': 2.5449500026297756, 'p95': 7.907100007287227, 'max': 298.10830000496935}` ms; 6046 issue captures contained latent bodies (maximum 59), and 4600 contained dormant bodies (maximum 28). Fresh/global transactions preserved 4196/4266 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9990 observations (9948 contact enabled, 42 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9990}`.
- The terminal-threat heuristic covered 11790 decisions with horizon counts `{'0': 33, '10': 11757}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 39, '3': 7495, '4': 3088, '5': 554, '6': 614}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1574, '3': 8393, '4': 1729, '5': 41, '6': 53}`.
- Adaptive delay supports were `{'1,2,3': 6, '1,2,3,4,5': 1, '1,2,3,4,5,6': 57, '2,3': 301, '2,3,4': 3625, '2,3,4,5': 3644, '2,3,4,5,6': 2940, '3,4': 197, '3,4,5': 507, '3,4,5,6': 392, '4,5': 3, '4,5,6': 91, '5,6': 21, '6': 5}`; 109 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 47/204.
- Robust viability supplied 4441 available policy queries (0 had new delay support outside the cached policy), constrained 380 decisions, and exposed 2148 empty queried action sets. Recovery guidance was available/selected on 743/0 empty-kernel queries; distant-kernel guidance was available/selected on 1188/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 670, '1': 601, '2': 493, '3': 503, '4': 528, '5': 544, '6': 559, '7': 543}`.
- Global-horizon/local-prefix cross-tab covered 2354 decisions: 2 had a winning global state but unsafe selected prefix, 1161 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 147 selected actions were outside the reported winning set. 1177 newer issue-time hazard versions and 4 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 643 unique policies with solve-time statistics `{'median': 123.39010000869166, 'p95': 217.54389999841806, 'max': 5290.126300009433}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1764.0}`. Policy status counts were `{'pending_future_epoch': 209, 'queryable': 4430, 'expired': 2624}`; 2822 robust-mode decisions had no query.
- Of 6348 unambiguous output transitions, 6083 (0.958) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 8, 'unresolved_planner_failure': 6, 'late_collision_after_positive_causal_margin': 1, 'robust_action_set_exhausted_before_hit': 7}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[0, 0, 0, 0, 0, 2, 0, 11, 16, 3, 5, 2, 8, 6, 0, 11, 0, 0, 18, 11, 12, 13]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.455 during the 60 frames preceding a hit versus 0.216 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Ordinary Exact-Authority Audit

- **Observed:** this `223ba01` trial completed 22/1291/no-Bomb with accepted
  replay SHA-256
  `8353c74ed6fd612996dd9df76b6a230ae5615802571a3e3093849362dedd0d5b`
  and full process/key cleanup. Thirteen hits were nonspell.
- **Observed:** eight-worker/background-low-priority controls were active.
  Ordinary authority was applicable/effective on 380/362 of 6,611 nonspell
  decisions. Solve median/p95 improved 123/230→123/218 ms relative to
  `022228`, but only 26 ordinary policies completed and one took 5,290 ms.
- **Observed:** 236 decisions lie in the 80-frame windows before nonspell
  hits. Only frames 2425/2446 had directional exact sets (14 actions); both
  arrived with 20-frame post-capture advance against pickup-support high 6,
  so effective directional pressure-window authority remained 0.
- **Observed:** auxiliary `0x05`/`0x2E` failures disappeared. Of 1,714
  incomplete future-source projections, 1,243 now fail on
  `ordinary_enemy_pool:0` armed phase transition. This is the dominant
  coverage blocker, not scalar reserve or local ranking.
- **Correction:** native recheck confirms timeout triggers only when the
  integer phase timer is `>= timeout`, while health uses signed
  `current_hp < threshold`; both start a captured successor. Source v6 now
  captures the complete successor/timer registry and proves a timeout
  irrelevant only when `elapsed + horizon < timeout`. Armed health or a
  timeout reachable within the horizon still fails closed. Linux/Windows
  focused tests pass and retained f817/833/835/850/910 action sets remain
  unchanged with no unresolved action.
