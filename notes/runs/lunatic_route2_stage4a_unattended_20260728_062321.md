# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_062321

## Scope And Integrity

- Valid practice scope: `1..45170` (14868 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 17, at `[1255, 2725, 3986, 4346, 9849, 11689, 12084, 12736, 21864, 22323, 30066, 30711, 31907, 35498, 37755, 38928, 39662]`.
- Hard no-Bomb verification: **PASS** across 14868 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1255-T1`. It occurred during a nonspell phase at player (329.128, 432.000), with 118 bullets and 0 lasers. The projectile model reported pipeline clearance -1.278.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 8 |
| `modeled_committed_prefix_collision` | 7 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 12
- `fast_mode`: 11
- `pool_density_over_1000`: 3
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1255 | nonspell | (329.128, 432.000) | `left` | 118/0 | -1.278/-1.278 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2725 | nonspell | (368.496, 428.747) | `down_left_fast` | 481/0 | -1.867/-1.867 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3986 | nonspell | (373.871, 432.000) | `stay` | 896/0 | -3.664/-3.664 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4346 | nonspell | (11.253, 429.596) | `up_fast` | 870/0 | -2.391/-14.316 | 0f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9849 | nonspell | (8.000, 424.000) | `up` | 478/0 | 5.506/-1.664 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11689 | 57 夢境「二重大結界」 | (40.884, 365.664) | `stay` | 579/0 | 45.174/-1.144 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 12084 | 57 夢境「二重大結界」 | (8.000, 428.000) | `up_right_fast` | 586/0 | -0.240/-0.240 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12736 | 57 夢境「二重大結界」 | (13.657, 422.343) | `up_fast` | 617/0 | -0.365/-3.199 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21864 | nonspell | (376.000, 429.914) | `left_fast` | 710/0 | -1.299/-4.821 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22323 | nonspell | (11.253, 432.000) | `up_right` | 594/0 | -0.001/-1.444 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30066 | 65 神技「八方龍殺陣」 | (376.000, 426.343) | `up_right_fast` | 1299/0 | -1.556/-2.813 | 4f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30711 | 65 神技「八方龍殺陣」 | (373.172, 420.686) | `up_left_fast` | 1220/0 | -14.789/-14.789 | 8f/8f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31907 | 65 神技「八方龍殺陣」 | (186.591, 426.343) | `left_fast` | 1153/0 | -0.420/-5.287 | 5f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35498 | nonspell | (376.000, 406.208) | `left_fast` | 153/0 | -4.700/-17.894 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37755 | 69 回霊「夢想封印　侘」 | (327.422, 343.471) | `down_left_fast` | 425/0 | -1.693/-1.693 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38928 | 69 回霊「夢想封印　侘」 | (107.045, 427.400) | `right_fast` | 685/0 | -0.497/-0.807 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39662 | 69 回霊「夢想封印　侘」 | (374.374, 425.774) | `up_left` | 713/0 | -1.305/-1.305 | 4f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 8646 | 8500 | 3854 | 0 | 4576 | 1039 | 110.249 | 0.138 |
| 57 夢境「二重大結界」 | 3 | 1324 | 1317 | 287 | 0 | 1008 | 183 | 157.733 | 0.307 |
| 61 | 0 | 1317 | 1307 | 408 | 0 | 878 | 167 | 102.940 | 0.239 |
| 65 神技「八方龍殺陣」 | 3 | 1091 | 1081 | 893 | 0 | 180 | 165 | 58.164 | 0.346 |
| 69 回霊「夢想封印　侘」 | 3 | 1412 | 1404 | 625 | 0 | 765 | 184 | 85.269 | 0.104 |
| 73 | 0 | 1078 | 1069 | 628 | 0 | 428 | 178 | 101.845 | 0.022 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.715 ms median and 17.584 ms p95.
- The full enemy sensor produced 7239 snapshots; capture read time was `{'median': 5.577199975959957, 'p95': 21.636300021782517, 'max': 43.48549997666851}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 9.0}` frames, and 6 phase-counter discontinuities were excluded; 14461 decisions retained at least one robust-union body (maximum 59); 2917 decisions contained latent contact-disabled geometry (maximum 59), and 7711 contained bounded inactive-slot memory (maximum 53). 266 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.362682342529297, 'p95': 4.569671630859375, 'max': 12.97161865234375}` / `{'median': 2.3975207805633545, 'p95': 4.310699462890625, 'max': 12.884002685546875}` / `{'median': 0.48021745681762695, 'p95': 1.9990636110305786, 'max': 4.477279424667358}`.
- The issue-time enemy guard retained 14868 observations, detected 2283 during-plan geometry changes, recertified 2283 decisions, and overrode 50 actions. Read/recertificate timing was `{'median': 1.7208499775733799, 'p95': 3.5066999844275415, 'max': 11.704000004101545}` / `{'median': 1.8351000035181642, 'p95': 3.417200001422316, 'max': 14.638599997851998}` ms; 2914 issue captures contained latent bodies (maximum 59), and 7700 contained dormant bodies (maximum 53). Fresh/global transactions preserved 2233/2283 planned actions, relaxed 1 fresh/global empty intersections, inherited 17 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11480 observations (11434 contact enabled, 46 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4857, '0x00597600': 6623}`.
- The terminal-threat heuristic covered 14868 decisions with horizon counts `{'0': 74, '10': 13832, '32': 962}`; it reported 24 collision and 174 sub-safety-clearance warnings, and relaxed 148 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 3554, '3': 10291, '4': 1023}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 60, '2': 9264, '3': 5126, '4': 418}`.
- Adaptive delay supports were `{'1,2': 67, '1,2,3': 116, '1,2,3,4': 255, '1,2,3,4,5': 62, '2,3': 2610, '2,3,4': 7696, '2,3,4,5': 3385, '2,3,4,5,6': 676, '3,4': 1}`; 77 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 14/113.
- Robust viability supplied 14678 available policy queries (0 had new delay support outside the cached policy), constrained 7835 decisions, and exposed 6695 empty queried action sets. Recovery guidance was available/selected on 1919/906 empty-kernel queries; distant-kernel guidance was available/selected on 3941/3849. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 12.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 97.32420048477151, 'p95': 295.0254226333724, 'max': 555.409758646713}`, and `{'median': 0.0, 'p95': 15.451543807983398, 'max': 42.53859543800354}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2323, '1': 1781, '2': 1585, '3': 1738, '4': 1783, '5': 1799, '6': 1833, '7': 1836}`.
- Global-horizon/local-prefix cross-tab covered 10232 decisions: 7 had a winning global state but unsafe selected prefix, 4364 had a losing global state but safe short prefix, 3 selected globally certified actions contradicted the fresh local prefix checker, and 81 selected actions were outside the reported winning set. 1771 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1916 unique policies with solve-time statistics `{'median': 104.67780000180937, 'p95': 301.4077999978326, 'max': 425.29869999270886}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1800.0}`. Policy status counts were `{'pending_future_epoch': 84, 'queryable': 14679, 'expired': 20}`; 105 robust-mode decisions had no query.
- Of 7363 unambiguous output transitions, 6856 (0.931) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 16, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 16 hit windows with a positive warning lead; those leads were `[6, 7, 5, 2, 9, 0, 6, 5, 4, 8, 12, 8, 10, 4, 3, 9, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.348 during the 60 frames preceding a hit versus 0.153 outside those windows.
- Mean selected control-reserve deficit was 7.243 during the 60 frames preceding a hit versus 3.502 outside those windows.
- Soft recovery was selected on 0.044 of alive decisions in the 60-frame pre-hit windows versus 0.065 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 4.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
