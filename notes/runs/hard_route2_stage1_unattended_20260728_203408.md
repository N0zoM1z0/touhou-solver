# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260728_203408

## Scope And Integrity

- Valid practice scope: `1..20950` (7755 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 1, at `[2520]`.
- Hard no-Bomb verification: **PASS** across 7755 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S0-F2520-T1`. It occurred during a nonspell phase at player (373.118, 432.000), with 76 bullets and 0 lasers. The projectile model reported pipeline clearance -0.992.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 1 |

Contributing factors:

- `corridor_deadline_miss`: 1
- `playfield_boundary`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2520 | nonspell | (373.118, 432.000) | `stay` | 76/0 | -0.992/-0.992 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 1 | 4612 | 4509 | 571 | 0 | 3921 | 538 | 142.923 | 0.088 |
| 0 | 0 | 1067 | 1059 | 257 | 0 | 781 | 127 | 58.391 | 0.178 |
| 4 | 0 | 958 | 944 | 154 | 0 | 779 | 114 | 73.595 | 0.069 |
| 8 | 0 | 1118 | 1110 | 186 | 0 | 911 | 137 | 89.427 | 0.141 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.476 ms median and 16.652 ms p95.
- The full enemy sensor produced 3640 snapshots; capture read time was `{'median': 5.665350006893277, 'p95': 23.05519999936223, 'max': 43.71210001409054}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 8.0}` frames, and 3 phase-counter discontinuities were excluded; 7510 decisions retained at least one robust-union body (maximum 22); 1224 decisions contained latent contact-disabled geometry (maximum 12), and 3897 contained bounded inactive-slot memory (maximum 14). 18 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.8155755996704102, 'p95': 4.04949951171875, 'max': 4.402656555175781}` / `{'median': 1.8155757188796997, 'p95': 3.3494935035705566, 'max': 4.402656555175781}` / `{'median': 1.6093254089355469e-06, 'p95': 0.7000083923339844, 'max': 1.2934327125549316}`.
- The issue-time enemy guard retained 7755 observations, detected 534 during-plan geometry changes, recertified 534 decisions, and overrode 0 actions. Read/recertificate timing was `{'median': 1.7203999450430274, 'p95': 3.527799970470369, 'max': 19.21530009713024}` / `{'median': 1.6856499714776874, 'p95': 3.0820000683888793, 'max': 5.8370999759063125}` ms; 1219 issue captures contained latent bodies (maximum 12), and 3896 contained dormant bodies (maximum 14). Fresh/global transactions preserved 534/534 planned actions, relaxed 0 fresh/global empty intersections, inherited 2 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 5680 observations (5606 contact enabled, 74 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 5680}`.
- The terminal-threat heuristic covered 7755 decisions with horizon counts `{'0': 75, '10': 7268, '32': 412}`; it reported 3 collision and 45 sub-safety-clearance warnings, and relaxed 62 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 5319, '3': 2436}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 14, '2': 7505, '3': 236}`.
- Adaptive delay supports were `{'1,2': 39, '1,2,3': 92, '1,2,3,4': 409, '1,2,3,4,5,6': 5, '2': 62, '2,3': 2006, '2,3,4': 3818, '2,3,4,5': 906, '2,3,4,5,6': 403, '3,4': 15}`; 4 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 25/142.
- Robust viability supplied 7622 available policy queries (0 had new delay support outside the cached policy), constrained 6392 decisions, and exposed 1168 empty queried action sets. Recovery guidance was available/selected on 423/232 empty-kernel queries; distant-kernel guidance was available/selected on 676/664. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 11.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 72.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 112.0, 'p95': 272.0, 'max': 393.547964039963}`, and `{'median': 0.0, 'p95': 16.0, 'max': 36.7473087310791}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1162, '1': 878, '2': 913, '3': 917, '4': 928, '5': 944, '6': 956, '7': 924}`.
- Global-horizon/local-prefix cross-tab covered 6783 decisions: 1 had a winning global state but unsafe selected prefix, 992 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 36 selected actions were outside the reported winning set. 452 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 916 unique policies with solve-time statistics `{'median': 106.12674994627014, 'p95': 295.808200025931, 'max': 389.4805000163615}` and first-observed ages `{'median': 1.0, 'p95': 3.0, 'max': 1794.0}`. Policy status counts were `{'pending_future_epoch': 77, 'queryable': 7621, 'expired': 13}`; 89 robust-mode decisions had no query.
- Of 2978 unambiguous output transitions, 2762 (0.927) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 1 hit windows with a positive warning lead; those leads were `[5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.214 during the 60 frames preceding a hit versus 0.106 outside those windows.
- Mean selected control-reserve deficit was 8.615 during the 60 frames preceding a hit versus 2.601 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.031 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
