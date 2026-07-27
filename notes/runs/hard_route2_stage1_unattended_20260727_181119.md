# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260727_181119

## Scope And Integrity

- Valid practice scope: `2..20911` (7686 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 1, at `[2043]`.
- Hard no-Bomb verification: **PASS** across 7686 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S0-F2043-T1`. It occurred during a nonspell phase at player (376.000, 23.812), with 144 bullets and 0 lasers. The projectile model reported pipeline clearance -1.257.

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
| canonical | 2043 | nonspell | (376.000, 23.812) | `down` | 144/0 | -1.257/-1.257 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 1 | 4565 | 4462 | 678 | 0 | 3746 | 539 | 165.815 | 0.093 |
| 0 | 0 | 1038 | 1031 | 469 | 0 | 556 | 123 | 57.648 | 0.171 |
| 4 | 0 | 956 | 943 | 193 | 0 | 749 | 114 | 67.939 | 0.078 |
| 8 | 0 | 1127 | 1116 | 141 | 0 | 962 | 136 | 90.923 | 0.080 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.658 ms median and 17.443 ms p95.
- The full enemy sensor produced 3606 snapshots; capture read time was `{'median': 5.873599991900846, 'p95': 23.316500009968877, 'max': 34.83369998866692}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 8.0}` frames, and 3 phase-counter discontinuities were excluded; 7441 decisions retained at least one robust-union body (maximum 25); 1159 decisions contained latent contact-disabled geometry (maximum 10), and 3811 contained bounded inactive-slot memory (maximum 17). 3 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 0.0, 'max': 0.646728515625}` / `{'median': 0.0, 'p95': 0.0, 'max': 0.6467156410217285}` / `{'median': 0.0, 'p95': 0.0, 'max': 1.2874603271484375e-05}`.
- The issue-time enemy guard retained 7686 observations, detected 513 during-plan geometry changes, recertified 513 decisions, and overrode 0 actions. Read/recertificate timing was `{'median': 1.7587500042282045, 'p95': 3.644999989774078, 'max': 11.666500009596348}` / `{'median': 1.712600002065301, 'p95': 3.1030999962240458, 'max': 10.070300020743161}` ms; 1167 issue captures contained latent bodies (maximum 10), and 3805 contained dormant bodies (maximum 17). Fresh/global transactions preserved 513/513 planned actions, relaxed 0 fresh/global empty intersections, inherited 3 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 5633 observations (5563 contact enabled, 70 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 5633}`.
- The terminal-threat heuristic covered 7686 decisions with horizon counts `{'0': 76, '10': 7153, '32': 457}`; it reported 0 collision and 32 sub-safety-clearance warnings, and relaxed 58 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 4454, '3': 3232}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 12, '2': 7669, '3': 5}`.
- Adaptive delay supports were `{'1,2': 32, '1,2,3': 67, '1,2,3,4': 227, '1,2,3,4,5': 38, '2': 42, '2,3': 2077, '2,3,4': 4136, '2,3,4,5': 619, '2,3,4,5,6': 447, '3,4': 1}`; 1 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 21/102.
- Robust viability supplied 7552 available policy queries (0 had new delay support outside the cached policy), constrained 6013 decisions, and exposed 1481 empty queried action sets. Recovery guidance was available/selected on 541/290 empty-kernel queries; distant-kernel guidance was available/selected on 903/899. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 11.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 71.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 81.58431221748455, 'p95': 208.61447696648477, 'max': 395.8181400592954}`, and `{'median': 0.0, 'p95': 16.0, 'max': 37.10000014305115}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1167, '1': 901, '2': 866, '3': 933, '4': 896, '5': 910, '6': 946, '7': 933}`.
- Global-horizon/local-prefix cross-tab covered 6693 decisions: 1 had a winning global state but unsafe selected prefix, 1222 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 42 selected actions were outside the reported winning set. 480 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 912 unique policies with solve-time statistics `{'median': 115.74509998899885, 'p95': 296.7850000131875, 'max': 419.71749998629093}` and first-observed ages `{'median': 2.0, 'p95': 3.0, 'max': 1786.0}`. Policy status counts were `{'pending_future_epoch': 79, 'queryable': 7551, 'expired': 14}`; 92 robust-mode decisions had no query.
- Of 3082 unambiguous output transitions, 2845 (0.923) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 1 hit windows with a positive warning lead; those leads were `[4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.000 during the 60 frames preceding a hit versus 0.100 outside those windows.
- Mean selected control-reserve deficit was 11.013 during the 60 frames preceding a hit versus 2.808 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.038 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
