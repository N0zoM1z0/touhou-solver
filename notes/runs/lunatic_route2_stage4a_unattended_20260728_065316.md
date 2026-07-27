# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_065316

## Scope And Integrity

- Valid practice scope: `2..43253` (13896 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 9, at `[1953, 4325, 8990, 9981, 11314, 12535, 37299, 37813, 42760]`.
- Hard no-Bomb verification: **PASS** across 13896 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1953-T1`. It occurred during a nonspell phase at player (157.274, 432.000), with 137 bullets and 0 lasers. The projectile model reported pipeline clearance -1.322.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 5 |
| `modeled_committed_prefix_collision` | 3 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 8
- `fast_mode`: 7
- `corridor_deadline_miss`: 2
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1953 | nonspell | (157.274, 432.000) | `right` | 137/0 | -1.322/-9.428 | 6f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4325 | nonspell | (66.310, 432.000) | `left_fast` | 1126/0 | 0.199/-5.838 | 4f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8990 | nonspell | (74.828, 432.000) | `up_fast` | 176/0 | -17.444/-26.850 | 3f/13f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9981 | nonspell | (167.611, 432.000) | `right_fast` | 161/0 | -35.107/-35.107 | 12f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11314 | 57 夢境「二重大結界」 | (43.974, 432.000) | `up_right_fast` | 586/0 | -1.767/-1.767 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12535 | 57 夢境「二重大結界」 | (10.828, 429.172) | `up_right_fast` | 601/0 | 1.821/-0.581 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37299 | 69 回霊「夢想封印　侘」 | (12.879, 432.000) | `down_right` | 713/0 | -1.930/-1.997 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37813 | 69 回霊「夢想封印　侘」 | (373.086, 397.938) | `down_fast` | 683/0 | -3.301/-3.301 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42760 | 73 大結界「博麗弾幕結界」 | (235.881, 407.515) | `down_left_fast` | 1348/0 | -2.137/-2.137 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 8023 | 7887 | 3592 | 0 | 4229 | 965 | 109.388 | 0.149 |
| 57 夢境「二重大結界」 | 2 | 1302 | 1294 | 309 | 0 | 977 | 181 | 155.536 | 0.312 |
| 61 | 0 | 1294 | 1286 | 391 | 0 | 876 | 167 | 122.604 | 0.101 |
| 65 | 0 | 767 | 757 | 675 | 0 | 82 | 120 | 58.314 | 0.408 |
| 69 回霊「夢想封印　侘」 | 2 | 1374 | 1360 | 654 | 0 | 701 | 179 | 82.662 | 0.097 |
| 73 大結界「博麗弾幕結界」 | 1 | 1136 | 1126 | 630 | 0 | 487 | 182 | 104.776 | 0.065 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.764 ms median and 17.910 ms p95.
- The full enemy sensor produced 6810 snapshots; capture read time was `{'median': 5.705799994757399, 'p95': 21.95570000912994, 'max': 50.07380002643913}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 5 phase-counter discontinuities were excluded; 13464 decisions retained at least one robust-union body (maximum 59); 2848 decisions contained latent contact-disabled geometry (maximum 59), and 6894 contained bounded inactive-slot memory (maximum 53). 149 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.95880126953125, 'p95': 4.135227203369141, 'max': 5.100006103515625}` / `{'median': 3.0118606090545654, 'p95': 4.210720062255859, 'max': 5.100006103515625}` / `{'median': 1.3828277587890625e-05, 'p95': 2.20001220703125, 'max': 3.9998773336410522}`.
- The issue-time enemy guard retained 13896 observations, detected 2207 during-plan geometry changes, recertified 2207 decisions, and overrode 37 actions. Read/recertificate timing was `{'median': 1.7015500052366406, 'p95': 3.3854999928735197, 'max': 18.65070004714653}` / `{'median': 1.8906000186689198, 'p95': 3.56919999467209, 'max': 12.268599995877594}` ms; 2847 issue captures contained latent bodies (maximum 59), and 6902 contained dormant bodies (maximum 53). Fresh/global transactions preserved 2170/2207 planned actions, relaxed 1 fresh/global empty intersections, inherited 10 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 10555 observations (10508 contact enabled, 47 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4606, '0x0059C9D0': 5949}`.
- The terminal-threat heuristic covered 13896 decisions with horizon counts `{'0': 75, '10': 12897, '32': 924}`; it reported 17 collision and 146 sub-safety-clearance warnings, and relaxed 107 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2536, '3': 10299, '4': 1060, '5': 1}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 8909, '3': 4540, '4': 434}`.
- Adaptive delay supports were `{'1,2': 38, '1,2,3': 223, '1,2,3,4': 49, '1,2,3,4,5': 36, '2': 8, '2,3': 2022, '2,3,4': 7881, '2,3,4,5': 2589, '2,3,4,5,6': 1045, '3,4': 2, '3,4,5,6': 1, '4,5,6': 2}`; 58 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 15/117.
- Robust viability supplied 13710 available policy queries (0 had new delay support outside the cached policy), constrained 7352 decisions, and exposed 6251 empty queried action sets. Recovery guidance was available/selected on 1842/809 empty-kernel queries; distant-kernel guidance was available/selected on 3702/3575. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 13.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 96.0, 'p95': 323.9753077010654, 'max': 524.8390229394153}`, and `{'median': 0.0, 'p95': 16.0, 'max': 39.16185998916626}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2132, '1': 1712, '2': 1435, '3': 1654, '4': 1645, '5': 1723, '6': 1712, '7': 1697}`.
- Global-horizon/local-prefix cross-tab covered 10271 decisions: 2 had a winning global state but unsafe selected prefix, 4428 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 70 selected actions were outside the reported winning set. 1941 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1794 unique policies with solve-time statistics `{'median': 108.41279997839592, 'p95': 310.5690999655053, 'max': 391.09190000453964}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1796.0}`. Policy status counts were `{'pending_future_epoch': 75, 'queryable': 13711, 'expired': 19}`; 95 robust-mode decisions had no query.
- Of 6988 unambiguous output transitions, 6535 (0.935) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 9}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[13, 10, 13, 19, 4, 5, 6, 8, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.465 during the 60 frames preceding a hit versus 0.157 outside those windows.
- Mean selected control-reserve deficit was 7.714 during the 60 frames preceding a hit versus 3.586 outside those windows.
- Soft recovery was selected on 0.106 of alive decisions in the 60-frame pre-hit windows versus 0.057 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 35.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
