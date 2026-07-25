# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260725_171023

## Scope And Integrity

- Valid practice scope: `1..40575` (7956 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 14, at `[2279, 4207, 10983, 12786, 14014, 14636, 23565, 25064, 30502, 34903, 35525, 36625, 38537, 39467]`.
- Hard no-Bomb verification: **PASS** across 7956 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2279-T1`. It occurred during a nonspell phase at player (12.950, 432.000), with 577 bullets and 0 lasers. The projectile model reported pipeline clearance -2.117.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 11
- `fast_mode`: 9
- `pool_density_over_1000`: 4
- `action_lag_over_model`: 1
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2279 | nonspell | (12.950, 432.000) | `up_fast` | 577/0 | -2.117/-2.117 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4207 | nonspell | (376.000, 432.000) | `up_fast` | 363/0 | -5.280/-5.280 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10983 | nonspell | (342.485, 432.000) | `right_fast` | 890/0 | -3.605/-3.605 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12786 | nonspell | (8.000, 425.495) | `up_left` | 181/0 | -2.919/-2.919 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14014 | nonspell | (197.812, 427.121) | `down_right_fast` | 511/0 | -5.383/-5.383 | 9f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14636 | nonspell | (41.850, 432.000) | `down_right_fast` | 471/0 | -1.099/-8.475 | 6f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23565 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 1050/0 | -2.233/-3.361 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25064 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `stay` | 1111/0 | -1.524/-1.524 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30502 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (240.055, 432.000) | `left_fast` | 1016/0 | -8.566/-9.240 | 37f/47f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34903 | 111 懶惰「生神停止(マインドストッパー)」 | (8.000, 16.000) | `stay` | 603/0 | -2.128/-30.000 | 0f/80f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35525 | 111 懶惰「生神停止(マインドストッパー)」 | (206.637, 193.996) | `up_fast` | 340/0 | -3.612/-3.612 | 7f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36625 | 111 懶惰「生神停止(マインドストッパー)」 | (175.285, 201.677) | `up_left` | 361/0 | -2.397/-2.397 | 3f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38537 | 115 散符「真実の月(インビジブルフルムーン)」 | (363.060, 432.000) | `up_right` | 972/0 | 0.159/-0.592 | 4f/8f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39467 | 115 散符「真実の月(インビジブルフルムーン)」 | (373.081, 432.000) | `up_fast` | 1300/0 | -1.246/-2.973 | 4f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 5059 | 4955 | 3386 | 0 | 1553 | 845 | 125.679 | 0.218 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 689 | 683 | 364 | 0 | 319 | 154 | 119.212 | 0.311 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 476 | 466 | 300 | 0 | 160 | 117 | 100.872 | 0.334 |
| 111 懶惰「生神停止(マインドストッパー)」 | 3 | 878 | 867 | 259 | 0 | 599 | 157 | 128.201 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 854 | 834 | 470 | 0 | 359 | 172 | 58.686 | 0.290 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 20.348 ms median and 39.152 ms p95.
- The full enemy sensor produced 5398 snapshots; capture read time was `{'median': 17.142899974714965, 'p95': 39.562499965541065, 'max': 82.35060004517436}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 15.0}` frames, and 5 phase-counter discontinuities were excluded; 7404 decisions retained at least one robust-union body (maximum 49); 3042 decisions contained latent contact-disabled geometry (maximum 49), and 4082 contained bounded inactive-slot memory (maximum 46). 281 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.6072845458984375, 'max': 8.879779815673828}` / `{'median': 0.0, 'p95': 4.41996955871582, 'max': 4.70754861831665}` / `{'median': 0.0, 'p95': 1.0, 'max': 5.028127670288086}`.
- The issue-time enemy guard retained 7956 observations, detected 2158 during-plan geometry changes, recertified 2158 decisions, and overrode 845 actions. Read/recertificate timing was `{'median': 1.7899999802466482, 'p95': 3.7834999966435134, 'max': 20.71589999832213}` / `{'median': 8.344250003574416, 'p95': 16.982499975711107, 'max': 26.992300001438707}` ms; 3028 issue captures contained latent bodies (maximum 49), and 4070 contained dormant bodies (maximum 46).
- The synchronous spell-owner guard retained 5541 observations (5519 contact enabled, 22 anticipatory, 0 errors). 5541 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 5541}`.
- The terminal-threat heuristic covered 7956 decisions with horizon counts `{'0': 49, '10': 7792, '32': 115}`; it reported 3 collision and 47 sub-safety-clearance warnings, and relaxed 36 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 52, '3': 440, '4': 5307, '5': 1386, '6': 771}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 92, '3': 732, '4': 6072, '5': 422, '6': 638}`.
- Adaptive delay supports were `{'1,2,3': 17, '1,2,3,4': 1, '2,3': 73, '2,3,4': 21, '2,3,4,5': 565, '2,3,4,5,6': 761, '3,4': 17, '3,4,5': 557, '3,4,5,6': 5739, '4,5,6': 205}`; 1028 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 77/282.
- Robust viability supplied 7805 available policy queries (0 had new delay support outside the cached policy), constrained 2990 decisions, and exposed 4779 empty queried action sets. Recovery guidance was available/selected on 597/277 empty-kernel queries; distant-kernel guidance was available/selected on 3697/3425. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 143.10835055998655, 'p95': 362.7450895601483, 'max': 524.8390229394153}`, and `{'median': 0.0, 'p95': 25.17552661895752, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1156, '1': 1096, '2': 990, '3': 905, '4': 894, '5': 944, '6': 923, '7': 897}`.
- Global-horizon/local-prefix cross-tab covered 4672 decisions: 1 had a winning global state but unsafe selected prefix, 2842 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 11 selected actions were outside the reported winning set. 1674 newer issue-time hazard versions and 1 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1445 unique policies with solve-time statistics `{'median': 114.57059998065233, 'p95': 425.2404000144452, 'max': 544.5443000062369}` and first-observed ages `{'median': 4.0, 'p95': 10.0, 'max': 1795.0}`. Policy status counts were `{'pending_future_epoch': 45, 'queryable': 7802, 'expired': 25}`; 67 robust-mode decisions had no query.
- Of 4395 unambiguous output transitions, 3684 (0.838) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 14}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[6, 4, 12, 8, 13, 13, 10, 0, 47, 80, 10, 12, 8, 12]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.480 during the 60 frames preceding a hit versus 0.210 outside those windows.
- Mean selected control-reserve deficit was 15.324 during the 60 frames preceding a hit versus 5.434 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.036 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
