# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260729_095849

## Scope And Integrity

- Valid practice scope: `2..42834` (11342 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 20, at `[1423, 2119, 7943, 11145, 12293, 13853, 14262, 14654, 23818, 25339, 29734, 30810, 33601, 35022, 35769, 37404, 38151, 38889, 40646, 41266]`.
- Hard no-Bomb verification: **PASS** across 11342 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1423-T1`. It occurred during a nonspell phase at player (354.887, 327.735), with 113 bullets and 0 lasers. The projectile model reported pipeline clearance 0.047.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 14 |
| `observed_bullet_overlap` | 4 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `fast_mode`: 13
- `playfield_boundary`: 12
- `pool_density_over_1000`: 5
- `corridor_deadline_miss`: 1
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1423 | nonspell | (354.887, 327.735) | `down_right_fast` | 113/0 | 0.047/-0.342 | 3f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2119 | nonspell | (371.253, 428.747) | `up_left` | 619/0 | -2.750/-2.750 | 3f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7943 | nonspell | (22.585, 415.067) | `down_right_fast` | 552/0 | -16.992/-16.992 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11145 | nonspell | (347.663, 365.464) | `up_left_fast` | 876/0 | -9.033/-19.246 | 3f/3f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12293 | nonspell | (8.000, 427.400) | `up` | 136/0 | -2.600/-2.600 | 2f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13853 | nonspell | (340.096, 38.844) | `down_right_fast` | 526/0 | -4.781/-9.173 | 5f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14262 | nonspell | (376.000, 348.947) | `down_right_fast` | 334/0 | -1.658/-2.116 | 0f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14654 | nonspell | (371.121, 403.121) | `down_left_fast` | 440/0 | 2.725/-22.427 | 13f/27f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23818 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 1113/0 | -3.017/-3.017 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25339 | 103 幻波「赤眼催眠(マインドブローイング)」 | (243.388, 432.000) | `right_fast` | 1076/0 | -2.536/-2.536 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29734 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (187.915, 432.000) | `left` | 990/0 | -8.380/-8.423 | 10f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30810 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (199.881, 432.000) | `down_right` | 1017/0 | -10.006/-10.006 | 8f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33601 | nonspell | (376.000, 409.332) | `stay` | 469/0 | -0.864/-0.864 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35022 | nonspell | (8.000, 430.264) | `right_fast` | 414/0 | -2.752/-2.752 | 2f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35769 | nonspell | (8.000, 432.000) | `right_fast` | 462/0 | -2.980/-2.980 | 4f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37404 | 111 懶惰「生神停止(マインドストッパー)」 | (171.696, 196.939) | `up_fast` | 367/0 | -3.233/-4.674 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38151 | 111 懶惰「生神停止(マインドストッパー)」 | (160.486, 199.181) | `down_left_fast` | 338/0 | 0.147/-5.502 | 3f/18f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38889 | 111 懶惰「生神停止(マインドストッパー)」 | (177.722, 189.167) | `left_fast` | 341/0 | -1.753/-3.358 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40646 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 429.700) | `up` | 1304/0 | -1.648/-2.024 | 11f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41266 | 115 散符「真実の月(インビジブルフルムーン)」 | (257.082, 430.374) | `up_right` | 1096/0 | -2.741/-2.961 | 6f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 11 | 7681 | 7556 | 5435 | 0 | 2077 | 1033 | 142.281 | 0.188 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 821 | 809 | 492 | 0 | 316 | 170 | 121.677 | 0.329 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 612 | 603 | 419 | 0 | 178 | 133 | 96.124 | 0.321 |
| 111 懶惰「生神停止(マインドストッパー)」 | 3 | 1049 | 1041 | 250 | 0 | 773 | 156 | 128.611 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1179 | 1169 | 652 | 0 | 506 | 182 | 60.679 | 0.408 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 12.098 ms median and 27.124 ms p95.
- The full enemy sensor produced 6306 snapshots; capture read time was `{'median': 9.480000066105276, 'p95': 36.59540007356554, 'max': 96.60869999788702}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 17.0}` frames, and 6 phase-counter discontinuities were excluded; 10754 decisions retained at least one robust-union body (maximum 41); 4462 decisions contained latent contact-disabled geometry (maximum 41), and 5370 contained bounded inactive-slot memory (maximum 40). 406 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.2784271240234375, 'max': 4.87840461730957}` / `{'median': 0.0, 'p95': 4.278404235839844, 'max': 4.7102179527282715}` / `{'median': 0.0, 'p95': 0.9999987483024597, 'max': 6.222534894943237}`.
- The issue-time enemy guard retained 11342 observations, detected 2339 during-plan geometry changes, recertified 2339 decisions, and overrode 57 actions. Read/recertificate timing was `{'median': 1.8435000092722476, 'p95': 3.6162000615149736, 'max': 23.230600054375827}` / `{'median': 3.2582998974248767, 'p95': 7.891400018706918, 'max': 22.615899913944304}` ms; 4439 issue captures contained latent bodies (maximum 41), and 5378 contained dormant bodies (maximum 40). Fresh/global transactions preserved 2282/2339 planned actions, relaxed 10 fresh/global empty intersections, inherited 18 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 7947 observations (7919 contact enabled, 28 anticipatory, 0 errors). 7947 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 7947}`.
- The terminal-threat heuristic covered 11342 decisions with horizon counts `{'0': 67, '10': 10932, '32': 343}`; it reported 4 collision and 76 sub-safety-clearance warnings, and relaxed 80 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 336, '3': 6897, '4': 2910, '5': 911, '6': 288}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1330, '3': 6976, '4': 2311, '5': 684, '6': 41}`.
- Adaptive delay supports were `{'1,2,3': 135, '1,2,3,4': 93, '1,2,3,4,5': 31, '1,2,3,4,5,6': 11, '2,3': 154, '2,3,4': 2261, '2,3,4,5': 3893, '2,3,4,5,6': 3455, '3,4': 13, '3,4,5': 188, '3,4,5,6': 873, '4,5,6': 234, '5,6': 1}`; 197 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 44/209.
- Robust viability supplied 11178 available policy queries (0 had new delay support outside the cached policy), constrained 3850 decisions, and exposed 7248 empty queried action sets. Recovery guidance was available/selected on 1045/490 empty-kernel queries; distant-kernel guidance was available/selected on 5632/5318. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 131.93938001976514, 'p95': 355.2576529787923, 'max': 520.9222590751906}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1816, '1': 1490, '2': 1198, '3': 1299, '4': 1321, '5': 1339, '6': 1422, '7': 1293}`.
- Global-horizon/local-prefix cross-tab covered 6876 decisions: 4 had a winning global state but unsafe selected prefix, 4514 had a losing global state but safe short prefix, 3 selected globally certified actions contradicted the fresh local prefix checker, and 31 selected actions were outside the reported winning set. 1812 newer issue-time hazard versions and 1 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1674 unique policies with solve-time statistics `{'median': 117.76620004093274, 'p95': 350.649599917233, 'max': 571.2461000075564}` and first-observed ages `{'median': 2.0, 'p95': 8.0, 'max': 1800.0}`. Policy status counts were `{'pending_future_epoch': 66, 'queryable': 11179, 'expired': 11}`; 78 robust-mode decisions had no query.
- Of 5890 unambiguous output transitions, 5295 (0.899) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 20}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[16, 7, 0, 3, 8, 9, 19, 27, 3, 12, 17, 17, 13, 9, 11, 8, 18, 7, 13, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.278 during the 60 frames preceding a hit versus 0.209 outside those windows.
- Mean selected control-reserve deficit was 10.788 during the 60 frames preceding a hit versus 5.259 outside those windows.
- Soft recovery was selected on 0.009 of alive decisions in the 60-frame pre-hit windows versus 0.040 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
