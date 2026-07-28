# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_185838

## Scope And Integrity

- Valid practice scope: `1..41601` (12216 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 10, at `[1490, 2041, 4021, 10980, 11634, 12330, 29670, 36941, 38218, 40914]`.
- Hard no-Bomb verification: **PASS** across 12216 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1490-T1`. It occurred during a nonspell phase at player (376.000, 418.915), with 80 bullets and 0 lasers. The projectile model reported pipeline clearance 0.478.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 6 |
| `modeled_committed_prefix_collision` | 3 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 6
- `corridor_deadline_miss`: 1
- `enemy_body_absent_from_action_snapshot`: 1
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1490 | nonspell | (376.000, 418.915) | `up_left_fast` | 80/0 | 0.478/-2.127 | 2f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2041 | nonspell | (372.000, 432.000) | `up_fast` | 721/0 | -1.700/-1.859 | 4f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4021 | nonspell | (13.657, 432.000) | `up_right_fast` | 723/0 | -4.145/-4.145 | 3f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10980 | nonspell | (329.241, 409.373) | `left_fast` | 872/0 | -12.240/-15.777 | 2f/2f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11634 | nonspell | (264.998, 417.858) | `up_left_fast` | 893/0 | 5.249/-7.911 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12330 | nonspell | (364.742, 432.000) | `left_fast` | 315/0 | 0.913/-3.122 | 2f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29670 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (82.181, 432.000) | `left_fast` | 953/0 | -7.714/-7.714 | 8f/26f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36941 | 111 懶惰「生神停止(マインドストッパー)」 | (210.289, 193.994) | `right_fast` | 352/0 | 0.602/-2.745 | 6f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38218 | 111 懶惰「生神停止(マインドストッパー)」 | (197.911, 16.000) | `up_right` | 476/0 | 1.674/-1.578 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40914 | 115 散符「真実の月(インビジブルフルムーン)」 | (10.828, 429.172) | `up_right_fast` | 1295/0 | 2.178/-1.307 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 8167 | 8028 | 5525 | 0 | 2464 | 1020 | 105.560 | 0.218 |
| 103 | 0 | 867 | 858 | 688 | 0 | 170 | 173 | 97.955 | 0.340 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 745 | 735 | 504 | 0 | 227 | 138 | 79.695 | 0.364 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1236 | 1227 | 585 | 0 | 635 | 181 | 90.022 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1201 | 1187 | 810 | 0 | 371 | 182 | 56.775 | 0.475 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 10.397 ms median and 21.515 ms p95.
- The full enemy sensor produced 6295 snapshots; capture read time was `{'median': 5.345100071281195, 'p95': 23.368899943307042, 'max': 66.25200004782528}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 11594 decisions retained at least one robust-union body (maximum 42); 4892 decisions contained latent contact-disabled geometry (maximum 41), and 6121 contained bounded inactive-slot memory (maximum 41). 148 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.11785125732421875, 'p95': 3.231964111328125, 'max': 6.133330345153809}` / `{'median': 0.1178511381149292, 'p95': 2.5731775760650635, 'max': 6.133330345153809}` / `{'median': 0.0, 'p95': 4.000000715255737, 'max': 12.266660690307617}`.
- The issue-time enemy guard retained 12216 observations, detected 2295 during-plan geometry changes, recertified 2295 decisions, and overrode 58 actions. Read/recertificate timing was `{'median': 1.6924499650485814, 'p95': 3.280599950812757, 'max': 15.469199977815151}` / `{'median': 2.875400008633733, 'p95': 5.968499928712845, 'max': 14.455099939368665}` ms; 4859 issue captures contained latent bodies (maximum 41), and 6141 contained dormant bodies (maximum 41). Fresh/global transactions preserved 2237/2295 planned actions, relaxed 6 fresh/global empty intersections, inherited 11 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8575 observations (8545 contact enabled, 30 anticipatory, 0 errors). 8575 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8575}`.
- The terminal-threat heuristic covered 12216 decisions with horizon counts `{'0': 75, '10': 11931, '32': 210}`; it reported 1 collision and 54 sub-safety-clearance warnings, and relaxed 56 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2099, '3': 8730, '4': 1187, '5': 200}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 63, '2': 5264, '3': 5709, '4': 1180}`.
- Adaptive delay supports were `{'1,2': 54, '1,2,3': 73, '1,2,3,4': 223, '2,3': 1152, '2,3,4': 6331, '2,3,4,5': 2234, '2,3,4,5,6': 1223, '3,4': 4, '3,4,5': 134, '3,4,5,6': 788}`; 106 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 24/215.
- Robust viability supplied 12035 available policy queries (0 had new delay support outside the cached policy), constrained 3867 decisions, and exposed 8112 empty queried action sets. Recovery guidance was available/selected on 1080/446 empty-kernel queries; distant-kernel guidance was available/selected on 6315/5995. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 136.7040599250805, 'p95': 352.3634487287238, 'max': 520.430590953299}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1935, '1': 1572, '2': 1248, '3': 1390, '4': 1457, '5': 1455, '6': 1560, '7': 1418}`.
- Global-horizon/local-prefix cross-tab covered 8413 decisions: 3 had a winning global state but unsafe selected prefix, 5603 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 26 selected actions were outside the reported winning set. 2049 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1694 unique policies with solve-time statistics `{'median': 92.1257000300102, 'p95': 298.3425999991596, 'max': 415.12999997939914}` and first-observed ages `{'median': 2.0, 'p95': 6.0, 'max': 1808.0}`. Policy status counts were `{'pending_future_epoch': 71, 'queryable': 12034, 'expired': 28}`; 98 robust-mode decisions had no query.
- Of 6453 unambiguous output transitions, 5888 (0.912) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 9, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[8, 6, 11, 2, 0, 11, 26, 9, 7, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.611 during the 60 frames preceding a hit versus 0.233 outside those windows.
- Mean selected control-reserve deficit was 11.009 during the 60 frames preceding a hit versus 4.418 outside those windows.
- Soft recovery was selected on 0.040 of alive decisions in the 60-frame pre-hit windows versus 0.039 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 13.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
