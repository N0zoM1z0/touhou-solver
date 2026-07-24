# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_103617

## Scope And Integrity

- Valid practice scope: `2..41593` (8205 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[10130, 11576, 12280, 23136, 24227, 30021, 31764, 34632, 38432, 39169, 40057, 41114]`.
- Hard no-Bomb verification: **PASS** across 8205 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F10130-T1`. It occurred during a nonspell phase at player (336.981, 388.287), with 900 bullets and 0 lasers. The projectile model reported pipeline clearance 10.605.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 6 |
| `observed_bullet_overlap` | 4 |
| `enemy_body_contact_candidate` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 9
- `fast_mode`: 7
- `pool_density_over_1000`: 7
- `corridor_deadline_miss`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 10130 | nonspell | (336.981, 388.287) | `up_fast` | 900/0 | 10.605/1.163 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11576 | nonspell | (373.707, 432.000) | `stay` | 341/0 | -3.598/-3.598 | 4f/23f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12280 | nonspell | (8.000, 91.529) | `up_right` | 156/0 | -1.747/-1.747 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23136 | 103 幻波「赤眼催眠(マインドブローイング)」 | (369.495, 432.000) | `up_left_fast` | 1113/0 | -0.571/-0.571 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24227 | 103 幻波「赤眼催眠(マインドブローイング)」 | (258.276, 432.000) | `up_right_fast` | 1017/0 | -1.777/-1.777 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30021 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (55.990, 432.000) | `up_left_fast` | 1016/0 | -4.605/-4.992 | 26f/60f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31764 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (130.058, 432.000) | `stay` | 1012/0 | -7.513/-7.513 | 27f/46f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34632 | nonspell | (20.000, 427.121) | `up_right_fast` | 409/0 | -1.107/-4.208 | 6f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38432 | 115 散符「真実の月(インビジブルフルムーン)」 | (192.924, 125.688) | `up_right_fast` | 0/0 | 9999.000/-0.365 | 0f/0f | `enemy_body_contact_candidate` | `unresolved_planner_failure` |
| discovery | 39169 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 425.495) | `stay` | 1275/0 | 1.907/-1.732 | 3f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40057 | 115 散符「真実の月(インビジブルフルムーン)」 | (221.490, 432.000) | `stay` | 1189/0 | -1.470/-1.555 | 5f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41114 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 432.000) | `up_left_fast` | 1162/0 | -3.005/-3.005 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 4714 | 4601 | 2798 | 0 | 1773 | 709 | 320.886 | 0.195 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 864 | 840 | 396 | 0 | 435 | 116 | 389.295 | 0.350 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 964 | 951 | 821 | 0 | 130 | 176 | 293.685 | 0.323 |
| 111 | 0 | 773 | 757 | 343 | 0 | 413 | 139 | 222.825 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 4 | 890 | 875 | 378 | 0 | 473 | 149 | 290.799 | 0.390 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 5.000 frames p95. The local plan took 22.356 ms median and 36.427 ms p95.
- The full enemy sensor produced 5895 snapshots; capture read time was `{'median': 27.552499988814816, 'p95': 44.512699998449534, 'max': 78.81249999627471}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 213 decisions retained at least one contact-enabled body (maximum 37).
- The terminal-threat heuristic covered 8205 decisions with horizon counts `{'0': 87, '10': 7816, '32': 302}`; it reported 1 collision and 78 sub-safety-clearance warnings, and relaxed 64 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 60, '3': 338, '4': 4722, '5': 3085}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 49, '3': 446, '4': 6501, '5': 1209}`.
- Adaptive delay supports were `{'1,2,3': 24, '1,2,3,4': 60, '1,2,3,4,5,6': 13, '2,3': 16, '2,3,4': 95, '2,3,4,5': 320, '2,3,4,5,6': 1117, '3,4,5': 554, '3,4,5,6': 5452, '4,5': 42, '4,5,6': 512}`; 510 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 104/652.
- Robust viability supplied 8024 available policy queries (0 had new delay support outside the cached policy), constrained 3224 decisions, and exposed 4736 empty queried action sets. Recovery guidance was available/selected on 715/384 empty-kernel queries; distant-kernel guidance was available/selected on 3418/3295. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 121.85236969382254, 'p95': 301.8873962258113, 'max': 458.4495610206209}`, and `{'median': 0.0, 'p95': 25.634264945983887, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1121, '1': 1010, '2': 997, '3': 992, '4': 1021, '5': 972, '6': 938, '7': 973}`.
- The rolling worker produced 1289 unique policies with solve-time statistics `{'median': 305.04999999538995, 'p95': 459.9488000094425, 'max': 530.9502999880351}` and first-observed ages `{'median': 6.0, 'p95': 13.0, 'max': 1813.0}`. Policy status counts were `{'pending_future_epoch': 39, 'queryable': 8022, 'expired': 42}`; 79 robust-mode decisions had no query.
- Of 4746 unambiguous output transitions, 3980 (0.839) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 11, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[0, 23, 6, 7, 5, 60, 46, 10, 0, 12, 8, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.440 during the 60 frames preceding a hit versus 0.211 outside those windows.
- Mean selected control-reserve deficit was 8.432 during the 60 frames preceding a hit versus 2.887 outside those windows.
- Soft recovery was selected on 0.022 of alive decisions in the 60-frame pre-hit windows versus 0.050 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 51.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
