# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260726_011639

## Scope And Integrity

- Valid practice scope: `2..74963` (14652 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 26, at `[496, 2155, 11927, 13171, 18835, 19287, 19792, 36164, 37712, 39557, 40356, 41465, 48439, 50169, 50905, 51489, 52082, 54799, 55936, 56614, 57126, 57935, 58417, 58902, 65363, 70856]`.
- Hard no-Bomb verification: **PASS** across 14652 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F496-T1`. It occurred during a nonspell phase at player (308.921, 432.000), with 970 bullets and 0 lasers. The projectile model reported pipeline clearance -2.040.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 18 |
| `observed_bullet_overlap` | 5 |
| `observed_laser_overlap` | 1 |
| `observed_multiple_hazard_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 19
- `fast_mode`: 13
- `corridor_deadline_miss`: 5
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 496 | nonspell | (308.921, 432.000) | `up_right_fast` | 970/0 | -2.040/-2.040 | 5f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2155 | nonspell | (103.239, 422.173) | `left_fast` | 280/0 | -2.186/-2.186 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11927 | 150 薬符「壺中の大銀河」 | (376.000, 427.500) | `down_left` | 343/0 | -1.708/-21.143 | 17f/31f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13171 | 150 薬符「壺中の大銀河」 | (8.000, 16.000) | `stay` | 330/0 | -14.569/-14.910 | 43f/102f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18835 | nonspell | (376.000, 430.342) | `up_fast` | 1189/0 | -2.162/-2.162 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19287 | nonspell | (13.109, 432.000) | `down_left_fast` | 1158/0 | -2.992/-2.992 | 4f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19792 | nonspell | (365.738, 432.000) | `down_right_fast` | 1084/0 | -4.480/-4.480 | 0f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36164 | nonspell | (342.785, 432.000) | `stay` | 643/0 | 0.870/0.172 | 0f/13f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37712 | nonspell | (272.186, 432.000) | `up_left_fast` | 589/0 | -2.715/-2.715 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39557 | 162 神宝「サラマンダーシールド」 | (20.840, 432.000) | `right` | 526/28 | 0.690/-1.810 | 4f/17f | `observed_multiple_hazard_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40356 | 162 神宝「サラマンダーシールド」 | (340.275, 432.000) | `stay` | 568/32 | -2.122/-2.122 | 4f/18f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41465 | 162 神宝「サラマンダーシールド」 | (8.000, 432.000) | `stay` | 524/32 | -1.292/-1.583 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 48439 | 166 神宝「ライフスプリングインフィニティ」 | (190.507, 372.625) | `up_left_fast` | 288/52 | -2.586/-4.667 | 6f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50169 | 166 神宝「ライフスプリングインフィニティ」 | (41.762, 410.664) | `down_right_fast` | 404/52 | -3.454/-3.454 | 5f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50905 | 166 神宝「ライフスプリングインフィニティ」 | (366.734, 401.609) | `down_left_fast` | 404/52 | -3.611/-3.611 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51489 | 166 神宝「ライフスプリングインフィニティ」 | (20.360, 432.000) | `up_right_fast` | 471/52 | -1.107/-1.107 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 52082 | 166 神宝「ライフスプリングインフィニティ」 | (368.526, 425.308) | `up_left` | 434/52 | -1.308/-1.308 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54799 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (210.405, 432.000) | `up_fast` | 336/0 | -6.579/-6.579 | 3f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55936 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (12.879, 430.250) | `right_fast` | 564/0 | -3.667/-3.667 | 7f/29f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56614 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 432.000) | `up` | 564/0 | -1.691/-1.691 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57126 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 422.800) | `stay` | 586/0 | -2.273/-2.390 | 4f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57935 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (352.000, 289.617) | `left` | 583/0 | -3.259/-3.259 | 19f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58417 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (355.707, 425.100) | `up` | 586/0 | -1.594/-1.594 | 4f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58902 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 432.000) | `stay` | 555/0 | -0.416/-0.416 | 0f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 65363 | 178 「永夜返し  -子の四つ-」 | (376.000, 432.000) | `stay` | 1003/0 | -3.843/-3.843 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 70856 | 186 「永夜返し  -寅の四つ-」 | (109.210, 432.000) | `left_fast` | 1507/0 | -1.397/-1.397 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 6681 | 6454 | 2676 | 0 | 3729 | 1136 | 90.806 | 0.075 |
| 150 薬符「壺中の大銀河」 | 2 | 729 | 712 | 313 | 0 | 392 | 138 | 208.901 | 0.065 |
| 154 | 0 | 397 | 389 | 165 | 0 | 201 | 99 | 141.810 | 0.194 |
| 158 | 0 | 1293 | 1288 | 806 | 0 | 416 | 261 | 47.013 | 0.253 |
| 162 神宝「サラマンダーシールド」 | 3 | 1014 | 1007 | 466 | 0 | 535 | 216 | 93.449 | 0.166 |
| 166 神宝「ライフスプリングインフィニティ」 | 5 | 1225 | 1218 | 419 | 0 | 727 | 245 | 167.261 | 0.166 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 7 | 1664 | 1648 | 743 | 0 | 902 | 306 | 87.900 | 0.126 |
| 174 | 0 | 267 | 256 | 134 | 0 | 120 | 46 | 77.027 | 0.145 |
| 178 「永夜返し  -子の四つ-」 | 1 | 194 | 174 | 119 | 0 | 55 | 28 | 60.679 | 0.159 |
| 182 | 0 | 395 | 377 | 308 | 0 | 69 | 62 | 27.576 | 0.256 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 137 | 120 | 65 | 0 | 53 | 19 | 296.558 | 0.094 |
| 190 | 0 | 656 | 636 | 404 | 0 | 230 | 109 | 53.938 | 0.095 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 1 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 21.855 ms median and 38.955 ms p95.
- The full enemy sensor produced 9728 snapshots; capture read time was `{'median': 19.392750022234395, 'p95': 43.490100011695176, 'max': 111.372199957259}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 13.0}` frames, and 13 phase-counter discontinuities were excluded; 13905 decisions retained at least one robust-union body (maximum 34); 3900 decisions contained latent contact-disabled geometry (maximum 33), and 4825 contained bounded inactive-slot memory (maximum 33). 169 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 6.1346435546875, 'max': 6.271697998046875}` / `{'median': 0.0, 'p95': 6.066329002380371, 'max': 6.2717061042785645}` / `{'median': 0.0, 'p95': 0.3214988708496094, 'max': 4.9055328369140625}`.
- The issue-time enemy guard retained 14652 observations, detected 860 during-plan geometry changes, recertified 860 decisions, and overrode 409 actions. Read/recertificate timing was `{'median': 1.7521999834571034, 'p95': 3.78989998716861, 'max': 22.48049998888746}` / `{'median': 8.088550006505102, 'p95': 19.601100008003414, 'max': 37.880699965171516}` ms; 2031 issue captures contained latent bodies (maximum 33), and 4819 contained dormant bodies (maximum 33).
- The synchronous spell-owner guard retained 13198 observations (11332 contact enabled, 1866 anticipatory, 0 errors). 13198 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 13198}`.
- The terminal-threat heuristic covered 14652 decisions with horizon counts `{'0': 77, '10': 13641, '32': 934}`; it reported 16 collision and 147 sub-safety-clearance warnings, and relaxed 232 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 58, '3': 1068, '4': 10387, '5': 2857, '6': 282}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 130, '3': 1389, '4': 12179, '5': 772, '6': 182}`.
- Adaptive delay supports were `{'1,2,3': 8, '1,2,3,4': 6, '2,3': 172, '2,3,4': 125, '2,3,4,5': 538, '2,3,4,5,6': 1265, '3,4': 89, '3,4,5': 1945, '3,4,5,6': 10500, '4,5,6': 4}`; 554 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 101/468.
- Robust viability supplied 14279 available policy queries (0 had new delay support outside the cached policy), constrained 7429 decisions, and exposed 6618 empty queried action sets. Recovery guidance was available/selected on 1634/885 empty-kernel queries; distant-kernel guidance was available/selected on 4261/4044. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 13.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 107.33126291998991, 'p95': 336.0, 'max': 531.8646444350292}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2268, '1': 2055, '2': 1798, '3': 1504, '4': 1671, '5': 1714, '6': 1644, '7': 1625}`.
- Global-horizon/local-prefix cross-tab covered 10866 decisions: 2 had a winning global state but unsafe selected prefix, 5416 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 97 selected actions were outside the reported winning set. 693 newer issue-time hazard versions and 8 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2665 unique policies with solve-time statistics `{'median': 95.01689998432994, 'p95': 421.6109999688342, 'max': 535.9371000085957}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1813.0}`. Policy status counts were `{'pending_future_epoch': 63, 'queryable': 14281, 'expired': 64}`; 129 robust-mode decisions had no query.
- Of 7446 unambiguous output transitions, 6431 (0.864) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 26}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 25 hit windows with a positive warning lead; those leads were `[13, 0, 31, 102, 5, 8, 14, 13, 3, 17, 18, 8, 14, 14, 10, 13, 12, 19, 29, 6, 11, 23, 12, 9, 8, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.326 during the 60 frames preceding a hit versus 0.115 outside those windows.
- Mean selected control-reserve deficit was 13.158 during the 60 frames preceding a hit versus 5.721 outside those windows.
- Soft recovery was selected on 0.019 of alive decisions in the 60-frame pre-hit windows versus 0.063 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 5.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
