# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_121028

## Scope And Integrity

- Valid practice scope: `1..44270` (14066 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 10, at `[4280, 11544, 12158, 12645, 13476, 22354, 22941, 37188, 38358, 43150]`.
- Hard no-Bomb verification: **PASS** across 14066 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F4280-T1`. It occurred during a nonspell phase at player (371.121, 432.000), with 990 bullets and 0 lasers. The projectile model reported pipeline clearance -2.666.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 3 |

Contributing factors:

- `fast_mode`: 8
- `playfield_boundary`: 8
- `corridor_deadline_miss`: 2
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4280 | nonspell | (371.121, 432.000) | `up_left` | 990/0 | -2.666/-4.865 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11544 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 607/0 | -1.456/-1.456 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12158 | 57 夢境「二重大結界」 | (376.000, 422.521) | `up_left_fast` | 583/0 | -2.220/-2.220 | 3f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12645 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left` | 606/0 | -1.074/-1.074 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13476 | 57 夢境「二重大結界」 | (376.000, 424.000) | `up_left_fast` | 588/0 | -2.217/-2.217 | 3f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22354 | nonspell | (8.075, 432.000) | `up_right_fast` | 815/0 | -2.696/-15.294 | 0f/27f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22941 | nonspell | (19.442, 429.158) | `right_fast` | 565/0 | 2.363/-17.648 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37188 | 69 回霊「夢想封印　侘」 | (376.000, 391.446) | `left_fast` | 496/0 | -2.194/-2.194 | 2f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38358 | 69 回霊「夢想封印　侘」 | (12.953, 425.379) | `up_right_fast` | 670/0 | -3.093/-3.093 | 7f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43150 | 73 大結界「博麗弾幕結界」 | (51.910, 203.104) | `up_left_fast` | 1354/0 | 1.025/-1.891 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 8403 | 8266 | 4056 | 0 | 4119 | 1034 | 107.389 | 0.140 |
| 57 夢境「二重大結界」 | 4 | 1305 | 1296 | 258 | 0 | 1018 | 183 | 168.143 | 0.262 |
| 61 | 0 | 1257 | 1251 | 388 | 0 | 849 | 166 | 116.105 | 0.113 |
| 65 | 0 | 686 | 676 | 528 | 0 | 148 | 108 | 59.664 | 0.446 |
| 69 回霊「夢想封印　侘」 | 2 | 1315 | 1307 | 666 | 0 | 631 | 179 | 92.045 | 0.119 |
| 73 大結界「博麗弾幕結界」 | 1 | 1100 | 1088 | 668 | 0 | 418 | 180 | 108.131 | 0.000 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 10.137 ms median and 18.734 ms p95.
- The full enemy sensor produced 6967 snapshots; capture read time was `{'median': 6.510000035632402, 'p95': 24.066300014965236, 'max': 51.57280003186315}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 6 phase-counter discontinuities were excluded; 13680 decisions retained at least one robust-union body (maximum 61); 2891 decisions contained latent contact-disabled geometry (maximum 52), and 7464 contained bounded inactive-slot memory (maximum 41). 78 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.4693336486816406, 'p95': 4.5213775634765625, 'max': 5.954595565795898}` / `{'median': 2.440371513366699, 'p95': 3.898773431777954, 'max': 4.100006103515625}` / `{'median': 0.6436854749917984, 'p95': 3.942972183227539, 'max': 8.20001220703125}`.
- The issue-time enemy guard retained 14066 observations, detected 2639 during-plan geometry changes, recertified 2639 decisions, and overrode 33 actions. Read/recertificate timing was `{'median': 1.754899974912405, 'p95': 3.533200011588633, 'max': 14.484299987088889}` / `{'median': 1.94089999422431, 'p95': 3.750199975911528, 'max': 15.699799987487495}` ms; 2896 issue captures contained latent bodies (maximum 52), and 7465 contained dormant bodies (maximum 41). Fresh/global transactions preserved 2606/2639 planned actions, relaxed 1 fresh/global empty intersections, inherited 24 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 10769 observations (10724 contact enabled, 45 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4951, '0x00597600': 5818}`.
- The terminal-threat heuristic covered 14066 decisions with horizon counts `{'0': 72, '10': 13021, '32': 973}`; it reported 14 collision and 165 sub-safety-clearance warnings, and relaxed 137 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 953, '3': 12067, '4': 1046}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 27, '2': 7403, '3': 6129, '4': 507}`.
- Adaptive delay supports were `{'1,2': 57, '1,2,3': 86, '1,2,3,4': 204, '1,2,3,4,5,6': 14, '2,3': 1455, '2,3,4': 7530, '2,3,4,5': 3530, '2,3,4,5,6': 1183, '3,4': 7}`; 59 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 19/126.
- Robust viability supplied 13884 available policy queries (0 had new delay support outside the cached policy), constrained 7183 decisions, and exposed 6564 empty queried action sets. Recovery guidance was available/selected on 1869/864 empty-kernel queries; distant-kernel guidance was available/selected on 4004/3872. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 10.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 97.32420048477151, 'p95': 307.34996339677673, 'max': 510.2469990112632}`, and `{'median': 0.0, 'p95': 16.0, 'max': 45.17157292366028}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2196, '1': 1769, '2': 1418, '3': 1696, '4': 1639, '5': 1711, '6': 1685, '7': 1770}`.
- Global-horizon/local-prefix cross-tab covered 9903 decisions: 0 had a winning global state but unsafe selected prefix, 4420 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 71 selected actions were outside the reported winning set. 2369 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1850 unique policies with solve-time statistics `{'median': 109.2874500027392, 'p95': 318.65420000394806, 'max': 423.66129998117685}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1805.0}`. Policy status counts were `{'pending_future_epoch': 78, 'queryable': 13886, 'expired': 25}`; 105 robust-mode decisions had no query.
- Of 7172 unambiguous output transitions, 6722 (0.937) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[4, 4, 5, 10, 5, 27, 4, 22, 10, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.444 during the 60 frames preceding a hit versus 0.144 outside those windows.
- Mean selected control-reserve deficit was 14.037 during the 60 frames preceding a hit versus 3.719 outside those windows.
- Soft recovery was selected on 0.115 of alive decisions in the 60-frame pre-hit windows versus 0.061 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 6.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
