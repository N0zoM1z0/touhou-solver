# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_224116

## Scope And Integrity

- Valid practice scope: `1..40036` (11735 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 10, at `[2397, 3533, 10371, 10698, 13759, 22368, 23236, 37636, 38897, 39516]`.
- Hard no-Bomb verification: **PASS** across 11735 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2397-T1`. It occurred during a nonspell phase at player (8.000, 432.000), with 438 bullets and 0 lasers. The projectile model reported pipeline clearance -3.050.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 3 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 8
- `pool_density_over_1000`: 3
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2397 | nonspell | (8.000, 432.000) | `up_fast` | 438/0 | -3.050/-3.050 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3533 | nonspell | (376.000, 408.000) | `up_fast` | 800/0 | -2.713/-2.713 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10371 | nonspell | (43.443, 365.687) | `up_right_fast` | 886/0 | 1.221/-25.164 | 4f/4f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10698 | nonspell | (249.520, 400.000) | `up_fast` | 742/0 | -15.843/-20.519 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13759 | nonspell | (9.626, 432.000) | `up_right` | 394/0 | -3.732/-3.732 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22368 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 885/0 | -2.785/-2.785 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23236 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `left_fast` | 974/0 | -2.789/-2.789 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37636 | 115 散符「真実の月(インビジブルフルムーン)」 | (258.768, 432.000) | `up_left_fast` | 1167/0 | -1.502/-1.502 | 8f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38897 | 115 散符「真実の月(インビジブルフルムーン)」 | (14.081, 429.172) | `up_right_fast` | 1302/0 | 0.402/-0.034 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39516 | 115 散符「真実の月(インビジブルフルムーン)」 | (135.295, 432.000) | `up_fast` | 1099/0 | -3.196/-3.196 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 7799 | 7672 | 5583 | 0 | 2055 | 977 | 106.723 | 0.216 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 1018 | 1009 | 477 | 0 | 529 | 175 | 106.091 | 0.293 |
| 107 | 0 | 601 | 592 | 352 | 0 | 239 | 108 | 83.992 | 0.308 |
| 111 | 0 | 1002 | 990 | 595 | 0 | 389 | 149 | 74.991 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 1315 | 1301 | 591 | 0 | 695 | 186 | 60.962 | 0.263 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 10.397 ms median and 21.200 ms p95.
- The full enemy sensor produced 5947 snapshots; capture read time was `{'median': 5.368000012822449, 'p95': 23.424600018188357, 'max': 52.76099999900907}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 11088 decisions retained at least one robust-union body (maximum 42); 4781 decisions contained latent contact-disabled geometry (maximum 42), and 5919 contained bounded inactive-slot memory (maximum 40). 215 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 3.06005859375, 'max': 5.297325134277344}` / `{'median': 0.8160808682441711, 'p95': 4.620661735534668, 'max': 8.95069694519043}` / `{'median': 1.3709068298339844e-06, 'p95': 2.8531696796417236, 'max': 8.95069694519043}`.
- The issue-time enemy guard retained 11735 observations, detected 2238 during-plan geometry changes, recertified 2238 decisions, and overrode 56 actions. Read/recertificate timing was `{'median': 1.7667999491095543, 'p95': 3.52609995752573, 'max': 14.974100049585104}` / `{'median': 2.726700040511787, 'p95': 5.620699957944453, 'max': 14.812899986281991}` ms; 4751 issue captures contained latent bodies (maximum 42), and 5911 contained dormant bodies (maximum 40). Fresh/global transactions preserved 2182/2238 planned actions, relaxed 7 fresh/global empty intersections, inherited 12 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8108 observations (8079 contact enabled, 29 anticipatory, 0 errors). 8108 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8108}`.
- The terminal-threat heuristic covered 11735 decisions with horizon counts `{'0': 72, '10': 11500, '32': 163}`; it reported 1 collision and 47 sub-safety-clearance warnings, and relaxed 59 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1375, '3': 9283, '4': 1077}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 59, '2': 4284, '3': 6394, '4': 998}`.
- Adaptive delay supports were `{'1,2': 14, '1,2,3': 292, '1,2,3,4': 54, '1,2,3,4,5': 15, '2,3': 1409, '2,3,4': 5490, '2,3,4,5': 2695, '2,3,4,5,6': 1360, '3,4': 8, '3,4,5': 48, '3,4,5,6': 349, '4,5,6': 1}`; 81 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 31/242.
- Robust viability supplied 11564 available policy queries (0 had new delay support outside the cached policy), constrained 3907 decisions, and exposed 7598 empty queried action sets. Recovery guidance was available/selected on 929/412 empty-kernel queries; distant-kernel guidance was available/selected on 6208/6005. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 128.9961239727768, 'p95': 336.3807366660582, 'max': 488.4588007191599}`, and `{'median': 0.0, 'p95': 19.06822109222412, 'max': 43.274728298187256}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1781, '1': 1551, '2': 1235, '3': 1345, '4': 1417, '5': 1357, '6': 1485, '7': 1393}`.
- Global-horizon/local-prefix cross-tab covered 8048 decisions: 2 had a winning global state but unsafe selected prefix, 5368 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 24 selected actions were outside the reported winning set. 1831 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1595 unique policies with solve-time statistics `{'median': 94.13169999606907, 'p95': 304.8940999433398, 'max': 419.38029997982085}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1808.0}`. Policy status counts were `{'pending_future_epoch': 73, 'queryable': 11565, 'expired': 25}`; 99 robust-mode decisions had no query.
- Of 5998 unambiguous output transitions, 5438 (0.907) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[7, 5, 4, 0, 4, 7, 8, 11, 5, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.529 during the 60 frames preceding a hit versus 0.203 outside those windows.
- Mean selected control-reserve deficit was 8.449 during the 60 frames preceding a hit versus 3.789 outside those windows.
- Soft recovery was selected on 0.022 of alive decisions in the 60-frame pre-hit windows versus 0.038 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 24.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
