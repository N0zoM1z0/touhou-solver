# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_212622

## Scope And Integrity

- Valid practice scope: `1..40984` (12100 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 9, at `[2038, 4202, 7998, 11923, 12768, 13735, 23000, 29569, 36025]`.
- Hard no-Bomb verification: **PASS** across 12100 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2038-T1`. It occurred during a nonspell phase at player (376.000, 422.343), with 723 bullets and 0 lasers. The projectile model reported pipeline clearance -2.493.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 4 |

Contributing factors:

- `fast_mode`: 7
- `playfield_boundary`: 6
- `corridor_deadline_miss`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2038 | nonspell | (376.000, 422.343) | `up_left_fast` | 723/0 | -2.493/-2.493 | 2f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4202 | nonspell | (335.324, 415.972) | `up_left_fast` | 384/0 | 1.444/-2.439 | 8f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7998 | nonspell | (138.985, 432.000) | `up_fast` | 781/0 | -2.682/-2.682 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11923 | nonspell | (371.400, 425.640) | `up_fast` | 368/0 | -3.764/-3.764 | 0f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12768 | nonspell | (190.407, 432.000) | `right_fast` | 125/0 | -1.042/-1.042 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13735 | nonspell | (369.059, 432.000) | `up_right_fast` | 370/0 | -6.582/-14.418 | 8f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23000 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 992/0 | -2.916/-2.916 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29569 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (169.148, 432.000) | `down_right` | 999/0 | -4.786/-6.036 | 10f/24f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36025 | 111 懶惰「生神停止(マインドストッパー)」 | (172.218, 188.842) | `up` | 348/0 | -3.001/-3.001 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 8002 | 7866 | 5352 | 0 | 2485 | 994 | 119.031 | 0.211 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 926 | 919 | 585 | 0 | 332 | 171 | 103.278 | 0.348 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 668 | 660 | 421 | 0 | 239 | 119 | 81.134 | 0.271 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1283 | 1276 | 592 | 0 | 672 | 180 | 78.476 | 0.000 |
| 115 | 0 | 1221 | 1204 | 926 | 0 | 269 | 182 | 54.522 | 0.538 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 10.430 ms median and 21.145 ms p95.
- The full enemy sensor produced 6182 snapshots; capture read time was `{'median': 5.750849959440529, 'p95': 24.991999962367117, 'max': 52.50649992376566}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 11415 decisions retained at least one robust-union body (maximum 41); 4627 decisions contained latent contact-disabled geometry (maximum 41), and 5654 contained bounded inactive-slot memory (maximum 39). 167 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.780120849609375, 'p95': 4.4199981689453125, 'max': 8.526130676269531}` / `{'median': 0.8765422701835632, 'p95': 4.327776908874512, 'max': 4.707539081573486}` / `{'median': 3.5762786865234375e-07, 'p95': 4.449994087219238, 'max': 6.693939447402954}`.
- The issue-time enemy guard retained 12100 observations, detected 2100 during-plan geometry changes, recertified 2100 decisions, and overrode 38 actions. Read/recertificate timing was `{'median': 1.7062500701285899, 'p95': 3.3174999989569187, 'max': 16.11680001951754}` / `{'median': 2.7929500211030245, 'p95': 5.912500084377825, 'max': 18.079600064083934}` ms; 4601 issue captures contained latent bodies (maximum 41), and 5667 contained dormant bodies (maximum 39). Fresh/global transactions preserved 2062/2100 planned actions, relaxed 9 fresh/global empty intersections, inherited 5 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8498 observations (8467 contact enabled, 31 anticipatory, 0 errors). 8498 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8498}`.
- The terminal-threat heuristic covered 12100 decisions with horizon counts `{'0': 74, '10': 11784, '32': 242}`; it reported 2 collision and 59 sub-safety-clearance warnings, and relaxed 52 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1040, '3': 9798, '4': 1073, '5': 189}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 14, '2': 5798, '3': 4940, '4': 1348}`.
- Adaptive delay supports were `{'1,2': 45, '1,2,3': 101, '1,2,3,4': 135, '1,2,3,4,5': 16, '2,3': 897, '2,3,4': 6023, '2,3,4,5': 2694, '2,3,4,5,6': 1499, '3,4': 3, '3,4,5': 160, '3,4,5,6': 527}`; 69 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 54/335.
- Robust viability supplied 11925 available policy queries (0 had new delay support outside the cached policy), constrained 3997 decisions, and exposed 7876 empty queried action sets. Recovery guidance was available/selected on 969/415 empty-kernel queries; distant-kernel guidance was available/selected on 6129/5850. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 136.7040599250805, 'p95': 353.45155254999236, 'max': 498.31716807671796}`, and `{'median': 0.0, 'p95': 21.09999942779541, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1880, '1': 1521, '2': 1263, '3': 1432, '4': 1414, '5': 1455, '6': 1491, '7': 1469}`.
- Global-horizon/local-prefix cross-tab covered 8595 decisions: 1 had a winning global state but unsafe selected prefix, 5657 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 26 selected actions were outside the reported winning set. 1849 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1646 unique policies with solve-time statistics `{'median': 97.23359998315573, 'p95': 314.4410999957472, 'max': 426.0435999603942}` and first-observed ages `{'median': 2.0, 'p95': 6.0, 'max': 1805.0}`. Policy status counts were `{'pending_future_epoch': 78, 'queryable': 11925, 'expired': 32}`; 110 robust-mode decisions had no query.
- Of 6373 unambiguous output transitions, 5823 (0.914) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 9}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[7, 13, 10, 16, 8, 13, 3, 24, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.439 during the 60 frames preceding a hit versus 0.235 outside those windows.
- Mean selected control-reserve deficit was 9.330 during the 60 frames preceding a hit versus 3.836 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.035 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 31.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
