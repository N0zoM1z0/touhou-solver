# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260726_160712

## Scope And Integrity

- Valid practice scope: `2..44765` (9963 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 13, at `[3795, 4254, 8811, 11835, 12982, 13425, 19412, 19870, 21761, 22407, 38115, 38763, 43488]`.
- Hard no-Bomb verification: **PASS** across 9963 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F3795-T1`. It occurred during a nonspell phase at player (8.000, 425.981), with 437 bullets and 0 lasers. The projectile model reported pipeline clearance -1.440.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 4 |

Contributing factors:

- `playfield_boundary`: 10
- `fast_mode`: 9
- `corridor_deadline_miss`: 2
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3795 | nonspell | (8.000, 425.981) | `up_right` | 437/0 | -1.440/-34.010 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4254 | nonspell | (376.000, 431.127) | `up_right` | 1156/0 | -2.384/-2.384 | 3f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8811 | nonspell | (338.312, 432.000) | `left_fast` | 770/0 | -9.227/-21.609 | 7f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11835 | 57 夢境「二重大結界」 | (8.000, 417.232) | `up_right_fast` | 600/0 | 0.461/-1.787 | 4f/17f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12982 | 57 夢境「二重大結界」 | (11.500, 432.000) | `up_fast` | 603/0 | -1.213/-1.213 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13425 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 619/0 | -1.533/-1.533 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19412 | 61 散霊「夢想封印　寂」 | (58.296, 407.322) | `up_right_fast` | 470/0 | -1.347/-1.347 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19870 | 61 散霊「夢想封印　寂」 | (334.924, 432.000) | `left_fast` | 176/0 | -3.494/-11.258 | 10f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21761 | nonspell | (71.858, 423.515) | `right` | 842/0 | -4.338/-26.180 | 11f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22407 | nonspell | (294.804, 432.000) | `left_fast` | 637/0 | -3.418/-3.418 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38115 | 69 回霊「夢想封印　侘」 | (8.000, 337.334) | `up_fast` | 563/0 | -3.532/-3.532 | 8f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38763 | 69 回霊「夢想封印　侘」 | (8.000, 432.000) | `up_fast` | 678/0 | -4.199/-4.199 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43488 | 73 大結界「博麗弾幕結界」 | (204.830, 369.214) | `up` | 1325/0 | -1.767/-1.767 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 5726 | 5613 | 2992 | 0 | 2534 | 929 | 128.567 | 0.160 |
| 57 夢境「二重大結界」 | 3 | 917 | 906 | 192 | 0 | 699 | 168 | 201.124 | 0.252 |
| 61 散霊「夢想封印　寂」 | 2 | 912 | 904 | 265 | 0 | 619 | 145 | 163.055 | 0.116 |
| 65 | 0 | 655 | 645 | 557 | 0 | 84 | 131 | 61.017 | 0.417 |
| 69 回霊「夢想封印　侘」 | 2 | 934 | 929 | 572 | 0 | 348 | 171 | 117.739 | 0.092 |
| 73 大結界「博麗弾幕結界」 | 1 | 819 | 801 | 412 | 0 | 381 | 159 | 118.472 | 0.018 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 16.732 ms median and 27.923 ms p95.
- The full enemy sensor produced 6079 snapshots; capture read time was `{'median': 20.28739999514073, 'p95': 41.73190001165494, 'max': 72.21549999667332}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 13.0}` frames, and 7 phase-counter discontinuities were excluded; 9698 decisions retained at least one robust-union body (maximum 51); 1954 decisions contained latent contact-disabled geometry (maximum 50), and 5138 contained bounded inactive-slot memory (maximum 46). 245 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 3.0366058349609375, 'p95': 4.94140625, 'max': 8.590206146240234}` / `{'median': 3.0695035457611084, 'p95': 4.748266220092773, 'max': 5.727921009063721}` / `{'median': 0.5220184326171875, 'p95': 4.843800401034421, 'max': 5.938511600233104}`.
- The issue-time enemy guard retained 9963 observations, detected 2944 during-plan geometry changes, recertified 2944 decisions, and overrode 1567 actions. Read/recertificate timing was `{'median': 1.9365000189282, 'p95': 3.9780999650247395, 'max': 18.677900021430105}` / `{'median': 3.324300021631643, 'p95': 7.0035000098869205, 'max': 17.883499967865646}` ms; 1953 issue captures contained latent bodies (maximum 50), and 5135 contained dormant bodies (maximum 46).
- The synchronous spell-owner guard retained 7728 observations (7692 contact enabled, 36 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 7728}`.
- The terminal-threat heuristic covered 9963 decisions with horizon counts `{'0': 44, '10': 9086, '32': 833}`; it reported 19 collision and 137 sub-safety-clearance warnings, and relaxed 143 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 46, '3': 518, '4': 8593, '5': 769, '6': 37}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 52, '3': 3263, '4': 6249, '5': 399}`.
- Adaptive delay supports were `{'1,2,3': 25, '1,2,3,4,5,6': 1, '2,3': 25, '2,3,4': 41, '2,3,4,5': 1283, '2,3,4,5,6': 1129, '3,4': 287, '3,4,5': 1956, '3,4,5,6': 5202, '4,5': 2, '4,5,6': 10, '5,6': 2}`; 1623 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 44/217.
- Robust viability supplied 9798 available policy queries (0 had new delay support outside the cached policy), constrained 4665 decisions, and exposed 4990 empty queried action sets. Recovery guidance was available/selected on 1354/683 empty-kernel queries; distant-kernel guidance was available/selected on 2979/2871. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 7.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 102.44998779892558, 'p95': 289.77232442039735, 'max': 524.8390229394153}`, and `{'median': 0.0, 'p95': 20.7473087310791, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1515, '1': 1347, '2': 1214, '3': 1062, '4': 1235, '5': 1182, '6': 1088, '7': 1155}`.
- Global-horizon/local-prefix cross-tab covered 5857 decisions: 2 had a winning global state but unsafe selected prefix, 2665 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 63 selected actions were outside the reported winning set. 2556 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1703 unique policies with solve-time statistics `{'median': 130.44120004633442, 'p95': 436.68599997181445, 'max': 565.7285000197589}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1802.0}`. Policy status counts were `{'pending_future_epoch': 36, 'queryable': 9798, 'expired': 11}`; 47 robust-mode decisions had no query.
- Of 6058 unambiguous output transitions, 5187 (0.856) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 13}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[6, 9, 13, 17, 7, 4, 0, 16, 19, 6, 16, 6, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.350 during the 60 frames preceding a hit versus 0.161 outside those windows.
- Mean selected control-reserve deficit was 13.764 during the 60 frames preceding a hit versus 6.512 outside those windows.
- Soft recovery was selected on 0.085 of alive decisions in the 60-frame pre-hit windows versus 0.071 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
