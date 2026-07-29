# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260729_154229

## Scope And Integrity

- Valid practice scope: `2..42335` (11710 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 10, at `[10740, 13761, 20210, 23467, 24881, 27715, 28610, 31348, 39129, 39929]`.
- Hard no-Bomb verification: **PASS** across 11710 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F10740-T1`. It occurred during a nonspell phase at player (349.070, 383.773), with 883 bullets and 0 lasers. The projectile model reported pipeline clearance -13.264.

The primary class is `observed_enemy_body_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 4 |
| `observed_bullet_overlap` | 4 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 7
- `fast_mode`: 6
- `pool_density_over_1000`: 6

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 10740 | nonspell | (349.070, 383.773) | `up_fast` | 883/0 | -13.264/-15.574 | 2f/2f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13761 | nonspell | (372.000, 16.000) | `left_fast` | 621/0 | -2.922/-3.668 | 5f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20210 | nonspell | (339.562, 417.609) | `up_right` | 428/0 | -0.820/-0.820 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23467 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 1427/0 | -2.340/-2.340 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24881 | 103 幻波「赤眼催眠(マインドブローイング)」 | (372.985, 432.000) | `stay` | 1105/0 | -1.796/-1.796 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27715 | nonspell | (195.483, 432.000) | `up_fast` | 1104/0 | 1.442/0.313 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28610 | nonspell | (20.000, 432.000) | `up_right_fast` | 1079/0 | 1.990/-1.477 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31348 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (37.784, 432.000) | `stay` | 1000/0 | -8.540/-8.540 | 9f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39129 | 111 懶惰「生神停止(マインドストッパー)」 | (190.003, 199.281) | `right` | 367/0 | -1.354/-6.596 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39929 | 115 散符「真実の月(インビジブルフルムーン)」 | (118.081, 432.000) | `up_right_fast` | 1085/0 | -2.042/-2.042 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 7693 | 7563 | 5396 | 0 | 2124 | 1007 | 126.292 | 0.160 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 915 | 900 | 524 | 0 | 372 | 170 | 111.347 | 0.311 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 823 | 814 | 594 | 0 | 217 | 163 | 87.323 | 0.378 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1134 | 1122 | 668 | 0 | 444 | 177 | 92.832 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1145 | 1132 | 808 | 0 | 318 | 178 | 63.484 | 0.423 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.430 ms median and 23.615 ms p95.
- The full enemy sensor produced 6269 snapshots; capture read time was `{'median': 5.617899936623871, 'p95': 25.920799933373928, 'max': 58.76230006106198}`, snapshot age was `{'median': 5.0, 'p95': 7.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 10994 decisions retained at least one robust-union body (maximum 51); 4659 decisions contained latent contact-disabled geometry (maximum 51), and 5638 contained bounded inactive-slot memory (maximum 48). 127 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 0.990478515625, 'max': 1.6131057739257812}` / `{'median': 0.0, 'p95': 0.9904825687408447, 'max': 1.571380615234375}` / `{'median': 0.0, 'p95': 1.2099742889404297e-05, 'max': 0.428424072265625}`.
- The issue-time enemy guard retained 11710 observations, detected 2382 during-plan geometry changes, recertified 2382 decisions, and overrode 41 actions. Read/recertificate timing was `{'median': 1.8507500062696636, 'p95': 3.6578000290319324, 'max': 13.080199947580695}` / `{'median': 3.438949992414564, 'p95': 7.092799991369247, 'max': 26.13859996199608}` ms; 4637 issue captures contained latent bodies (maximum 51), and 5635 contained dormant bodies (maximum 48). Fresh/global transactions preserved 2341/2382 planned actions, relaxed 8 fresh/global empty intersections, inherited 11 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8271 observations (8243 contact enabled, 28 anticipatory, 0 errors). 8271 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8271}`.
- The terminal-threat heuristic covered 11710 decisions with horizon counts `{'0': 73, '10': 11358, '32': 279}`; it reported 2 collision and 64 sub-safety-clearance warnings, and relaxed 66 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 378, '3': 8522, '4': 1869, '5': 941}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 12, '2': 1243, '3': 8911, '4': 1501, '5': 43}`.
- Adaptive delay supports were `{'1,2,3': 172, '1,2,3,4': 91, '1,2,3,4,5,6': 12, '2,3': 494, '2,3,4': 1929, '2,3,4,5': 4610, '2,3,4,5,6': 3284, '3,4,5,6': 1118}`; 193 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 44/443.
- Robust viability supplied 11531 available policy queries (0 had new delay support outside the cached policy), constrained 3475 decisions, and exposed 7990 empty queried action sets. Recovery guidance was available/selected on 1032/428 empty-kernel queries; distant-kernel guidance was available/selected on 6212/5890. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 131.93938001976514, 'p95': 355.2576529787923, 'max': 532.8264257710948}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1836, '1': 1584, '2': 1206, '3': 1305, '4': 1423, '5': 1323, '6': 1460, '7': 1394}`.
- Global-horizon/local-prefix cross-tab covered 8059 decisions: 5 had a winning global state but unsafe selected prefix, 5295 had a losing global state but safe short prefix, 3 selected globally certified actions contradicted the fresh local prefix checker, and 34 selected actions were outside the reported winning set. 2099 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1695 unique policies with solve-time statistics `{'median': 105.34069989807904, 'p95': 345.77450004871935, 'max': 449.6381999924779}` and first-observed ages `{'median': 2.0, 'p95': 7.0, 'max': 1807.0}`. Policy status counts were `{'pending_future_epoch': 63, 'queryable': 11529, 'expired': 37}`; 98 robust-mode decisions had no query.
- Of 6097 unambiguous output transitions, 5212 (0.855) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 8 hit windows with a positive warning lead; those leads were `[2, 9, 0, 8, 8, 0, 6, 21, 9, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.405 during the 60 frames preceding a hit versus 0.187 outside those windows.
- Mean selected control-reserve deficit was 10.924 during the 60 frames preceding a hit versus 4.716 outside those windows.
- Soft recovery was selected on 0.010 of alive decisions in the 60-frame pre-hit windows versus 0.038 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
