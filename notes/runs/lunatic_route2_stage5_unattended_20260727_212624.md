# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260727_212624

## Scope And Integrity

- Valid practice scope: `2..41508` (12770 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 8, at `[11504, 11936, 12952, 13466, 24394, 30393, 31143, 41238]`.
- Hard no-Bomb verification: **PASS** across 12770 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F11504-T1`. It occurred during a nonspell phase at player (376.000, 296.471), with 257 bullets and 0 lasers. The projectile model reported pipeline clearance 0.182.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 3 |

Contributing factors:

- `fast_mode`: 8
- `playfield_boundary`: 7
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 11504 | nonspell | (376.000, 296.471) | `up_left_fast` | 257/0 | 0.182/-1.314 | 2f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11936 | nonspell | (372.747, 421.113) | `right_fast` | 304/0 | 0.180/-10.431 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12952 | nonspell | (376.000, 28.000) | `down_fast` | 469/0 | -3.247/-20.570 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13466 | nonspell | (340.790, 432.000) | `up_fast` | 469/0 | -4.843/-4.843 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24394 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 1125/0 | -1.803/-1.803 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30393 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (158.728, 432.000) | `up_right_fast` | 1004/0 | -4.646/-4.646 | 4f/48f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31143 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (217.577, 312.541) | `down_left_fast` | 1006/0 | -4.763/-7.541 | 11f/70f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41238 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 432.000) | `up_fast` | 1298/0 | -0.650/-0.650 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 8220 | 8089 | 5988 | 0 | 2065 | 1036 | 105.322 | 0.191 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 1319 | 1305 | 886 | 0 | 417 | 180 | 105.111 | 0.315 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 768 | 760 | 515 | 0 | 236 | 138 | 82.054 | 0.326 |
| 111 | 0 | 1042 | 1030 | 590 | 0 | 436 | 154 | 77.309 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1421 | 1404 | 1130 | 0 | 266 | 183 | 57.103 | 0.518 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 10.332 ms median and 20.529 ms p95.
- The full enemy sensor produced 6375 snapshots; capture read time was `{'median': 5.175400001462549, 'p95': 22.185000008903444, 'max': 49.167599994689226}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 11.0}` frames, and 7 phase-counter discontinuities were excluded; 12155 decisions retained at least one robust-union body (maximum 42); 5124 decisions contained latent contact-disabled geometry (maximum 41), and 6536 contained bounded inactive-slot memory (maximum 41). 149 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.0, 'p95': 4.5343017578125, 'max': 5.019969940185547}` / `{'median': 1.0, 'p95': 4.534304618835449, 'max': 4.707547187805176}` / `{'median': 0.0, 'p95': 0.9999942779541016, 'max': 1.0000038146972656}`.
- The issue-time enemy guard retained 12770 observations, detected 2281 during-plan geometry changes, recertified 2281 decisions, and overrode 40 actions. Read/recertificate timing was `{'median': 1.7531000194139779, 'p95': 3.5018999478779733, 'max': 12.451999995391816}` / `{'median': 2.179899951443076, 'p95': 5.626099999062717, 'max': 14.065399998798966}` ms; 5078 issue captures contained latent bodies (maximum 41), and 6533 contained dormant bodies (maximum 41). Fresh/global transactions preserved 2241/2281 planned actions, relaxed 7 fresh/global empty intersections, inherited 12 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9111 observations (9078 contact enabled, 33 anticipatory, 0 errors). 9111 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9111}`.
- The terminal-threat heuristic covered 12770 decisions with horizon counts `{'0': 74, '10': 12397, '32': 299}`; it reported 2 collision and 104 sub-safety-clearance warnings, and relaxed 59 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1678, '3': 10623, '4': 469}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 46, '2': 5429, '3': 6912, '4': 383}`.
- Adaptive delay supports were `{'1,2': 175, '1,2,3': 68, '1,2,3,4': 90, '1,2,3,4,5': 16, '1,2,3,4,5,6': 11, '2': 80, '2,3': 1621, '2,3,4': 6901, '2,3,4,5': 2569, '2,3,4,5,6': 899, '3,4,5,6': 339, '4,5,6': 1}`; 64 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 35/317.
- Robust viability supplied 12588 available policy queries (0 had new delay support outside the cached policy), constrained 3420 decisions, and exposed 9109 empty queried action sets. Recovery guidance was available/selected on 1110/498 empty-kernel queries; distant-kernel guidance was available/selected on 7008/6737. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 144.0, 'p95': 320.3997503120126, 'max': 512.2499389946279}`, and `{'median': 0.0, 'p95': 19.575735330581665, 'max': 43.16202735900879}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2016, '1': 1606, '2': 1237, '3': 1573, '4': 1515, '5': 1510, '6': 1617, '7': 1514}`.
- Global-horizon/local-prefix cross-tab covered 9345 decisions: 1 had a winning global state but unsafe selected prefix, 6652 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 31 selected actions were outside the reported winning set. 2001 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1691 unique policies with solve-time statistics `{'median': 90.24250000948086, 'p95': 304.32660004589707, 'max': 435.8172000502236}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1792.0}`. Policy status counts were `{'pending_future_epoch': 69, 'queryable': 12587, 'expired': 22}`; 90 robust-mode decisions had no query.
- Of 6977 unambiguous output transitions, 6332 (0.908) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 8}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 8 hit windows with a positive warning lead; those leads were `[9, 6, 8, 4, 5, 48, 70, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.328 during the 60 frames preceding a hit versus 0.229 outside those windows.
- Mean selected control-reserve deficit was 9.330 during the 60 frames preceding a hit versus 3.898 outside those windows.
- Soft recovery was selected on 0.086 of alive decisions in the 60-frame pre-hit windows versus 0.040 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 24.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
