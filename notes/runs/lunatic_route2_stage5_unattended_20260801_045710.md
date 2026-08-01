# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_045710

## Scope And Integrity

- Valid practice scope: `2..43692` (11363 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[1837, 2186, 2735, 12219, 12799, 24195, 30527, 31727, 37425, 39379, 39771, 41495]`.
- Hard no-Bomb verification: **PASS** across 11363 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1837-T1`. It occurred during a nonspell phase at player (21.657, 432.000), with 387 bullets and 0 lasers. The projectile model reported pipeline clearance 0.942.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 8 |
| `modeled_committed_prefix_collision` | 3 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 8
- `playfield_boundary`: 7
- `pool_density_over_1000`: 3
- `action_lag_over_model`: 2
- `corridor_deadline_miss`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1837 | nonspell | (21.657, 432.000) | `down_right_fast` | 387/0 | 0.942/-0.061 | 7f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 2186 | nonspell | (376.000, 432.000) | `stay` | 526/0 | -1.978/-2.125 | 0f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 2735 | nonspell | (49.370, 395.230) | `up_right_fast` | 848/0 | 8.568/2.756 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 12219 | nonspell | (355.926, 432.000) | `down_fast` | 354/0 | -3.618/-3.618 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12799 | nonspell | (376.000, 60.422) | `left_fast` | 279/0 | -3.258/-3.258 | 3f/26f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 24195 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `stay` | 1101/0 | -1.112/-1.542 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30527 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (73.368, 423.515) | `right` | 978/0 | -6.956/-8.161 | 26f/60f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31727 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (30.006, 427.121) | `down_left_fast` | 1024/0 | -5.101/-6.681 | 10f/63f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37425 | nonspell | (8.000, 410.286) | `up_fast` | 466/0 | -1.428/-1.428 | 3f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 39379 | 111 懶惰「生神停止(マインドストッパー)」 | (177.619, 199.429) | `down_left` | 368/0 | -3.481/-3.481 | 4f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39771 | 111 懶惰「生神停止(マインドストッパー)」 | (176.395, 198.311) | `up_left_fast` | 341/0 | 1.961/-7.001 | 3f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41495 | 115 散符「真実の月(インビジブルフルムーン)」 | (246.018, 432.000) | `up_fast` | 1096/0 | -2.526/-2.526 | 0f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 7908 | 0 | 0 | 0 | 0 | 0 | - | 0.379 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 803 | 765 | 490 | 0 | 0 | 150 | 107.476 | 0.468 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 647 | 641 | 448 | 0 | 0 | 141 | 77.936 | 0.344 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1025 | 1019 | 537 | 0 | 0 | 179 | 72.432 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 980 | 973 | 715 | 0 | 0 | 181 | 65.820 | 0.482 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.549 ms median and 33.865 ms p95.
- The full enemy sensor produced 6258 snapshots; capture read time was `{'median': 5.282550002448261, 'p95': 24.021799996262416, 'max': 58.9895000011893}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 19.0}` frames, and 7 phase-counter discontinuities were excluded; 10721 decisions retained at least one robust-union body (maximum 42); 8316 decisions contained latent contact-disabled geometry (maximum 41), and 4005 contained bounded inactive-slot memory (maximum 38). 283 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 2.757720947265625, 'max': 11.598118527730305}` / `{'median': 0.0, 'p95': 2.4184398651123047, 'max': 3.4799976348876953}` / `{'median': 0.0, 'p95': 1.0000028610229492, 'max': 11.598118527730305}`.
- The issue-time enemy guard retained 11363 observations, detected 3261 during-plan geometry changes, recertified 3261 decisions, and overrode 44 actions. Read/recertificate timing was `{'median': 1.65049999486655, 'p95': 3.2608999899821356, 'max': 55.22130000463221}` / `{'median': 3.094200001214631, 'p95': 6.495399997220375, 'max': 133.24300000385847}` ms; 8296 issue captures contained latent bodies (maximum 41), and 4002 contained dormant bodies (maximum 38). Fresh/global transactions preserved 3217/3261 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8264 observations (8240 contact enabled, 24 anticipatory, 0 errors). 8264 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8264}`.
- The terminal-threat heuristic covered 11363 decisions with horizon counts `{'0': 535, '10': 10828}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 471, '3': 6408, '4': 2814, '5': 1240, '6': 430}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 250, '2': 255, '3': 8068, '4': 2091, '5': 699}`.
- Adaptive delay supports were `{'1,2': 161, '1,2,3': 77, '1,2,3,4': 53, '1,2,3,4,5': 168, '1,2,3,4,5,6': 301, '2,3': 495, '2,3,4': 1777, '2,3,4,5': 3063, '2,3,4,5,6': 3609, '3,4,5': 150, '3,4,5,6': 1422, '4,5,6': 87}`; 214 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 37/226.
- Robust viability supplied 3398 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 2190 empty queried action sets. Recovery guidance was available/selected on 186/0 empty-kernel queries; distant-kernel guidance was available/selected on 1294/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 551, '1': 485, '2': 418, '3': 334, '4': 371, '5': 403, '6': 432, '7': 404}`.
- Global-horizon/local-prefix cross-tab covered 1239 decisions: 1 had a winning global state but unsafe selected prefix, 661 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 20 selected actions were outside the reported winning set. 1427 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 651 unique policies with solve-time statistics `{'median': 77.68750000104774, 'p95': 174.92130000027828, 'max': 212.5293999997666}` and first-observed ages `{'median': 4.0, 'p95': 6.0, 'max': 8.0}`. Policy status counts were `{'pending_future_epoch': 42, 'queryable': 3399, 'expired': 2}`; 45 robust-mode decisions had no query.
- Of 6146 unambiguous output transitions, 5762 (0.938) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 5, 'unresolved_planner_failure': 1, 'global_viability_kernel_exhausted_before_hit': 6}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 11 hit windows with a positive warning lead; those leads were `[9, 7, 0, 5, 26, 9, 60, 63, 5, 10, 11, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.401 during the 60 frames preceding a hit versus 0.363 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 4.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
