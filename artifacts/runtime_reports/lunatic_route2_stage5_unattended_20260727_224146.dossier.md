# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260727_224146

## Scope And Integrity

- Valid practice scope: `1..43371` (13953 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 13, at `[1564, 2586, 3997, 10708, 23857, 29721, 30098, 30989, 35245, 35763, 37079, 38412, 39854]`.
- Hard no-Bomb verification: **PASS** across 13953 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1564-T1`. It occurred during a nonspell phase at player (376.000, 430.109), with 53 bullets and 0 lasers. The projectile model reported pipeline clearance -1.210.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 3 |

Contributing factors:

- `fast_mode`: 11
- `playfield_boundary`: 9
- `pool_density_over_1000`: 2
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1564 | nonspell | (376.000, 430.109) | `left_fast` | 53/0 | -1.210/-1.210 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2586 | nonspell | (376.000, 432.000) | `up_left_fast` | 442/0 | -1.759/-1.759 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3997 | nonspell | (8.000, 432.000) | `up_fast` | 723/0 | -4.159/-4.159 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10708 | nonspell | (44.770, 401.944) | `up_right_fast` | 882/0 | 2.192/-24.094 | 41f/47f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23857 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `right_fast` | 1429/0 | -1.669/-1.669 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29721 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (191.788, 432.000) | `up_left_fast` | 977/0 | -5.619/-5.619 | 10f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30098 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (168.186, 404.000) | `up` | 993/0 | -6.945/-6.945 | 8f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30989 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (97.322, 432.000) | `up_left_fast` | 1020/0 | -5.195/-5.195 | 7f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35245 | nonspell | (8.000, 432.000) | `up_right_fast` | 420/0 | -3.738/-3.738 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35763 | nonspell | (376.000, 414.027) | `up_left_fast` | 456/0 | -1.422/-1.422 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37079 | nonspell | (376.000, 414.736) | `down_left_fast` | 442/0 | -2.382/-2.382 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38412 | 111 懶惰「生神停止(マインドストッパー)」 | (220.825, 190.716) | `right` | 328/0 | 1.010/-1.902 | 5f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39854 | 111 懶惰「生神停止(マインドストッパー)」 | (173.418, 195.495) | `up_right_fast` | 348/0 | -1.296/-1.296 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 8908 | 8762 | 6289 | 0 | 2449 | 1095 | 112.741 | 0.193 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 1374 | 1365 | 920 | 0 | 438 | 181 | 102.980 | 0.347 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 3 | 930 | 922 | 687 | 0 | 228 | 169 | 78.930 | 0.297 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1299 | 1283 | 597 | 0 | 673 | 180 | 90.324 | 0.000 |
| 115 | 0 | 1442 | 1433 | 1152 | 0 | 271 | 183 | 53.239 | 0.530 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 10.081 ms median and 19.933 ms p95.
- The full enemy sensor produced 6907 snapshots; capture read time was `{'median': 4.936399986036122, 'p95': 21.49929996812716, 'max': 42.67340002115816}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 11.0}` frames, and 6 phase-counter discontinuities were excluded; 13303 decisions retained at least one robust-union body (maximum 41); 5474 decisions contained latent contact-disabled geometry (maximum 40), and 7243 contained bounded inactive-slot memory (maximum 40). 192 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 5.297319412231445, 'max': 8.35100507736206}` / `{'median': 0.0, 'p95': 4.620643615722656, 'max': 6.133330345153809}` / `{'median': 0.0, 'p95': 5.749991297721863, 'max': 12.266660690307617}`.
- The issue-time enemy guard retained 13953 observations, detected 2419 during-plan geometry changes, recertified 2419 decisions, and overrode 58 actions. Read/recertificate timing was `{'median': 1.7216000123880804, 'p95': 3.49209998967126, 'max': 14.49309999588877}` / `{'median': 2.24170001456514, 'p95': 5.706899974029511, 'max': 15.635700023267418}` ms; 5445 issue captures contained latent bodies (maximum 40), and 7240 contained dormant bodies (maximum 40). Fresh/global transactions preserved 2361/2419 planned actions, relaxed 8 fresh/global empty intersections, inherited 11 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 10224 observations (10194 contact enabled, 30 anticipatory, 0 errors). 10224 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 10224}`.
- The terminal-threat heuristic covered 13953 decisions with horizon counts `{'0': 77, '10': 13535, '32': 341}`; it reported 5 collision and 85 sub-safety-clearance warnings, and relaxed 61 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 3222, '3': 10104, '4': 627}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 8531, '3': 4868, '4': 541}`.
- Adaptive delay supports were `{'1,2': 33, '1,2,3': 103, '1,2,3,4': 178, '1,2,3,4,5': 14, '2,3': 1330, '2,3,4': 7843, '2,3,4,5': 2591, '2,3,4,5,6': 1369, '3,4': 1, '3,4,5': 93, '3,4,5,6': 396, '4,5,6': 2}`; 82 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 23/230.
- Robust viability supplied 13765 available policy queries (0 had new delay support outside the cached policy), constrained 4059 decisions, and exposed 9645 empty queried action sets. Recovery guidance was available/selected on 1281/571 empty-kernel queries; distant-kernel guidance was available/selected on 7339/7042. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 128.9961239727768, 'p95': 334.0898082851376, 'max': 486.6210024238576}`, and `{'median': 0.0, 'p95': 20.0, 'max': 42.399930238723755}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2183, '1': 1707, '2': 1445, '3': 1690, '4': 1680, '5': 1653, '6': 1746, '7': 1661}`.
- Global-horizon/local-prefix cross-tab covered 9746 decisions: 1 had a winning global state but unsafe selected prefix, 7015 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 26 selected actions were outside the reported winning set. 2061 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1808 unique policies with solve-time statistics `{'median': 92.55719999782741, 'p95': 290.96280003432184, 'max': 404.81740003451705}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1786.0}`. Policy status counts were `{'pending_future_epoch': 80, 'queryable': 13766, 'expired': 13}`; 94 robust-mode decisions had no query.
- Of 7347 unambiguous output transitions, 6592 (0.897) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 13}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[7, 4, 6, 47, 6, 18, 19, 22, 7, 7, 6, 10, 11]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.296 during the 60 frames preceding a hit versus 0.238 outside those windows.
- Mean selected control-reserve deficit was 9.629 during the 60 frames preceding a hit versus 3.961 outside those windows.
- Soft recovery was selected on 0.015 of alive decisions in the 60-frame pre-hit windows versus 0.043 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 13.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
