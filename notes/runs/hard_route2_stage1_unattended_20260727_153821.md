# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260727_153821

## Scope And Integrity

- Valid practice scope: `2..20950` (7574 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 1, at `[2651]`.
- Hard no-Bomb verification: **PASS** across 7574 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S0-F2651-T1`. It occurred during a nonspell phase at player (124.965, 19.253), with 42 bullets and 0 lasers. The projectile model reported pipeline clearance -19.248.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 1 |

Contributing factors:

- `fast_mode`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2651 | nonspell | (124.965, 19.253) | `right_fast` | 42/0 | -19.248/-19.248 | 2f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 1 | 4466 | 4368 | 714 | 0 | 3631 | 535 | 164.937 | 0.091 |
| 0 | 0 | 1058 | 1050 | 236 | 0 | 806 | 126 | 58.664 | 0.144 |
| 4 | 0 | 946 | 937 | 243 | 0 | 692 | 114 | 72.121 | 0.105 |
| 8 | 0 | 1104 | 1096 | 175 | 0 | 897 | 136 | 94.790 | 0.086 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.943 ms median and 17.892 ms p95.
- The full enemy sensor produced 3596 snapshots; capture read time was `{'median': 6.102349987486377, 'p95': 25.13109997380525, 'max': 36.03230003500357}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 9.0}` frames, and 3 phase-counter discontinuities were excluded; 7341 decisions retained at least one robust-union body (maximum 32); 1218 decisions contained latent contact-disabled geometry (maximum 11), and 3900 contained bounded inactive-slot memory (maximum 16). 28 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 3.6934967041015625, 'p95': 3.699676513671875, 'max': 3.99456787109375}` / `{'median': 3.690148949623108, 'p95': 3.6988368034362793, 'max': 3.699995279312134}` / `{'median': 9.328126907348633e-06, 'p95': 7.393682241439819, 'max': 7.399992227554321}`.
- The issue-time enemy guard retained 7574 observations, detected 539 during-plan geometry changes, recertified 539 decisions, and overrode 7 actions. Read/recertificate timing was `{'median': 1.763649983331561, 'p95': 3.7043000338599086, 'max': 18.20729998871684}` / `{'median': 1.8648000550456345, 'p95': 3.91740002669394, 'max': 11.816500045824796}` ms; 1223 issue captures contained latent bodies (maximum 11), and 3898 contained dormant bodies (maximum 16). Fresh/global transactions preserved 532/539 planned actions, relaxed 0 fresh/global empty intersections, inherited 1 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 5592 observations (5522 contact enabled, 70 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3881, '0x00587A90': 1711}`.
- The terminal-threat heuristic covered 7574 decisions with horizon counts `{'0': 71, '10': 7053, '32': 450}`; it reported 0 collision and 25 sub-safety-clearance warnings, and relaxed 57 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 3658, '3': 3916}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 14, '2': 7044, '3': 516}`.
- Adaptive delay supports were `{'1,2,3': 373, '1,2,3,4': 64, '1,2,3,4,5': 85, '1,2,3,4,5,6': 39, '2,3': 1551, '2,3,4': 4206, '2,3,4,5': 684, '2,3,4,5,6': 572}`; 8 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 30/173.
- Robust viability supplied 7451 available policy queries (0 had new delay support outside the cached policy), constrained 6026 decisions, and exposed 1368 empty queried action sets. Recovery guidance was available/selected on 556/254 empty-kernel queries; distant-kernel guidance was available/selected on 771/767. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 12.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 76.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 80.0, 'p95': 256.4995126701024, 'max': 466.47615158762403}`, and `{'median': 0.0, 'p95': 16.0, 'max': 27.338982820510864}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1185, '1': 879, '2': 867, '3': 898, '4': 903, '5': 890, '6': 949, '7': 880}`.
- Global-horizon/local-prefix cross-tab covered 6609 decisions: 0 had a winning global state but unsafe selected prefix, 1110 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 41 selected actions were outside the reported winning set. 473 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 911 unique policies with solve-time statistics `{'median': 118.2676000171341, 'p95': 306.32480001077056, 'max': 401.23070002300665}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1793.0}`. Policy status counts were `{'pending_future_epoch': 72, 'queryable': 7453, 'expired': 13}`; 87 robust-mode decisions had no query.
- Of 3067 unambiguous output transitions, 2807 (0.915) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 1 hit windows with a positive warning lead; those leads were `[8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.000 during the 60 frames preceding a hit versus 0.100 outside those windows.
- Mean selected control-reserve deficit was 7.977 during the 60 frames preceding a hit versus 3.006 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.033 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 10.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
