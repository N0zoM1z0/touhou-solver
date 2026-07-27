# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260727_213748

## Scope And Integrity

- Valid practice scope: `2..73670` (22430 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 16, at `[12366, 12814, 13527, 18671, 19899, 29441, 30536, 36602, 47253, 47813, 49726, 53203, 53809, 54974, 55508, 69563]`.
- Hard no-Bomb verification: **PASS** across 22430 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F12366-T1`. It occurred during spell 150 `薬符「壺中の大銀河」` at player (370.343, 430.814), with 395 bullets and 0 lasers. The projectile model reported pipeline clearance 0.484.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 7 |
| `modeled_committed_prefix_collision` | 6 |
| `observed_laser_overlap` | 2 |
| `observed_multiple_hazard_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 13
- `fast_mode`: 10
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 12366 | 150 薬符「壺中の大銀河」 | (370.343, 430.814) | `up` | 395/0 | 0.484/-1.500 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12814 | 150 薬符「壺中の大銀河」 | (8.044, 426.343) | `up_fast` | 46/0 | -26.827/-28.298 | 26f/30f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13527 | 150 薬符「壺中の大銀河」 | (337.858, 417.858) | `stay` | 534/0 | -1.781/-16.835 | 8f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18671 | nonspell | (362.842, 432.000) | `up_left` | 1116/0 | -1.118/-1.494 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19899 | nonspell | (11.344, 429.172) | `right_fast` | 1042/0 | -0.386/-0.386 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29441 | 158 神宝「ブディストダイアモンド」 | (40.282, 425.100) | `up_left` | 255/33 | -0.049/-0.949 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30536 | 158 神宝「ブディストダイアモンド」 | (10.828, 424.033) | `right_fast` | 252/33 | -2.096/-3.689 | 2f/6f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36602 | nonspell | (166.340, 432.000) | `up_right_fast` | 536/0 | -1.751/-1.751 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 47253 | 166 神宝「ライフスプリングインフィニティ」 | (376.000, 427.400) | `left_fast` | 291/52 | -2.295/-2.295 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 47813 | 166 神宝「ライフスプリングインフィニティ」 | (323.550, 432.000) | `up_left_fast` | 373/52 | -3.512/-3.512 | 4f/10f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 49726 | 166 神宝「ライフスプリングインフィニティ」 | (20.879, 432.000) | `right_fast` | 247/52 | -0.083/-8.718 | 2f/7f | `observed_multiple_hazard_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 53203 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (173.425, 432.000) | `up_fast` | 336/0 | -6.109/-6.109 | 2f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 53809 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (20.302, 432.000) | `up_right` | 555/0 | -2.443/-2.443 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54974 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (34.288, 417.682) | `down_right_fast` | 563/0 | -1.676/-1.823 | 6f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55508 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (38.972, 432.000) | `stay` | 570/0 | -3.969/-3.969 | 3f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 69563 | 186 「永夜返し  -寅の四つ-」 | (336.642, 432.000) | `left_fast` | 843/0 | -2.418/-2.564 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 9696 | 9456 | 4045 | 0 | 5361 | 1160 | 79.232 | 0.095 |
| 150 薬符「壺中の大銀河」 | 3 | 994 | 971 | 440 | 0 | 525 | 135 | 168.628 | 0.113 |
| 154 | 0 | 861 | 850 | 313 | 0 | 497 | 128 | 100.868 | 0.209 |
| 158 神宝「ブディストダイアモンド」 | 2 | 2244 | 2236 | 1247 | 0 | 954 | 279 | 44.016 | 0.274 |
| 162 | 0 | 1607 | 1599 | 987 | 0 | 612 | 224 | 72.072 | 0.109 |
| 166 神宝「ライフスプリングインフィニティ」 | 3 | 1865 | 1854 | 676 | 0 | 1012 | 254 | 121.705 | 0.297 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 4 | 2528 | 2511 | 1251 | 0 | 1250 | 329 | 75.206 | 0.205 |
| 174 | 0 | 489 | 474 | 280 | 0 | 164 | 68 | 72.302 | 0.303 |
| 178 | 0 | 283 | 274 | 182 | 0 | 92 | 36 | 70.361 | 0.090 |
| 182 | 0 | 592 | 582 | 481 | 0 | 101 | 70 | 26.480 | 0.377 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 268 | 258 | 169 | 0 | 88 | 38 | 204.819 | 0.106 |
| 190 | 0 | 1003 | 985 | 614 | 0 | 368 | 120 | 51.202 | 0.171 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 2 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.761 ms median and 18.842 ms p95.
- The full enemy sensor produced 10923 snapshots; capture read time was `{'median': 5.1194000407122076, 'p95': 20.834899973124266, 'max': 55.91429997002706}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 13 phase-counter discontinuities were excluded; 21658 decisions retained at least one robust-union body (maximum 38); 6006 decisions contained latent contact-disabled geometry (maximum 38), and 7346 contained bounded inactive-slot memory (maximum 33). 71 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 6.664581298828125, 'max': 7.162994384765625}` / `{'median': 0.0, 'p95': 7.1629638671875, 'max': 28.283981323242188}` / `{'median': 0.0, 'p95': 0.067138671875, 'max': 28.283981323242188}`.
- The issue-time enemy guard retained 22430 observations, detected 649 during-plan geometry changes, recertified 649 decisions, and overrode 12 actions. Read/recertificate timing was `{'median': 1.6786999767646194, 'p95': 3.411400015465915, 'max': 15.701500000432134}` / `{'median': 2.341600018553436, 'p95': 5.9946000110358, 'max': 15.448399994056672}` ms; 3131 issue captures contained latent bodies (maximum 38), and 7315 contained dormant bodies (maximum 33). Fresh/global transactions preserved 637/649 planned actions, relaxed 3 fresh/global empty intersections, inherited 5 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 20383 observations (17500 contact enabled, 2883 anticipatory, 0 errors). 20383 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 20383}`.
- The terminal-threat heuristic covered 22430 decisions with horizon counts `{'0': 95, '10': 20613, '32': 1722}`; it reported 15 collision and 212 sub-safety-clearance warnings, and relaxed 341 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 4843, '3': 16874, '4': 713}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 12, '2': 13330, '3': 9088}`.
- Adaptive delay supports were `{'1,2': 56, '1,2,3': 69, '1,2,3,4': 188, '1,2,3,4,5': 11, '1,2,3,4,5,6': 10, '2': 51, '2,3': 3241, '2,3,4': 12106, '2,3,4,5': 4405, '2,3,4,5,6': 2283, '3,4': 10}`; 46 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 40/235.
- Robust viability supplied 22050 available policy queries (0 had new delay support outside the cached policy), constrained 11024 decisions, and exposed 10685 empty queried action sets. Recovery guidance was available/selected on 2473/1276 empty-kernel queries; distant-kernel guidance was available/selected on 7082/6869. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 8.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 96.0, 'p95': 323.9753077010654, 'max': 543.529208046817}`, and `{'median': 0.0, 'p95': 18.37365436553955, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 3427, '1': 2828, '2': 2142, '3': 2683, '4': 2752, '5': 2692, '6': 2730, '7': 2796}`.
- Global-horizon/local-prefix cross-tab covered 18835 decisions: 11 had a winning global state but unsafe selected prefix, 9469 had a losing global state but safe short prefix, 10 selected globally certified actions contradicted the fresh local prefix checker, and 103 selected actions were outside the reported winning set. 535 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2841 unique policies with solve-time statistics `{'median': 79.9743999959901, 'p95': 315.1712999679148, 'max': 401.53719997033477}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1805.0}`. Policy status counts were `{'pending_future_epoch': 95, 'queryable': 22055, 'expired': 69}`; 169 robust-mode decisions had no query.
- Of 10194 unambiguous output transitions, 9424 (0.924) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 16}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 15 hit windows with a positive warning lead; those leads were `[7, 30, 11, 4, 0, 5, 6, 4, 6, 10, 7, 16, 6, 11, 11, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.421 during the 60 frames preceding a hit versus 0.157 outside those windows.
- Mean selected control-reserve deficit was 10.868 during the 60 frames preceding a hit versus 4.203 outside those windows.
- Soft recovery was selected on 0.046 of alive decisions in the 60-frame pre-hit windows versus 0.055 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 6.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
