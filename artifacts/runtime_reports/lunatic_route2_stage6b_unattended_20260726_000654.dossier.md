# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260726_000654

## Scope And Integrity

- Valid practice scope: `2..75563` (14339 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 23, at `[8378, 11986, 12552, 12895, 13308, 13854, 18589, 19063, 19753, 20591, 21465, 23318, 24232, 31868, 49419, 50456, 51648, 52151, 56974, 57484, 57994, 59139, 63505]`.
- Hard no-Bomb verification: **PASS** across 14339 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F8378-T1`. It occurred during a nonspell phase at player (376.000, 430.402), with 355 bullets and 0 lasers. The projectile model reported pipeline clearance -1.974.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 12 |
| `observed_bullet_overlap` | 8 |
| `observed_laser_overlap` | 2 |
| `observed_multiple_hazard_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 18
- `fast_mode`: 13
- `corridor_deadline_miss`: 7
- `pool_density_over_1000`: 5
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 8378 | nonspell | (376.000, 430.402) | `down_right` | 355/0 | -1.974/-1.974 | 0f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11986 | 150 薬符「壺中の大銀河」 | (8.000, 403.164) | `stay` | 782/0 | -1.588/-22.987 | 19f/48f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12552 | 150 薬符「壺中の大銀河」 | (360.000, 432.000) | `left_fast` | 311/0 | -11.025/-22.365 | 15f/74f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12895 | 150 薬符「壺中の大銀河」 | (376.000, 432.000) | `up_left_fast` | 317/0 | -17.210/-17.210 | 5f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13308 | 150 薬符「壺中の大銀河」 | (8.000, 420.741) | `down_fast` | 572/0 | -1.351/-1.351 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13854 | 150 薬符「壺中の大銀河」 | (356.201, 56.607) | `left_fast` | 295/0 | 1.266/-19.393 | 32f/41f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18589 | nonspell | (371.940, 432.000) | `right_fast` | 1173/0 | -1.709/-1.709 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19063 | nonspell | (8.000, 432.000) | `up_left_fast` | 1166/0 | -3.448/-3.448 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19753 | nonspell | (17.200, 431.737) | `up_fast` | 1061/0 | -2.521/-3.313 | 4f/22f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20591 | nonspell | (376.000, 424.565) | `down` | 1078/0 | -0.348/-0.348 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21465 | nonspell | (376.000, 432.000) | `up_right` | 1209/0 | -1.732/-1.732 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23318 | 154 神宝「ブリリアントドラゴンバレッタ」 | (133.790, 388.484) | `up_right` | 117/230 | -1.055/-1.055 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24232 | 154 神宝「ブリリアントドラゴンバレッタ」 | (376.000, 432.000) | `up_right_fast` | 130/215 | -3.284/-3.284 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31868 | 158 神宝「ブディストダイアモンド」 | (65.163, 418.200) | `down_left_fast` | 238/33 | -0.426/-2.399 | 3f/9f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 49419 | 166 神宝「ライフスプリングインフィニティ」 | (198.800, 388.148) | `up` | 288/52 | -4.599/-4.599 | 0f/9f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50456 | 166 神宝「ライフスプリングインフィニティ」 | (66.082, 432.000) | `stay` | 433/52 | -1.639/-1.639 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51648 | 166 神宝「ライフスプリングインフィニティ」 | (8.953, 432.000) | `up_right_fast` | 307/52 | -2.981/-2.981 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 52151 | 166 神宝「ライフスプリングインフィニティ」 | (13.657, 422.343) | `right_fast` | 214/52 | 2.783/-2.301 | 0f/0f | `observed_multiple_hazard_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56974 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 432.000) | `stay` | 590/0 | -1.753/-1.753 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57484 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 425.308) | `down_fast` | 565/0 | -1.543/-1.543 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57994 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (32.613, 432.000) | `up` | 551/0 | -1.916/-1.916 | 4f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 59139 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 421.285) | `down` | 570/0 | -0.103/-1.342 | 0f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 63505 | 174 「永夜返し  -待宵-」 | (13.437, 432.000) | `right_fast` | 891/0 | -0.339/-0.339 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 6221 | 6005 | 2525 | 0 | 3413 | 1094 | 101.000 | 0.095 |
| 150 薬符「壺中の大銀河」 | 5 | 752 | 729 | 269 | 0 | 452 | 136 | 229.937 | 0.099 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 2 | 790 | 782 | 339 | 0 | 400 | 199 | 141.662 | 0.158 |
| 158 神宝「ブディストダイアモンド」 | 1 | 1301 | 1295 | 829 | 0 | 421 | 261 | 49.299 | 0.278 |
| 162 | 0 | 917 | 912 | 539 | 0 | 369 | 207 | 81.409 | 0.122 |
| 166 神宝「ライフスプリングインフィニティ」 | 4 | 1169 | 1160 | 403 | 0 | 654 | 238 | 164.580 | 0.270 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 4 | 1591 | 1573 | 782 | 0 | 775 | 307 | 89.430 | 0.161 |
| 174 「永夜返し  -待宵-」 | 1 | 224 | 214 | 106 | 0 | 108 | 35 | 90.107 | 0.222 |
| 178 | 0 | 201 | 180 | 123 | 0 | 57 | 28 | 65.550 | 0.112 |
| 182 | 0 | 402 | 384 | 321 | 0 | 63 | 62 | 25.186 | 0.276 |
| 186 | 0 | 111 | 91 | 43 | 0 | 48 | 14 | 326.628 | 0.000 |
| 190 | 0 | 660 | 639 | 444 | 0 | 193 | 109 | 55.258 | 0.173 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 2 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 21.204 ms median and 42.090 ms p95.
- The full enemy sensor produced 9745 snapshots; capture read time was `{'median': 22.142799978610128, 'p95': 47.27470001671463, 'max': 116.22409999836236}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 15.0}` frames, and 10 phase-counter discontinuities were excluded; 13775 decisions retained at least one robust-union body (maximum 34); 4177 decisions contained latent contact-disabled geometry (maximum 33), and 5249 contained bounded inactive-slot memory (maximum 33). 155 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 3.58892822265625, 'p95': 8.227253723144532, 'max': 9.036044311523437}` / `{'median': 3.473114013671875, 'p95': 8.613922119140625, 'max': 9.880340576171875}` / `{'median': 0.11663818359375, 'p95': 4.18680419921875, 'max': 4.706622314453125}`.
- The issue-time enemy guard retained 14339 observations, detected 1025 during-plan geometry changes, recertified 1025 decisions, and overrode 516 actions. Read/recertificate timing was `{'median': 1.827100000809878, 'p95': 3.9204999920912087, 'max': 25.713999988511205}` / `{'median': 9.846400003880262, 'p95': 21.41679998021573, 'max': 41.3031000061892}` ms; 2363 issue captures contained latent bodies (maximum 33), and 5247 contained dormant bodies (maximum 33).
- The synchronous spell-owner guard retained 12999 observations (11201 contact enabled, 1798 anticipatory, 0 errors). 12999 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 12999}`.
- The terminal-threat heuristic covered 14339 decisions with horizon counts `{'0': 77, '10': 13095, '32': 1167}`; it reported 8 collision and 226 sub-safety-clearance warnings, and relaxed 288 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 45, '3': 966, '4': 9138, '5': 3328, '6': 862}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 54, '3': 1611, '4': 11502, '5': 887, '6': 285}`.
- Adaptive delay supports were `{'1,2,3': 17, '1,2,3,4': 1, '2,3': 160, '2,3,4': 11, '2,3,4,5': 567, '2,3,4,5,6': 609, '3': 30, '3,4': 231, '3,4,5': 1970, '3,4,5,6': 10457, '4,5,6': 285, '5,6': 1}`; 694 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 101/282.
- Robust viability supplied 13964 available policy queries (0 had new delay support outside the cached policy), constrained 6953 decisions, and exposed 6723 empty queried action sets. Recovery guidance was available/selected on 1555/870 empty-kernel queries; distant-kernel guidance was available/selected on 4409/4247. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 9.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 102.44998779892558, 'p95': 321.5960198758685, 'max': 505.9644256269407}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2199, '1': 1969, '2': 1819, '3': 1491, '4': 1584, '5': 1658, '6': 1652, '7': 1592}`.
- Global-horizon/local-prefix cross-tab covered 10732 decisions: 2 had a winning global state but unsafe selected prefix, 5415 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 106 selected actions were outside the reported winning set. 843 newer issue-time hazard versions and 11 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2690 unique policies with solve-time statistics `{'median': 100.30605000793003, 'p95': 427.15669999597594, 'max': 565.5373000190593}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1810.0}`. Policy status counts were `{'pending_future_epoch': 50, 'queryable': 13963, 'expired': 80}`; 129 robust-mode decisions had no query.
- Of 7849 unambiguous output transitions, 6841 (0.872) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 22, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 21 hit windows with a positive warning lead; those leads were `[16, 48, 74, 10, 4, 41, 4, 7, 22, 13, 10, 0, 4, 9, 9, 9, 8, 0, 10, 9, 10, 19, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.331 during the 60 frames preceding a hit versus 0.144 outside those windows.
- Mean selected control-reserve deficit was 16.167 during the 60 frames preceding a hit versus 6.492 outside those windows.
- Soft recovery was selected on 0.048 of alive decisions in the 60-frame pre-hit windows versus 0.064 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 5.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
