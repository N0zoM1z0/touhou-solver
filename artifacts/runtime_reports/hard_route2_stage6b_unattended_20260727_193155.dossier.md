# TH08 Final B / Kaguya No-Bomb Practice Review: hard_route2_stage6b_unattended_20260727_193155

## Scope And Integrity

- Valid practice scope: `1..72862` (22140 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 13, at `[873, 10927, 11586, 11965, 12556, 30872, 46053, 54532, 55522, 56570, 60052, 62672, 68786]`.
- Hard no-Bomb verification: **PASS** across 22140 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S7-F873-T1`. It occurred during a nonspell phase at player (376.000, 417.100), with 275 bullets and 0 lasers. The projectile model reported pipeline clearance -2.886.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 10 |
| `modeled_committed_prefix_collision` | 2 |
| `observed_laser_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 11
- `fast_mode`: 7
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 873 | nonspell | (376.000, 417.100) | `up_fast` | 275/0 | -2.886/-5.090 | 2f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10927 | 149 薬符「壺中の大銀河」 | (376.000, 432.000) | `right_fast` | 350/0 | -0.559/-2.180 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11586 | 149 薬符「壺中の大銀河」 | (376.000, 256.687) | `stay` | 615/0 | -2.247/-2.247 | 3f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11965 | 149 薬符「壺中の大銀河」 | (10.657, 380.502) | `down_fast` | 639/0 | -2.041/-8.611 | 6f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12556 | 149 薬符「壺中の大銀河」 | (376.000, 16.000) | `up_left` | 507/0 | -2.216/-3.230 | 5f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30872 | 157 神宝「ブディストダイアモンド」 | (376.000, 415.180) | `up_fast` | 247/33 | 0.746/-3.436 | 2f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 46053 | 165 神宝「ライフスプリングインフィニティ」 | (202.844, 384.427) | `up` | 224/52 | -2.617/-4.733 | 2f/7f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54532 | 169 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 416.994) | `up` | 509/0 | 1.511/-2.177 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55522 | 169 神宝「蓬莱の玉の枝  -夢色の郷-」 | (339.521, 430.374) | `up_left` | 521/0 | -1.410/-1.410 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56570 | 169 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 422.943) | `right_fast` | 467/0 | 0.008/-0.287 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 60052 | 173 「永夜返し  -上つ弓張-」 | (368.000, 429.700) | `up` | 912/0 | -3.306/-3.306 | 3f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 62672 | 177 「永夜返し  -子の三つ-」 | (8.000, 425.495) | `up_fast` | 1097/0 | -3.190/-3.190 | 2f/2f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 68786 | 185 「永夜返し  -寅の三つ-」 | (368.000, 426.960) | `left_fast` | 781/0 | -2.079/-2.321 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 1 | 9388 | 9146 | 4076 | 0 | 4979 | 1112 | 82.383 | 0.106 |
| 149 薬符「壺中の大銀河」 | 4 | 1142 | 1124 | 425 | 0 | 681 | 155 | 174.337 | 0.031 |
| 153 | 0 | 687 | 678 | 302 | 0 | 351 | 104 | 103.496 | 0.170 |
| 157 神宝「ブディストダイアモンド」 | 1 | 2231 | 2223 | 988 | 0 | 1166 | 277 | 42.368 | 0.261 |
| 161 | 0 | 1623 | 1614 | 949 | 0 | 660 | 223 | 70.040 | 0.122 |
| 165 神宝「ライフスプリングインフィニティ」 | 1 | 1897 | 1886 | 496 | 0 | 1267 | 252 | 119.923 | 0.129 |
| 169 神宝「蓬莱の玉の枝  -夢色の郷-」 | 3 | 2531 | 2521 | 1179 | 0 | 1303 | 331 | 76.318 | 0.248 |
| 173 「永夜返し  -上つ弓張-」 | 1 | 335 | 321 | 113 | 0 | 170 | 45 | 84.428 | 0.229 |
| 177 「永夜返し  -子の三つ-」 | 1 | 299 | 289 | 185 | 0 | 104 | 40 | 61.473 | 0.357 |
| 181 | 0 | 593 | 580 | 477 | 0 | 103 | 70 | 23.687 | 0.310 |
| 185 「永夜返し  -寅の三つ-」 | 1 | 416 | 403 | 257 | 0 | 143 | 62 | 178.316 | 0.151 |
| 189 | 0 | 998 | 987 | 632 | 0 | 347 | 121 | 55.519 | 0.121 |

## Interpretation

- Retained witnesses classify 10 bullet overlaps, 1 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.809 ms median and 18.634 ms p95.
- The full enemy sensor produced 10771 snapshots; capture read time was `{'median': 5.230600014328957, 'p95': 21.746699989307672, 'max': 55.91009999625385}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 12 phase-counter discontinuities were excluded; 21414 decisions retained at least one robust-union body (maximum 34); 6205 decisions contained latent contact-disabled geometry (maximum 33), and 7327 contained bounded inactive-slot memory (maximum 33). 66 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 4.7449493408203125, 'p95': 6.837337017059326, 'max': 7.162994384765625}` / `{'median': 6.066315174102783, 'p95': 8.955413818359375, 'max': 9.48992919921875}` / `{'median': 0.026270548502604147, 'p95': 4.4777069091796875, 'max': 4.744964599609375}`.
- The issue-time enemy guard retained 22140 observations, detected 632 during-plan geometry changes, recertified 632 decisions, and overrode 10 actions. Read/recertificate timing was `{'median': 1.7057500081136823, 'p95': 3.422799985855818, 'max': 14.859699993394315}` / `{'median': 2.062300016405061, 'p95': 5.642100004479289, 'max': 15.646599989850074}` ms; 3321 issue captures contained latent bodies (maximum 33), and 7329 contained dormant bodies (maximum 33). Fresh/global transactions preserved 622/632 planned actions, relaxed 1 fresh/global empty intersections, inherited 10 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 20058 observations (17163 contact enabled, 2895 anticipatory, 0 errors). 20058 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 20058}`.
- The terminal-threat heuristic covered 22140 decisions with horizon counts `{'0': 92, '10': 20117, '32': 1931}`; it reported 36 collision and 336 sub-safety-clearance warnings, and relaxed 419 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 4966, '3': 16358, '4': 816}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 62, '2': 13070, '3': 8814, '4': 194}`.
- Adaptive delay supports were `{'1,2': 36, '1,2,3': 96, '1,2,3,4': 93, '1,2,3,4,5': 101, '1,2,3,4,5,6': 15, '2': 9, '2,3': 3822, '2,3,4': 12220, '2,3,4,5': 4208, '2,3,4,5,6': 1518, '3,4': 22}`; 34 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 25/209.
- Robust viability supplied 21772 available policy queries (0 had new delay support outside the cached policy), constrained 11274 decisions, and exposed 10079 empty queried action sets. Recovery guidance was available/selected on 2536/1253 empty-kernel queries; distant-kernel guidance was available/selected on 6426/6302. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 10.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 93.29523031752481, 'p95': 293.7209560109731, 'max': 555.409758646713}`, and `{'median': 0.0, 'p95': 16.0, 'max': 40.0543053150177}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 3388, '1': 2708, '2': 2228, '3': 2604, '4': 2664, '5': 2675, '6': 2720, '7': 2785}`.
- Global-horizon/local-prefix cross-tab covered 19197 decisions: 3 had a winning global state but unsafe selected prefix, 9040 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 146 selected actions were outside the reported winning set. 511 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2792 unique policies with solve-time statistics `{'median': 81.69044999522157, 'p95': 316.1144999903627, 'max': 429.0428999811411}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1804.0}`. Policy status counts were `{'pending_future_epoch': 95, 'queryable': 21775, 'expired': 50}`; 148 robust-mode decisions had no query.
- Of 10064 unambiguous output transitions, 9289 (0.923) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 13}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[9, 6, 5, 14, 10, 9, 7, 4, 11, 5, 14, 2, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.237 during the 60 frames preceding a hit versus 0.151 outside those windows.
- Mean selected control-reserve deficit was 9.754 during the 60 frames preceding a hit versus 3.659 outside those windows.
- Soft recovery was selected on 0.055 of alive decisions in the 60-frame pre-hit windows versus 0.054 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 6.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
