# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_155426

## Scope And Integrity

- Valid practice scope: `1..41612` (11891 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 11, at `[2390, 4436, 12368, 12919, 23153, 24643, 27470, 29835, 30268, 37507, 40084]`.
- Hard no-Bomb verification: **PASS** across 11891 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2390-T1`. It occurred during a nonspell phase at player (8.000, 432.000), with 432 bullets and 0 lasers. The projectile model reported pipeline clearance -2.344.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 3 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 9
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2390 | nonspell | (8.000, 432.000) | `up_fast` | 432/0 | -2.344/-2.344 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4436 | nonspell | (343.690, 432.000) | `left_fast` | 367/0 | -2.768/-33.828 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12368 | nonspell | (370.343, 342.652) | `down_left_fast` | 300/0 | -2.078/-2.078 | 4f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12919 | nonspell | (371.121, 432.000) | `up_left` | 340/0 | -1.234/-1.234 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23153 | 103 幻波「赤眼催眠(マインドブローイング)」 | (171.691, 432.000) | `up_right_fast` | 872/0 | -1.391/-2.360 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24643 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 1107/0 | -2.769/-2.769 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27470 | nonspell | (168.435, 428.747) | `up_left_fast` | 1030/0 | -0.955/-2.996 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29835 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (271.861, 432.000) | `down_right` | 1009/0 | -4.924/-6.850 | 8f/49f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30268 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (205.011, 432.000) | `up_right_fast` | 1021/0 | -6.360/-6.360 | 5f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37507 | 111 懶惰「生神停止(マインドストッパー)」 | (189.544, 26.480) | `up_left_fast` | 509/0 | -1.417/-1.535 | 3f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40084 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 432.000) | `up_fast` | 1294/0 | -2.067/-2.067 | 4f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 8014 | 7885 | 5620 | 0 | 2225 | 1031 | 113.399 | 0.190 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 853 | 846 | 366 | 0 | 478 | 148 | 121.072 | 0.234 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 704 | 694 | 465 | 0 | 220 | 135 | 83.574 | 0.293 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1152 | 1141 | 591 | 0 | 544 | 177 | 86.050 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1168 | 1158 | 741 | 0 | 410 | 181 | 60.039 | 0.465 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 10.952 ms median and 21.798 ms p95.
- The full enemy sensor produced 6138 snapshots; capture read time was `{'median': 5.931199993938208, 'p95': 25.118099991232157, 'max': 62.599699944257736}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 13.0}` frames, and 7 phase-counter discontinuities were excluded; 11165 decisions retained at least one robust-union body (maximum 44); 4672 decisions contained latent contact-disabled geometry (maximum 44), and 5726 contained bounded inactive-slot memory (maximum 41). 140 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 1.6898492986505682, 'max': 2.8519954681396484}` / `{'median': 0.0, 'p95': 1.8004505634307861, 'max': 2.8519957065582275}` / `{'median': 0.0, 'p95': 1.7913442850112915, 'max': 3.9217867070978336}`.
- The issue-time enemy guard retained 11891 observations, detected 2189 during-plan geometry changes, recertified 2189 decisions, and overrode 36 actions. Read/recertificate timing was `{'median': 1.7775000305846334, 'p95': 3.5004999954253435, 'max': 22.966000018641353}` / `{'median': 2.9223000165075064, 'p95': 6.439300021156669, 'max': 13.944300008006394}` ms; 4650 issue captures contained latent bodies (maximum 44), and 5726 contained dormant bodies (maximum 41). Fresh/global transactions preserved 2153/2189 planned actions, relaxed 8 fresh/global empty intersections, inherited 9 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8338 observations (8309 contact enabled, 29 anticipatory, 0 errors). 8338 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8338}`.
- The terminal-threat heuristic covered 11891 decisions with horizon counts `{'0': 71, '10': 11609, '32': 211}`; it reported 11 collision and 61 sub-safety-clearance warnings, and relaxed 64 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 606, '3': 9229, '4': 1598, '5': 458}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 3521, '3': 7106, '4': 1251}`.
- Adaptive delay supports were `{'1,2,3': 305, '1,2,3,4': 7, '2,3': 810, '2,3,4': 5013, '2,3,4,5': 3341, '2,3,4,5,6': 1852, '3,4,5': 1, '3,4,5,6': 561, '4,5,6': 1}`; 149 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 55/373.
- Robust viability supplied 11724 available policy queries (0 had new delay support outside the cached policy), constrained 3877 decisions, and exposed 7783 empty queried action sets. Recovery guidance was available/selected on 972/416 empty-kernel queries; distant-kernel guidance was available/selected on 6146/5860. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 128.9961239727768, 'p95': 351.2719744016024, 'max': 520.430590953299}`, and `{'median': 0.0, 'p95': 20.0, 'max': 45.85926365852356}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1857, '1': 1588, '2': 1173, '3': 1393, '4': 1394, '5': 1431, '6': 1419, '7': 1469}`.
- Global-horizon/local-prefix cross-tab covered 8201 decisions: 0 had a winning global state but unsafe selected prefix, 5484 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 30 selected actions were outside the reported winning set. 1865 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1672 unique policies with solve-time statistics `{'median': 98.1049999827519, 'p95': 326.9346999004483, 'max': 449.384699924849}` and first-observed ages `{'median': 2.0, 'p95': 6.0, 'max': 1806.0}`. Policy status counts were `{'pending_future_epoch': 70, 'queryable': 11726, 'expired': 36}`; 108 robust-mode decisions had no query.
- Of 6198 unambiguous output transitions, 5586 (0.901) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 11}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 11 hit windows with a positive warning lead; those leads were `[4, 7, 9, 5, 5, 4, 7, 49, 13, 5, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.390 during the 60 frames preceding a hit versus 0.202 outside those windows.
- Mean selected control-reserve deficit was 10.169 during the 60 frames preceding a hit versus 3.741 outside those windows.
- Soft recovery was selected on 0.017 of alive decisions in the 60-frame pre-hit windows versus 0.037 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
