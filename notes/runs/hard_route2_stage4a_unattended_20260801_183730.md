# TH08 Stage 4A / Reimu No-Bomb Practice Review: hard_route2_stage4a_unattended_20260801_183730

## Scope And Integrity

- Valid practice scope: `2..43965` (12924 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 11, at `[9352, 12641, 13411, 16813, 19351, 22180, 27427, 28276, 36941, 38026, 43212]`.
- Hard no-Bomb verification: **PASS** across 12924 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S3-F9352-T1`. It occurred during a nonspell phase at player (252.800, 432.000), with 407 bullets and 0 lasers. The projectile model reported pipeline clearance -1.751.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 6 |
| `modeled_committed_prefix_collision` | 5 |

Contributing factors:

- `fast_mode`: 10
- `playfield_boundary`: 7
- `corridor_deadline_miss`: 3
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 9352 | nonspell | (252.800, 432.000) | `up_left_fast` | 407/0 | -1.751/-3.815 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12641 | 56 夢境「二重大結界」 | (281.375, 284.012) | `up_right` | 511/0 | -2.661/-2.661 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13411 | 56 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 544/0 | -1.780/-1.780 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 16813 | nonspell | (16.000, 428.000) | `up_fast` | 201/0 | 2.246/-6.393 | 5f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 19351 | 60 散霊「夢想封印　寂」 | (133.189, 425.657) | `down_right_fast` | 73/0 | 1.495/-4.290 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22180 | nonspell | (376.000, 412.000) | `up_fast` | 520/0 | -3.290/-3.290 | 3f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 27427 | nonspell | (13.657, 426.343) | `up_right_fast` | 66/0 | 1.878/-3.045 | 2f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 28276 | nonspell | (375.222, 293.217) | `up_fast` | 157/0 | -3.946/-3.946 | 0f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36941 | 68 回霊「夢想封印　侘」 | (35.779, 432.000) | `right_fast` | 542/0 | -0.490/-1.089 | 3f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38026 | 68 回霊「夢想封印　侘」 | (10.828, 429.172) | `up_right_fast` | 644/0 | -3.323/-3.323 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43212 | 72 大結界「博麗弾幕結界」 | (299.287, 366.343) | `up_fast` | 1065/0 | -2.122/-2.122 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 8229 | 0 | 0 | 0 | 0 | 0 | - | 0.188 |
| 56 夢境「二重大結界」 | 2 | 1057 | 1021 | 393 | 0 | 0 | 167 | 203.929 | 0.202 |
| 60 散霊「夢想封印　寂」 | 1 | 1015 | 1008 | 356 | 0 | 0 | 165 | 142.234 | 0.198 |
| 64 | 0 | 581 | 573 | 441 | 0 | 0 | 99 | 56.019 | 0.389 |
| 68 回霊「夢想封印　侘」 | 2 | 1074 | 1068 | 542 | 0 | 0 | 180 | 100.191 | 0.218 |
| 72 大結界「博麗弾幕結界」 | 1 | 968 | 961 | 463 | 0 | 0 | 180 | 126.152 | 0.000 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 17.152 ms median and 27.415 ms p95.
- The full enemy sensor produced 6590 snapshots; capture read time was `{'median': 5.506050001713447, 'p95': 17.326500004855916, 'max': 64.31570000131615}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 12234 decisions retained at least one robust-union body (maximum 44); 7161 decisions contained latent contact-disabled geometry (maximum 44), and 5249 contained bounded inactive-slot memory (maximum 30). 112 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.851637840270996, 'p95': 4.697471618652344, 'max': 17.846179132876188}` / `{'median': 2.9284448623657227, 'p95': 4.404354095458984, 'max': 5.727027416229248}` / `{'median': 1.2278556823730469e-05, 'p95': 0.7272701263427734, 'max': 17.731389281866342}`.
- The issue-time enemy guard retained 12924 observations, detected 4424 during-plan geometry changes, recertified 4424 decisions, and overrode 30 actions. Read/recertificate timing was `{'median': 1.6055499872891232, 'p95': 2.8962999931536615, 'max': 19.969499990111217}` / `{'median': 2.114700007950887, 'p95': 3.777500009164214, 'max': 12.616499996511266}` ms; 7170 issue captures contained latent bodies (maximum 44), and 5246 contained dormant bodies (maximum 30). Fresh/global transactions preserved 4394/4424 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9546 observations (9502 contact enabled, 44 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9546}`.
- The terminal-threat heuristic covered 12924 decisions with horizon counts `{'0': 689, '10': 12235}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 770, '3': 9009, '4': 3145}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 495, '2': 2361, '3': 8922, '4': 1146}`.
- Adaptive delay supports were `{'1': 279, '1,2': 97, '1,2,3': 87, '1,2,3,4': 471, '1,2,3,4,5': 89, '1,2,3,4,5,6': 53, '2,3': 598, '2,3,4': 5252, '2,3,4,5': 3373, '2,3,4,5,6': 1701, '3,4': 10, '3,4,5': 482, '3,4,5,6': 431, '4,5,6': 1}`; 45 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 41/315.
- Robust viability supplied 4631 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 2195 empty queried action sets. Recovery guidance was available/selected on 700/0 empty-kernel queries; distant-kernel guidance was available/selected on 1232/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 742, '1': 657, '2': 504, '3': 507, '4': 565, '5': 542, '6': 545, '7': 569}`.
- Global-horizon/local-prefix cross-tab covered 2954 decisions: 0 had a winning global state but unsafe selected prefix, 1419 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 210 selected actions were outside the reported winning set. 937 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 791 unique policies with solve-time statistics `{'median': 129.6030000085011, 'p95': 234.1014000121504, 'max': 303.5260000033304}` and first-observed ages `{'median': 3.0, 'p95': 4.0, 'max': 5.0}`. Policy status counts were `{'pending_future_epoch': 47, 'queryable': 4632, 'expired': 3}`; 51 robust-mode decisions had no query.
- Of 6917 unambiguous output transitions, 6533 (0.944) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 5, 'global_viability_kernel_exhausted_before_hit': 6}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[3, 7, 6, 7, 5, 6, 6, 5, 12, 6, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.404 during the 60 frames preceding a hit versus 0.184 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 3.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
