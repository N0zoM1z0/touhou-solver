# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260729_104222

## Scope And Integrity

- Valid practice scope: `1..40304` (11058 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 11, at `[11807, 13702, 28903, 32866, 33731, 34907, 35637, 36078, 36798, 38114, 39160]`.
- Hard no-Bomb verification: **PASS** across 11058 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F11807-T1`. It occurred during a nonspell phase at player (376.000, 428.747), with 382 bullets and 0 lasers. The projectile model reported pipeline clearance -2.517.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 7 |
| `modeled_committed_prefix_collision` | 4 |

Contributing factors:

- `playfield_boundary`: 7
- `fast_mode`: 5
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 11807 | nonspell | (376.000, 428.747) | `up_right` | 382/0 | -2.517/-2.663 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13702 | nonspell | (26.917, 429.700) | `up_right` | 162/0 | -1.158/-19.398 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28903 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (54.960, 432.000) | `right` | 997/0 | -5.462/-5.462 | 15f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32866 | nonspell | (8.000, 432.000) | `right_fast` | 509/0 | -2.619/-2.619 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33731 | nonspell | (8.000, 432.000) | `down_right_fast` | 398/0 | -2.824/-2.824 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34907 | 111 懶惰「生神停止(マインドストッパー)」 | (186.740, 205.905) | `left` | 379/0 | -1.952/-1.952 | 5f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35637 | 111 懶惰「生神停止(マインドストッパー)」 | (195.118, 196.713) | `up_fast` | 350/0 | -0.161/-0.161 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36078 | 111 懶惰「生神停止(マインドストッパー)」 | (187.299, 198.114) | `up_right` | 335/0 | -1.702/-6.505 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36798 | 111 懶惰「生神停止(マインドストッパー)」 | (211.224, 193.406) | `stay` | 341/0 | -2.366/-2.366 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38114 | 115 散符「真実の月(インビジブルフルムーン)」 | (369.183, 429.172) | `up_right_fast` | 1161/0 | -0.133/-14.095 | 6f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39160 | 115 散符「真実の月(インビジブルフルムーン)」 | (134.031, 428.747) | `up_right_fast` | 1081/0 | -0.343/-14.071 | 4f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 7210 | 7088 | 4847 | 0 | 2210 | 931 | 119.499 | 0.173 |
| 103 | 0 | 818 | 808 | 640 | 0 | 164 | 171 | 107.309 | 0.350 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 640 | 630 | 409 | 0 | 217 | 125 | 85.151 | 0.236 |
| 111 懶惰「生神停止(マインドストッパー)」 | 4 | 1205 | 1192 | 365 | 0 | 815 | 173 | 116.262 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1185 | 1170 | 643 | 0 | 524 | 180 | 62.760 | 0.394 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.104 ms median and 23.160 ms p95.
- The full enemy sensor produced 5848 snapshots; capture read time was `{'median': 6.004749971907586, 'p95': 26.050399988889694, 'max': 56.49210000410676}`, snapshot age was `{'median': 5.0, 'p95': 7.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 10315 decisions retained at least one robust-union body (maximum 41); 4277 decisions contained latent contact-disabled geometry (maximum 40), and 5212 contained bounded inactive-slot memory (maximum 40). 166 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 1.719024658203125, 'max': 1.99444580078125}` / `{'median': 0.0, 'p95': 1.719030737876892, 'max': 2.545360565185547}` / `{'median': 0.0, 'p95': 0.9999847412109375, 'max': 1.9798939228057861}`.
- The issue-time enemy guard retained 11058 observations, detected 2124 during-plan geometry changes, recertified 2124 decisions, and overrode 32 actions. Read/recertificate timing was `{'median': 1.7913500196300447, 'p95': 3.393899998627603, 'max': 16.206600004807115}` / `{'median': 3.0240999767556787, 'p95': 6.835999898612499, 'max': 18.195999902673066}` ms; 4248 issue captures contained latent bodies (maximum 40), and 5222 contained dormant bodies (maximum 40). Fresh/global transactions preserved 2092/2124 planned actions, relaxed 10 fresh/global empty intersections, inherited 11 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 7574 observations (7547 contact enabled, 27 anticipatory, 0 errors). 7574 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 7574}`.
- The terminal-threat heuristic covered 11058 decisions with horizon counts `{'0': 67, '10': 10798, '32': 193}`; it reported 0 collision and 39 sub-safety-clearance warnings, and relaxed 54 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 460, '3': 8798, '4': 966, '5': 834}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1858, '3': 8253, '4': 719, '5': 228}`.
- Adaptive delay supports were `{'1,2,3': 149, '1,2,3,4': 74, '1,2,3,4,5': 6, '2,3': 573, '2,3,4': 3218, '2,3,4,5': 4554, '2,3,4,5,6': 1700, '3,4': 16, '3,4,5,6': 767, '4,5,6': 1}`; 162 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 31/259.
- Robust viability supplied 10888 available policy queries (0 had new delay support outside the cached policy), constrained 3930 decisions, and exposed 6904 empty queried action sets. Recovery guidance was available/selected on 883/359 empty-kernel queries; distant-kernel guidance was available/selected on 5384/5057. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 128.9961239727768, 'p95': 355.2576529787923, 'max': 487.6720209321015}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1739, '1': 1432, '2': 1120, '3': 1284, '4': 1288, '5': 1300, '6': 1351, '7': 1374}`.
- Global-horizon/local-prefix cross-tab covered 7399 decisions: 1 had a winning global state but unsafe selected prefix, 4710 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 15 selected actions were outside the reported winning set. 1855 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1580 unique policies with solve-time statistics `{'median': 103.73770003207028, 'p95': 346.85309999622405, 'max': 453.0893999617547}` and first-observed ages `{'median': 2.0, 'p95': 7.0, 'max': 1807.0}`. Policy status counts were `{'pending_future_epoch': 68, 'queryable': 10889, 'expired': 26}`; 95 robust-mode decisions had no query.
- Of 5701 unambiguous output transitions, 5049 (0.886) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 11}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 11 hit windows with a positive warning lead; those leads were `[4, 5, 22, 10, 5, 16, 4, 6, 7, 8, 12]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.475 during the 60 frames preceding a hit versus 0.193 outside those windows.
- Mean selected control-reserve deficit was 7.476 during the 60 frames preceding a hit versus 4.133 outside those windows.
- Soft recovery was selected on 0.004 of alive decisions in the 60-frame pre-hit windows versus 0.031 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
