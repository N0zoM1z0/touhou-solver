# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_043724

## Scope And Integrity

- Valid practice scope: `1..45742` (15009 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 20, at `[918, 1331, 1753, 2443, 3970, 4283, 9983, 10932, 11738, 22293, 22965, 27790, 31207, 32211, 35924, 37528, 38440, 39211, 40021, 45564]`.
- Hard no-Bomb verification: **PASS** across 15009 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F918-T1`. It occurred during a nonspell phase at player (366.217, 432.000), with 136 bullets and 0 lasers. The projectile model reported pipeline clearance 0.496.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 11 |
| `modeled_committed_prefix_collision` | 8 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 15
- `playfield_boundary`: 12
- `corridor_deadline_miss`: 4
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 918 | nonspell | (366.217, 432.000) | `stay` | 136/0 | 0.496/-0.038 | 3f/5f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1331 | nonspell | (13.657, 432.000) | `down_right_fast` | 187/0 | -1.868/-2.014 | 4f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1753 | nonspell | (8.000, 424.000) | `up_fast` | 429/0 | 0.250/-12.889 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2443 | nonspell | (8.000, 422.374) | `up_fast` | 537/0 | 1.299/-3.509 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3970 | nonspell | (356.120, 415.515) | `up_right_fast` | 857/0 | -2.054/-2.488 | 3f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4283 | nonspell | (26.257, 432.000) | `left` | 1002/0 | -1.861/-1.861 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9983 | nonspell | (21.301, 409.143) | `up_fast` | 165/0 | 0.243/-24.525 | 16f/24f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10932 | nonspell | (8.000, 432.000) | `up_left` | 216/0 | -12.027/-12.027 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11738 | 57 夢境「二重大結界」 | (9.410, 428.000) | `up_right_fast` | 589/0 | 0.390/-0.908 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22293 | nonspell | (372.747, 428.747) | `up_fast` | 735/0 | -1.289/-2.838 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22965 | nonspell | (296.841, 427.121) | `left_fast` | 598/0 | -0.349/-0.349 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27790 | nonspell | (357.464, 40.968) | `up_right_fast` | 176/0 | -2.943/-2.943 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31207 | 65 神技「八方龍殺陣」 | (117.776, 426.343) | `up` | 1342/0 | 1.289/-2.621 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32211 | 65 神技「八方龍殺陣」 | (29.758, 427.121) | `right_fast` | 1201/0 | 0.105/-21.533 | 11f/20f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35924 | nonspell | (303.215, 432.000) | `right_fast` | 99/0 | -1.510/-21.852 | 3f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37528 | nonspell | (17.657, 409.434) | `up_right_fast` | 91/0 | 1.533/-10.423 | 14f/18f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38440 | 69 回霊「夢想封印　侘」 | (23.515, 428.747) | `right_fast` | 479/0 | -0.185/-2.833 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39211 | 69 回霊「夢想封印　侘」 | (16.163, 432.000) | `right_fast` | 578/0 | -2.510/-2.510 | 6f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40021 | 69 回霊「夢想封印　侘」 | (11.253, 264.546) | `up_fast` | 662/0 | -19.085/-29.133 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45564 | 73 大結界「博麗弾幕結界」 | (34.992, 364.607) | `down_left` | 1345/0 | -2.689/-2.689 | 4f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 13 | 8908 | 8762 | 4181 | 0 | 4532 | 1073 | 111.197 | 0.129 |
| 57 夢境「二重大結界」 | 1 | 1261 | 1253 | 356 | 0 | 883 | 180 | 153.683 | 0.354 |
| 61 | 0 | 1307 | 1298 | 417 | 0 | 856 | 167 | 105.765 | 0.152 |
| 65 神技「八方龍殺陣」 | 2 | 1051 | 1041 | 852 | 0 | 148 | 163 | 59.141 | 0.358 |
| 69 回霊「夢想封印　侘」 | 3 | 1389 | 1376 | 623 | 0 | 747 | 183 | 89.592 | 0.097 |
| 73 大結界「博麗弾幕結界」 | 1 | 1093 | 1076 | 606 | 0 | 463 | 179 | 106.213 | 0.028 |

## Interpretation

- Retained witnesses classify 11 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.730 ms median and 17.660 ms p95.
- The full enemy sensor produced 7340 snapshots; capture read time was `{'median': 5.632149986922741, 'p95': 21.469299972523004, 'max': 38.09230000479147}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 9.0}` frames, and 7 phase-counter discontinuities were excluded; 14607 decisions retained at least one robust-union body (maximum 59); 2976 decisions contained latent contact-disabled geometry (maximum 59), and 7323 contained bounded inactive-slot memory (maximum 53). 355 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.61761474609375, 'p95': 4.330047607421875, 'max': 15.16455078125}` / `{'median': 2.6335620880126953, 'p95': 3.8987674713134766, 'max': 64.58580017089844}` / `{'median': 0.006251811981201172, 'p95': 0.793304443359375, 'max': 64.58580017089844}`.
- The issue-time enemy guard retained 15009 observations, detected 2482 during-plan geometry changes, recertified 2482 decisions, and overrode 47 actions. Read/recertificate timing was `{'median': 1.6905000084079802, 'p95': 3.4192000166513026, 'max': 13.368000043556094}` / `{'median': 1.8722499953582883, 'p95': 3.5439999774098396, 'max': 12.760300014633685}` ms; 2974 issue captures contained latent bodies (maximum 59), and 7331 contained dormant bodies (maximum 53). Fresh/global transactions preserved 2435/2482 planned actions, relaxed 2 fresh/global empty intersections, inherited 11 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11616 observations (11569 contact enabled, 47 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 11616}`.
- The terminal-threat heuristic covered 15009 decisions with horizon counts `{'0': 76, '10': 13981, '32': 952}`; it reported 15 collision and 150 sub-safety-clearance warnings, and relaxed 142 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2373, '3': 11483, '4': 1153}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 9357, '3': 5181, '4': 458}`.
- Adaptive delay supports were `{'1,2': 150, '1,2,3': 110, '1,2,3,4': 290, '1,2,3,4,5': 44, '2,3': 1801, '2,3,4': 8509, '2,3,4,5': 3035, '2,3,4,5,6': 1068, '3,4': 2}`; 72 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 31/241.
- Robust viability supplied 14806 available policy queries (0 had new delay support outside the cached policy), constrained 7629 decisions, and exposed 7035 empty queried action sets. Recovery guidance was available/selected on 2098/1000 empty-kernel queries; distant-kernel guidance was available/selected on 3949/3823. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 11.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 97.32420048477151, 'p95': 314.350123270216, 'max': 502.41019097944263}`, and `{'median': 0.0, 'p95': 16.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2308, '1': 1859, '2': 1510, '3': 1833, '4': 1738, '5': 1882, '6': 1815, '7': 1861}`.
- Global-horizon/local-prefix cross-tab covered 9959 decisions: 2 had a winning global state but unsafe selected prefix, 4363 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 79 selected actions were outside the reported winning set. 1878 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1945 unique policies with solve-time statistics `{'median': 109.42320001777261, 'p95': 307.73450003471226, 'max': 389.73220001207665}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1804.0}`. Policy status counts were `{'pending_future_epoch': 88, 'queryable': 14806, 'expired': 32}`; 120 robust-mode decisions had no query.
- Of 7530 unambiguous output transitions, 7026 (0.933) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 20}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[5, 13, 4, 4, 14, 8, 24, 7, 5, 4, 6, 0, 5, 20, 13, 18, 7, 12, 9, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.379 during the 60 frames preceding a hit versus 0.145 outside those windows.
- Mean selected control-reserve deficit was 7.312 during the 60 frames preceding a hit versus 3.715 outside those windows.
- Soft recovery was selected on 0.028 of alive decisions in the 60-frame pre-hit windows versus 0.071 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
