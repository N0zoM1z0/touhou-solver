# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_200739

## Scope And Integrity

- Valid practice scope: `2..43163` (13097 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 10, at `[4184, 11206, 11665, 12314, 12786, 23566, 25065, 32057, 36515, 42417]`.
- Hard no-Bomb verification: **PASS** across 13097 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F4184-T1`. It occurred during a nonspell phase at player (364.500, 432.000), with 334 bullets and 0 lasers. The projectile model reported pipeline clearance -0.239.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 3 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 8
- `fast_mode`: 7
- `corridor_deadline_miss`: 2
- `pool_density_over_1000`: 2
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4184 | nonspell | (364.500, 432.000) | `left` | 334/0 | -0.239/-0.239 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11206 | nonspell | (344.000, 432.000) | `up_left_fast` | 927/0 | -11.376/-14.125 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11665 | nonspell | (31.147, 374.810) | `up_fast` | 876/0 | -10.938/-11.345 | 2f/2f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12314 | nonspell | (376.000, 87.719) | `down_right` | 303/0 | -1.790/-1.790 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12786 | nonspell | (298.716, 100.256) | `up_left` | 234/0 | -4.502/-4.502 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23566 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `left_fast` | 1054/0 | -2.966/-2.966 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25065 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 1107/0 | -1.273/-3.104 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32057 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (150.781, 432.000) | `up_left_fast` | 997/0 | -4.985/-5.206 | 7f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36515 | nonspell | (376.000, 414.210) | `left_fast` | 532/0 | -2.835/-2.835 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42417 | 115 散符「真実の月(インビジブルフルムーン)」 | (23.253, 432.000) | `up_right_fast` | 963/0 | 2.181/-0.937 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 8983 | 8843 | 6393 | 0 | 2419 | 1129 | 105.009 | 0.200 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 1025 | 1017 | 512 | 0 | 501 | 177 | 105.729 | 0.271 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 669 | 663 | 416 | 0 | 241 | 123 | 80.340 | 0.297 |
| 111 | 0 | 1185 | 1174 | 751 | 0 | 418 | 177 | 77.895 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1235 | 1225 | 725 | 0 | 488 | 183 | 56.158 | 0.483 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 10.359 ms median and 20.877 ms p95.
- The full enemy sensor produced 6643 snapshots; capture read time was `{'median': 5.301500088535249, 'p95': 23.051799973472953, 'max': 45.909499982371926}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 12.0}` frames, and 6 phase-counter discontinuities were excluded; 12416 decisions retained at least one robust-union body (maximum 41); 4746 decisions contained latent contact-disabled geometry (maximum 39), and 6207 contained bounded inactive-slot memory (maximum 39). 177 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 2.48272705078125, 'max': 4.700004577636719}` / `{'median': 0.0, 'p95': 2.1572952270507812, 'max': 4.650016784667969}` / `{'median': 0.0, 'p95': 0.9937163591384888, 'max': 1.000030517578125}`.
- The issue-time enemy guard retained 13097 observations, detected 2217 during-plan geometry changes, recertified 2217 decisions, and overrode 43 actions. Read/recertificate timing was `{'median': 1.6915000742301345, 'p95': 3.3129999646916986, 'max': 12.679500039666891}` / `{'median': 2.8179000364616513, 'p95': 5.8651999570429325, 'max': 15.452599967829883}` ms; 4707 issue captures contained latent bodies (maximum 39), and 6225 contained dormant bodies (maximum 39). Fresh/global transactions preserved 2174/2217 planned actions, relaxed 6 fresh/global empty intersections, inherited 16 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9441 observations (9412 contact enabled, 29 anticipatory, 0 errors). 9441 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9441}`.
- The terminal-threat heuristic covered 13097 decisions with horizon counts `{'0': 74, '10': 12743, '32': 280}`; it reported 1 collision and 81 sub-safety-clearance warnings, and relaxed 58 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2191, '3': 9749, '4': 958, '5': 199}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 5223, '3': 6502, '4': 1359}`.
- Adaptive delay supports were `{'1,2': 36, '1,2,3': 67, '1,2,3,4': 249, '1,2,3,4,5,6': 14, '2,3': 1649, '2,3,4': 6930, '2,3,4,5': 2267, '2,3,4,5,6': 1211, '3,4,5': 48, '3,4,5,6': 626}`; 89 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 49/365.
- Robust viability supplied 12922 available policy queries (0 had new delay support outside the cached policy), constrained 4067 decisions, and exposed 8797 empty queried action sets. Recovery guidance was available/selected on 1162/509 empty-kernel queries; distant-kernel guidance was available/selected on 7047/6867. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 144.0, 'p95': 332.938432746957, 'max': 487.6720209321015}`, and `{'median': 0.0, 'p95': 20.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2091, '1': 1656, '2': 1357, '3': 1534, '4': 1570, '5': 1536, '6': 1641, '7': 1537}`.
- Global-horizon/local-prefix cross-tab covered 9328 decisions: 4 had a winning global state but unsafe selected prefix, 6431 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 25 selected actions were outside the reported winning set. 1965 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1789 unique policies with solve-time statistics `{'median': 93.79690000787377, 'p95': 295.1522000366822, 'max': 399.0831000264734}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1795.0}`. Policy status counts were `{'pending_future_epoch': 81, 'queryable': 12923, 'expired': 14}`; 96 robust-mode decisions had no query.
- Of 6808 unambiguous output transitions, 6234 (0.916) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[9, 0, 2, 3, 6, 8, 7, 21, 6, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.371 during the 60 frames preceding a hit versus 0.212 outside those windows.
- Mean selected control-reserve deficit was 11.033 during the 60 frames preceding a hit versus 3.525 outside those windows.
- Soft recovery was selected on 0.004 of alive decisions in the 60-frame pre-hit windows versus 0.040 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 4.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
