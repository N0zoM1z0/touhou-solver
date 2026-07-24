# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_093713

## Scope And Integrity

- Valid practice scope: `2..40607` (8171 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 15, at `[11620, 12233, 22442, 23890, 30257, 33655, 35043, 35449, 35751, 36248, 36607, 36980, 37534, 38572, 39735]`.
- Hard no-Bomb verification: **PASS** across 8171 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F11620-T1`. It occurred during a nonspell phase at player (376.000, 326.894), with 289 bullets and 0 lasers. The projectile model reported pipeline clearance -2.297.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 6 |
| `observed_bullet_overlap` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 4 |
| `enemy_body_contact_candidate` | 1 |

Contributing factors:

- `fast_mode`: 8
- `playfield_boundary`: 6
- `corridor_deadline_miss`: 5
- `pool_density_over_1000`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 11620 | nonspell | (376.000, 326.894) | `stay` | 289/0 | -2.297/-2.297 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12233 | nonspell | (364.686, 432.000) | `left_fast` | 320/0 | 0.071/-3.946 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22442 | 103 幻波「赤眼催眠(マインドブローイング)」 | (196.196, 430.374) | `up_right_fast` | 1275/0 | -2.005/-2.005 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23890 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left` | 1108/0 | -1.742/-1.742 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30257 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (191.032, 423.868) | `down_right_fast` | 996/0 | -2.930/-5.995 | 10f/25f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33655 | nonspell | (376.000, 432.000) | `stay` | 447/0 | -1.412/-1.412 | 0f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35043 | 111 懶惰「生神停止(マインドストッパー)」 | (193.865, 229.972) | `right` | 245/0 | -2.918/-3.035 | 3f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 35449 | 111 懶惰「生神停止(マインドストッパー)」 | (204.421, 207.380) | `up_left` | 338/0 | -3.953/-3.953 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35751 | 111 懶惰「生神停止(マインドストッパー)」 | (198.562, 112.467) | `up_fast` | 96/0 | 67.366/24.646 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `missing_pre_hit_alive_decision` |
| discovery | 36248 | 111 懶惰「生神停止(マインドストッパー)」 | (207.708, 234.571) | `up_left_fast` | 336/0 | 0.007/-0.461 | 4f/38f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36607 | 111 懶惰「生神停止(マインドストッパー)」 | (188.282, 89.300) | `up_fast` | 96/0 | 62.267/24.897 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 36980 | 111 懶惰「生神停止(マインドストッパー)」 | (194.828, 95.001) | `up` | 96/0 | 67.817/30.825 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 37534 | 115 散符「真実の月(インビジブルフルムーン)」 | (208.429, 136.329) | `up_left` | 0/0 | 9999.000/5.426 | 0f/0f | `enemy_body_contact_candidate` | `unresolved_planner_failure` |
| discovery | 38572 | 115 散符「真実の月(インビジブルフルムーン)」 | (12.879, 427.121) | `right_fast` | 957/0 | -1.258/-1.258 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39735 | 115 散符「真実の月(インビジブルフルムーン)」 | (129.066, 432.000) | `right_fast` | 1164/0 | 1.249/-0.274 | 0f/8f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 5079 | 4965 | 3320 | 0 | 1607 | 782 | 311.270 | 0.240 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 785 | 769 | 338 | 0 | 413 | 109 | 364.239 | 0.356 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 551 | 542 | 417 | 0 | 125 | 97 | 266.814 | 0.273 |
| 111 懶惰「生神停止(マインドストッパー)」 | 6 | 848 | 838 | 143 | 0 | 695 | 134 | 278.291 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 908 | 896 | 484 | 0 | 399 | 161 | 267.643 | 0.435 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 22.461 ms median and 38.254 ms p95.
- The full enemy sensor produced 5556 snapshots; capture read time was `{'median': 25.814399996306747, 'p95': 45.69160001119599, 'max': 78.8477000023704}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 11.0}` frames, and 9 phase-counter discontinuities were excluded; 150 decisions retained at least one contact-enabled body (maximum 37).
- The terminal-threat heuristic covered 8171 decisions with horizon counts `{'0': 78, '10': 7852, '32': 241}`; it reported 1 collision and 67 sub-safety-clearance warnings, and relaxed 69 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 51, '3': 328, '4': 5459, '5': 2333}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 63, '3': 483, '4': 7580, '5': 45}`.
- Adaptive delay supports were `{'2,3': 79, '2,3,4': 62, '2,3,4,5': 484, '2,3,4,5,6': 1076, '3,4': 100, '3,4,5': 948, '3,4,5,6': 5422}`; 341 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 96/554.
- Robust viability supplied 8010 available policy queries (0 had new delay support outside the cached policy), constrained 3239 decisions, and exposed 4702 empty queried action sets. Recovery guidance was available/selected on 883/440 empty-kernel queries; distant-kernel guidance was available/selected on 3411/3302. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 113.13708498984761, 'p95': 300.61270764889497, 'max': 464.0}`, and `{'median': 0.0, 'p95': 26.988025426864624, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1044, '1': 1050, '2': 1042, '3': 972, '4': 980, '5': 952, '6': 1001, '7': 969}`.
- The rolling worker produced 1283 unique policies with solve-time statistics `{'median': 298.81240002578124, 'p95': 444.6618999936618, 'max': 539.2035999975633}` and first-observed ages `{'median': 5.0, 'p95': 13.0, 'max': 1810.0}`. Policy status counts were `{'pending_future_epoch': 33, 'queryable': 8006, 'expired': 42}`; 71 robust-mode decisions had no query.
- Of 4930 unambiguous output transitions, 4247 (0.861) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10, 'robust_action_set_exhausted_before_hit': 1, 'missing_pre_hit_alive_decision': 1, 'unresolved_planner_failure': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[7, 7, 4, 4, 25, 18, 8, 9, 0, 38, 0, 0, 0, 0, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.335 during the 60 frames preceding a hit versus 0.257 outside those windows.
- Mean selected control-reserve deficit was 8.729 during the 60 frames preceding a hit versus 3.111 outside those windows.
- Soft recovery was selected on 0.036 of alive decisions in the 60-frame pre-hit windows versus 0.060 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 9.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
