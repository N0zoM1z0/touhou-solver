# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_230314

## Scope And Integrity

- Valid practice scope: `4..20972` (4909 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **NO**.
- Native hit edges: 11, at `[1231, 1704, 4169, 4500, 9409, 9986, 11950, 12636, 13319, 13849, 20151]`.
- Hard no-Bomb verification: **PASS** across 4909 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1231-T1`. It occurred during a nonspell phase at player (34.299, 432.000), with 246 bullets and 0 lasers. The projectile model reported pipeline clearance 1.520.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 11
- `fast_mode`: 8
- `corridor_deadline_miss`: 2
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1231 | nonspell | (34.299, 432.000) | `up_left` | 246/0 | 1.520/-4.124 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1704 | nonspell | (8.000, 426.822) | `stay` | 517/0 | -0.977/-0.977 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4169 | nonspell | (8.000, 409.568) | `down_right_fast` | 1053/0 | -2.004/-7.738 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4500 | nonspell | (8.000, 428.306) | `down_left` | 878/0 | -2.635/-2.635 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9409 | nonspell | (20.000, 432.000) | `right_fast` | 324/0 | -2.500/-2.500 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9986 | nonspell | (68.907, 432.000) | `up_right_fast` | 177/0 | -13.959/-13.959 | 7f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11950 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 635/0 | -1.456/-1.456 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12636 | 57 夢境「二重大結界」 | (57.334, 432.000) | `right_fast` | 602/0 | -3.142/-3.142 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13319 | 57 夢境「二重大結界」 | (8.000, 432.000) | `right_fast` | 607/0 | -3.385/-3.385 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13849 | 57 夢境「二重大結界」 | (354.878, 432.000) | `up_left_fast` | 596/0 | 0.876/-3.108 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20151 | 61 散霊「夢想封印　寂」 | (354.511, 431.418) | `up_right_fast` | 364/0 | -3.631/-11.081 | 9f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 3206 | 3136 | 1300 | 0 | 1785 | 536 | 103.143 | 0.153 |
| 57 夢境「二重大結界」 | 4 | 947 | 938 | 138 | 0 | 778 | 169 | 196.462 | 0.289 |
| 61 散霊「夢想封印　寂」 | 1 | 756 | 748 | 196 | 0 | 546 | 131 | 152.058 | 0.095 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.787 ms median and 33.686 ms p95.
- The full enemy sensor produced 2961 snapshots; capture read time was `{'median': 20.583100005751476, 'p95': 40.934499993454665, 'max': 71.9667999946978}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 3 phase-counter discontinuities were excluded; 4607 decisions retained at least one robust-union body (maximum 52); 1248 decisions contained latent contact-disabled geometry (maximum 52), and 2464 contained bounded inactive-slot memory (maximum 48). 200 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 3.0055588483810425, 'p95': 4.5374704996744795, 'max': 5.887451171875}` / `{'median': 3.0334203243255615, 'p95': 3.9908790588378906, 'max': 13.526081085205078}` / `{'median': 0.08855884326131719, 'p95': 3.9778714179992676, 'max': 13.526081085205078}`.
- The issue-time enemy guard retained 4909 observations, detected 1125 during-plan geometry changes, recertified 1125 decisions, and overrode 544 actions. Read/recertificate timing was `{'median': 1.8604999931994826, 'p95': 3.902399999788031, 'max': 13.76549998531118}` / `{'median': 6.7995999997947365, 'p95': 12.668699986534193, 'max': 20.68320001126267}` ms; 1247 issue captures contained latent bodies (maximum 52), and 2460 contained dormant bodies (maximum 48).
- The synchronous spell-owner guard retained 1703 observations (1703 contact enabled, 0 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 1703}`.
- The terminal-threat heuristic covered 4909 decisions with horizon counts `{'0': 47, '10': 4371, '32': 491}`; it reported 7 collision and 69 sub-safety-clearance warnings, and relaxed 79 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 41, '3': 351, '4': 4485, '5': 32}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 81, '3': 1137, '4': 3691}`.
- Adaptive delay supports were `{'1,2,3,4,5': 78, '1,2,3,4,5,6': 39, '2,3': 2, '2,3,4': 125, '2,3,4,5': 232, '2,3,4,5,6': 474, '3,4': 84, '3,4,5': 582, '3,4,5,6': 3283, '4,5,6': 10}`; 570 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 53/264.
- Robust viability supplied 4822 available policy queries (0 had new delay support outside the cached policy), constrained 3109 decisions, and exposed 1634 empty queried action sets. Recovery guidance was available/selected on 488/307 empty-kernel queries; distant-kernel guidance was available/selected on 1018/964. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 7.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 38.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 143.10835055998655, 'p95': 337.5203697556638, 'max': 436.7150100465978}`, and `{'median': 0.0, 'p95': 25.097910404205322, 'max': 47.634671211242676}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 744, '1': 705, '2': 570, '3': 537, '4': 579, '5': 595, '6': 540, '7': 552}`.
- Global-horizon/local-prefix cross-tab covered 2826 decisions: 2 had a winning global state but unsafe selected prefix, 821 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 39 selected actions were outside the reported winning set. 848 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 836 unique policies with solve-time statistics `{'median': 131.7039499990642, 'p95': 406.50519999326207, 'max': 530.935299990233}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1794.0}`. Policy status counts were `{'pending_future_epoch': 35, 'queryable': 4821, 'expired': 14}`; 48 robust-mode decisions had no query.
- Of 2835 unambiguous output transitions, 2342 (0.826) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 11}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 11 hit windows with a positive warning lead; those leads were `[7, 4, 11, 5, 7, 18, 7, 6, 3, 9, 12]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.440 during the 60 frames preceding a hit versus 0.150 outside those windows.
- Mean selected control-reserve deficit was 9.119 during the 60 frames preceding a hit versus 1.123 outside those windows.
- Soft recovery was selected on 0.071 of alive decisions in the 60-frame pre-hit windows versus 0.062 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
