# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_055104

## Scope And Integrity

- Valid practice scope: `2..45092` (14643 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 13, at `[1487, 2360, 4491, 8991, 10451, 11611, 12215, 12803, 13822, 21964, 22714, 27323, 31202]`.
- Hard no-Bomb verification: **PASS** across 14643 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1487-T1`. It occurred during a nonspell phase at player (372.723, 429.172), with 263 bullets and 0 lasers. The projectile model reported pipeline clearance -2.782.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 6 |
| `modeled_committed_prefix_collision` | 5 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 12
- `fast_mode`: 10
- `corridor_deadline_miss`: 3
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1487 | nonspell | (372.723, 429.172) | `up_fast` | 263/0 | -2.782/-2.782 | 2f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2360 | nonspell | (372.747, 428.747) | `left` | 191/0 | -1.763/-1.763 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4491 | nonspell | (15.983, 426.343) | `up_right_fast` | 892/0 | 2.723/-1.451 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8991 | nonspell | (120.772, 432.000) | `down_right` | 174/0 | -24.697/-24.697 | 7f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10451 | nonspell | (55.410, 432.000) | `right_fast` | 178/0 | 3.705/-19.467 | 6f/13f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11611 | 57 夢境「二重大結界」 | (11.106, 428.000) | `up_right_fast` | 614/0 | -1.771/-1.771 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12215 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 608/0 | -1.455/-1.455 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12803 | 57 夢境「二重大結界」 | (373.172, 425.172) | `up_fast` | 607/0 | 1.417/-0.594 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13822 | 57 夢境「二重大結界」 | (367.121, 432.000) | `up_fast` | 584/0 | -0.078/-1.194 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21964 | nonspell | (8.000, 425.172) | `down_right_fast` | 800/0 | -1.393/-18.910 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22714 | nonspell | (8.000, 432.000) | `up` | 836/0 | -2.133/-2.133 | 8f/27f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27323 | nonspell | (376.000, 71.258) | `down_left_fast` | 146/0 | -19.336/-20.311 | 8f/13f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31202 | 65 神技「八方龍殺陣」 | (135.328, 432.000) | `right_fast` | 1266/0 | -10.618/-24.388 | 11f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 8636 | 8479 | 4272 | 0 | 4153 | 1042 | 104.444 | 0.172 |
| 57 夢境「二重大結界」 | 4 | 1339 | 1331 | 285 | 0 | 1025 | 185 | 158.581 | 0.367 |
| 61 | 0 | 1289 | 1281 | 391 | 0 | 871 | 166 | 116.807 | 0.126 |
| 65 神技「八方龍殺陣」 | 1 | 1023 | 1013 | 845 | 0 | 134 | 161 | 57.009 | 0.476 |
| 69 | 0 | 1273 | 1265 | 819 | 0 | 436 | 177 | 80.177 | 0.103 |
| 73 | 0 | 1083 | 1066 | 640 | 0 | 419 | 177 | 102.141 | 0.030 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.700 ms median and 17.506 ms p95.
- The full enemy sensor produced 7150 snapshots; capture read time was `{'median': 5.622149968985468, 'p95': 21.740500000305474, 'max': 42.59720002301037}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 7 phase-counter discontinuities were excluded; 14245 decisions retained at least one robust-union body (maximum 49); 2944 decisions contained latent contact-disabled geometry (maximum 49), and 7494 contained bounded inactive-slot memory (maximum 36). 239 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.748030662536621, 'p95': 4.08245849609375, 'max': 15.057200113932291}` / `{'median': 2.7978734970092773, 'p95': 3.9229540824890137, 'max': 14.883148193359375}` / `{'median': 0.35997772216796875, 'p95': 2.7599945068359375, 'max': 7.943432569503784}`.
- The issue-time enemy guard retained 14643 observations, detected 2361 during-plan geometry changes, recertified 2361 decisions, and overrode 60 actions. Read/recertificate timing was `{'median': 1.7151999636553228, 'p95': 3.4853999968618155, 'max': 13.852300005964935}` / `{'median': 1.8890000064857304, 'p95': 3.642600029706955, 'max': 10.978500009514391}` ms; 2944 issue captures contained latent bodies (maximum 49), and 7506 contained dormant bodies (maximum 36). Fresh/global transactions preserved 2301/2361 planned actions, relaxed 2 fresh/global empty intersections, inherited 16 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11259 observations (11212 contact enabled, 47 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 11259}`.
- The terminal-threat heuristic covered 14643 decisions with horizon counts `{'0': 74, '10': 13593, '32': 976}`; it reported 23 collision and 170 sub-safety-clearance warnings, and relaxed 145 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2266, '3': 11269, '4': 1108}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 27, '2': 8714, '3': 5580, '4': 322}`.
- Adaptive delay supports were `{'1,2': 116, '1,2,3': 71, '1,2,3,4': 265, '2,3': 1619, '2,3,4': 8799, '2,3,4,5': 2780, '2,3,4,5,6': 965, '3,4': 28}`; 83 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 59/388.
- Robust viability supplied 14435 available policy queries (0 had new delay support outside the cached policy), constrained 7038 decisions, and exposed 7252 empty queried action sets. Recovery guidance was available/selected on 1892/845 empty-kernel queries; distant-kernel guidance was available/selected on 4416/4294. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 7.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 97.32420048477151, 'p95': 300.61270764889497, 'max': 483.7189266505912}`, and `{'median': 0.0, 'p95': 15.25360369682312, 'max': 45.17157292366028}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2243, '1': 1797, '2': 1526, '3': 1726, '4': 1748, '5': 1776, '6': 1831, '7': 1788}`.
- Global-horizon/local-prefix cross-tab covered 10387 decisions: 1 had a winning global state but unsafe selected prefix, 4997 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 68 selected actions were outside the reported winning set. 2012 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1908 unique policies with solve-time statistics `{'median': 103.78954996122047, 'p95': 308.661499992013, 'max': 408.3797999774106}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1803.0}`. Policy status counts were `{'pending_future_epoch': 72, 'queryable': 14433, 'expired': 42}`; 112 robust-mode decisions had no query.
- Of 7603 unambiguous output transitions, 7079 (0.931) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 13}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[3, 4, 6, 15, 13, 3, 4, 4, 6, 5, 27, 13, 16]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.436 during the 60 frames preceding a hit versus 0.177 outside those windows.
- Mean selected control-reserve deficit was 10.970 during the 60 frames preceding a hit versus 3.544 outside those windows.
- Soft recovery was selected on 0.094 of alive decisions in the 60-frame pre-hit windows versus 0.060 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 20.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
