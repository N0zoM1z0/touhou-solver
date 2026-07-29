# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260729_120859

## Scope And Integrity

- Valid practice scope: `2..42725` (11746 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 14, at `[1914, 12187, 12932, 21655, 23183, 29331, 29918, 30222, 30597, 31062, 36152, 37155, 37921, 41408]`.
- Hard no-Bomb verification: **PASS** across 11746 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1914-T1`. It occurred during a nonspell phase at player (376.000, 55.815), with 633 bullets and 0 lasers. The projectile model reported pipeline clearance -2.654.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 4 |

Contributing factors:

- `fast_mode`: 13
- `playfield_boundary`: 8
- `pool_density_over_1000`: 5
- `corridor_deadline_miss`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1914 | nonspell | (376.000, 55.815) | `up_right_fast` | 633/0 | -2.654/-2.654 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12187 | nonspell | (370.343, 426.343) | `up_left_fast` | 371/0 | -2.522/-2.522 | 6f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12932 | nonspell | (336.000, 432.000) | `left_fast` | 166/0 | -1.469/-8.675 | 5f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21655 | nonspell | (13.657, 426.343) | `up_right_fast` | 415/0 | 0.661/-2.661 | 2f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23183 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 994/0 | -2.147/-2.147 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29331 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (128.069, 432.000) | `up_left_fast` | 970/0 | -7.424/-7.424 | 13f/49f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29918 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (206.265, 324.203) | `right_fast` | 1015/0 | -7.144/-8.355 | 34f/105f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30222 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (208.055, 427.121) | `up_right` | 1015/0 | -3.295/-8.170 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 30597 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (268.175, 432.000) | `left_fast` | 1013/0 | -7.079/-7.205 | 25f/75f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31062 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (203.533, 432.000) | `left_fast` | 1018/0 | -9.287/-9.287 | 21f/32f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36152 | nonspell | (342.413, 432.000) | `left_fast` | 475/0 | -4.140/-4.140 | 6f/27f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37155 | 111 懶惰「生神停止(マインドストッパー)」 | (195.388, 39.301) | `down_fast` | 488/0 | -0.573/-0.603 | 4f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37921 | 111 懶惰「生神停止(マインドストッパー)」 | (161.699, 29.405) | `down_fast` | 456/0 | -2.638/-2.638 | 3f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41408 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 432.000) | `up_fast` | 1276/0 | -1.968/-12.170 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 7813 | 7691 | 5680 | 0 | 1979 | 1036 | 131.815 | 0.196 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 871 | 857 | 559 | 0 | 296 | 170 | 113.242 | 0.292 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 5 | 753 | 744 | 505 | 0 | 217 | 151 | 87.415 | 0.304 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1164 | 1157 | 545 | 0 | 606 | 176 | 110.995 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1145 | 1129 | 728 | 0 | 392 | 179 | 63.229 | 0.454 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.368 ms median and 23.499 ms p95.
- The full enemy sensor produced 6281 snapshots; capture read time was `{'median': 6.086800014600158, 'p95': 27.13389997370541, 'max': 56.6850999603048}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 6 phase-counter discontinuities were excluded; 11117 decisions retained at least one robust-union body (maximum 42); 4652 decisions contained latent contact-disabled geometry (maximum 41), and 5918 contained bounded inactive-slot memory (maximum 40). 219 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 2.8519973754882812, 'max': 3.609649658203125}` / `{'median': 0.0, 'p95': 2.5927233695983887, 'max': 3.5591018199920654}` / `{'median': 0.0, 'p95': 1.0000057220458984, 'max': 5.939693212509155}`.
- The issue-time enemy guard retained 11746 observations, detected 2296 during-plan geometry changes, recertified 2296 decisions, and overrode 51 actions. Read/recertificate timing was `{'median': 1.8334000487811863, 'p95': 3.451499971561134, 'max': 13.626200030557811}` / `{'median': 3.1989500275813043, 'p95': 7.055200054310262, 'max': 21.956600015982985}` ms; 4616 issue captures contained latent bodies (maximum 41), and 5923 contained dormant bodies (maximum 40). Fresh/global transactions preserved 2245/2296 planned actions, relaxed 8 fresh/global empty intersections, inherited 21 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8330 observations (8304 contact enabled, 26 anticipatory, 0 errors). 8330 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8330}`.
- The terminal-threat heuristic covered 11746 decisions with horizon counts `{'0': 70, '10': 11390, '32': 286}`; it reported 3 collision and 86 sub-safety-clearance warnings, and relaxed 71 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 296, '3': 8940, '4': 1643, '5': 867}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1736, '3': 8698, '4': 873, '5': 439}`.
- Adaptive delay supports were `{'1,2,3': 218, '1,2,3,4': 1, '2,3': 641, '2,3,4': 2819, '2,3,4,5': 4725, '2,3,4,5,6': 2503, '3,4': 2, '3,4,5': 9, '3,4,5,6': 828}`; 187 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 39/275.
- Robust viability supplied 11578 available policy queries (0 had new delay support outside the cached policy), constrained 3490 decisions, and exposed 8017 empty queried action sets. Recovery guidance was available/selected on 1176/524 empty-kernel queries; distant-kernel guidance was available/selected on 6113/5813. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 121.85236969382254, 'p95': 342.0409332229112, 'max': 520.430590953299}`, and `{'median': 0.0, 'p95': 21.595833778381348, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1788, '1': 1606, '2': 1194, '3': 1324, '4': 1427, '5': 1361, '6': 1432, '7': 1446}`.
- Global-horizon/local-prefix cross-tab covered 7954 decisions: 6 had a winning global state but unsafe selected prefix, 5381 had a losing global state but safe short prefix, 5 selected globally certified actions contradicted the fresh local prefix checker, and 29 selected actions were outside the reported winning set. 1831 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1712 unique policies with solve-time statistics `{'median': 108.84479997912422, 'p95': 343.83240004535764, 'max': 465.23239999078214}` and first-observed ages `{'median': 2.0, 'p95': 7.0, 'max': 1796.0}`. Policy status counts were `{'pending_future_epoch': 69, 'queryable': 11578, 'expired': 21}`; 90 robust-mode decisions had no query.
- Of 6269 unambiguous output transitions, 5535 (0.883) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 13, 'missing_pre_hit_alive_decision': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[4, 10, 5, 10, 8, 49, 105, 0, 75, 32, 27, 7, 3, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.448 during the 60 frames preceding a hit versus 0.210 outside those windows.
- Mean selected control-reserve deficit was 11.001 during the 60 frames preceding a hit versus 4.463 outside those windows.
- Soft recovery was selected on 0.015 of alive decisions in the 60-frame pre-hit windows versus 0.040 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
