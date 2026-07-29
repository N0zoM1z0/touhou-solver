# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260729_125453

## Scope And Integrity

- Valid practice scope: `2..44053` (12039 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[731, 1414, 2222, 4232, 12376, 23418, 23951, 30162, 30649, 31263, 31644, 35523, 39329, 40083, 42036, 42638, 43369, 43951]`.
- Hard no-Bomb verification: **PASS** across 12039 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F731-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 429 bullets and 0 lasers. The projectile model reported pipeline clearance 1.057.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 12 |
| `observed_bullet_overlap` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 2 |

Contributing factors:

- `fast_mode`: 15
- `playfield_boundary`: 14
- `pool_density_over_1000`: 9

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 731 | nonspell | (376.000, 432.000) | `up_fast` | 429/0 | 1.057/1.057 | 0f/3f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1414 | nonspell | (376.000, 426.191) | `up_right_fast` | 119/0 | -1.553/-1.553 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2222 | nonspell | (255.413, 432.000) | `up_right_fast` | 592/0 | -2.026/-8.243 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4232 | nonspell | (372.747, 432.000) | `down_left` | 321/0 | -1.975/-2.121 | 4f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12376 | nonspell | (376.000, 38.858) | `right_fast` | 208/0 | -2.159/-3.512 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23418 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 1052/0 | -1.767/-1.767 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23951 | 103 幻波「赤眼催眠(マインドブローイング)」 | (178.313, 432.000) | `left_fast` | 1061/0 | -2.511/-2.511 | 5f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30162 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (171.280, 349.711) | `up` | 1007/0 | -7.556/-7.556 | 26f/99f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30649 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (239.035, 432.000) | `up_right` | 1022/0 | -5.018/-5.498 | 8f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31263 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (139.794, 432.000) | `right_fast` | 1027/0 | -6.972/-8.724 | 29f/41f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31644 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (125.935, 417.787) | `down_fast` | 1008/0 | -7.936/-9.673 | 22f/76f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35523 | nonspell | (8.000, 432.000) | `right_fast` | 502/0 | -3.720/-3.720 | 2f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39329 | 111 懶惰「生神停止(マインドストッパー)」 | (253.176, 221.405) | `down_right_fast` | 336/0 | 0.992/-2.986 | 0f/32f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40083 | 111 懶惰「生神停止(マインドストッパー)」 | (183.372, 198.488) | `up_right_fast` | 332/0 | -2.148/-4.033 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42036 | 115 散符「真実の月(インビジブルフルムーン)」 | (231.848, 432.000) | `up_left_fast` | 1195/0 | -1.692/-3.810 | 2f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42638 | 115 散符「真実の月(インビジブルフルムーン)」 | (128.793, 432.000) | `up_fast` | 1087/0 | -3.638/-3.638 | 5f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43369 | 115 散符「真実の月(インビジブルフルムーン)」 | (96.662, 432.000) | `up_right_fast` | 1139/0 | -2.968/-11.058 | 5f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43951 | 115 散符「真実の月(インビジブルフルムーン)」 | (204.379, 432.000) | `up_right_fast` | 889/0 | -1.777/-2.510 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 8250 | 8136 | 5906 | 0 | 2211 | 1115 | 138.148 | 0.224 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 619 | 612 | 225 | 0 | 387 | 107 | 154.380 | 0.214 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 4 | 860 | 854 | 658 | 0 | 190 | 184 | 89.567 | 0.281 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1145 | 1138 | 476 | 0 | 653 | 180 | 109.406 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 4 | 1165 | 1152 | 562 | 0 | 585 | 181 | 67.468 | 0.295 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.813 ms median and 24.257 ms p95.
- The full enemy sensor produced 6506 snapshots; capture read time was `{'median': 7.326799968723208, 'p95': 28.71820004656911, 'max': 69.67739993706346}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 14.0}` frames, and 7 phase-counter discontinuities were excluded; 11350 decisions retained at least one robust-union body (maximum 42); 4396 decisions contained latent contact-disabled geometry (maximum 41), and 5689 contained bounded inactive-slot memory (maximum 41). 303 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 3.934795379638672, 'max': 8.702301025390625}` / `{'median': 0.0, 'p95': 3.9172286987304688, 'max': 4.70754861831665}` / `{'median': 0.0, 'p95': 1.0000152587890625, 'max': 7.300048828125}`.
- The issue-time enemy guard retained 12039 observations, detected 2256 during-plan geometry changes, recertified 2256 decisions, and overrode 45 actions. Read/recertificate timing was `{'median': 1.9031999399885535, 'p95': 3.646800061687827, 'max': 15.845799935050309}` / `{'median': 3.2531500328332186, 'p95': 7.28220003657043, 'max': 20.314699970185757}` ms; 4377 issue captures contained latent bodies (maximum 41), and 5678 contained dormant bodies (maximum 41). Fresh/global transactions preserved 2211/2256 planned actions, relaxed 9 fresh/global empty intersections, inherited 13 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8748 observations (8720 contact enabled, 28 anticipatory, 0 errors). 8748 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8748}`.
- The terminal-threat heuristic covered 12039 decisions with horizon counts `{'0': 66, '10': 11790, '32': 183}`; it reported 0 collision and 28 sub-safety-clearance warnings, and relaxed 39 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 195, '3': 9040, '4': 2104, '5': 700}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 11, '2': 707, '3': 9833, '4': 1017, '5': 471}`.
- Adaptive delay supports were `{'1,2,3': 133, '1,2,3,4': 52, '1,2,3,4,5': 95, '2,3': 352, '2,3,4': 2174, '2,3,4,5': 5063, '2,3,4,5,6': 3562, '3,4': 4, '3,4,5,6': 597, '4,5,6': 7}`; 229 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 36/294.
- Robust viability supplied 11892 available policy queries (0 had new delay support outside the cached policy), constrained 4026 decisions, and exposed 7827 empty queried action sets. Recovery guidance was available/selected on 859/396 empty-kernel queries; distant-kernel guidance was available/selected on 6513/6269. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 144.0, 'p95': 329.84845004941286, 'max': 475.7141999141922}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1848, '1': 1661, '2': 1228, '3': 1389, '4': 1463, '5': 1411, '6': 1446, '7': 1446}`.
- Global-horizon/local-prefix cross-tab covered 7990 decisions: 1 had a winning global state but unsafe selected prefix, 5464 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 11 selected actions were outside the reported winning set. 1714 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1767 unique policies with solve-time statistics `{'median': 117.25250002928078, 'p95': 361.6365999914706, 'max': 508.9804999297485}` and first-observed ages `{'median': 2.0, 'p95': 8.0, 'max': 1798.0}`. Policy status counts were `{'pending_future_epoch': 66, 'queryable': 11889, 'expired': 21}`; 84 robust-mode decisions had no query.
- Of 6318 unambiguous output transitions, 5677 (0.899) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 18}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[3, 4, 12, 13, 4, 9, 9, 99, 16, 41, 76, 10, 32, 9, 7, 9, 12, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.355 during the 60 frames preceding a hit versus 0.207 outside those windows.
- Mean selected control-reserve deficit was 8.314 during the 60 frames preceding a hit versus 4.783 outside those windows.
- Soft recovery was selected on 0.005 of alive decisions in the 60-frame pre-hit windows versus 0.031 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
