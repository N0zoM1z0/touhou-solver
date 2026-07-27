# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_040144

## Scope And Integrity

- Valid practice scope: `1..44215` (14642 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 17, at `[2608, 3958, 9340, 10796, 11859, 12745, 13646, 14029, 21179, 21708, 27903, 29955, 30831, 36014, 37929, 41813, 42315]`.
- Hard no-Bomb verification: **PASS** across 14642 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2608-T1`. It occurred during a nonspell phase at player (289.904, 428.747), with 506 bullets and 0 lasers. The projectile model reported pipeline clearance -0.015.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 8 |
| `modeled_committed_prefix_collision` | 7 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `fast_mode`: 16
- `playfield_boundary`: 13
- `corridor_deadline_miss`: 3
- `pool_density_over_1000`: 3
- `enemy_body_absent_from_action_snapshot`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2608 | nonspell | (289.904, 428.747) | `up_left` | 506/0 | -0.015/-1.888 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3958 | nonspell | (376.000, 427.400) | `up_left_fast` | 735/0 | -20.725/-20.725 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9340 | nonspell | (40.160, 400.857) | `right_fast` | 594/0 | 30.834/7.050 | 0f/0f | `observed_enemy_body_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 10796 | nonspell | (376.000, 424.000) | `up_fast` | 660/0 | 2.306/-26.331 | 13f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11859 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 613/0 | -1.403/-1.403 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12745 | 57 夢境「二重大結界」 | (376.000, 428.000) | `up_left_fast` | 593/0 | -3.455/-3.455 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13646 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 581/0 | -1.802/-1.802 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14029 | 57 夢境「二重大結界」 | (367.515, 432.000) | `up_left_fast` | 595/0 | -2.422/-2.422 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21179 | nonspell | (239.391, 432.000) | `left_fast` | 783/0 | -2.069/-2.069 | 2f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21708 | nonspell | (374.242, 397.023) | `up_left_fast` | 588/0 | 1.145/-5.779 | 5f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27903 | nonspell | (368.648, 432.000) | `up_left_fast` | 152/0 | -3.584/-3.584 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29955 | 65 神技「八方龍殺陣」 | (316.564, 432.000) | `left_fast` | 1098/0 | -2.931/-2.931 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30831 | 65 神技「八方龍殺陣」 | (103.949, 432.000) | `down_fast` | 1197/0 | -15.636/-15.636 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36014 | nonspell | (8.000, 413.990) | `up_fast` | 129/0 | -3.291/-9.488 | 14f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37929 | 69 回霊「夢想封印　侘」 | (23.242, 388.626) | `up_right_fast` | 704/0 | -3.234/-3.234 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41813 | 73 大結界「博麗弾幕結界」 | (216.046, 373.221) | `down_left_fast` | 992/0 | -0.688/-0.688 | 0f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42315 | 73 大結界「博麗弾幕結界」 | (157.959, 369.789) | `right_fast` | 1272/0 | 0.092/-1.852 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 8862 | 8723 | 4065 | 0 | 4590 | 1067 | 112.727 | 0.145 |
| 57 夢境「二重大結界」 | 4 | 1332 | 1323 | 256 | 0 | 1048 | 185 | 156.937 | 0.258 |
| 61 | 0 | 823 | 812 | 232 | 0 | 573 | 100 | 121.846 | 0.168 |
| 65 神技「八方龍殺陣」 | 2 | 1124 | 1111 | 993 | 0 | 110 | 147 | 56.250 | 0.435 |
| 69 回霊「夢想封印　侘」 | 1 | 1331 | 1321 | 680 | 0 | 631 | 180 | 81.526 | 0.098 |
| 73 大結界「博麗弾幕結界」 | 2 | 1170 | 1154 | 544 | 0 | 596 | 183 | 106.309 | 0.090 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 2 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.810 ms median and 17.550 ms p95.
- The full enemy sensor produced 7091 snapshots; capture read time was `{'median': 5.5596999591216445, 'p95': 21.263600036036223, 'max': 35.609500017017126}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 9.0}` frames, and 7 phase-counter discontinuities were excluded; 14242 decisions retained at least one robust-union body (maximum 56); 2986 decisions contained latent contact-disabled geometry (maximum 56), and 7403 contained bounded inactive-slot memory (maximum 51). 269 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.5445213317871094, 'p95': 4.1666412353515625, 'max': 8.565541585286459}` / `{'median': 2.544520854949951, 'p95': 3.859997034072876, 'max': 16.600189208984375}` / `{'median': 0.6467094421386719, 'p95': 1.9902316331863403, 'max': 16.600189208984375}`.
- The issue-time enemy guard retained 14642 observations, detected 2408 during-plan geometry changes, recertified 2408 decisions, and overrode 53 actions. Read/recertificate timing was `{'median': 1.6921499918680638, 'p95': 3.39590001385659, 'max': 17.681199999060482}` / `{'median': 1.904999982798472, 'p95': 3.58260003849864, 'max': 10.962699947413057}` ms; 2987 issue captures contained latent bodies (maximum 56), and 7403 contained dormant bodies (maximum 51). Fresh/global transactions preserved 2355/2408 planned actions, relaxed 3 fresh/global empty intersections, inherited 19 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11246 observations (11199 contact enabled, 47 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4567, '0x0059C9D0': 6679}`.
- The terminal-threat heuristic covered 14642 decisions with horizon counts `{'0': 74, '10': 13674, '32': 894}`; it reported 17 collision and 167 sub-safety-clearance warnings, and relaxed 126 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 3189, '3': 10957, '4': 496}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 47, '2': 10217, '3': 4062, '4': 316}`.
- Adaptive delay supports were `{'1,2': 41, '1,2,3': 128, '1,2,3,4': 375, '1,2,3,4,5': 53, '2,3': 1499, '2,3,4': 8599, '2,3,4,5': 3153, '2,3,4,5,6': 731, '3,4': 27, '3,4,5': 17, '3,4,5,6': 19}`; 75 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 40/281.
- Robust viability supplied 14444 available policy queries (0 had new delay support outside the cached policy), constrained 7548 decisions, and exposed 6770 empty queried action sets. Recovery guidance was available/selected on 1888/904 empty-kernel queries; distant-kernel guidance was available/selected on 3915/3810. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 11.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 102.44998779892558, 'p95': 288.44410203711914, 'max': 520.9222590751906}`, and `{'median': 0.0, 'p95': 16.0, 'max': 44.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2290, '1': 1765, '2': 1501, '3': 1792, '4': 1712, '5': 1804, '6': 1794, '7': 1786}`.
- Global-horizon/local-prefix cross-tab covered 9949 decisions: 3 had a winning global state but unsafe selected prefix, 4310 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 72 selected actions were outside the reported winning set. 1930 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1862 unique policies with solve-time statistics `{'median': 108.66930001066066, 'p95': 308.1215000129305, 'max': 397.4158999626525}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1805.0}`. Policy status counts were `{'pending_future_epoch': 66, 'queryable': 14445, 'expired': 30}`; 97 robust-mode decisions had no query.
- Of 7325 unambiguous output transitions, 6749 (0.921) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 16, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 15 hit windows with a positive warning lead; those leads were `[6, 11, 0, 19, 5, 3, 5, 7, 5, 13, 7, 4, 0, 16, 13, 16, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.361 during the 60 frames preceding a hit versus 0.159 outside those windows.
- Mean selected control-reserve deficit was 8.698 during the 60 frames preceding a hit versus 3.603 outside those windows.
- Soft recovery was selected on 0.059 of alive decisions in the 60-frame pre-hit windows versus 0.064 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
