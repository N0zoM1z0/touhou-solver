# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260726_151821

## Scope And Integrity

- Valid practice scope: `2..44614` (10080 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 19, at `[4177, 9428, 9998, 12279, 12749, 13287, 20874, 22069, 28680, 29580, 30009, 30598, 31015, 33849, 34320, 36121, 37325, 42197, 44107]`.
- Hard no-Bomb verification: **PASS** across 10080 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F4177-T1`. It occurred during a nonspell phase at player (356.979, 432.000), with 957 bullets and 0 lasers. The projectile model reported pipeline clearance -2.318.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 3 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 18
- `playfield_boundary`: 14
- `corridor_deadline_miss`: 6
- `pool_density_over_1000`: 6

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4177 | nonspell | (356.979, 432.000) | `up_left_fast` | 957/0 | -2.318/-15.194 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9428 | nonspell | (137.654, 432.000) | `right_fast` | 299/0 | 1.169/-6.525 | 6f/15f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9998 | nonspell | (157.588, 417.921) | `right_fast` | 160/0 | -27.851/-35.235 | 13f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12279 | 57 夢境「二重大結界」 | (8.000, 413.358) | `right_fast` | 592/0 | -0.146/-2.457 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12749 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 580/0 | -1.468/-1.468 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13287 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 606/0 | -1.807/-1.807 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20874 | nonspell | (8.000, 432.000) | `up_fast` | 239/0 | 1.741/-3.358 | 3f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22069 | nonspell | (376.000, 317.792) | `up_right_fast` | 425/0 | -1.355/-1.355 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28680 | nonspell | (13.657, 371.632) | `down_right_fast` | 165/0 | -0.065/-1.726 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29580 | 65 神技「八方龍殺陣」 | (258.040, 432.000) | `left_fast` | 1275/0 | 0.301/0.301 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30009 | 65 神技「八方龍殺陣」 | (227.236, 432.000) | `up` | 1081/0 | -1.272/-2.824 | 0f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30598 | 65 神技「八方龍殺陣」 | (39.113, 432.000) | `down_right_fast` | 1130/0 | -1.989/-32.473 | 16f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31015 | 65 神技「八方龍殺陣」 | (98.757, 404.000) | `right_fast` | 1095/0 | 0.138/-3.033 | 4f/4f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33849 | nonspell | (131.167, 432.000) | `up_right_fast` | 114/0 | -1.772/-1.772 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34320 | nonspell | (376.000, 432.000) | `up_fast` | 128/0 | -14.861/-14.861 | 8f/15f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36121 | nonspell | (376.000, 432.000) | `right_fast` | 104/0 | -5.573/-5.573 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37325 | 69 回霊「夢想封印　侘」 | (376.000, 420.740) | `up_left_fast` | 394/0 | -1.351/-1.351 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42197 | 73 大結界「博麗弾幕結界」 | (220.741, 388.672) | `up_fast` | 1000/0 | -2.102/-2.102 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44107 | 73 大結界「博麗弾幕結界」 | (227.739, 400.039) | `left_fast` | 1339/0 | 0.382/0.382 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 5612 | 5492 | 2616 | 0 | 2839 | 882 | 141.465 | 0.160 |
| 57 夢境「二重大結界」 | 3 | 935 | 926 | 227 | 0 | 689 | 167 | 199.999 | 0.231 |
| 61 | 0 | 908 | 902 | 247 | 0 | 638 | 156 | 143.489 | 0.095 |
| 65 神技「八方龍殺陣」 | 4 | 814 | 804 | 651 | 0 | 152 | 153 | 65.073 | 0.285 |
| 69 回霊「夢想封印　侘」 | 1 | 922 | 916 | 529 | 0 | 379 | 168 | 102.616 | 0.099 |
| 73 大結界「博麗弾幕結界」 | 2 | 889 | 871 | 430 | 0 | 431 | 163 | 114.197 | 0.101 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.031 ms median and 30.699 ms p95.
- The full enemy sensor produced 6077 snapshots; capture read time was `{'median': 18.334400025196373, 'p95': 36.5804000175558, 'max': 65.65730000147596}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 12.0}` frames, and 5 phase-counter discontinuities were excluded; 9754 decisions retained at least one robust-union body (maximum 46); 1868 decisions contained latent contact-disabled geometry (maximum 45), and 4891 contained bounded inactive-slot memory (maximum 38). 300 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.9988250732421875, 'p95': 3.1982803344726562, 'max': 10.3087158203125}` / `{'median': 1.9993409514427185, 'p95': 3.1987783908843994, 'max': 128.14285278320312}` / `{'median': 0.004653364419937134, 'p95': 1.9876430034637451, 'max': 128.14285278320312}`.
- The issue-time enemy guard retained 10080 observations, detected 2882 during-plan geometry changes, recertified 2882 decisions, and overrode 1519 actions. Read/recertificate timing was `{'median': 1.8348000012338161, 'p95': 3.918499976862222, 'max': 19.858600047882646}` / `{'median': 3.726899973116815, 'p95': 8.154899987857789, 'max': 15.653799986466765}` ms; 1868 issue captures contained latent bodies (maximum 45), and 4875 contained dormant bodies (maximum 38).
- The synchronous spell-owner guard retained 7833 observations (7799 contact enabled, 34 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 7833}`.
- The terminal-threat heuristic covered 10080 decisions with horizon counts `{'0': 49, '10': 9318, '32': 713}`; it reported 18 collision and 103 sub-safety-clearance warnings, and relaxed 83 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 51, '3': 884, '4': 8485, '5': 660}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 56, '3': 2256, '4': 7768}`.
- Adaptive delay supports were `{'1,2,3': 29, '1,2,3,4': 26, '2,3': 32, '2,3,4': 255, '2,3,4,5': 697, '2,3,4,5,6': 1661, '3,4': 240, '3,4,5': 1290, '3,4,5,6': 5847, '4,5,6': 3}`; 1563 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 57/341.
- Robust viability supplied 9911 available policy queries (0 had new delay support outside the cached policy), constrained 5128 decisions, and exposed 4700 empty queried action sets. Recovery guidance was available/selected on 1297/740 empty-kernel queries; distant-kernel guidance was available/selected on 2862/2756. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 14.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 115.37764081484765, 'p95': 317.5909318604673, 'max': 486.6210024238576}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1564, '1': 1323, '2': 1148, '3': 1166, '4': 1261, '5': 1113, '6': 1178, '7': 1158}`.
- Global-horizon/local-prefix cross-tab covered 5561 decisions: 2 had a winning global state but unsafe selected prefix, 2225 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 41 selected actions were outside the reported winning set. 2336 newer issue-time hazard versions and 1 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1689 unique policies with solve-time statistics `{'median': 133.75519996043295, 'p95': 436.2043000292033, 'max': 558.313800022006}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1798.0}`. Policy status counts were `{'pending_future_epoch': 42, 'queryable': 9912, 'expired': 14}`; 57 robust-mode decisions had no query.
- Of 5822 unambiguous output transitions, 5014 (0.861) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 19}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[7, 15, 19, 3, 7, 6, 16, 7, 5, 6, 21, 24, 4, 6, 15, 11, 6, 10, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.427 during the 60 frames preceding a hit versus 0.143 outside those windows.
- Mean selected control-reserve deficit was 10.652 during the 60 frames preceding a hit versus 6.781 outside those windows.
- Soft recovery was selected on 0.085 of alive decisions in the 60-frame pre-hit windows versus 0.072 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
